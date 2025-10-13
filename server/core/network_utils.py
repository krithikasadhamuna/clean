"""
Network utilities for IP address detection
"""

import socket
import platform
import subprocess
import re
from typing import Optional


def get_enhanced_ip_address() -> str:
    """
    Enhanced IP address detection that tries multiple methods
    to find the best non-loopback IP address
    """
    try:
        # Method 1: Try to connect to a remote address to get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            if local_ip and not local_ip.startswith('127.'):
                return local_ip
    except:
        pass
    
    try:
        # Method 2: Get hostname and resolve it
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip and not local_ip.startswith('127.'):
            return local_ip
    except:
        pass
    
    try:
        # Method 3: Platform-specific detection
        if platform.system() == "Windows":
            # Windows: use ipconfig
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Look for IPv4 addresses
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'IPv4 Address' in line or 'IP Address' in line:
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            ip = ip_match.group(1)
                            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                return ip
        else:
            # Linux/Mac: use ifconfig or ip
            try:
                result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Look for inet addresses
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'inet ' in line and not '127.0.0.1' in line:
                            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                            if ip_match:
                                ip = ip_match.group(1)
                                if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                    return ip
            except:
                # Fallback to ifconfig
                result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'inet ' in line and not '127.0.0.1' in line:
                            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                            if ip_match:
                                ip = ip_match.group(1)
                                if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                    return ip
    except:
        pass
    
    # Fallback to localhost
    return "127.0.0.1"


def get_local_ip() -> str:
    """Simple local IP detection"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"


def get_network_interfaces() -> list:
    """Get list of network interfaces and their IP addresses"""
    interfaces = []
    
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_interface = None
                for line in lines:
                    if 'adapter' in line.lower() or 'interface' in line.lower():
                        current_interface = line.strip()
                    elif 'IPv4 Address' in line or 'IP Address' in line:
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match and current_interface:
                            interfaces.append({
                                'name': current_interface,
                                'ip': ip_match.group(1),
                                'type': 'ethernet' if 'ethernet' in current_interface.lower() else 'wireless'
                            })
        else:
            # Linux/Mac
            try:
                result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    current_interface = None
                    for line in lines:
                        if line.strip().startswith(('1:', '2:', '3:')) and ':' in line:
                            current_interface = line.split(':')[1].strip()
                        elif 'inet ' in line and current_interface:
                            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                            if ip_match:
                                interfaces.append({
                                    'name': current_interface,
                                    'ip': ip_match.group(1),
                                    'type': 'ethernet'
                                })
            except:
                pass
    except:
        pass
    
    return interfaces
