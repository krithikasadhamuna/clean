#!/usr/bin/env python3
"""
Network Discovery Module for Windows Client Agent
Discovers network topology and running services
"""

import socket
import subprocess
import threading
import time
import ipaddress
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import concurrent.futures

logger = logging.getLogger(__name__)

class NetworkDiscovery:
    """Network discovery and topology mapping"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.discovery_interval = config.get('network_discovery', {}).get('interval', 1800)  # 30 minutes
        self.max_threads = config.get('network_discovery', {}).get('max_threads', 50)
        self.timeout = config.get('network_discovery', {}).get('timeout', 3)
        self.discovered_hosts = {}
        self.running = False
        
    def start_discovery(self):
        """Start network discovery thread"""
        if not self.running:
            self.running = True
            discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
            discovery_thread.start()
            logger.info("Network discovery started")
    
    def stop_discovery(self):
        """Stop network discovery"""
        self.running = False
        logger.info("Network discovery stopped")
    
    def _discovery_loop(self):
        """Main discovery loop"""
        while self.running:
            try:
                logger.info("Starting network discovery scan...")
                
                # Get local network interfaces
                local_networks = self._get_local_networks()
                
                # Discover hosts on each network
                for network in local_networks:
                    discovered = self._scan_network(network)
                    self.discovered_hosts.update(discovered)
                
                logger.info(f"Network discovery complete. Found {len(self.discovered_hosts)} hosts")
                
                # Sleep until next discovery
                time.sleep(self.discovery_interval)
                
            except Exception as e:
                logger.error(f"Network discovery error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _get_local_networks(self) -> List[str]:
        """Get local network ranges to scan"""
        networks = []
        
        try:
            # Get network interfaces
            import psutil
            
            for interface, addresses in psutil.net_if_addrs().items():
                for address in addresses:
                    if address.family == socket.AF_INET:  # IPv4
                        ip = address.address
                        netmask = address.netmask
                        
                        # Skip loopback
                        if ip.startswith('127.'):
                            continue
                        
                        # Calculate network range
                        try:
                            network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                            networks.append(str(network))
                        except:
                            # Fallback to /24 for common private networks
                            if ip.startswith(('192.168.', '10.', '172.')):
                                base_ip = '.'.join(ip.split('.')[:-1]) + '.0/24'
                                networks.append(base_ip)
            
            logger.info(f"Scanning networks: {networks}")
            return networks
            
        except Exception as e:
            logger.error(f"Failed to get local networks: {e}")
            return ['192.168.1.0/24']  # Default fallback
    
    def _scan_network(self, network_range: str) -> Dict[str, Dict]:
        """Scan a network range for active hosts"""
        discovered = {}
        
        try:
            network = ipaddress.IPv4Network(network_range, strict=False)
            hosts_to_scan = list(network.hosts())
            
            # Limit scan size for performance
            if len(hosts_to_scan) > 254:
                hosts_to_scan = hosts_to_scan[:254]
            
            logger.info(f"Scanning {len(hosts_to_scan)} hosts in {network_range}")
            
            # Parallel host scanning
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                future_to_ip = {
                    executor.submit(self._scan_host, str(ip)): str(ip) 
                    for ip in hosts_to_scan
                }
                
                for future in concurrent.futures.as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        host_info = future.result()
                        if host_info:
                            discovered[ip] = host_info
                    except Exception as e:
                        logger.debug(f"Host scan failed for {ip}: {e}")
            
            return discovered
            
        except Exception as e:
            logger.error(f"Network scan failed for {network_range}: {e}")
            return {}
    
    def _scan_host(self, ip: str) -> Optional[Dict]:
        """Scan a single host for services and info"""
        try:
            # Quick ping test
            if not self._ping_host(ip):
                return None
            
            host_info = {
                'ip_address': ip,
                'hostname': self._get_hostname(ip),
                'services': self._scan_services(ip),
                'os_fingerprint': self._fingerprint_os(ip),
                'last_seen': datetime.now().isoformat(),
                'response_time': self._measure_response_time(ip)
            }
            
            return host_info
            
        except Exception as e:
            logger.debug(f"Host scan error for {ip}: {e}")
            return None
    
    def _ping_host(self, ip: str) -> bool:
        """Quick ping test to check if host is alive"""
        try:
            # Windows ping command
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '1000', ip],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.returncode == 0
            
        except:
            return False
    
    def _get_hostname(self, ip: str) -> str:
        """Get hostname for IP address"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return f"host-{ip.replace('.', '-')}"
    
    def _scan_services(self, ip: str) -> List[Dict]:
        """Scan common ports for services"""
        common_ports = [
            (21, 'FTP'), (22, 'SSH'), (23, 'Telnet'), (25, 'SMTP'),
            (53, 'DNS'), (80, 'HTTP'), (110, 'POP3'), (143, 'IMAP'),
            (443, 'HTTPS'), (993, 'IMAPS'), (995, 'POP3S'),
            (135, 'RPC'), (139, 'NetBIOS'), (445, 'SMB'),
            (1433, 'MSSQL'), (3306, 'MySQL'), (3389, 'RDP'),
            (5432, 'PostgreSQL'), (6379, 'Redis'), (27017, 'MongoDB')
        ]
        
        services = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_port = {
                executor.submit(self._check_port, ip, port): (port, service)
                for port, service in common_ports
            }
            
            for future in concurrent.futures.as_completed(future_to_port):
                port, service = future_to_port[future]
                try:
                    if future.result():
                        services.append({
                            'port': port,
                            'service': service,
                            'state': 'open'
                        })
                except:
                    pass
        
        return services
    
    def _check_port(self, ip: str, port: int) -> bool:
        """Check if a specific port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _fingerprint_os(self, ip: str) -> str:
        """Basic OS fingerprinting"""
        try:
            # Check for common Windows services
            if self._check_port(ip, 135) and self._check_port(ip, 445):
                return "Windows"
            
            # Check for common Linux services
            if self._check_port(ip, 22):
                return "Linux/Unix"
            
            # Check for web services
            if self._check_port(ip, 80) or self._check_port(ip, 443):
                return "Web Server"
            
            # Check for network devices
            if self._check_port(ip, 23) and not self._check_port(ip, 80):
                return "Network Device"
            
            return "Unknown"
            
        except:
            return "Unknown"
    
    def _measure_response_time(self, ip: str) -> float:
        """Measure response time to host"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect_ex((ip, 80))
            sock.close()
            return round((time.time() - start_time) * 1000, 2)  # ms
        except:
            return -1
    
    def get_discovery_results(self) -> Dict[str, Any]:
        """Get current network discovery results"""
        return {
            'discovered_hosts': dict(self.discovered_hosts),
            'total_hosts': len(self.discovered_hosts),
            'last_scan': datetime.now().isoformat(),
            'scan_status': 'active' if self.running else 'stopped'
        }
    
    def get_network_topology_data(self) -> Dict[str, Any]:
        """Get network topology data for server"""
        topology_data = []
        
        for ip, host_info in self.discovered_hosts.items():
            topology_data.append({
                'hostname': host_info.get('hostname'),
                'ipAddress': ip,
                'platform': host_info.get('os_fingerprint', 'Unknown'),
                'services': [s.get('service') for s in host_info.get('services', [])],
                'ports': [s.get('port') for s in host_info.get('services', [])],
                'responseTime': host_info.get('response_time', -1),
                'lastSeen': host_info.get('last_seen'),
                'discoveredBy': 'network_scan'
            })
        
        return {
            'networkTopology': topology_data,
            'scanMetadata': {
                'totalHosts': len(topology_data),
                'lastScan': datetime.now().isoformat(),
                'scannerStatus': 'active' if self.running else 'stopped'
            }
        }
