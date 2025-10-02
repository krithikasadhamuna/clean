"""
Windows-specific client agent implementation
"""

import os
import sys
import json
import time
import asyncio
import logging
import platform
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import queue
import requests
import psutil

# Import Windows-specific modules
try:
    import win32evtlog
    import win32evtlogutil
    import win32con
    WINDOWS_EVENTS_AVAILABLE = True
except ImportError:
    WINDOWS_EVENTS_AVAILABLE = False

class WindowsClientAgent:
    """Windows-specific client agent for CodeGrey AI SOC Platform"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.server_url = config.get('server_endpoint', 'http://localhost:8080')
        self.agent_id = config.get('agent_id', f"windows-{platform.node()}")
        self.heartbeat_interval = config.get('heartbeat_interval', 60)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('codegrey-agent.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.log_forwarder = WindowsLogForwarder(self.server_url, self.agent_id)
        self.command_executor = WindowsCommandExecutor()
        self.container_manager = WindowsContainerManager()
        
        # Initialize network discovery and location detection
        from network_discovery import NetworkDiscovery
        from location_detector import LocationDetector
        self.network_discovery = NetworkDiscovery(config)
        self.location_detector = LocationDetector()
        
        # Stats tracking
        self.stats = {
            'logs_sent': 0,
            'commands_executed': 0,
            'containers_created': 0,
            'network_scans': 0,
            'hosts_discovered': 0,
            'start_time': datetime.now(),
            'last_heartbeat': None
        }
    
    def start(self):
        """Start the client agent"""
        self.running = True
        self.logger.info(f"Starting Windows client agent {self.agent_id}")
        
        # Start background threads
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._log_forwarding_loop, daemon=True).start()
        threading.Thread(target=self._command_polling_loop, daemon=True).start()
        
        # Start network discovery
        if self.network_discovery:
            self.network_discovery.start_discovery()
            self.logger.info("Network discovery started")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the client agent"""
        self.running = False
        self.logger.info("Stopping Windows client agent")
    
    def _heartbeat_loop(self):
        """Send heartbeat to server"""
        while self.running:
            try:
                self._send_heartbeat()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                time.sleep(10)
    
    def _send_heartbeat(self):
        """Send heartbeat with system info"""
        try:
            system_info = self._get_system_info()
            
            heartbeat_data = {
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'active',
                'platform': 'Windows',
                'system_info': system_info,
                'stats': {
                    'logs_sent': self.stats['logs_sent'],
                    'commands_executed': self.stats['commands_executed'],
                    'containers_created': self.stats['containers_created'],
                    'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds()
                }
            }
            
            response = requests.post(
                f"{self.server_url}/api/agents/{self.agent_id}/heartbeat",
                json=heartbeat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.stats['last_heartbeat'] = datetime.now()
                self.logger.debug("Heartbeat sent successfully")
            else:
                self.logger.warning(f"Heartbeat failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send heartbeat: {e}")
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get Windows system information"""
        try:
            return {
                'hostname': platform.node(),
                'os': platform.system(),
                'os_version': platform.version(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': {
                    'total': psutil.disk_usage('C:\\').total,
                    'free': psutil.disk_usage('C:\\').free
                },
                'network_interfaces': self._get_network_interfaces(),
                'processes_count': len(psutil.pids()),
                'boot_time': psutil.boot_time()
            }
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}
    
    def _get_network_interfaces(self) -> List[Dict[str, str]]:
        """Get network interface information"""
        interfaces = []
        try:
            for interface, addresses in psutil.net_if_addrs().items():
                for address in addresses:
                    if address.family == 2:  # IPv4
                        interfaces.append({
                            'interface': interface,
                            'ip': address.address,
                            'netmask': address.netmask
                        })
        except Exception as e:
            self.logger.error(f"Failed to get network interfaces: {e}")
        
        return interfaces
    
    def _log_forwarding_loop(self):
        """Forward logs to server"""
        while self.running:
            try:
                logs = self.log_forwarder.collect_logs()
                if logs:
                    self.log_forwarder.forward_logs(logs)
                    self.stats['logs_sent'] += len(logs)
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Log forwarding error: {e}")
                time.sleep(10)
    
    def _command_polling_loop(self):
        """Poll server for commands"""
        while self.running:
            try:
                commands = self._get_pending_commands()
                for command in commands:
                    self._execute_command(command)
                time.sleep(10)
            except Exception as e:
                self.logger.error(f"Command polling error: {e}")
                time.sleep(30)
    
    def _get_pending_commands(self) -> List[Dict[str, Any]]:
        """Get pending commands from server"""
        try:
            response = requests.get(
                f"{self.server_url}/api/agents/{self.agent_id}/commands",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('commands', [])
            
        except Exception as e:
            self.logger.error(f"Failed to get pending commands: {e}")
        
        return []
    
    def _execute_command(self, command: Dict[str, Any]):
        """Execute a command from the server"""
        try:
            command_type = command.get('type')
            command_data = command.get('data', {})
            
            if command_type == 'shell':
                result = self.command_executor.execute_shell_command(command_data)
            elif command_type == 'container':
                result = self.container_manager.execute_container_command(command_data)
            elif command_type == 'file':
                result = self.command_executor.execute_file_operation(command_data)
            else:
                result = {'success': False, 'error': f'Unknown command type: {command_type}'}
            
            # Send result back to server
            self._send_command_result(command['id'], result)
            self.stats['commands_executed'] += 1
            
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            self._send_command_result(command['id'], {'success': False, 'error': str(e)})
    
    def _send_command_result(self, command_id: str, result: Dict[str, Any]):
        """Send command execution result to server"""
        try:
            response = requests.post(
                f"{self.server_url}/api/agents/{self.agent_id}/commands/{command_id}/result",
                json=result,
                timeout=30
            )
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to send command result: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send command result: {e}")


class WindowsLogForwarder:
    """Windows-specific log forwarding"""
    
    def __init__(self, server_url: str, agent_id: str):
        self.server_url = server_url
        self.agent_id = agent_id
        self.logger = logging.getLogger(__name__)
    
    def collect_logs(self) -> List[Dict[str, Any]]:
        """Collect Windows logs"""
        logs = []
        
        # Collect Windows Event Logs
        if WINDOWS_EVENTS_AVAILABLE:
            logs.extend(self._collect_windows_event_logs())
        
        # Collect process logs
        logs.extend(self._collect_process_logs())
        
        # Collect network logs
        logs.extend(self._collect_network_logs())
        
        return logs
    
    def _collect_windows_event_logs(self) -> List[Dict[str, Any]]:
        """Collect Windows Event Logs with privilege handling"""
        logs = []
        
        try:
            # Try to collect from accessible logs first (non-Security)
            accessible_logs = ['System', 'Application']
            
            for log_type in accessible_logs:
                try:
                    handle = win32evtlog.OpenEventLog(None, log_type)
                    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                    
                    events = win32evtlog.ReadEventLog(handle, flags, 0)
                    
                    for event in events[:10]:  # Limit to recent events
                        log_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'source': f'Windows-{log_type}',
                            'level': self._get_event_level(event.EventType),
                            'event_id': event.EventID,
                            'message': win32evtlogutil.SafeFormatMessage(event, log_type),
                            'agent_id': self.agent_id
                        }
                        logs.append(log_entry)
                    
                    win32evtlog.CloseEventLog(handle)
                    
                except Exception as e:
                    self.logger.warning(f"Could not access {log_type} events: {e}")
            
            # Try Security log only if running as Administrator
            try:
                handle = win32evtlog.OpenEventLog(None, 'Security')
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                
                events = win32evtlog.ReadEventLog(handle, flags, 0)
                
                for event in events[:5]:  # Limit Security events
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'source': 'Windows-Security',
                        'level': self._get_event_level(event.EventType),
                        'event_id': event.EventID,
                        'message': win32evtlogutil.SafeFormatMessage(event, 'Security'),
                        'agent_id': self.agent_id
                    }
                    logs.append(log_entry)
                
                win32evtlog.CloseEventLog(handle)
                
            except Exception as e:
                # This is expected if not running as Administrator
                if "privilege" in str(e).lower():
                    self.logger.debug("Security event log requires Administrator privileges (this is normal)")
                else:
                    self.logger.warning(f"Could not access Security events: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error collecting Windows event logs: {e}")
        
        return logs
    
    def _get_event_level(self, event_type: int) -> str:
        """Convert Windows event type to log level"""
        if event_type == win32con.EVENTLOG_ERROR_TYPE:
            return 'ERROR'
        elif event_type == win32con.EVENTLOG_WARNING_TYPE:
            return 'WARNING'
        elif event_type == win32con.EVENTLOG_INFORMATION_TYPE:
            return 'INFO'
        else:
            return 'UNKNOWN'
    
    def _collect_process_logs(self) -> List[Dict[str, Any]]:
        """Collect process information"""
        logs = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'source': 'Windows-Process',
                        'level': 'INFO',
                        'message': f"Process {proc.info['name']} (PID: {proc.info['pid']}) - CPU: {proc.info['cpu_percent']}%, Memory: {proc.info['memory_percent']}%",
                        'process_info': proc.info,
                        'agent_id': self.agent_id
                    }
                    logs.append(log_entry)
                    
                    # Limit to avoid overwhelming
                    if len(logs) >= 50:
                        break
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error collecting process logs: {e}")
        
        return logs
    
    def _collect_network_logs(self) -> List[Dict[str, Any]]:
        """Collect network connection information"""
        logs = []
        
        try:
            connections = psutil.net_connections()
            
            for conn in connections[:20]:  # Limit connections
                if conn.status == 'ESTABLISHED':
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'source': 'Windows-Network',
                        'level': 'INFO',
                        'message': f"Network connection {conn.laddr} -> {conn.raddr} ({conn.status})",
                        'connection_info': {
                            'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            'status': conn.status,
                            'pid': conn.pid
                        },
                        'agent_id': self.agent_id
                    }
                    logs.append(log_entry)
                    
        except Exception as e:
            self.logger.error(f"Error collecting network logs: {e}")
        
        return logs
    
    def forward_logs(self, logs: List[Dict[str, Any]]):
        """Forward logs to server"""
        try:
            response = requests.post(
                f"{self.server_url}/api/logs/ingest",
                json={'logs': logs},
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.debug(f"Forwarded {len(logs)} logs successfully")
            else:
                self.logger.warning(f"Log forwarding failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to forward logs: {e}")


class WindowsCommandExecutor:
    """Execute commands on Windows"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def execute_shell_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command"""
        try:
            command = command_data.get('command', '')
            timeout = command_data.get('timeout', 30)
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': True,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def execute_file_operation(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file operations"""
        try:
            operation = command_data.get('operation')
            file_path = command_data.get('file_path')
            
            if operation == 'read':
                with open(file_path, 'r') as f:
                    content = f.read()
                return {'success': True, 'content': content}
            
            elif operation == 'write':
                content = command_data.get('content', '')
                with open(file_path, 'w') as f:
                    f.write(content)
                return {'success': True, 'message': 'File written successfully'}
            
            elif operation == 'delete':
                os.remove(file_path)
                return {'success': True, 'message': 'File deleted successfully'}
            
            else:
                return {'success': False, 'error': f'Unknown operation: {operation}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}


class WindowsContainerManager:
    """Manage containers on Windows (Docker)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.docker_available = self._check_docker()
    
    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def execute_container_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute container-related commands"""
        if not self.docker_available:
            return {'success': False, 'error': 'Docker is not available'}
        
        try:
            operation = command_data.get('operation')
            
            if operation == 'create':
                return self._create_container(command_data)
            elif operation == 'start':
                return self._start_container(command_data)
            elif operation == 'stop':
                return self._stop_container(command_data)
            elif operation == 'remove':
                return self._remove_container(command_data)
            else:
                return {'success': False, 'error': f'Unknown operation: {operation}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_container(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new container"""
        try:
            image = command_data.get('image', 'alpine:latest')
            name = command_data.get('name', f'codegrey-{int(time.time())}')
            command = command_data.get('command', 'sh')
            
            docker_cmd = [
                'docker', 'run', '-d', '--name', name, image, command
            ]
            
            result = subprocess.run(docker_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                container_id = result.stdout.strip()
                return {
                    'success': True,
                    'container_id': container_id,
                    'name': name,
                    'message': 'Container created successfully'
                }
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _start_container(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a container"""
        try:
            container_id = command_data.get('container_id')
            
            result = subprocess.run(['docker', 'start', container_id], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'Container started successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _stop_container(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a container"""
        try:
            container_id = command_data.get('container_id')
            
            result = subprocess.run(['docker', 'stop', container_id], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'Container stopped successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _remove_container(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a container"""
        try:
            container_id = command_data.get('container_id')
            
            result = subprocess.run(['docker', 'rm', container_id], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'Container removed successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
