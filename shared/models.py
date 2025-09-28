"""
Shared data models for log forwarding system
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class LogLevel(Enum):
    """Log severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogSource(Enum):
    """Log source types"""
    WINDOWS_SYSTEM = "windows_system"
    LINUX_SYSTEM = "linux_system"
    ATTACK_AGENT = "attack_agent"
    APPLICATION = "application"
    NETWORK = "network"
    SECURITY = "security"


class ThreatLevel(Enum):
    """Threat severity levels"""
    BENIGN = "benign"
    SUSPICIOUS = "suspicious" 
    MALICIOUS = "malicious"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Individual log entry model"""
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    source: LogSource = LogSource.APPLICATION
    
    # Timestamps
    timestamp: datetime = field(default_factory=datetime.utcnow)
    collected_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Content
    message: str = ""
    raw_data: str = ""
    level: LogLevel = LogLevel.INFO
    
    # Structured data
    parsed_data: Dict[str, Any] = field(default_factory=dict)
    enriched_data: Dict[str, Any] = field(default_factory=dict)
    
    # Security context
    event_id: Optional[str] = None
    event_type: Optional[str] = None
    process_info: Dict[str, Any] = field(default_factory=dict)
    network_info: Dict[str, Any] = field(default_factory=dict)
    
    # Attack context (if from attack agent)
    attack_technique: Optional[str] = None
    attack_command: Optional[str] = None
    attack_result: Optional[str] = None
    
    # Detection results
    threat_score: float = 0.0
    threat_level: ThreatLevel = ThreatLevel.BENIGN
    detection_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'source': self.source.value,
            'timestamp': self.timestamp.isoformat(),
            'collected_at': self.collected_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'message': self.message,
            'raw_data': self.raw_data,
            'level': self.level.value,
            'parsed_data': self.parsed_data,
            'enriched_data': self.enriched_data,
            'event_id': self.event_id,
            'event_type': self.event_type,
            'process_info': self.process_info,
            'network_info': self.network_info,
            'attack_technique': self.attack_technique,
            'attack_command': self.attack_command,
            'attack_result': self.attack_result,
            'threat_score': self.threat_score,
            'threat_level': self.threat_level.value,
            'detection_results': self.detection_results,
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create from dictionary"""
        entry = cls()
        entry.id = data.get('id', str(uuid.uuid4()))
        entry.agent_id = data.get('agent_id', '')
        entry.source = LogSource(data.get('source', 'application'))
        entry.timestamp = datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat()))
        entry.collected_at = datetime.fromisoformat(data.get('collected_at', datetime.utcnow().isoformat()))
        if data.get('processed_at'):
            entry.processed_at = datetime.fromisoformat(data['processed_at'])
        entry.message = data.get('message', '')
        entry.raw_data = data.get('raw_data', '')
        entry.level = LogLevel(data.get('level', 'info'))
        entry.parsed_data = data.get('parsed_data', {})
        entry.enriched_data = data.get('enriched_data', {})
        entry.event_id = data.get('event_id')
        entry.event_type = data.get('event_type')
        entry.process_info = data.get('process_info', {})
        entry.network_info = data.get('network_info', {})
        entry.attack_technique = data.get('attack_technique')
        entry.attack_command = data.get('attack_command')
        entry.attack_result = data.get('attack_result')
        entry.threat_score = data.get('threat_score', 0.0)
        entry.threat_level = ThreatLevel(data.get('threat_level', 'benign'))
        entry.detection_results = data.get('detection_results', [])
        entry.tags = data.get('tags', [])
        entry.metadata = data.get('metadata', {})
        return entry


@dataclass
class AgentInfo:
    """Agent information model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hostname: str = ""
    ip_address: str = ""
    platform: str = ""
    os_version: str = ""
    agent_version: str = "1.0.0"
    
    # Status
    status: str = "online"
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    last_log_sent: Optional[datetime] = None
    
    # Capabilities
    capabilities: List[str] = field(default_factory=list)
    log_sources: List[str] = field(default_factory=list)
    
    # Configuration
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    # Security context
    security_zone: str = "internal"
    importance: str = "medium"
    
    # Statistics
    logs_sent_count: int = 0
    bytes_sent: int = 0
    errors_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'platform': self.platform,
            'os_version': self.os_version,
            'agent_version': self.agent_version,
            'status': self.status,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'last_log_sent': self.last_log_sent.isoformat() if self.last_log_sent else None,
            'capabilities': self.capabilities,
            'log_sources': self.log_sources,
            'configuration': self.configuration,
            'security_zone': self.security_zone,
            'importance': self.importance,
            'logs_sent_count': self.logs_sent_count,
            'bytes_sent': self.bytes_sent,
            'errors_count': self.errors_count
        }


@dataclass
class DetectionResult:
    """Detection analysis result"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    log_entry_id: str = ""
    
    # Detection info
    threat_detected: bool = False
    confidence_score: float = 0.0
    threat_type: str = ""
    severity: str = "low"
    
    # Analysis details
    ml_results: Dict[str, Any] = field(default_factory=dict)
    ai_analysis: Dict[str, Any] = field(default_factory=dict)
    rule_matches: List[str] = field(default_factory=list)
    
    # MITRE ATT&CK mapping
    mitre_techniques: List[str] = field(default_factory=list)
    tactics: List[str] = field(default_factory=list)
    
    # Context
    analyst_notes: str = ""
    false_positive: bool = False
    verified: bool = False
    
    # Timestamps
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'log_entry_id': self.log_entry_id,
            'threat_detected': self.threat_detected,
            'confidence_score': self.confidence_score,
            'threat_type': self.threat_type,
            'severity': self.severity,
            'ml_results': self.ml_results,
            'ai_analysis': self.ai_analysis,
            'rule_matches': self.rule_matches,
            'mitre_techniques': self.mitre_techniques,
            'tactics': self.tactics,
            'analyst_notes': self.analyst_notes,
            'false_positive': self.false_positive,
            'verified': self.verified,
            'detected_at': self.detected_at.isoformat()
        }


@dataclass
class LogBatch:
    """Batch of log entries for efficient processing"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    logs: List[LogEntry] = field(default_factory=list)
    batch_size: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    compressed: bool = False
    
    def __post_init__(self):
        self.batch_size = len(self.logs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for transmission"""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'logs': [log.to_dict() for log in self.logs],
            'batch_size': self.batch_size,
            'created_at': self.created_at.isoformat(),
            'compressed': self.compressed
        }
