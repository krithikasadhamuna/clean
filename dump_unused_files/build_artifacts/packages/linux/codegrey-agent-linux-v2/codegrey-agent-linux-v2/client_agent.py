"""
Main log forwarding client agent
"""

import asyncio
import logging
import platform
import signal
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import json

from shared.config import config
from shared.models import LogBatch, AgentInfo
from shared.utils import setup_logging, get_system_info, compress_data, retry_async

from .forwarders.windows_forwarder import WindowsLogForwarder
from .forwarders.linux_forwarder import LinuxLogForwarder
from .forwarders.application_forwarder import ApplicationLogForwarder
from .forwarders.ebpf_forwarder import EBPFLogForwarder
from .command_executor import CommandExecutionEngine
from .container_attack_executor import ContainerAttackExecutor


logger = logging.getLogger(__name__)


class LogForwardingClient:
    """Main log forwarding client"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Load configuration
        if config_file:
            config.client_config_file = config_file
        
        self.client_config = config.load_client_config()
        
        # Agent identification
        self.agent_id = self._generate_agent_id()
        self.agent_info = self._create_agent_info()
        
        # Server connection
        self.server_endpoint = self.client_config.get('client', {}).get('server_endpoint')
        self.api_key = self.client_config.get('client', {}).get('api_key')
        self.reconnect_interval = self.client_config.get('client', {}).get('reconnect_interval', 30)
        
        # Log forwarding settings
        self.batch_size = self.client_config.get('log_forwarding', {}).get('batch_size', 100)
        self.flush_interval = self.client_config.get('log_forwarding', {}).get('flush_interval', 5)
        self.compression_enabled = self.client_config.get('log_forwarding', {}).get('compression', True)
        
        # State
        self.running = False
        self.connected = False
        self.log_buffer = []
        self.last_heartbeat = None
        
        # Statistics
        self.stats = {
            'logs_sent': 0,
            'bytes_sent': 0,
            'batches_sent': 0,
            'connection_errors': 0,
            'start_time': None
        }
        
        # Initialize forwarders
        self.forwarders = self._initialize_forwarders()
        
        # Command execution engine
        self.command_executor = CommandExecutionEngine(
            self.agent_id, 
            self.server_endpoint, 
            self.api_key
        ) if self.client_config.get('command_execution', {}).get('enabled', True) else None
        
        # Container attack executor
        self.container_executor = ContainerAttackExecutor(
            self.agent_id,
            self.server_endpoint,
            self.client_config
        ) if self.client_config.get('containers', {}).get('enabled', True) else None
        
        # HTTP session
        self.session = None
    
    def _generate_agent_id(self) -> str:
        """Generate unique agent ID"""
        configured_id = self.client_config.get('client', {}).get('agent_id')
        
        if configured_id and configured_id != 'auto':
            return configured_id
        
        # Auto-generate based on system info
        import uuid
        system_info = get_system_info()
        hostname = system_info.get('hostname', 'unknown')
        mac_address = system_info.get('mac_address', str(uuid.uuid4()))
        
        # Create deterministic ID based on hostname and MAC
        agent_id = f"{hostname}_{mac_address.replace(':', '')[:8]}"
        return agent_id
    
    def _create_agent_info(self) -> AgentInfo:
        """Create agent information"""
        system_info = get_system_info()
        
        agent_info = AgentInfo()
        agent_info.id = self.agent_id
        agent_info.hostname = system_info.get('hostname', 'unknown')
        agent_info.ip_address = system_info.get('ip_address', 'unknown')
        agent_info.platform = system_info.get('platform', 'unknown')
        agent_info.os_version = system_info.get('platform_version', 'unknown')
        agent_info.agent_version = "1.0.0"
        
        # Set capabilities based on platform
        capabilities = ['log_forwarding']
        if platform.system() == "Windows":
            capabilities.extend(['windows_events', 'wmi_monitoring'])
        elif platform.system() == "Linux":
            capabilities.extend(['syslog_monitoring', 'auditd_monitoring', 'systemd_journal'])
        
        agent_info.capabilities = capabilities
        
        # Set log sources
        log_sources = []
        if self.client_config.get('log_sources', {}).get('system_logs', {}).get('enabled'):
            log_sources.append('system_logs')
        if self.client_config.get('log_sources', {}).get('security_logs', {}).get('enabled'):
            log_sources.append('security_logs')
        if self.client_config.get('log_sources', {}).get('application_logs', {}).get('enabled'):
            log_sources.append('application_logs')
        if self.client_config.get('log_sources', {}).get('attack_logs', {}).get('enabled'):
            log_sources.append('attack_logs')
        
        agent_info.log_sources = log_sources
        agent_info.configuration = self.client_config
        
        return agent_info
    
    def _initialize_forwarders(self) -> List:
        """Initialize log forwarders based on platform and configuration"""
        forwarders = []
        
        # Platform-specific forwarders
        if platform.system() == "Windows":
            if self.client_config.get('log_sources', {}).get('system_logs', {}).get('enabled', True):
                forwarders.append(WindowsLogForwarder(self.agent_id, self.client_config))
        
        elif platform.system() == "Linux":
            if self.client_config.get('log_sources', {}).get('system_logs', {}).get('enabled', True):
                forwarders.append(LinuxLogForwarder(self.agent_id, self.client_config))
                
                # Add eBPF forwarder if enabled
                if self.client_config.get('ebpf', {}).get('enabled', False):
                    forwarders.append(EBPFLogForwarder(self.agent_id, self.client_config))
        
        # Application log forwarder (always enabled)
        if self.client_config.get('log_sources', {}).get('application_logs', {}).get('enabled', True):
            forwarders.append(ApplicationLogForwarder(self.agent_id, self.client_config))
        
        logger.info(f"Initialized {len(forwarders)} log forwarders")
        return forwarders
    
    async def start(self) -> None:
        """Start the log forwarding client"""
        if self.running:
            return
        
        logger.info(f"Starting Log Forwarding Client (Agent ID: {self.agent_id})")
        self.running = True
        self.stats['start_time'] = datetime.utcnow()
        
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=10)
        self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        
        # Register with server
        await self._register_agent()
        
        # Start main tasks
        tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._log_forwarding_loop()),
            asyncio.create_task(self._batch_sender_loop()),
        ]
        
        # Start forwarder tasks
        for forwarder in self.forwarders:
            task = asyncio.create_task(self._run_forwarder(forwarder))
            tasks.append(task)
        
        # Start command execution engine if enabled
        if self.command_executor:
            command_task = asyncio.create_task(self.command_executor.start())
            tasks.append(command_task)
        
        # Start container executor if enabled
        if self.container_executor:
            container_task = asyncio.create_task(self.container_executor.start())
            tasks.append(container_task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in client main loop: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the log forwarding client"""
        logger.info("Stopping Log Forwarding Client")
        self.running = False
        
        # Stop all forwarders
        for forwarder in self.forwarders:
            try:
                if hasattr(forwarder, 'stop') and callable(forwarder.stop):
                    if asyncio.iscoroutinefunction(forwarder.stop):
                        await forwarder.stop()
                    else:
                        forwarder.stop()
            except Exception as e:
                logger.error(f"Error stopping {forwarder.__class__.__name__}: {e}")
        
        # Stop command executor
        if self.command_executor:
            await self.command_executor.stop()
        
        # Stop container executor
        if self.container_executor:
            await self.container_executor.stop()
        
        # Send final batch
        if self.log_buffer:
            await self._send_log_batch()
        
        # Close HTTP session
        if self.session:
            await self.session.close()
    
    async def _register_agent(self) -> None:
        """Register agent with server"""
        logger.info("Registering agent with server")
        
        try:
            await retry_async(self._do_register_agent, max_retries=5, delay=2.0)
            logger.info("Successfully registered with server")
        except Exception as e:
            logger.error(f"Failed to register with server: {e}")
    
    async def _do_register_agent(self) -> None:
        """Perform agent registration"""
        if not self.session:
            raise Exception("HTTP session not available")
        
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        async with self.session.post(
            f"{self.server_endpoint}/api/agents/register",
            json=self.agent_info.to_dict(),
            headers=headers
        ) as response:
            if response.status == 200:
                self.connected = True
                result = await response.json()
                logger.info(f"Agent registered: {result}")
            else:
                error_text = await response.text()
                raise Exception(f"Registration failed: {response.status} - {error_text}")
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to server"""
        heartbeat_interval = self.client_config.get('client', {}).get('heartbeat_interval', 60)
        
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(heartbeat_interval)
    
    async def _send_heartbeat(self) -> None:
        """Send heartbeat to server"""
        if not self.session or not self.connected:
            return
        
        try:
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # Include current statistics (convert datetime objects to strings)
            stats_serializable = {}
            for key, value in self.stats.items():
                if isinstance(value, datetime):
                    stats_serializable[key] = value.isoformat()
                elif hasattr(value, 'isoformat'):  # Handle other datetime-like objects
                    stats_serializable[key] = value.isoformat()
                else:
                    stats_serializable[key] = value
            
            heartbeat_data = {
                'agent_id': self.agent_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'online',
                'statistics': stats_serializable,
                'forwarder_stats': [f.get_statistics() for f in self.forwarders]
            }
            
            async with self.session.post(
                f"{self.server_endpoint}/api/agents/{self.agent_id}/heartbeat",
                json=heartbeat_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    self.last_heartbeat = datetime.utcnow()
                else:
                    logger.warning(f"Heartbeat failed: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            self.stats['connection_errors'] += 1
    
    async def _run_forwarder(self, forwarder) -> None:
        """Run a log forwarder"""
        try:
            logger.info(f"Starting {forwarder.__class__.__name__}")
            if hasattr(forwarder, 'start') and callable(forwarder.start):
                if asyncio.iscoroutinefunction(forwarder.start):
                    await forwarder.start()
                else:
                    forwarder.start()
        except Exception as e:
            logger.error(f"Error in {forwarder.__class__.__name__}: {e}")
    
    async def _log_forwarding_loop(self) -> None:
        """Collect logs from forwarders and buffer them"""
        while self.running:
            try:
                # Collect logs from all forwarders
                for forwarder in self.forwarders:
                    if hasattr(forwarder, 'log_queue'):
                        while not forwarder.log_queue.empty():
                            try:
                                log_entry = forwarder.log_queue.get_nowait()
                                self.log_buffer.append(log_entry)
                                
                                # Send batch if buffer is full
                                if len(self.log_buffer) >= self.batch_size:
                                    await self._send_log_batch()
                            except asyncio.QueueEmpty:
                                break
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy loop
            
            except Exception as e:
                logger.error(f"Error in log forwarding loop: {e}")
                await asyncio.sleep(1)
    
    async def _batch_sender_loop(self) -> None:
        """Periodically send buffered logs"""
        while self.running:
            try:
                await asyncio.sleep(self.flush_interval)
                
                if self.log_buffer:
                    await self._send_log_batch()
            
            except Exception as e:
                logger.error(f"Error in batch sender loop: {e}")
    
    async def _send_log_batch(self) -> None:
        """Send batch of logs to server"""
        if not self.log_buffer or not self.session or not self.connected:
            return
        
        try:
            # Create batch
            batch = LogBatch(
                agent_id=self.agent_id,
                logs=self.log_buffer.copy(),
                compressed=self.compression_enabled
            )
            
            # Clear buffer
            self.log_buffer.clear()
            
            # Prepare data
            batch_data = batch.to_dict()
            
            # Compress if enabled
            if self.compression_enabled:
                batch_json = json.dumps(batch_data)
                compressed_data = compress_data(batch_json)
                
                headers = {
                    'Content-Type': 'application/octet-stream',
                    'Content-Encoding': 'gzip',
                    'X-Batch-Size': str(batch.batch_size)
                }
                
                data = compressed_data
            else:
                headers = {'Content-Type': 'application/json'}
                data = batch_data
            
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # Send to server
            async with self.session.post(
                f"{self.server_endpoint}/api/logs/ingest",
                data=data if isinstance(data, bytes) else json.dumps(data),
                headers=headers
            ) as response:
                if response.status == 200:
                    # Update statistics
                    self.stats['logs_sent'] += batch.batch_size
                    self.stats['batches_sent'] += 1
                    
                    if isinstance(data, bytes):
                        self.stats['bytes_sent'] += len(data)
                    else:
                        self.stats['bytes_sent'] += len(json.dumps(data))
                    
                    logger.debug(f"Sent batch of {batch.batch_size} logs")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send log batch: {response.status} - {error_text}")
                    
                    # Re-queue logs on failure
                    self.log_buffer.extend(batch.logs)
                    self.stats['connection_errors'] += 1
        
        except Exception as e:
            logger.error(f"Error sending log batch: {e}")
            self.stats['connection_errors'] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status"""
        runtime = (datetime.utcnow() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
        
        status = {
            'agent_id': self.agent_id,
            'running': self.running,
            'connected': self.connected,
            'server_endpoint': self.server_endpoint,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'buffer_size': len(self.log_buffer),
            'forwarders': len(self.forwarders),
            'statistics': {
                **self.stats,
                'runtime_seconds': runtime,
                'logs_per_second': self.stats['logs_sent'] / runtime if runtime > 0 else 0
            },
            'forwarder_status': [f.get_statistics() for f in self.forwarders]
        }
        
        # Add command executor status
        if self.command_executor:
            status['command_executor'] = self.command_executor.get_statistics()
        
        # Add container executor status
        if self.container_executor:
            status['container_executor'] = self.container_executor.get_execution_status()
        
        return status


def setup_signal_handlers(client: LogForwardingClient):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(client.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI SOC Log Forwarding Client")
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--log-level', '-l', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Log level')
    parser.add_argument('--log-file', help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Create and start client
    client = LogForwardingClient(args.config)
    setup_signal_handlers(client)
    
    try:
        await client.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Client error: {e}")
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
