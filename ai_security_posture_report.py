#!/usr/bin/env python3
"""
AI Security Posture Report Generator for CodeGrey SOC Platform
Comprehensive security posture analysis with AI-powered recommendations
"""

import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class SecurityPostureReport:
    """Comprehensive security posture report"""
    report_id: str
    generated_at: datetime
    
    # Overall Security Posture
    overall_risk_score: float  # 0-100 (0=excellent, 100=critical)
    security_grade: str  # A, B, C, D, F
    posture_trend: str  # improving, stable, declining
    
    # Endpoint Security
    total_endpoints: int
    endpoints_at_risk: int
    endpoints_compliant: int
    endpoint_security_breakdown: Dict[str, Any]
    
    # Threat Landscape
    active_threats: int
    resolved_threats: int
    threat_velocity: float  # threats per hour
    threat_types_distribution: Dict[str, int]
    
    # Security Controls
    antivirus_coverage: float  # 0-100%
    firewall_coverage: float  # 0-100%
    encryption_coverage: float  # 0-100%
    patch_compliance: float  # 0-100%
    
    # Vulnerabilities
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int
    vulnerability_details: List[Dict[str, Any]]
    
    # Attack Surface
    exposed_services: List[Dict[str, Any]]
    open_ports: List[Dict[str, Any]]
    external_ips: List[str]
    attack_surface_score: float  # 0-100
    
    # Compliance & Best Practices
    compliance_score: float  # 0-100%
    compliance_gaps: List[str]
    security_best_practices: Dict[str, bool]
    
    # AI Analysis
    ai_insights: List[str]
    risk_predictions: Dict[str, Any]
    anomaly_detections: List[Dict[str, Any]]
    
    # Recommendations
    critical_actions: List[str]
    high_priority_actions: List[str]
    medium_priority_actions: List[str]
    long_term_improvements: List[str]


