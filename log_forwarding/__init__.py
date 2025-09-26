"""
AI SOC Platform - Log Forwarding System
Comprehensive log collection, forwarding, and real-time threat detection
"""

__version__ = "1.0.0"
__author__ = "AI SOC Team"

from .shared.models import LogEntry, AgentInfo, DetectionResult
from .shared.config import Config
from .shared.utils import setup_logging, get_system_info

__all__ = [
    'LogEntry',
    'AgentInfo', 
    'DetectionResult',
    'Config',
    'setup_logging',
    'get_system_info'
]
