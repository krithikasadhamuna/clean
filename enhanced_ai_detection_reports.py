#!/usr/bin/env python3
"""
Enhanced AI Detection Report System for CodeGrey SOC Platform
Comprehensive threat analysis, MITRE ATT&CK mapping, and executive summaries
"""

import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class ThreatIntelligence:
    """Threat intelligence data for correlation"""
    ioc_type: str  # IP, Domain, Hash, etc.
    ioc_value: str
    threat_type: str
    confidence: float
    source: str
    first_seen: datetime
    last_seen: datetime
    related_threats: List[str] = field(default_factory=list)

@dataclass
class MITREMapping:
    """MITRE ATT&CK technique mapping"""
    technique_id: str
    technique_name: str
    tactic: str
    description: str
    confidence: float
    evidence: List[str] = field(default_factory=list)

@dataclass
class DetectionReport:
    """Comprehensive detection report"""
    report_id: str
    generated_at: datetime
    time_range: Tuple[datetime, datetime]
    
    # Executive Summary
    total_threats: int
    critical_threats: int
    high_threats: int
    medium_threats: int
    low_threats: int
    
    # Threat Analysis
    threat_types: Dict[str, int]
    top_attackers: List[Dict[str, Any]]
    affected_assets: List[Dict[str, Any]]
    
    # MITRE ATT&CK Analysis
    mitre_techniques: List[MITREMapping]
    attack_campaigns: List[Dict[str, Any]]
    
    # Threat Intelligence
    iocs: List[ThreatIntelligence]
    threat_correlations: List[Dict[str, Any]]
    
    # Trends and Statistics
    detection_trends: Dict[str, Any]
    false_positive_rate: float
    analyst_workload: Dict[str, Any]
    
    # Recommendations
    immediate_actions: List[str]
    long_term_recommendations: List[str]
    security_improvements: List[str]