class AISecurityPostureReporter:
    """AI-powered Security Posture Report Generator"""
    
    def __init__(self, db_path: str = "soc_database.db"):
        self.db_path = db_path
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.use_ai = bool(self.openai_api_key)
    
    async def generate_security_posture_report(self, time_range_hours: int = 24) -> SecurityPostureReport:
        """Generate comprehensive AI security posture report"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        logger.info(f"Generating AI Security Posture Report for {start_time} to {end_time}")
        
        # Gather all security data
        endpoints_data = await self._get_endpoints_security_data()
        threats_data = await self._get_threats_data(start_time, end_time)
        vulnerabilities_data = await self._analyze_vulnerabilities(endpoints_data)
        attack_surface_data = await self._analyze_attack_surface(endpoints_data)
        compliance_data = await self._assess_compliance(endpoints_data)
        
        # Calculate security scores
        overall_risk_score = self._calculate_overall_risk_score(
            endpoints_data, threats_data, vulnerabilities_data, attack_surface_data
        )
        security_grade = self._calculate_security_grade(overall_risk_score)
        posture_trend = await self._calculate_posture_trend(start_time, end_time)
        
        # Get AI insights if available
        ai_insights = []
        risk_predictions = {}
        if self.use_ai:
            ai_analysis = await self._get_ai_insights(
                endpoints_data, threats_data, vulnerabilities_data, 
                attack_surface_data, compliance_data
            )
            ai_insights = ai_analysis.get('insights', [])
            risk_predictions = ai_analysis.get('predictions', {})
        
        # Generate recommendations
        recommendations = self._generate_prioritized_recommendations(
            overall_risk_score, endpoints_data, threats_data, 
            vulnerabilities_data, attack_surface_data, compliance_data
        )
        
        # Create comprehensive report
        report = SecurityPostureReport(
            report_id=f"security_posture_{int(end_time.timestamp())}",
            generated_at=end_time,
            overall_risk_score=overall_risk_score,
            security_grade=security_grade,
            posture_trend=posture_trend,
            total_endpoints=endpoints_data['total'],
            endpoints_at_risk=endpoints_data['at_risk'],
            endpoints_compliant=endpoints_data['compliant'],
            endpoint_security_breakdown=endpoints_data['breakdown'],
            active_threats=threats_data['active'],
            resolved_threats=threats_data['resolved'],
            threat_velocity=threats_data['velocity'],
            threat_types_distribution=threats_data['types'],
            antivirus_coverage=endpoints_data['antivirus_coverage'],
            firewall_coverage=endpoints_data['firewall_coverage'],
            encryption_coverage=endpoints_data['encryption_coverage'],
            patch_compliance=endpoints_data['patch_compliance'],
            critical_vulnerabilities=vulnerabilities_data['critical'],
            high_vulnerabilities=vulnerabilities_data['high'],
            medium_vulnerabilities=vulnerabilities_data['medium'],
            low_vulnerabilities=vulnerabilities_data['low'],
            vulnerability_details=vulnerabilities_data['details'],
            exposed_services=attack_surface_data['services'],
            open_ports=attack_surface_data['ports'],
            external_ips=attack_surface_data['external_ips'],
            attack_surface_score=attack_surface_data['score'],
            compliance_score=compliance_data['score'],
            compliance_gaps=compliance_data['gaps'],
            security_best_practices=compliance_data['best_practices'],
            ai_insights=ai_insights,
            risk_predictions=risk_predictions,
            anomaly_detections=await self._detect_anomalies(endpoints_data, threats_data),
            critical_actions=recommendations['critical'],
            high_priority_actions=recommendations['high'],
            medium_priority_actions=recommendations['medium'],
            long_term_improvements=recommendations['long_term']
        )
        
        return report
    
    async def _get_endpoints_security_data(self) -> Dict[str, Any]:
        """Get comprehensive endpoint security data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, hostname, ip_address, platform, os_version, status,
                       quick_summary, system_info, last_heartbeat
                FROM agents
            ''')
            
            endpoints = cursor.fetchall()
            conn.close()
            
            total = len(endpoints)
            at_risk = 0
            compliant = 0
            
            antivirus_count = 0
            firewall_count = 0
            encryption_count = 0
            patched_count = 0
            
            breakdown = {
                'windows': 0,
                'linux': 0,
                'macos': 0,
                'online': 0,
                'offline': 0
            }
            
            for endpoint in endpoints:
                platform = endpoint[3] or 'unknown'
                status = endpoint[5] or 'offline'
                quick_summary = json.loads(endpoint[6]) if endpoint[6] else {}
                system_info = json.loads(endpoint[7]) if endpoint[7] else {}
                
                # Platform breakdown
                if 'windows' in platform.lower():
                    breakdown['windows'] += 1
                elif 'linux' in platform.lower():
                    breakdown['linux'] += 1
                elif 'darwin' in platform.lower() or 'mac' in platform.lower():
                    breakdown['macos'] += 1
                
                # Status breakdown
                if status == 'online':
                    breakdown['online'] += 1
                else:
                    breakdown['offline'] += 1
                
                # Security controls
                security_info = system_info.get('security', {})
                has_antivirus = security_info.get('antivirus_status') == 'Protected'
                has_firewall = security_info.get('firewall_status') == 'Enabled'
                has_encryption = security_info.get('encryption_status') == 'Enabled'
                has_updates = security_info.get('windows_updates') not in ['Updates required', 'Critical updates pending']
                
                if has_antivirus:
                    antivirus_count += 1
                if has_firewall:
                    firewall_count += 1
                if has_encryption:
                    encryption_count += 1
                if has_updates:
                    patched_count += 1
                
                # Risk assessment
                security_score = 0
                if has_antivirus:
                    security_score += 25
                if has_firewall:
                    security_score += 25
                if has_encryption:
                    security_score += 25
                if has_updates:
                    security_score += 25
                
                if security_score >= 75:
                    compliant += 1
                else:
                    at_risk += 1
            
            return {
                'total': total,
                'at_risk': at_risk,
                'compliant': compliant,
                'breakdown': breakdown,
                'antivirus_coverage': (antivirus_count / total * 100) if total > 0 else 0,
                'firewall_coverage': (firewall_count / total * 100) if total > 0 else 0,
                'encryption_coverage': (encryption_count / total * 100) if total > 0 else 0,
                'patch_compliance': (patched_count / total * 100) if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get endpoints security data: {e}")
            return {
                'total': 0, 'at_risk': 0, 'compliant': 0,
                'breakdown': {}, 'antivirus_coverage': 0,
                'firewall_coverage': 0, 'encryption_coverage': 0,
                'patch_compliance': 0
            }
    
    async def _get_threats_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get threat landscape data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Active threats
            cursor.execute('''
                SELECT COUNT(*) FROM detection_results
                WHERE threat_detected = 1 AND detected_at >= ? AND detected_at <= ?
            ''', (start_time.isoformat(), end_time.isoformat()))
            active_threats = cursor.fetchone()[0]
            
            # Resolved threats (marked as false positive or verified)
            cursor.execute('''
                SELECT COUNT(*) FROM detection_results
                WHERE threat_detected = 1 AND (false_positive = 1 OR verified = 1)
                AND detected_at >= ? AND detected_at <= ?
            ''', (start_time.isoformat(), end_time.isoformat()))
            resolved_threats = cursor.fetchone()[0]
            
            # Threat types
            cursor.execute('''
                SELECT threat_type, COUNT(*) FROM detection_results
                WHERE threat_detected = 1 AND detected_at >= ? AND detected_at <= ?
                GROUP BY threat_type
            ''', (start_time.isoformat(), end_time.isoformat()))
            threat_types = dict(cursor.fetchall())
            
            conn.close()
            
            # Calculate threat velocity (threats per hour)
            hours = (end_time - start_time).total_seconds() / 3600
            velocity = active_threats / hours if hours > 0 else 0
            
            return {
                'active': active_threats,
                'resolved': resolved_threats,
                'velocity': velocity,
                'types': threat_types
            }
            
        except Exception as e:
            logger.error(f"Failed to get threats data: {e}")
            return {'active': 0, 'resolved': 0, 'velocity': 0, 'types': {}}
    
    async def _analyze_vulnerabilities(self, endpoints_data: Dict) -> Dict[str, Any]:
        """Analyze vulnerabilities across endpoints"""
        # This would integrate with vulnerability scanners
        # For now, we'll assess based on security controls
        
        vulnerabilities = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'details': []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT hostname, system_info FROM agents
            ''')
            
            for row in cursor.fetchall():
                hostname = row[0]
                system_info = json.loads(row[1]) if row[1] else {}
                security = system_info.get('security', {})
                
                # Check for missing security controls
                if security.get('antivirus_status') != 'Protected':
                    vulnerabilities['high'] += 1
                    vulnerabilities['details'].append({
                        'hostname': hostname,
                        'severity': 'high',
                        'vulnerability': 'Missing or disabled antivirus protection',
                        'recommendation': 'Install and enable antivirus software'
                    })
                
                if security.get('firewall_status') != 'Enabled':
                    vulnerabilities['high'] += 1
                    vulnerabilities['details'].append({
                        'hostname': hostname,
                        'severity': 'high',
                        'vulnerability': 'Firewall disabled or not configured',
                        'recommendation': 'Enable and configure firewall'
                    })
                
                if security.get('windows_updates') in ['Updates required', 'Critical updates pending']:
                    vulnerabilities['critical'] += 1
                    vulnerabilities['details'].append({
                        'hostname': hostname,
                        'severity': 'critical',
                        'vulnerability': 'Critical security updates missing',
                        'recommendation': 'Apply security updates immediately'
                    })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to analyze vulnerabilities: {e}")
        
        return vulnerabilities
    
    async def _analyze_attack_surface(self, endpoints_data: Dict) -> Dict[str, Any]:
        """Analyze attack surface"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT system_info FROM agents
            ''')
            
            all_services = []
            all_ports = []
            external_ips = set()
            
            for row in cursor.fetchall():
                system_info = json.loads(row[0]) if row[0] else {}
                
                # Extract services
                services = system_info.get('services', [])
                for service in services:
                    if isinstance(service, dict):
                        all_services.append(service)
                
                # Extract network info
                network = system_info.get('network', {})
                connections = network.get('connections', [])
                for conn in connections:
                    if isinstance(conn, dict):
                        remote_ip = conn.get('remote_address', '')
                        if remote_ip and not remote_ip.startswith(('127.', '192.168.', '10.', '172.')):
                            external_ips.add(remote_ip)
            
            conn.close()
            
            # Calculate attack surface score (0-100, lower is better)
            score = 0
            if len(all_services) > 10:
                score += 30
            elif len(all_services) > 5:
                score += 15
            
            if len(external_ips) > 5:
                score += 40
            elif len(external_ips) > 0:
                score += 20
            
            return {
                'services': all_services[:10],  # Top 10
                'ports': all_ports[:10],
                'external_ips': list(external_ips)[:10],
                'score': score
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze attack surface: {e}")
            return {'services': [], 'ports': [], 'external_ips': [], 'score': 0}
    
    async def _assess_compliance(self, endpoints_data: Dict) -> Dict[str, Any]:
        """Assess compliance with security best practices"""
        
        total_checks = 10
        passed_checks = 0
        gaps = []
        
        best_practices = {
            'antivirus_deployed': False,
            'firewall_enabled': False,
            'encryption_enabled': False,
            'patches_current': False,
            'password_policy': False,
            'mfa_enabled': False,
            'backup_configured': False,
            'logging_enabled': True,  # We assume logging is enabled if agents are reporting
            'monitoring_active': True,
            'incident_response_plan': False
        }
        
        # Check antivirus
        if endpoints_data.get('antivirus_coverage', 0) >= 90:
            best_practices['antivirus_deployed'] = True
            passed_checks += 1
        else:
            gaps.append(f"Antivirus coverage is {endpoints_data.get('antivirus_coverage', 0):.1f}% (target: 90%)")
        
        # Check firewall
        if endpoints_data.get('firewall_coverage', 0) >= 95:
            best_practices['firewall_enabled'] = True
            passed_checks += 1
        else:
            gaps.append(f"Firewall coverage is {endpoints_data.get('firewall_coverage', 0):.1f}% (target: 95%)")
        
        # Check encryption
        if endpoints_data.get('encryption_coverage', 0) >= 80:
            best_practices['encryption_enabled'] = True
            passed_checks += 1
        else:
            gaps.append(f"Encryption coverage is {endpoints_data.get('encryption_coverage', 0):.1f}% (target: 80%)")
        
        # Check patches
        if endpoints_data.get('patch_compliance', 0) >= 85:
            best_practices['patches_current'] = True
            passed_checks += 1
        else:
            gaps.append(f"Patch compliance is {endpoints_data.get('patch_compliance', 0):.1f}% (target: 85%)")
        
        # Logging and monitoring are enabled
        passed_checks += 2
        
        compliance_score = (passed_checks / total_checks) * 100
        
        return {
            'score': compliance_score,
            'gaps': gaps,
            'best_practices': best_practices
        }
    
    def _calculate_overall_risk_score(self, endpoints_data: Dict, threats_data: Dict, 
                                     vulnerabilities_data: Dict, attack_surface_data: Dict) -> float:
        """Calculate overall risk score (0-100, where 0 is best, 100 is worst)"""
        
        # Endpoint risk (0-25)
        endpoint_risk = (endpoints_data['at_risk'] / max(endpoints_data['total'], 1)) * 25
        
        # Threat risk (0-25)
        threat_risk = min(threats_data['active'] * 2, 25)
        
        # Vulnerability risk (0-30)
        vuln_risk = (
            vulnerabilities_data['critical'] * 5 +
            vulnerabilities_data['high'] * 3 +
            vulnerabilities_data['medium'] * 1
        )
        vuln_risk = min(vuln_risk, 30)
        
        # Attack surface risk (0-20)
        attack_surface_risk = attack_surface_data['score'] * 0.2
        
        total_risk = endpoint_risk + threat_risk + vuln_risk + attack_surface_risk
        
        return min(total_risk, 100)
    
    def _calculate_security_grade(self, risk_score: float) -> str:
        """Calculate security grade A-F"""
        if risk_score <= 20:
            return 'A'
        elif risk_score <= 40:
            return 'B'
        elif risk_score <= 60:
            return 'C'
        elif risk_score <= 80:
            return 'D'
        else:
            return 'F'
    
    async def _calculate_posture_trend(self, start_time: datetime, end_time: datetime) -> str:
        """Calculate security posture trend"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            midpoint = start_time + (end_time - start_time) / 2
            
            # First half threats
            cursor.execute('''
                SELECT COUNT(*) FROM detection_results
                WHERE threat_detected = 1 AND detected_at >= ? AND detected_at < ?
            ''', (start_time.isoformat(), midpoint.isoformat()))
            first_half = cursor.fetchone()[0]
            
            # Second half threats
            cursor.execute('''
                SELECT COUNT(*) FROM detection_results
                WHERE threat_detected = 1 AND detected_at >= ? AND detected_at <= ?
            ''', (midpoint.isoformat(), end_time.isoformat()))
            second_half = cursor.fetchone()[0]
            
            conn.close()
            
            if second_half > first_half * 1.2:
                return 'declining'
            elif second_half < first_half * 0.8:
                return 'improving'
            else:
                return 'stable'
                
        except Exception as e:
            logger.error(f"Failed to calculate posture trend: {e}")
            return 'unknown'
    
    async def _get_ai_insights(self, endpoints_data: Dict, threats_data: Dict,
                              vulnerabilities_data: Dict, attack_surface_data: Dict,
                              compliance_data: Dict) -> Dict[str, Any]:
        """Get AI-powered insights and predictions"""
        if not self.use_ai:
            return {'insights': [], 'predictions': {}}
        
        try:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.3,
                openai_api_key=self.openai_api_key
            )
            
            prompt = f"""Analyze the following security posture data and provide insights:

Endpoints:
- Total: {endpoints_data['total']}
- At Risk: {endpoints_data['at_risk']}
- Antivirus Coverage: {endpoints_data['antivirus_coverage']:.1f}%
- Firewall Coverage: {endpoints_data['firewall_coverage']:.1f}%
- Patch Compliance: {endpoints_data['patch_compliance']:.1f}%

Threats:
- Active Threats: {threats_data['active']}
- Threat Velocity: {threats_data['velocity']:.2f} per hour
- Threat Types: {threats_data['types']}

Vulnerabilities:
- Critical: {vulnerabilities_data['critical']}
- High: {vulnerabilities_data['high']}
- Medium: {vulnerabilities_data['medium']}

Attack Surface:
- External IPs: {len(attack_surface_data['external_ips'])}
- Exposed Services: {len(attack_surface_data['services'])}
- Attack Surface Score: {attack_surface_data['score']}/100

Compliance Score: {compliance_data['score']:.1f}%

Provide:
1. 5 key insights about the current security posture
2. 3 risk predictions for the next 7 days
3. Overall security assessment

Format as JSON:
{{
  "insights": ["insight 1", "insight 2", ...],
  "predictions": {{
    "next_7_days": ["prediction 1", "prediction 2", "prediction 3"],
    "confidence": "high|medium|low"
  }},
  "assessment": "overall assessment summary"
}}"""

            response = await llm.ainvoke(prompt)
            
            # Parse AI response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                ai_analysis = json.loads(json_match.group())
                return ai_analysis
            
            return {'insights': [], 'predictions': {}}
            
        except Exception as e:
            logger.error(f"AI insights failed: {e}")
            return {'insights': [], 'predictions': {}}
    
    async def _detect_anomalies(self, endpoints_data: Dict, threats_data: Dict) -> List[Dict[str, Any]]:
        """Detect anomalies in security data"""
        anomalies = []
        
        # High threat velocity
        if threats_data['velocity'] > 5:
            anomalies.append({
                'type': 'high_threat_velocity',
                'severity': 'high',
                'description': f"Unusually high threat detection rate: {threats_data['velocity']:.2f} per hour",
                'recommendation': 'Investigate potential attack campaign'
            })
        
        # Low security coverage
        if endpoints_data['antivirus_coverage'] < 50:
            anomalies.append({
                'type': 'low_antivirus_coverage',
                'severity': 'critical',
                'description': f"Critical: Only {endpoints_data['antivirus_coverage']:.1f}% antivirus coverage",
                'recommendation': 'Deploy antivirus to all endpoints immediately'
            })
        
        return anomalies
    
    def _generate_prioritized_recommendations(self, overall_risk_score: float,
                                            endpoints_data: Dict, threats_data: Dict,
                                            vulnerabilities_data: Dict, attack_surface_data: Dict,
                                            compliance_data: Dict) -> Dict[str, List[str]]:
        """Generate prioritized recommendations"""
        
        critical = []
        high = []
        medium = []
        long_term = []
        
        # Critical actions
        if vulnerabilities_data['critical'] > 0:
            critical.append(f"🚨 IMMEDIATE: Patch {vulnerabilities_data['critical']} critical vulnerabilities")
        
        if endpoints_data['antivirus_coverage'] < 70:
            critical.append(f"🚨 IMMEDIATE: Deploy antivirus to {endpoints_data['total'] - int(endpoints_data['total'] * endpoints_data['antivirus_coverage'] / 100)} unprotected endpoints")
        
        if threats_data['active'] > 10:
            critical.append(f"🚨 IMMEDIATE: Investigate and respond to {threats_data['active']} active threats")
        
        # High priority
        if vulnerabilities_data['high'] > 0:
            high.append(f"⚠️ HIGH: Remediate {vulnerabilities_data['high']} high-severity vulnerabilities")
        
        if endpoints_data['firewall_coverage'] < 90:
            high.append(f"⚠️ HIGH: Enable firewall on all endpoints (current: {endpoints_data['firewall_coverage']:.1f}%)")
        
        if endpoints_data['patch_compliance'] < 85:
            high.append(f"⚠️ HIGH: Improve patch compliance to 85% (current: {endpoints_data['patch_compliance']:.1f}%)")
        
        # Medium priority
        if endpoints_data['encryption_coverage'] < 80:
            medium.append(f"📋 MEDIUM: Enable encryption on more endpoints (current: {endpoints_data['encryption_coverage']:.1f}%)")
        
        if attack_surface_data['score'] > 50:
            medium.append(f"📋 MEDIUM: Reduce attack surface (current score: {attack_surface_data['score']}/100)")
        
        # Long-term improvements
        if compliance_data['score'] < 80:
            long_term.append(f"📈 Improve overall compliance score to 80% (current: {compliance_data['score']:.1f}%)")
        
        long_term.append("📚 Implement security awareness training program")
        long_term.append("🔍 Deploy advanced threat hunting capabilities")
        long_term.append("🤖 Implement automated incident response workflows")
        
        return {
            'critical': critical,
            'high': high,
            'medium': medium,
            'long_term': long_term
        }
    
    def format_report_for_api(self, report: SecurityPostureReport) -> Dict[str, Any]:
        """Format report for API consumption"""
        
        return {
            'reportId': report.report_id,
            'generatedAt': report.generated_at.isoformat(),
            'executiveSummary': {
                'overallRiskScore': report.overall_risk_score,
                'securityGrade': report.security_grade,
                'postureTrend': report.posture_trend,
                'riskLevel': self._get_risk_level(report.overall_risk_score),
                'keyMetrics': {
                    'totalEndpoints': report.total_endpoints,
                    'endpointsAtRisk': report.endpoints_at_risk,
                    'activeThreats': report.active_threats,
                    'criticalVulnerabilities': report.critical_vulnerabilities
                }
            },
            'endpointSecurity': {
                'totalEndpoints': report.total_endpoints,
                'endpointsAtRisk': report.endpoints_at_risk,
                'endpointsCompliant': report.endpoints_compliant,
                'breakdown': report.endpoint_security_breakdown,
                'securityControls': {
                    'antivirusCoverage': report.antivirus_coverage,
                    'firewallCoverage': report.firewall_coverage,
                    'encryptionCoverage': report.encryption_coverage,
                    'patchCompliance': report.patch_compliance
                }
            },
            'threatLandscape': {
                'activeThreats': report.active_threats,
                'resolvedThreats': report.resolved_threats,
                'threatVelocity': report.threat_velocity,
                'threatTypesDistribution': report.threat_types_distribution
            },
            'vulnerabilities': {
                'summary': {
                    'critical': report.critical_vulnerabilities,
                    'high': report.high_vulnerabilities,
                    'medium': report.medium_vulnerabilities,
                    'low': report.low_vulnerabilities
                },
                'details': report.vulnerability_details[:10]  # Top 10
            },
            'attackSurface': {
                'exposedServices': report.exposed_services,
                'openPorts': report.open_ports,
                'externalIps': report.external_ips,
                'attackSurfaceScore': report.attack_surface_score
            },
            'compliance': {
                'complianceScore': report.compliance_score,
                'complianceGaps': report.compliance_gaps,
                'securityBestPractices': report.security_best_practices
            },
            'aiAnalysis': {
                'insights': report.ai_insights,
                'riskPredictions': report.risk_predictions,
                'anomalyDetections': report.anomaly_detections
            },
            'recommendations': {
                'critical': report.critical_actions,
                'high': report.high_priority_actions,
                'medium': report.medium_priority_actions,
                'longTerm': report.long_term_improvements
            }
        }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level description"""
        if risk_score <= 20:
            return 'LOW'
        elif risk_score <= 40:
            return 'MODERATE'
        elif risk_score <= 60:
            return 'ELEVATED'
        elif risk_score <= 80:
            return 'HIGH'
        else:
            return 'CRITICAL'


# Global instance
security_posture_reporter = AISecurityPostureReporter()


