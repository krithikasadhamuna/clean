"""
Linux-specific client agent implementation with eBPF support
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
import socket

# eBPF support (optional)
try:
    from bcc import BPF
    EBPF_AVAILABLE = True
except ImportError:
    EBPF_AVAILABLE = False

class LinuxClientAgent:
    """Linux-specific client agent for CodeGrey AI SOC Platform"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.server_url = config.get('server_endpoint', 'http://localhost:8080')
        self.agent_id = config.get('agent_id', f"linux-{platform.node()}")
        self.heartbeat_interval = config.get('heartbeat_interval', 60)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.get('logging', {}).get('level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.get('logging', {}).get('file', 'codegrey-agent.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.log_forwarder = LinuxLogForwarder(self.server_url, self.agent_id, config)
        self.command_executor = LinuxCommandExecutor()
        self.container_manager = LinuxContainerManager()
        
        # Stats tracking
        self.stats = {
            'logs_sent': 0,
            'commands_executed': 0,
            'containers_created': 0,
            'start_time': datetime.now(),
            'last_heartbeat': None
        }
        
        self.logger.info(f"Linux client agent initialized: {self.agent_id}")
    
    def start(self):
        """Start the client agent"""
        self.running = True
        self.logger.info(f"Starting Linux client agent {self.agent_id}")
        
        # Start background threads
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._log_forwarding_loop, daemon=True).start()
        threading.Thread(target=self._command_polling_loop, daemon=True).start()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the client agent"""
        self.running = False
        self.log_forwarder.stop()
        self.logger.info("Stopping Linux client agent")
    
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
                'platform': 'Linux',
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
        """Get Linux system information"""
        try:
            # Get distribution info
            try:
                with open('/etc/os-release', 'r') as f:
                    os_info = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os_info[key] = value.strip('"')
            except:
                os_info = {'NAME': 'Unknown Linux'}
            
            return {
                'hostname': platform.node(),
                'os': platform.system(),
                'os_version': platform.version(),
                'distribution': os_info.get('NAME', 'Unknown'),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': {
                    'total': psutil.disk_usage('/').total,
                    'free': psutil.disk_usage('/').free
                },
                'network_interfaces': self._get_network_interfaces(),
                'processes_count': len(psutil.pids()),
                'boot_time': psutil.boot_time(),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                'ebpf_available': EBPF_AVAILABLE
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
                    if address.family == socket.AF_INET:  # IPv4
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


class LinuxLogForwarder:
    """Linux-specific log forwarding with eBPF support"""
    
    def __init__(self, server_url: str, agent_id: str, config: Dict[str, Any]):
        self.server_url = server_url
        self.agent_id = agent_id
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ebpf_monitor = None
        
        # Initialize eBPF if available
        if EBPF_AVAILABLE and config.get('log_forwarding', {}).get('ebpf_enabled', True):
            self._init_ebpf_monitor()
    
    def _init_ebpf_monitor(self):
        """Initialize eBPF monitoring"""
        try:
            # Simple eBPF program to monitor syscalls
            bpf_program = """
            #include <uapi/linux/ptrace.h>
            #include <linux/sched.h>
            
            BPF_PERF_OUTPUT(events);
            
            struct data_t {
                u32 pid;
                u32 uid;
                char comm[TASK_COMM_LEN];
                char syscall[64];
            };
            
            int trace_syscall(struct pt_regs *ctx) {
                struct data_t data = {};
                data.pid = bpf_get_current_pid_tgid() >> 32;
                data.uid = bpf_get_current_uid_gid() & 0xffffffff;
                bpf_get_current_comm(&data.comm, sizeof(data.comm));
                
                events.perf_submit(ctx, &data, sizeof(data));
                return 0;
            }
            """
            
            self.ebpf_monitor = BPF(text=bpf_program)
            self.logger.info("eBPF monitoring initialized")
            
        except Exception as e:
            self.logger.warning(f"eBPF initialization failed: {e}")
            self.ebpf_monitor = None
    
    def collect_logs(self) -> List[Dict[str, Any]]:
        """Collect Linux logs"""
        logs = []
        
        # Collect system logs
        logs.extend(self._collect_syslog())
        
        # Collect process logs
        logs.extend(self._collect_process_logs())
        
        # Collect network logs
        logs.extend(self._collect_network_logs())
        
        # Collect eBPF logs if available
        if self.ebpf_monitor:
            logs.extend(self._collect_ebpf_logs())
        
        return logs
    
    def _collect_syslog(self) -> List[Dict[str, Any]]:
        """Collect system logs"""
        logs = []
        
        try:
            # Read recent syslog entries
            syslog_files = ['/var/log/syslog', '/var/log/messages', '/var/log/auth.log']
            
            for log_file in syslog_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()[-50:]  # Last 50 lines
                            
                        for line in lines:
                            if line.strip():
                                log_entry = {
                                    'timestamp': datetime.now().isoformat(),
                                    'source': f'Linux-{os.path.basename(log_file)}',
                                    'level': 'INFO',
                                    'message': line.strip(),
                                    'agent_id': self.agent_id
                                }
                                logs.append(log_entry)
                                
                    except PermissionError:
                        self.logger.warning(f"Permission denied reading {log_file}")
                    except Exception as e:
                        self.logger.error(f"Error reading {log_file}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error collecting syslog: {e}")
        
        return logs
    
    def _collect_process_logs(self) -> List[Dict[str, Any]]:
        """Collect process information"""
        logs = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
                try:
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'source': 'Linux-Process',
                        'level': 'INFO',
                        'message': f"Process {proc.info['name']} (PID: {proc.info['pid']}) - CPU: {proc.info['cpu_percent']}%, Memory: {proc.info['memory_percent']}%",
                        'process_info': proc.info,
                        'agent_id': self.agent_id
                    }
                    logs.append(log_entry)
                    
                    # Limit to avoid overwhelming
                    if len(logs) >= 30:
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
            
            for conn in connections[:15]:  # Limit connections
                if conn.status == 'ESTABLISHED':
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'source': 'Linux-Network',
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
    
    def _collect_ebpf_logs(self) -> List[Dict[str, Any]]:
        """Collect eBPF-based logs"""
        logs = []
        
        try:
            if self.ebpf_monitor:
                # This is a simplified example - in production, you'd have more sophisticated eBPF programs
                self.logger.debug("eBPF log collection available but not implemented in this demo")
                
        except Exception as e:
            self.logger.error(f"Error collecting eBPF logs: {e}")
        
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
    
    def stop(self):
        """Stop log forwarding"""
        if self.ebpf_monitor:
            try:
                self.ebpf_monitor.cleanup()
            except:
                pass


class LinuxCommandExecutor:
    """Execute commands on Linux"""
    
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


class LinuxContainerManager:
    """Manage containers on Linux (Docker/Podman)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.container_runtime = self._detect_container_runtime()
    
    def _detect_container_runtime(self) -> str:
        """Detect available container runtime"""
        # Check for Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return 'docker'
        except:
            pass
        
        # Check for Podman
        try:
            result = subprocess.run(['podman', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return 'podman'
        except:
            pass
        
        return None
    
    def execute_container_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute container-related commands"""
        if not self.container_runtime:
            return {'success': False, 'error': 'No container runtime available (Docker/Podman)'}
        
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
            elif operation == 'snapshot':
                return self._create_snapshot(command_data)
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
                self.container_runtime, 'run', '-d', '--name', name, image, command
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
            
            result = subprocess.run([self.container_runtime, 'start', container_id], capture_output=True, text=True)
            
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
            
            result = subprocess.run([self.container_runtime, 'stop', container_id], capture_output=True, text=True)
            
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
            
            result = subprocess.run([self.container_runtime, 'rm', container_id], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'Container removed successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_snapshot(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create container snapshot (golden image)"""
        try:
            container_id = command_data.get('container_id')
            snapshot_name = command_data.get('snapshot_name', f'codegrey-snapshot-{int(time.time())}')
            
            result = subprocess.run([
                self.container_runtime, 'commit', container_id, snapshot_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'snapshot_name': snapshot_name,
                    'message': 'Snapshot created successfully'
                }
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
