#!/usr/bin/env python3
"""
Enhanced Threat Scoring System
Fixes scoring logic, severity calculation, and adds context awareness
Implements all critical improvements from security analysis
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class EnhancedThreatScorer:
    """
    Enhanced threat scoring with weighted maximum approach
    Priority: Zero false negatives (never miss real threats)
    """
    
    def __init__(self):
        # Detection patterns with base scores
        self.detection_patterns = {
            'attack_tools': {
                'patterns': [
                    'nmap', 'sqlmap', 'metasploit', 'msfconsole', 'exploit',
                    'nikto', 'dirb', 'gobuster', 'hydra', 'john',
                    'mimikatz', 'psexec', 'wmic', 'powershell -enc',
                    'certutil -decode', 'bitsadmin', 'regsvr32'
                ],
                'base_score': 0.7,
                'threat_type': 'attack_tool_usage'
            },
            'suspicious_commands': {
                'patterns': [
                    'whoami', 'net user', 'net localgroup', 'net group',
                    'tasklist', 'ps aux', 'netstat', 'arp -a',
                    'ipconfig', 'ifconfig', 'route print', 'cat /etc/passwd',
                    'cat /etc/shadow', 'sudo -l', 'find / -perm',
                    'chmod +x', 'wget', 'curl', 'nc -', 'netcat'
                ],
                'base_score': 0.4,
                'threat_type': 'reconnaissance'
            },
            'malicious_patterns': {
                'patterns': [
                    'reverse shell', 'bind shell', 'backdoor', 'rootkit',
                    'privilege escalation', 'lateral movement', 'persistence',
                    'credential dump', 'password crack', 'hash dump',
                    'buffer overflow', 'code injection', 'sql injection',
                    'xss', 'csrf', 'directory traversal', 'file inclusion'
                ],
                'base_score': 0.8,
                'threat_type': 'active_attack'
            },
            'network_attacks': {
                'patterns': [
                    'port scan', 'vulnerability scan', 'brute force',
                    'dos attack', 'ddos', 'man in the middle',
                    'arp spoofing', 'dns poisoning', 'packet injection'
                ],
                'base_score': 0.6,
                'threat_type': 'network_attack'
            },
            'system_compromise': {
                'patterns': [
                    'malware', 'virus', 'trojan', 'ransomware',
                    'keylogger', 'spyware', 'adware', 'botnet',
                    'c2 server', 'command and control', 'exfiltration'
                ],
                'base_score': 0.9,
                'threat_type': 'system_compromise'
            },
            'auth_failures': {
                'patterns': [
                    'failed login', 'authentication failed', 'invalid credentials',
                    'access denied', 'unauthorized access', 'permission denied',
                    'login attempt', 'brute force'
                ],
                'base_score': 0.5,
                'threat_type': 'authentication_attack'
            }
        }
        
        # Asset criticality multipliers
        self.asset_criticality = {
            'domain_controller': 2.0,
            'database_server': 1.8,
            'file_server': 1.5,
            'web_server': 1.3,
            'workstation': 1.0,
            'test_system': 0.8
        }
        
        # Deduplication cache (detection_hash -> (timestamp, count))
        self.detection_cache = {}
        self.dedup_window = timedelta(minutes=60)
        
        # Cross-host attack tracking
        self.attack_patterns = defaultdict(list)
        self.correlation_window = timedelta(minutes=30)
    
    def calculate_threat_score(self, message: str, source: str, log_entry: Dict,
                              agent_id: str = None, hostname: str = None, 
                              ip_address: str = None) -> Dict[str, Any]:
        """
        Calculate threat score using weighted maximum approach
        Returns enhanced threat assessment with context
        """
        
        message_lower = message.lower()
        source_lower = source.lower()
        
        # Collect all matched patterns with their scores
        matched_patterns = []
        indicators = []
        threat_types = set()
        
        # 1. Pattern matching (collect all matches)
        for category, config in self.detection_patterns.items():
            for pattern in config['patterns']:
                if pattern in message_lower:
                    matched_patterns.append({
                        'pattern': pattern,
                        'category': category,
                        'base_score': config['base_score'],
                        'threat_type': config['threat_type']
                    })
                    indicators.append(f"{category}: {pattern}")
                    threat_types.add(config['threat_type'])
        
        # 2. Container/Attack context
        if log_entry.get('container_context') or 'attackcontainer' in source_lower:
            matched_patterns.append({
                'pattern': 'container_attack',
                'category': 'container_context',
                'base_score': 0.5,
                'threat_type': 'container_attack'
            })
            indicators.append("Container attack context")
            threat_types.add('container_attack')
        
        # 3. Calculate weighted maximum score (FIXED SCORING LOGIC)
        if not matched_patterns:
            return {
                'threat_score': 0.0,
                'threat_type': 'benign',
                'indicators': [],
                'matched_patterns': 0,
                'severity': 'info',
                'analysis_type': 'signature_detection'
            }
        
        # Get maximum base score
        base_scores = [p['base_score'] for p in matched_patterns]
        max_score = max(base_scores)
        primary_threat_type = max(matched_patterns, key=lambda x: x['base_score'])['threat_type']
        
        # Add correlation boost for multiple indicators (10% per additional indicator)
        correlation_count = len(matched_patterns)
        if correlation_count > 1:
            correlation_boost = (correlation_count - 1) * (max_score * 0.1)
            threat_score = min(max_score + correlation_boost, 1.0)
        else:
            threat_score = max_score
        
        # 4. Apply context enhancements
        context_adjustments = {
            'asset_multiplier': 1.0,
            'temporal_boost': 1.0,
            'deduplication_factor': 1.0,
            'campaign_boost': 0.0
        }
        
        # Asset-based risk scoring
        if hostname:
            asset_multiplier = self._calculate_asset_multiplier(hostname)
            context_adjustments['asset_multiplier'] = asset_multiplier
            threat_score = min(threat_score * asset_multiplier, 1.0)
        
        # Temporal context (off-hours boost)
        temporal_boost = self._calculate_temporal_boost(datetime.now())
        context_adjustments['temporal_boost'] = temporal_boost
        threat_score = min(threat_score * temporal_boost, 1.0)
        
        # Deduplication check
        if agent_id and message:
            is_duplicate, occurrence_count = self._check_deduplication(
                agent_id, message, primary_threat_type, datetime.now()
            )
            context_adjustments['deduplication_factor'] = occurrence_count
            
            # Boost severity if many repetitions (possible persistence/campaign)
            if occurrence_count > 10:
                threat_score = min(threat_score + 0.1, 1.0)
        
        # Cross-host correlation check
        if agent_id and hostname and threat_score > 0.5:
            campaign_info = self._check_cross_host_correlation(
                agent_id, hostname, ip_address, primary_threat_type,
                threat_score, datetime.now()
            )
            if campaign_info['is_campaign']:
                context_adjustments['campaign_boost'] = campaign_info['severity_boost']
                threat_score = min(threat_score + campaign_info['severity_boost'], 1.0)
                indicators.append(f"Campaign detected: {campaign_info['affected_hosts']} hosts")
        
        # 5. Calculate consistent severity
        severity = self._calculate_severity(threat_score, primary_threat_type)
        
        return {
            'threat_score': round(threat_score, 3),
            'threat_type': primary_threat_type,
            'indicators': indicators,
            'matched_patterns': correlation_count,
            'severity': severity,
            'context_adjustments': context_adjustments,
            'analysis_type': 'enhanced_signature_detection'
        }
    
    def _calculate_asset_multiplier(self, hostname: str) -> float:
        """Calculate asset criticality multiplier"""
        hostname_lower = hostname.lower()
        
        if 'dc' in hostname_lower or 'domain' in hostname_lower:
            return self.asset_criticality['domain_controller']
        elif 'db' in hostname_lower or 'sql' in hostname_lower:
            return self.asset_criticality['database_server']
        elif 'file' in hostname_lower or 'share' in hostname_lower:
            return self.asset_criticality['file_server']
        elif 'web' in hostname_lower or 'iis' in hostname_lower:
            return self.asset_criticality['web_server']
        elif 'test' in hostname_lower or 'dev' in hostname_lower:
            return self.asset_criticality['test_system']
        else:
            return self.asset_criticality['workstation']
    
    def _calculate_temporal_boost(self, timestamp: datetime) -> float:
        """Calculate temporal risk boost for off-hours activity"""
        hour = timestamp.hour
        day_of_week = timestamp.weekday()  # 0 = Monday, 6 = Sunday
        
        # Define normal business hours
        business_hours = range(8, 18)  # 8 AM to 6 PM
        business_days = range(0, 5)    # Monday to Friday
        
        # Off-hours activity (nights, weekends)
        if hour not in business_hours or day_of_week not in business_days:
            return 1.3  # 30% boost for off-hours
        
        # Extreme off-hours (midnight to 6 AM)
        if hour >= 0 and hour < 6:
            return 1.5  # 50% boost for middle of night
        
        return 1.0  # Normal hours
    
    def _check_deduplication(self, agent_id: str, message: str, 
                           threat_type: str, timestamp: datetime) -> Tuple[bool, int]:
        """
        Check if this is a duplicate detection
        Returns: (is_duplicate, occurrence_count)
        """
        # Create detection hash
        detection_hash = f"{agent_id}_{threat_type}_{hash(message[:100])}"
        
        if detection_hash in self.detection_cache:
            cached_time, count = self.detection_cache[detection_hash]
            
            # If within time window, it's a duplicate
            if timestamp - cached_time < self.dedup_window:
                self.detection_cache[detection_hash] = (cached_time, count + 1)
                return True, count + 1
            else:
                # Outside window, treat as new
                self.detection_cache[detection_hash] = (timestamp, 1)
                return False, 1
        else:
            self.detection_cache[detection_hash] = (timestamp, 1)
            return False, 1
    
    def _check_cross_host_correlation(self, agent_id: str, hostname: str,
                                     ip_address: str, threat_type: str,
                                     threat_score: float, timestamp: datetime) -> Dict:
        """
        Check for cross-host attack patterns (lateral movement, campaigns)
        """
        pattern_key = f"{threat_type}_{ip_address or 'unknown'}"
        
        # Add current detection
        detection_info = {
            'agent_id': agent_id,
            'hostname': hostname,
            'ip_address': ip_address,
            'threat_score': threat_score,
            'timestamp': timestamp
        }
        
        # Get recent detections for this pattern
        recent_detections = self.attack_patterns[pattern_key]
        
        # Filter by time window
        recent_detections = [
            d for d in recent_detections
            if timestamp - d['timestamp'] < self.correlation_window
        ]
        
        # Add current detection
        recent_detections.append(detection_info)
        self.attack_patterns[pattern_key] = recent_detections
        
        # Check for campaign indicators
        unique_hosts = len(set(d['hostname'] for d in recent_detections))
        
        if unique_hosts >= 3:
            # Campaign detected!
            return {
                'is_campaign': True,
                'campaign_type': 'lateral_movement',
                'affected_hosts': unique_hosts,
                'severity_boost': 0.3,  # 30% boost for campaigns
                'recommendation': 'Investigate coordinated attack across multiple hosts'
            }
        
        return {'is_campaign': False}
    
    def _calculate_severity(self, threat_score: float, threat_type: str) -> str:
        """
        Calculate severity based on score AND context
        Consistent severity assignment (FIXED)
        Priority: Never miss real threats (err on higher severity)
        """
        
        # Base severity thresholds
        if threat_score >= 0.85:
            base_severity = 'critical'
        elif threat_score >= 0.65:
            base_severity = 'high'
        elif threat_score >= 0.45:
            base_severity = 'medium'
        elif threat_score >= 0.25:
            base_severity = 'low'
        else:
            base_severity = 'info'
        
        # Context-based severity boost for zero false negatives
        critical_types = ['system_compromise', 'active_attack', 'ransomware', 'malware']
        if threat_type in critical_types and threat_score >= 0.6:
            return 'critical'  # Boost severity for critical threat types
        
        return base_severity
    
    def cleanup_old_entries(self, current_time: datetime):
        """Clean up old cache entries to prevent memory bloat"""
        # Clean deduplication cache
        old_detection_keys = [
            k for k, (t, _) in self.detection_cache.items()
            if current_time - t > self.dedup_window * 2
        ]
        for key in old_detection_keys:
            del self.detection_cache[key]
        
        # Clean attack pattern cache
        for pattern_key in list(self.attack_patterns.keys()):
            recent = [
                d for d in self.attack_patterns[pattern_key]
                if current_time - d['timestamp'] < self.correlation_window * 2
            ]
            if recent:
                self.attack_patterns[pattern_key] = recent
            else:
                del self.attack_patterns[pattern_key]


# Global instance
enhanced_threat_scorer = EnhancedThreatScorer()


