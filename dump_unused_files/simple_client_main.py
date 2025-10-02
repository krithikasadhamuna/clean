#!/usr/bin/env python3
"""
Simplified CodeGrey AI SOC Platform Client Agent
This version focuses on core functionality without problematic dependencies
"""

import asyncio
import logging
import platform
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class SimpleCodeGreyClient:
    """Simplified CodeGrey client agent"""
    
    def __init__(self, config_file=None):
        self.agent_id = f"agent_{int(time.time())}"
        self.hostname = platform.node()
        self.platform = platform.system()
        self.running = False
        
        # Load configuration
        self.config = self._load_config(config_file)
        self.server_endpoint = self.config.get('server_endpoint', 'http://backend.codegrey.ai:8080')
        
        # Statistics
        self.stats = {
            'start_time': datetime.now(),
            'logs_sent': 0,
            'heartbeats_sent': 0,
            'connection_errors': 0
        }
        
        logger.info(f"Initialized Simple CodeGrey Client")
        logger.info(f"Agent ID: {self.agent_id}")
        logger.info(f"Hostname: {self.hostname}")
        logger.info(f"Platform: {self.platform}")
        logger.info(f"Server: {self.server_endpoint}")
    
    def _load_config(self, config_file):
        """Load configuration from file or use defaults"""
        default_config = {
            'server_endpoint': 'http://backend.codegrey.ai:8080',
            'heartbeat_interval': 60,
            'log_interval': 30,
            'api_key': ''
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    # Extract client config
                    client_config = config_data.get('client', {})
                    default_config.update({
                        'server_endpoint': client_config.get('server_endpoint', default_config['server_endpoint']),
                        'api_key': client_config.get('api_key', default_config['api_key'])
                    })
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        return default_config
    
    async def start(self):
        """Start the client agent"""
        if self.running:
            return
        
        logger.info("Starting Simple CodeGrey Client Agent")
        self.running = True
        
        # Register with server
        await self._register_agent()
        
        # Start main tasks
        tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._log_collection_loop()),
            asyncio.create_task(self._status_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in client main loop: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the client agent"""
        logger.info("Stopping Simple CodeGrey Client Agent")
        self.running = False
    
    async def _register_agent(self):
        """Register agent with server"""
        logger.info("Registering agent with server")
        
        agent_data = {
            'agent_id': self.agent_id,
            'hostname': self.hostname,
            'platform': self.platform,
            'timestamp': datetime.now().isoformat(),
            'capabilities': ['log_forwarding', 'heartbeat', 'system_monitoring']
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_endpoint}/api/agents/register",
                    json=agent_data,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Successfully registered: {result}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Registration failed: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            self.stats['connection_errors'] += 1
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        heartbeat_interval = self.config.get('heartbeat_interval', 60)
        
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(heartbeat_interval)
    
    async def _send_heartbeat(self):
        """Send heartbeat to server"""
        heartbeat_data = {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'online',
            'statistics': self.stats
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_endpoint}/api/agents/{self.agent_id}/heartbeat",
                    json=heartbeat_data,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        self.stats['heartbeats_sent'] += 1
                        logger.debug("Heartbeat sent successfully")
                    else:
                        logger.warning(f"Heartbeat failed: {response.status}")
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            self.stats['connection_errors'] += 1
    
    async def _log_collection_loop(self):
        """Collect and send system logs"""
        log_interval = self.config.get('log_interval', 30)
        
        while self.running:
            try:
                await self._collect_and_send_logs()
                await asyncio.sleep(log_interval)
            except Exception as e:
                logger.error(f"Log collection error: {e}")
                await asyncio.sleep(log_interval)
    
    async def _collect_and_send_logs(self):
        """Collect system logs and send to server"""
        # Collect basic system information
        system_logs = []
        
        # System info log
        system_log = {
            'timestamp': datetime.now().isoformat(),
            'level': 'info',
            'message': f"System status check - {self.hostname}",
            'event_type': 'system_status',
            'agent_id': self.agent_id,
            'hostname': self.hostname,
            'platform': self.platform,
            'cpu_percent': self._get_cpu_usage(),
            'memory_percent': self._get_memory_usage(),
            'disk_usage': self._get_disk_usage()
        }
        system_logs.append(system_log)
        
        # Process information
        process_log = {
            'timestamp': datetime.now().isoformat(),
            'level': 'info',
            'message': f"Process count: {self._get_process_count()}",
            'event_type': 'process_info',
            'agent_id': self.agent_id,
            'process_count': self._get_process_count()
        }
        system_logs.append(process_log)
        
        # Send logs to server
        if system_logs:
            await self._send_logs(system_logs)
    
    async def _send_logs(self, logs):
        """Send logs to server"""
        log_batch = {
            'agent_id': self.agent_id,
            'logs': logs,
            'batch_size': len(logs),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_endpoint}/api/logs/ingest",
                    json=log_batch,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        self.stats['logs_sent'] += len(logs)
                        logger.debug(f"Sent {len(logs)} logs successfully")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send logs: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error sending logs: {e}")
            self.stats['connection_errors'] += 1
    
    def _get_cpu_usage(self):
        """Get CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except:
            return 0
    
    def _get_memory_usage(self):
        """Get memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except:
            return 0
    
    def _get_disk_usage(self):
        """Get disk usage percentage"""
        try:
            import psutil
            return psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:').percent
        except:
            return 0
    
    def _get_process_count(self):
        """Get number of running processes"""
        try:
            import psutil
            return len(psutil.pids())
        except:
            return 0
    
    async def _status_loop(self):
        """Print status information periodically"""
        while self.running:
            try:
                runtime = (datetime.now() - self.stats['start_time']).total_seconds()
                logger.info(f"Status - Runtime: {runtime:.0f}s, Logs: {self.stats['logs_sent']}, Heartbeats: {self.stats['heartbeats_sent']}, Errors: {self.stats['connection_errors']}")
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Status loop error: {e}")
                await asyncio.sleep(300)

async def main():
    """Main entry point"""
    print("CodeGrey AI SOC Platform - Simple Client Agent")
    print("=" * 50)
    
    # Check for config file
    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        # Look for config in common locations
        possible_configs = [
            "config.yaml",
            "build_artifacts/packages/windows/codegrey-agent-windows-v2/config.yaml"
        ]
        for config_path in possible_configs:
            if Path(config_path).exists():
                config_file = config_path
                break
    
    if config_file:
        print(f"Using config file: {config_file}")
    else:
        print("No config file found, using defaults")
    
    # Create and start client
    client = SimpleCodeGreyClient(config_file)
    
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

