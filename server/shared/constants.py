"""
Constants for AI SOC Platform
"""

# API Configuration
DEFAULT_SERVER_PORT = 8080
DEFAULT_CLIENT_RECONNECT_INTERVAL = 30
DEFAULT_HEARTBEAT_INTERVAL = 60

# Log Processing
DEFAULT_BATCH_SIZE = 100
DEFAULT_FLUSH_INTERVAL = 5
MAX_LOG_MESSAGE_LENGTH = 10000
MAX_BATCH_SIZE = 1000

# Detection Thresholds
DEFAULT_ANOMALY_THRESHOLD = 0.7
DEFAULT_MALWARE_CONFIDENCE = 0.8
DEFAULT_BEHAVIORAL_RISK = 0.6
DEFAULT_NETWORK_ANOMALY = 0.75

# Container Configuration
MAX_CONTAINERS_PER_AGENT = 5
DEFAULT_CONTAINER_TIMEOUT = 300
CONTAINER_LOG_RETENTION_HOURS = 24

# Command Queue
DEFAULT_COMMAND_TIMEOUT = 300
MAX_CONCURRENT_COMMANDS = 10
COMMAND_CLEANUP_INTERVAL = 3600

# Network Topology
TOPOLOGY_CACHE_TTL = 300
TOPOLOGY_REFRESH_INTERVAL = 300
NETWORK_SCAN_TIMEOUT = 60

# Security
MAX_FAILED_ATTEMPTS = 5
SESSION_TIMEOUT = 3600
API_RATE_LIMIT = 1000

# File Paths
DEFAULT_DB_PATH = "soc_database.db"
DEFAULT_MODELS_PATH = "ml_models"
DEFAULT_LOGS_PATH = "logs"
DEFAULT_CONFIG_PATH = "config"

# Agent Types
AI_AGENT_TYPES = ['attack', 'detection', 'intelligence', 'deploy', 'orchestration']
ENDPOINT_AGENT_TYPES = ['endpoint', 'server', 'critical_endpoint']

# Status Values
AGENT_STATUS_VALUES = ['active', 'idle', 'inactive', 'offline', 'development']
COMMAND_STATUS_VALUES = ['queued', 'sent', 'executing', 'completed', 'failed', 'timeout', 'cancelled']

# MITRE ATT&CK
MITRE_TECHNIQUE_PATTERN = r'T\d{4}(?:\.\d{3})?'

# Log Sources
SUPPORTED_LOG_SOURCES = [
    'windows_system', 'linux_system', 'application', 
    'security', 'network', 'container', 'attack_agent'
]

# Threat Levels
THREAT_LEVELS = ['benign', 'suspicious', 'malicious', 'critical']
SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical']
