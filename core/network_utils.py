"""
Enhanced Network Discovery and IP Detection Utilities
Provides improved IP address detection and network interface analysis
"""

import socket
import platform
import subprocess
import psutil
import logging
from typing import Dict, List, Optional, Tuple
from ipaddress import ip_address, ip_network
import json

logger = logging.getLogger(__name__)


class NetworkDiscovery:
    """Enhanced network discovery with improved IP detection"""
    
    def __init__(self):
        self.system_platform = platform.system().lower()
        self.detected_interfaces = []
        self.primary_ip = None
        
    def get_enhanced_ip_address(self, fallback_ip: str = '127.0.0.1') -> str:
        """
        Get the best available IP address with multiple detection methods
        
        Args:
            fallback_ip: Fallback IP if no better option is found
            
        Returns:
            Best detected IP address
        """
        try:
            # Method 1: Try socket connection to external service
            external_ip = self._get_external_ip()
            if external_ip and external_ip != '127.0.0.1':
                logger.info(f"External IP detected: {external_ip}")
                return external_ip
                
            # Method 2: Analyze network interfaces
            interface_ip = self._get_best_interface_ip()
            if interface_ip and interface_ip != '127.0.0.1':
                logger.info(f"Interface IP detected: {interface_ip}")
                return interface_ip
                
            # Method 3: Try socket hostname resolution
            hostname_ip = self._get_hostname_ip()
            if hostname_ip and hostname_ip != '127.0.0.1':
                logger.info(f"Hostname IP detected: {hostname_ip}")
                return hostname_ip
                
            # Method 4: Platform-specific detection
            platform_ip = self._get_platform_specific_ip()
            if platform_ip and platform_ip != '127.0.0.1':
                logger.info(f"Platform IP detected: {platform_ip}")
                return platform_ip
                
            logger.warning(f"Using fallback IP: {fallback_ip}")
            return fallback_ip
            
        except Exception as e:
            logger.error(f"IP detection failed: {e}")
            return fallback_ip
    
    def _get_external_ip(self) -> Optional[str]:
        """Get external IP by connecting to external service"""
        try:
            # Try multiple external services for reliability
            external_services = [
                ('8.8.8.8', 53),  # Google DNS
                ('1.1.1.1', 53),  # Cloudflare DNS
                ('208.67.222.222', 53)  # OpenDNS
            ]
            
            for service_ip, port in external_services:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                        s.settimeout(2)
                        s.connect((service_ip, port))
                        local_ip = s.getsockname()[0]
                        if local_ip and local_ip != '127.0.0.1':
                            return local_ip
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"External IP detection failed: {e}")
            
        return None
    
    def _get_best_interface_ip(self) -> Optional[str]:
        """Get the best IP from network interfaces"""
        try:
            interfaces = self._get_network_interfaces()
            
            # Priority order for IP selection
            priority_patterns = [
                r'^192\.168\.',      # Private class C
                r'^10\.',            # Private class A
                r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # Private class B
                r'^169\.254\.',      # Link-local
                r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'  # Any other valid IP
            ]
            
            for pattern in priority_patterns:
                for interface in interfaces:
                    ip = interface.get('ip')
                    if ip and self._matches_pattern(ip, pattern) and ip != '127.0.0.1':
                        logger.debug(f"Selected IP {ip} from interface {interface.get('name')}")
                        return ip
                        
        except Exception as e:
            logger.debug(f"Interface IP detection failed: {e}")
            
        return None
    
    def _get_hostname_ip(self) -> Optional[str]:
        """Get IP from hostname resolution"""
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip and ip != '127.0.0.1':
                return ip
        except Exception as e:
            logger.debug(f"Hostname IP detection failed: {e}")
            
        return None
    
    def _get_platform_specific_ip(self) -> Optional[str]:
        """Platform-specific IP detection methods"""
        try:
            if self.system_platform == 'windows':
                return self._get_windows_ip()
            elif self.system_platform == 'linux':
                return self._get_linux_ip()
            elif self.system_platform == 'darwin':  # macOS
                return self._get_macos_ip()
        except Exception as e:
            logger.debug(f"Platform-specific IP detection failed: {e}")
            
        return None
    
    def _get_windows_ip(self) -> Optional[str]:
        """Windows-specific IP detection"""
        try:
            # Use ipconfig command
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'IPv4 Address' in line and '127.0.0.1' not in line:
                        # Extract IP from next line
                        if i + 1 < len(lines):
                            ip_line = lines[i + 1].strip()
                            if ':' in ip_line:
                                ip = ip_line.split(':')[-1].strip()
                                if self._is_valid_ip(ip):
                                    return ip
        except Exception as e:
            logger.debug(f"Windows IP detection failed: {e}")
            
        return None
    
    def _get_linux_ip(self) -> Optional[str]:
        """Linux-specific IP detection"""
        try:
            # Try ip command first
            result = subprocess.run(['ip', 'route', 'get', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'src' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'src' and i + 1 < len(parts):
                                ip = parts[i + 1]
                                if self._is_valid_ip(ip):
                                    return ip
                                    
            # Fallback to ifconfig
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'inet ' in line and '127.0.0.1' not in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'inet' and i + 1 < len(parts):
                                ip = parts[i + 1]
                                if self._is_valid_ip(ip):
                                    return ip
        except Exception as e:
            logger.debug(f"Linux IP detection failed: {e}")
            
        return None
    
    def _get_macos_ip(self) -> Optional[str]:
        """macOS-specific IP detection"""
        try:
            # Use ifconfig command
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'inet ' in line and '127.0.0.1' not in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'inet' and i + 1 < len(parts):
                                ip = parts[i + 1]
                                if self._is_valid_ip(ip):
                                    return ip
        except Exception as e:
            logger.debug(f"macOS IP detection failed: {e}")
            
        return None
    
    def _get_network_interfaces(self) -> List[Dict]:
        """Get detailed network interface information"""
        try:
            interfaces = []
            
            # Use psutil for cross-platform interface detection
            for interface_name, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        interface_info = {
                            'name': interface_name,
                            'ip': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        }
                        interfaces.append(interface_info)
                        
            self.detected_interfaces = interfaces
            return interfaces
            
        except Exception as e:
            logger.error(f"Network interface detection failed: {e}")
            return []
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _matches_pattern(self, ip: str, pattern: str) -> bool:
        """Check if IP matches regex pattern"""
        import re
        try:
            return bool(re.match(pattern, ip))
        except:
            return False
    
    def get_network_topology_info(self) -> Dict:
        """Get comprehensive network topology information"""
        try:
            interfaces = self._get_network_interfaces()
            primary_ip = self.get_enhanced_ip_address()
            
            topology_info = {
                'primary_ip': primary_ip,
                'hostname': socket.gethostname(),
                'platform': self.system_platform,
                'interfaces': interfaces,
                'detection_method': 'enhanced',
                'timestamp': self._get_timestamp()
            }
            
            return topology_info
            
        except Exception as e:
            logger.error(f"Network topology detection failed: {e}")
            return {
                'primary_ip': '127.0.0.1',
                'hostname': socket.gethostname(),
                'platform': self.system_platform,
                'interfaces': [],
                'detection_method': 'fallback',
                'error': str(e),
                'timestamp': self._get_timestamp()
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()


def get_enhanced_ip_address(fallback_ip: str = '127.0.0.1') -> str:
    """
    Convenience function to get enhanced IP address
    
    Args:
        fallback_ip: Fallback IP if detection fails
        
    Returns:
        Best detected IP address
    """
    discovery = NetworkDiscovery()
    return discovery.get_enhanced_ip_address(fallback_ip)


def get_network_topology_info() -> Dict:
    """
    Convenience function to get network topology information
    
    Returns:
        Comprehensive network topology information
    """
    discovery = NetworkDiscovery()
    return discovery.get_network_topology_info()
