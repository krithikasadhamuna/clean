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
            
            # Get network discovery results if available
            network_discovery_data = {}
            if self.network_discovery:
                network_discovery_data = self.network_discovery.get_discovery_results()
            
            heartbeat_data = {
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'active',
                'platform': 'Windows',
                'system_info': system_info,
                'network_discovery': network_discovery_data,
                'stats': {
                    'logs_sent': self.stats['logs_sent'],
                    'commands_executed': self.stats['commands_executed'],
                    'containers_created': self.stats['containers_created'],
                    'network_scans': self.stats.get('network_scans', 0),
                    'hosts_discovered': self.stats.get('hosts_discovered', 0),
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
        """Get complete Windows system information for exact container replication"""
        try:
            return {
                'hostname': platform.node(),
                'os': platform.system(),
                'os_version': platform.version(),
                'os_release': platform.release(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': self._get_all_disk_usage(),
                'network_interfaces': self._get_network_interfaces(),
                'processes_count': len(psutil.pids()),
                'boot_time': psutil.boot_time(),
                
                # Additional system details for exact replication
                'installed_software': self._get_installed_software(),
                'running_services': self._get_running_services(),
                'open_ports': self._get_open_ports(),
                'environment_variables': self._get_environment_variables(),
                'system_configuration': self._get_system_configuration(),
                'security_settings': self._get_security_settings(),
                'network_configuration': self._get_network_configuration(),
                'user_accounts': self._get_user_accounts(),
                'system_patches': self._get_system_patches(),
                'registry_settings': self._get_critical_registry_settings()
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
    
    def _get_all_disk_usage(self) -> Dict[str, Dict]:
        """Get disk usage for all drives"""
        disk_usage = {}
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.device] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'filesystem': partition.fstype
                    }
                except:
                    continue
        except Exception as e:
            self.logger.error(f"Failed to get disk usage: {e}")
        return disk_usage
    
    def _get_installed_software(self) -> List[Dict[str, str]]:
        """Get list of installed software"""
        software = []
        try:
            import winreg
            
            # Check common installation locations
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            for hkey, path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                        software.append({
                                            'name': name,
                                            'version': version,
                                            'key': subkey_name
                                        })
                                    except:
                                        continue
                            except:
                                continue
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to get installed software: {e}")
        
        return software[:50]  # Limit to first 50 for performance
    
    def _get_running_services(self) -> List[Dict[str, str]]:
        """Get list of running Windows services"""
        services = []
        try:
            import win32service
            import win32serviceutil
            
            # Get all services
            service_list = win32service.EnumServicesStatus(
                win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE),
                win32service.SERVICE_WIN32,
                win32service.SERVICE_STATE_ALL
            )
            
            for service in service_list:
                service_name = service[0]
                display_name = service[1]
                status = service[2]
                
                services.append({
                    'name': service_name,
                    'display_name': display_name,
                    'status': 'running' if status[1] == win32service.SERVICE_RUNNING else 'stopped'
                })
                
        except Exception as e:
            self.logger.error(f"Failed to get services: {e}")
            # Fallback to psutil
            try:
                for proc in psutil.process_iter(['name', 'status']):
                    if 'svchost' in proc.info['name'].lower():
                        services.append({
                            'name': proc.info['name'],
                            'status': proc.info['status']
                        })
            except:
                pass
        
        return services[:30]  # Limit for performance
    
    def _get_open_ports(self) -> List[Dict[str, Any]]:
        """Get list of open network ports"""
        ports = []
        try:
            connections = psutil.net_connections()
            for conn in connections:
                if conn.status == 'LISTEN':
                    ports.append({
                        'port': conn.laddr.port,
                        'protocol': 'TCP' if conn.type == 1 else 'UDP',
                        'address': conn.laddr.ip,
                        'pid': conn.pid
                    })
        except Exception as e:
            self.logger.error(f"Failed to get open ports: {e}")
        
        return ports
    
    def _get_environment_variables(self) -> Dict[str, str]:
        """Get system environment variables"""
        try:
            # Only get non-sensitive environment variables
            safe_env_vars = {}
            for key, value in os.environ.items():
                # Skip sensitive variables
                if not any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'TOKEN', 'KEY']):
                    safe_env_vars[key] = value
            return safe_env_vars
        except Exception as e:
            self.logger.error(f"Failed to get environment variables: {e}")
            return {}
    
    def _get_system_configuration(self) -> Dict[str, Any]:
        """Get Windows system configuration"""
        config = {}
        try:
            # Get Windows version details
            import winreg
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                try:
                    config['build_number'] = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
                    config['product_name'] = winreg.QueryValueEx(key, "ProductName")[0]
                    config['edition_id'] = winreg.QueryValueEx(key, "EditionID")[0]
                except:
                    pass
            
            # Get system features
            config['features'] = {
                'hyper_v': self._check_hyper_v_enabled(),
                'wsl': self._check_wsl_enabled(),
                'docker': self._check_docker_installed()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system configuration: {e}")
        
        return config
    
    def _get_security_settings(self) -> Dict[str, Any]:
        """Get Windows security settings"""
        security = {}
        try:
            # Get Windows Defender status
            security['defender'] = {
                'enabled': self._check_defender_enabled(),
                'real_time_protection': self._check_real_time_protection()
            }
            
            # Get firewall status
            security['firewall'] = {
                'enabled': self._check_firewall_enabled()
            }
            
            # Get UAC status
            security['uac'] = {
                'enabled': self._check_uac_enabled()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get security settings: {e}")
        
        return security
    
    def _get_network_configuration(self) -> Dict[str, Any]:
        """Get network configuration details"""
        network_config = {}
        try:
            # Get DNS settings
            network_config['dns_servers'] = self._get_dns_servers()
            
            # Get gateway information
            network_config['default_gateway'] = self._get_default_gateway()
            
            # Get network adapters
            network_config['adapters'] = self._get_network_adapters()
            
        except Exception as e:
            self.logger.error(f"Failed to get network configuration: {e}")
        
        return network_config
    
    def _get_user_accounts(self) -> List[Dict[str, str]]:
        """Get user account information (non-sensitive)"""
        users = []
        try:
            import win32net
            import win32netcon
            
            # Get local users
            user_info = win32net.NetUserEnum(None, 0)[0]
            for user in user_info:
                users.append({
                    'username': user['name'],
                    'account_type': 'local'
                })
                
        except Exception as e:
            self.logger.error(f"Failed to get user accounts: {e}")
            # Fallback
            try:
                import getpass
                users.append({
                    'username': getpass.getuser(),
                    'account_type': 'current'
                })
            except:
                pass
        
        return users
    
    def _get_system_patches(self) -> List[Dict[str, str]]:
        """Get installed Windows updates/patches"""
        patches = []
        try:
            import winreg
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\Packages") as key:
                for i in range(min(20, winreg.QueryInfoKey(key)[0])):  # Limit to first 20
                    try:
                        patch_name = winreg.EnumKey(key, i)
                        if 'KB' in patch_name:
                            patches.append({
                                'name': patch_name,
                                'type': 'security_update' if 'Security' in patch_name else 'update'
                            })
                    except:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Failed to get system patches: {e}")
        
        return patches
    
    def _get_critical_registry_settings(self) -> Dict[str, Any]:
        """Get critical registry settings for system replication"""
        registry_settings = {}
        try:
            import winreg
            
            # Get important registry values for system configuration
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", "PATH"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "ProductName"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "Domain")
            ]
            
            for hkey, path, value_name in registry_paths:
                try:
                    with winreg.OpenKey(hkey, path) as key:
                        value = winreg.QueryValueEx(key, value_name)[0]
                        registry_settings[f"{path}\\{value_name}"] = str(value)[:200]  # Limit length
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to get registry settings: {e}")
        
        return registry_settings
    
    # Helper methods for system checks
    def _check_hyper_v_enabled(self) -> bool:
        """Check if Hyper-V is enabled"""
        try:
            result = subprocess.run(['powershell', '-Command', 'Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V'], 
                                  capture_output=True, text=True, timeout=10)
            return 'Enabled' in result.stdout
        except:
            return False
    
    def _check_wsl_enabled(self) -> bool:
        """Check if WSL is enabled"""
        try:
            result = subprocess.run(['wsl', '--list'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_docker_installed(self) -> bool:
        """Check if Docker is installed"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_defender_enabled(self) -> bool:
        """Check Windows Defender status"""
        try:
            result = subprocess.run(['powershell', '-Command', 'Get-MpComputerStatus'], 
                                  capture_output=True, text=True, timeout=10)
            return 'True' in result.stdout
        except:
            return False
    
    def _check_real_time_protection(self) -> bool:
        """Check real-time protection status"""
        try:
            result = subprocess.run(['powershell', '-Command', 'Get-MpPreference | Select-Object DisableRealtimeMonitoring'], 
                                  capture_output=True, text=True, timeout=10)
            return 'False' in result.stdout
        except:
            return False
    
    def _check_firewall_enabled(self) -> bool:
        """Check Windows Firewall status"""
        try:
            result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles', 'state'], 
                                  capture_output=True, text=True, timeout=10)
            return 'ON' in result.stdout
        except:
            return False
    
    def _check_uac_enabled(self) -> bool:
        """Check UAC status"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System") as key:
                uac_value = winreg.QueryValueEx(key, "EnableLUA")[0]
                return uac_value == 1
        except:
            return False
    
    def _get_dns_servers(self) -> List[str]:
        """Get DNS server configuration"""
        dns_servers = []
        try:
            result = subprocess.run(['nslookup', 'localhost'], capture_output=True, text=True, timeout=5)
            # Parse DNS servers from nslookup output
            for line in result.stdout.split('\n'):
                if 'Server:' in line:
                    dns_server = line.split(':')[1].strip()
                    if dns_server and dns_server != 'localhost':
                        dns_servers.append(dns_server)
        except Exception as e:
            self.logger.error(f"Failed to get DNS servers: {e}")
        
        return dns_servers
    
    def _get_default_gateway(self) -> str:
        """Get default gateway"""
        try:
            result = subprocess.run(['route', 'print', '0.0.0.0'], capture_output=True, text=True, timeout=10)
            for line in result.stdout.split('\n'):
                if '0.0.0.0' in line and 'Gateway' not in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[2]
        except Exception as e:
            self.logger.error(f"Failed to get default gateway: {e}")
        
        return "Unknown"
    
    def _get_network_adapters(self) -> List[Dict[str, str]]:
        """Get network adapter information"""
        adapters = []
        try:
            result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, timeout=10)
            # Parse adapter information from ipconfig output
            current_adapter = {}
            for line in result.stdout.split('\n'):
                line = line.strip()
                if 'adapter' in line.lower() and ':' in line:
                    if current_adapter:
                        adapters.append(current_adapter)
                    current_adapter = {'name': line}
                elif 'Physical Address' in line:
                    current_adapter['mac_address'] = line.split(':')[1].strip()
                elif 'IPv4 Address' in line:
                    current_adapter['ip_address'] = line.split(':')[1].strip().split('(')[0]
            
            if current_adapter:
                adapters.append(current_adapter)
                
        except Exception as e:
            self.logger.error(f"Failed to get network adapters: {e}")
        
        return adapters
    
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
