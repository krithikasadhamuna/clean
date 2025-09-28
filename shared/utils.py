"""
Shared utilities for log forwarding system
"""

import os
import sys
import platform
import socket
import logging
import asyncio
import gzip
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
import psutil


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup logging configuration"""
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information"""
    
    try:
        # Basic system info
        system_info = {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
        }
        
        # Network info
        try:
            system_info['ip_address'] = get_local_ip()
            system_info['mac_address'] = get_mac_address()
        except Exception:
            system_info['ip_address'] = 'unknown'
            system_info['mac_address'] = 'unknown'
        
        # System resources
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_info.update({
                'total_memory_gb': round(memory.total / (1024**3), 2),
                'available_memory_gb': round(memory.available / (1024**3), 2),
                'cpu_count': psutil.cpu_count(),
                'disk_total_gb': round(disk.total / (1024**3), 2),
                'disk_free_gb': round(disk.free / (1024**3), 2),
            })
        except Exception:
            pass
        
        # OS-specific info
        if platform.system() == "Windows":
            system_info.update(get_windows_info())
        elif platform.system() == "Linux":
            system_info.update(get_linux_info())
        
        return system_info
        
    except Exception as e:
        logging.error(f"Failed to get system info: {e}")
        return {
            'hostname': 'unknown',
            'platform': 'unknown',
            'error': str(e)
        }


def get_local_ip() -> str:
    """Get local IP address"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def get_mac_address() -> str:
    """Get MAC address"""
    try:
        import uuid
        mac = uuid.getnode()
        return ':'.join(f"{(mac >> (8*i)) & 0xff:02x}" for i in range(6)[::-1])
    except Exception:
        return "unknown"


def get_windows_info() -> Dict[str, Any]:
    """Get Windows-specific information"""
    info = {}
    
    try:
        import winreg
        
        # Windows version from registry
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        try:
            info['windows_version'] = winreg.QueryValueEx(key, "ProductName")[0]
            info['windows_build'] = winreg.QueryValueEx(key, "CurrentBuild")[0]
        except FileNotFoundError:
            pass
        finally:
            winreg.CloseKey(key)
            
    except ImportError:
        pass
    except Exception as e:
        info['windows_info_error'] = str(e)
    
    return info


def get_linux_info() -> Dict[str, Any]:
    """Get Linux-specific information"""
    info = {}
    
    try:
        # Read /etc/os-release
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key in ['NAME', 'VERSION', 'ID', 'VERSION_ID']:
                            info[f'linux_{key.lower()}'] = value.strip('"')
        
        # Kernel version
        if os.path.exists('/proc/version'):
            with open('/proc/version', 'r') as f:
                info['kernel_version'] = f.read().strip()
                
    except Exception as e:
        info['linux_info_error'] = str(e)
    
    return info


def compress_data(data: Union[str, bytes]) -> bytes:
    """Compress data using gzip"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return gzip.compress(data)


def decompress_data(compressed_data: bytes) -> str:
    """Decompress gzip data"""
    return gzip.decompress(compressed_data).decode('utf-8')


def hash_data(data: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """Generate hash of data"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem operations"""
    import re
    
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = filename.strip('._')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename or 'unknown'


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse various timestamp formats"""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%b %d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if necessary"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes"""
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def is_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
    """Check if a port is open on a host"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.error, socket.timeout):
        return False


async def retry_async(func, max_retries: int = 3, delay: float = 1.0, 
                     backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """Retry async function with exponential backoff"""
    
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            if attempt == max_retries - 1:
                raise e
            
            wait_time = delay * (backoff_factor ** attempt)
            logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)


def format_bytes(bytes_count: int) -> str:
    """Format bytes count in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def truncate_string(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely dump object to JSON string"""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return default


class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if call is allowed"""
        now = datetime.utcnow().timestamp()
        
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        # Check if we can make another call
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