class EnhancedAIDetectionReporter:
    """Enhanced AI Detection Report Generator"""
    
    def __init__(self, db_path: str = "soc_database.db"):
        self.db_path = db_path
        self.mitre_techniques_db = self._load_mitre_techniques()
        self.threat_intelligence_db = self._load_threat_intelligence()
    
    def _load_mitre_techniques(self) -> Dict[str, Dict[str, Any]]:
        """Load MITRE ATT&CK techniques database"""
        return {
            "T1055": {"name": "Process Injection", "tactic": "Defense Evasion", "description": "Injection of malicious code into running processes"},
            "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution", "description": "Use of command line interfaces for execution"},
            "T1071": {"name": "Application Layer Protocol", "tactic": "Command and Control", "description": "Communication using application layer protocols"},
            "T1083": {"name": "File and Directory Discovery", "tactic": "Discovery", "description": "Enumeration of files and directories"},
            "T1105": {"name": "Ingress Tool Transfer", "tactic": "Command and Control", "description": "Transfer of tools from external systems"},
            "T1112": {"name": "Modify Registry", "tactic": "Defense Evasion", "description": "Modification of Windows registry"},
            "T1124": {"name": "System Time Discovery", "tactic": "Discovery", "description": "Gathering system time information"},
            "T1135": {"name": "Network Share Discovery", "tactic": "Discovery", "description": "Discovery of network shares"},
            "T1140": {"name": "Deobfuscate/Decode Files or Information", "tactic": "Defense Evasion", "description": "Deobfuscation of files or information"},
            "T1204": {"name": "User Execution", "tactic": "Execution", "description": "Execution of malicious code by user interaction"},
            "T1218": {"name": "Signed Binary Proxy Execution", "tactic": "Defense Evasion", "description": "Use of signed binaries for malicious purposes"},
            "T1486": {"name": "Data Encrypted for Impact", "tactic": "Impact", "description": "Encryption of data for ransom or destruction"},
            "T1566": {"name": "Phishing", "tactic": "Initial Access", "description": "Social engineering attacks via email or messaging"},
            "T1573": {"name": "Encrypted Channel", "tactic": "Command and Control", "description": "Use of encrypted communication channels"},
            "T1053": {"name": "Scheduled Task/Job", "tactic": "Execution", "description": "Use of scheduled tasks for persistence and execution"},
            "T1070": {"name": "Indicator Removal", "tactic": "Defense Evasion", "description": "Removal of forensic artifacts"},
            "T1082": {"name": "System Information Discovery", "tactic": "Discovery", "description": "Gathering system information"},
            "T1090": {"name": "Proxy", "tactic": "Command and Control", "description": "Use of proxy servers for communication"},
            "T1027": {"name": "Obfuscated Files or Information", "tactic": "Defense Evasion", "description": "Obfuscation of files or information"},
            "T1041": {"name": "Exfiltration Over C2 Channel", "tactic": "Exfiltration", "description": "Data exfiltration over command and control channels"}
        }
    
    def _load_threat_intelligence(self) -> Dict[str, ThreatIntelligence]:
        """Load threat intelligence database"""
        # This would typically load from external threat feeds
        return {}
    
    async def generate_comprehensive_report(self, 
                                          time_range_hours: int = 24,
                                          include_benign: bool = False) -> DetectionReport:
        """Generate comprehensive AI detection report"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        logger.info(f"Generating AI detection report for {start_time} to {end_time}")
        
        # Get detection data
        detections = await self._get_detection_data(start_time, end_time, include_benign)
        
        # Analyze threats
        threat_analysis = self._analyze_threats(detections)
        
        # Map MITRE ATT&CK techniques
        mitre_analysis = self._map_mitre_techniques(detections)
        
        # Correlate threat intelligence
        threat_intel = self._correlate_threat_intelligence(detections)
        
        # Calculate trends
        trends = await self._calculate_trends(start_time, end_time)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(threat_analysis, mitre_analysis, trends)
        
        # Create comprehensive report
        report = DetectionReport(
            report_id=f"ai_detection_report_{int(end_time.timestamp())}",
            generated_at=end_time,
            time_range=(start_time, end_time),
            total_threats=threat_analysis['total_threats'],
            critical_threats=threat_analysis['critical_threats'],
            high_threats=threat_analysis['high_threats'],
            medium_threats=threat_analysis['medium_threats'],
            low_threats=threat_analysis['low_threats'],
            threat_types=threat_analysis['threat_types'],
            top_attackers=threat_analysis['top_attackers'],
            affected_assets=threat_analysis['affected_assets'],
            mitre_techniques=mitre_analysis['techniques'],
            attack_campaigns=mitre_analysis['campaigns'],
            iocs=threat_intel['iocs'],
            threat_correlations=threat_intel['correlations'],
            detection_trends=trends,
            false_positive_rate=trends.get('false_positive_rate', 0.0),
            analyst_workload=trends.get('analyst_workload', {}),
            immediate_actions=recommendations['immediate'],
            long_term_recommendations=recommendations['long_term'],
            security_improvements=recommendations['improvements']
        )
        
        return report
    
    async def _get_detection_data(self, start_time: datetime, end_time: datetime, 
                                include_benign: bool = False) -> List[Dict[str, Any]]:
        """Get detection data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query
            where_clause = "WHERE dr.detected_at >= ? AND dr.detected_at <= ?"
            if not include_benign:
                where_clause += " AND dr.threat_detected = 1"
            
            query = f'''
                SELECT 
                    dr.id, dr.threat_detected, dr.confidence_score, dr.threat_type,
                    dr.severity, dr.detected_at, dr.ml_results, dr.ai_analysis,
                    dr.mitre_techniques, dr.tactics, dr.rule_matches,
                    le.agent_id, le.source, le.message, le.timestamp,
                    a.hostname, a.ip_address, a.platform, a.status
                FROM detection_results dr
                JOIN log_entries le ON dr.log_entry_id = le.id
                LEFT JOIN agents a ON le.agent_id = a.id
                {where_clause}
                ORDER BY dr.detected_at DESC
            '''
            
            cursor.execute(query, (start_time.isoformat(), end_time.isoformat()))
            
            detections = []
            for row in cursor.fetchall():
                detection = {
                    'id': row[0],
                    'threat_detected': bool(row[1]),
                    'confidence_score': row[2],
                    'threat_type': row[3],
                    'severity': row[4],
                    'detected_at': row[5],
                    'ml_results': json.loads(row[6]) if row[6] else {},
                    'ai_analysis': json.loads(row[7]) if row[7] else {},
                    'mitre_techniques': json.loads(row[8]) if row[8] else [],
                    'tactics': json.loads(row[9]) if row[9] else [],
                    'rule_matches': json.loads(row[10]) if row[10] else [],
                    'agent_id': row[11],
                    'source': row[12],
                    'message': row[13],
                    'log_timestamp': row[14],
                    'hostname': row[15],
                    'ip_address': row[16],
                    'platform': row[17],
                    'agent_status': row[18]
                }
                detections.append(detection)
            
            conn.close()
            logger.info(f"Retrieved {len(detections)} detections")
            return detections
            
        except Exception as e:
            logger.error(f"Failed to get detection data: {e}")
            return []
    
    def _analyze_threats(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze threat patterns and statistics"""
        
        # Count threats by severity
        severity_counts = Counter()
        threat_type_counts = Counter()
        attacker_ips = Counter()
        affected_assets = Counter()
        
        for detection in detections:
            if detection['threat_detected']:
                severity_counts[detection['severity']] += 1
                threat_type_counts[detection['threat_type']] += 1
                
                # Extract attacker IPs from AI analysis
                ai_analysis = detection.get('ai_analysis', {})
                if 'attacker_ip' in ai_analysis:
                    attacker_ips[ai_analysis['attacker_ip']] += 1
                
                # Track affected assets
                asset_key = f"{detection['hostname']} ({detection['ip_address']})"
                affected_assets[asset_key] += 1
        
        # Get top attackers
        top_attackers = []
        for ip, count in attacker_ips.most_common(10):
            top_attackers.append({
                'ip_address': ip,
                'threat_count': count,
                'threat_types': [d['threat_type'] for d in detections 
                               if d.get('ai_analysis', {}).get('attacker_ip') == ip and d['threat_detected']]
            })
        
        # Get affected assets
        affected_assets_list = []
        for asset, count in affected_assets.most_common(10):
            hostname, ip = asset.split(' (')
            ip = ip.rstrip(')')
            affected_assets_list.append({
                'hostname': hostname,
                'ip_address': ip,
                'threat_count': count,
                'threat_types': [d['threat_type'] for d in detections 
                               if d['hostname'] == hostname and d['threat_detected']]
            })
        
        return {
            'total_threats': sum(severity_counts.values()),
            'critical_threats': severity_counts.get('critical', 0),
            'high_threats': severity_counts.get('high', 0),
            'medium_threats': severity_counts.get('medium', 0),
            'low_threats': severity_counts.get('low', 0),
            'threat_types': dict(threat_type_counts),
            'top_attackers': top_attackers,
            'affected_assets': affected_assets_list
        }
    
    def _map_mitre_techniques(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Map detections to MITRE ATT&CK techniques"""
        
        technique_mappings = []
        campaign_analysis = defaultdict(list)
        
        for detection in detections:
            if not detection['threat_detected']:
                continue
            
            # Get MITRE techniques from detection
            mitre_techniques = detection.get('mitre_techniques', [])
            tactics = detection.get('tactics', [])
            
            for technique_id in mitre_techniques:
                if technique_id in self.mitre_techniques_db:
                    technique_info = self.mitre_techniques_db[technique_id]
                    
                    # Calculate confidence based on detection confidence and evidence
                    evidence = []
                    if detection.get('rule_matches'):
                        evidence.extend(detection['rule_matches'])
                    if detection.get('ai_analysis', {}).get('indicators'):
                        evidence.extend(detection['ai_analysis']['indicators'])
                    
                    confidence = detection['confidence_score']
                    if evidence:
                        confidence = min(confidence + 0.1, 1.0)  # Boost confidence with evidence
                    
                    mapping = MITREMapping(
                        technique_id=technique_id,
                        technique_name=technique_info['name'],
                        tactic=technique_info['tactic'],
                        description=technique_info['description'],
                        confidence=confidence,
                        evidence=evidence
                    )
                    technique_mappings.append(mapping)
                    
                    # Group by campaign (same technique + similar timeframe)
                    campaign_key = f"{technique_id}_{detection['threat_type']}"
                    campaign_analysis[campaign_key].append(detection)
        
        # Analyze attack campaigns
        campaigns = []
        for campaign_key, campaign_detections in campaign_analysis.items():
            if len(campaign_detections) >= 2:  # Only campaigns with multiple detections
                technique_id, threat_type = campaign_key.split('_', 1)
                
                # Calculate campaign metrics
                start_time = min(d['detected_at'] for d in campaign_detections)
                end_time = max(d['detected_at'] for d in campaign_detections)
                affected_assets = set(d['hostname'] for d in campaign_detections)
                
                campaigns.append({
                    'campaign_id': f"campaign_{technique_id}_{int(start_time.timestamp())}",
                    'technique_id': technique_id,
                    'threat_type': threat_type,
                    'detection_count': len(campaign_detections),
                    'affected_assets': len(affected_assets),
                    'start_time': start_time,
                    'end_time': end_time,
                    'confidence': sum(d['confidence_score'] for d in campaign_detections) / len(campaign_detections),
                    'severity': max((d['severity'] for d in campaign_detections), key=lambda x: ['low', 'medium', 'high', 'critical'].index(x))
                })
        
        return {
            'techniques': technique_mappings,
            'campaigns': campaigns
        }
    
    def _correlate_threat_intelligence(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Correlate with threat intelligence and extract IOCs"""
        
        iocs = []
        correlations = []
        
        for detection in detections:
            if not detection['threat_detected']:
                continue
            
            ai_analysis = detection.get('ai_analysis', {})
            ml_results = detection.get('ml_results', {})
            
            # Extract IOCs from AI analysis
            if 'indicators' in ai_analysis:
                for indicator in ai_analysis['indicators']:
                    # Simple IOC type detection
                    ioc_type = "unknown"
                    if indicator.startswith(('http://', 'https://')):
                        ioc_type = "URL"
                    elif '.' in indicator and not indicator.startswith('/'):
                        ioc_type = "Domain"
                    elif indicator.count('.') == 3:
                        ioc_type = "IP"
                    elif len(indicator) == 32 or len(indicator) == 40:
                        ioc_type = "Hash"
                    
                    ioc = ThreatIntelligence(
                        ioc_type=ioc_type,
                        ioc_value=indicator,
                        threat_type=detection['threat_type'],
                        confidence=detection['confidence_score'],
                        source="AI Analysis",
                        first_seen=datetime.fromisoformat(detection['detected_at']),
                        last_seen=datetime.fromisoformat(detection['detected_at']),
                        related_threats=[detection['id']]
                    )
                    iocs.append(ioc)
            
            # Correlate with known threat intelligence
            if detection['threat_type'] in ['malware', 'ransomware', 'apt']:
                # This would typically query external threat feeds
                correlation = {
                    'detection_id': detection['id'],
                    'threat_type': detection['threat_type'],
                    'correlation_type': 'threat_family',
                    'confidence': detection['confidence_score'],
                    'source': 'threat_intelligence',
                    'details': f"Correlated with known {detection['threat_type']} campaign"
                }
                correlations.append(correlation)
        
        return {
            'iocs': iocs,
            'correlations': correlations
        }
    
    async def _calculate_trends(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Calculate detection trends and statistics"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get hourly detection counts
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m-%d %H:00:00', detected_at) as hour,
                    COUNT(*) as total_detections,
                    SUM(CASE WHEN threat_detected = 1 THEN 1 ELSE 0 END) as threats,
                    SUM(CASE WHEN threat_detected = 0 THEN 1 ELSE 0 END) as benign,
                    AVG(confidence_score) as avg_confidence
                FROM detection_results 
                WHERE detected_at >= ? AND detected_at <= ?
                GROUP BY hour
                ORDER BY hour
            ''', (start_time.isoformat(), end_time.isoformat()))
            
            hourly_data = cursor.fetchall()
            
            # Calculate trends
            if len(hourly_data) >= 2:
                first_half = hourly_data[:len(hourly_data)//2]
                second_half = hourly_data[len(hourly_data)//2:]
                
                first_avg = sum(row[2] for row in first_half) / len(first_half)
                second_avg = sum(row[2] for row in second_half) / len(second_half)
                
                trend_direction = "increasing" if second_avg > first_avg else "decreasing"
                trend_percentage = abs((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            else:
                trend_direction = "stable"
                trend_percentage = 0
            
            # Calculate false positive rate
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_detections,
                    SUM(CASE WHEN threat_detected = 0 THEN 1 ELSE 0 END) as false_positives
                FROM detection_results 
                WHERE detected_at >= ? AND detected_at <= ?
            ''', (start_time.isoformat(), end_time.isoformat()))
            
            fp_result = cursor.fetchone()
            false_positive_rate = (fp_result[1] / fp_result[0] * 100) if fp_result[0] > 0 else 0
            
            # Calculate analyst workload
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_threats,
                    COUNT(DISTINCT agent_id) as affected_assets,
                    COUNT(DISTINCT threat_type) as unique_threat_types
                FROM detection_results dr
                JOIN log_entries le ON dr.log_entry_id = le.id
                WHERE dr.threat_detected = 1 AND dr.detected_at >= ? AND dr.detected_at <= ?
            ''', (start_time.isoformat(), end_time.isoformat()))
            
            workload_result = cursor.fetchone()
            
            conn.close()
            
            return {
                'hourly_detections': [{'hour': row[0], 'threats': row[2], 'benign': row[3], 'avg_confidence': row[4]} for row in hourly_data],
                'trend_direction': trend_direction,
                'trend_percentage': trend_percentage,
                'false_positive_rate': false_positive_rate,
                'analyst_workload': {
                    'total_threats': workload_result[0],
                    'affected_assets': workload_result[1],
                    'unique_threat_types': workload_result[2],
                    'estimated_investigation_time_hours': workload_result[0] * 0.5  # 30 min per threat
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            return {
                'hourly_detections': [],
                'trend_direction': 'unknown',
                'trend_percentage': 0,
                'false_positive_rate': 0,
                'analyst_workload': {}
            }
    
    def _generate_recommendations(self, threat_analysis: Dict[str, Any], 
                                mitre_analysis: Dict[str, Any], 
                                trends: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate actionable recommendations"""
        
        immediate_actions = []
        long_term_recommendations = []
        security_improvements = []
        
        # Immediate actions based on critical threats
        if threat_analysis['critical_threats'] > 0:
            immediate_actions.append("🚨 IMMEDIATE: Investigate critical threats - potential active compromise")
            immediate_actions.append("🔍 Isolate affected systems and begin incident response procedures")
        
        if threat_analysis['high_threats'] > 5:
            immediate_actions.append("⚠️ HIGH PRIORITY: Multiple high-severity threats detected - review security controls")
        
        # Long-term recommendations based on threat types
        threat_types = threat_analysis['threat_types']
        if 'malware' in threat_types and threat_types['malware'] > 3:
            long_term_recommendations.append("🛡️ Implement advanced endpoint detection and response (EDR) solution")
            long_term_recommendations.append("📚 Conduct security awareness training on malware prevention")
        
        if 'phishing' in threat_types and threat_types['phishing'] > 2:
            long_term_recommendations.append("📧 Deploy email security gateway with advanced threat protection")
            long_term_recommendations.append("🎓 Conduct phishing simulation training for all users")
        
        # MITRE-based recommendations
        techniques = mitre_analysis['techniques']
        if any(t.technique_id == 'T1055' for t in techniques):  # Process Injection
            security_improvements.append("🔒 Enable process injection protection in endpoint security")
        
        if any(t.technique_id == 'T1059' for t in techniques):  # Command and Scripting
            security_improvements.append("📝 Implement application whitelisting for command line tools")
        
        if any(t.technique_id == 'T1071' for t in techniques):  # Application Layer Protocol
            security_improvements.append("🌐 Deploy network monitoring for suspicious application layer traffic")
        
        # Trend-based recommendations
        if trends.get('trend_direction') == 'increasing':
            immediate_actions.append("📈 Threat volume increasing - consider additional monitoring resources")
        
        if trends.get('false_positive_rate', 0) > 20:
            long_term_recommendations.append("🎯 Tune detection rules to reduce false positive rate")
            long_term_recommendations.append("🤖 Implement machine learning-based false positive reduction")
        
        # Campaign-based recommendations
        campaigns = mitre_analysis['campaigns']
        if len(campaigns) > 0:
            immediate_actions.append(f"🎯 {len(campaigns)} attack campaigns detected - investigate coordinated attacks")
            security_improvements.append("🔍 Implement threat hunting procedures for campaign detection")
        
        return {
            'immediate': immediate_actions,
            'long_term': long_term_recommendations,
            'improvements': security_improvements
        }
    
    def format_report_for_api(self, report: DetectionReport) -> Dict[str, Any]:
        """Format report for API consumption"""
        
        return {
            'reportId': report.report_id,
            'generatedAt': report.generated_at.isoformat(),
            'timeRange': {
                'start': report.time_range[0].isoformat(),
                'end': report.time_range[1].isoformat()
            },
            'executiveSummary': {
                'totalThreats': report.total_threats,
                'threatBreakdown': {
                    'critical': report.critical_threats,
                    'high': report.high_threats,
                    'medium': report.medium_threats,
                    'low': report.low_threats
                },
                'riskLevel': self._calculate_overall_risk_level(report),
                'keyFindings': self._extract_key_findings(report)
            },
            'threatAnalysis': {
                'threatTypes': report.threat_types,
                'topAttackers': report.top_attackers,
                'affectedAssets': report.affected_assets
            },
            'mitreAnalysis': {
                'techniques': [
                    {
                        'techniqueId': t.technique_id,
                        'techniqueName': t.technique_name,
                        'tactic': t.tactic,
                        'description': t.description,
                        'confidence': t.confidence,
                        'evidence': t.evidence
                    } for t in report.mitre_techniques
                ],
                'campaigns': report.attack_campaigns
            },
            'threatIntelligence': {
                'iocs': [
                    {
                        'type': ioc.ioc_type,
                        'value': ioc.ioc_value,
                        'threatType': ioc.threat_type,
                        'confidence': ioc.confidence,
                        'source': ioc.source,
                        'firstSeen': ioc.first_seen.isoformat(),
                        'lastSeen': ioc.last_seen.isoformat()
                    } for ioc in report.iocs
                ],
                'correlations': report.threat_correlations
            },
            'trendsAndStatistics': {
                'detectionTrends': report.detection_trends,
                'falsePositiveRate': report.false_positive_rate,
                'analystWorkload': report.analyst_workload
            },
            'recommendations': {
                'immediateActions': report.immediate_actions,
                'longTermRecommendations': report.long_term_recommendations,
                'securityImprovements': report.security_improvements
            }
        }
    
    def _calculate_overall_risk_level(self, report: DetectionReport) -> str:
        """Calculate overall risk level"""
        if report.critical_threats > 0:
            return "CRITICAL"
        elif report.high_threats > 5:
            return "HIGH"
        elif report.high_threats > 0 or report.medium_threats > 10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_key_findings(self, report: DetectionReport) -> List[str]:
        """Extract key findings for executive summary"""
        findings = []
        
        if report.critical_threats > 0:
            findings.append(f"🚨 {report.critical_threats} critical threats require immediate attention")
        
        if len(report.attack_campaigns) > 0:
            findings.append(f"🎯 {len(report.attack_campaigns)} coordinated attack campaigns detected")
        
        if report.false_positive_rate > 20:
            findings.append(f"⚠️ High false positive rate ({report.false_positive_rate:.1f}%) - tuning required")
        
        top_threat_type = max(report.threat_types.items(), key=lambda x: x[1]) if report.threat_types else None
        if top_threat_type:
            findings.append(f"📊 Most common threat type: {top_threat_type[0]} ({top_threat_type[1]} detections)")
        
        return findings

# Global instance
enhanced_detection_reporter = EnhancedAIDetectionReporter()
