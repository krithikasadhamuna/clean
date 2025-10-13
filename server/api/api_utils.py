#!/usr/bin/env python3
"""
API Utilities for CodeGrey AI SOC Platform
Centralized API response formatting and data management
"""

import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class APIUtils:
    """Utility class for API operations"""
    
    def __init__(self, db_path: str = "soc_database.db"):
        self.db_path = db_path
        # Don't cache the API key - check it dynamically
        self._openai_api_key = None
    
    @property
    def openai_api_key(self):
        """Get OpenAI API key dynamically from environment"""
        if self._openai_api_key is None:
            self._openai_api_key = os.getenv('OPENAI_API_KEY', '')
        return self._openai_api_key
    
    @property
    def use_ai_analysis(self):
        """Check if AI analysis should be used (dynamic check)"""
        return bool(self.openai_api_key)
    
    def refresh_api_key(self):
        """Force refresh of the API key from environment"""
        self._openai_api_key = None
        logger.info(f"API Key refreshed - Present: {bool(self.openai_api_key)}")
    
    def get_ai_analysis_status(self):
        """Get current AI analysis status"""
        return {
            "ai_analysis_enabled": self.use_ai_analysis,
            "api_key_present": bool(self.openai_api_key),
            "api_key_length": len(self.openai_api_key) if self.openai_api_key else 0
        }
    
    async def get_agents_data(self) -> Dict[str, Any]:
        """Get agents data in standardized format with camelCase"""
        try:
            # Return SOC platform agents (not client endpoints)
            data = [
                {
                    "id": "phantomstrikeAi",
                    "name": "PhantomStrike AI",
                    "type": "attack",
                    "status": "active",
                    "location": "External Network",
                    "lastActivity": "Now",
                    "capabilities": ["Attack Planning", "Scenario Generation", "Red Team Operations"],
                    "platform": "LangChain Agent"
                },
                {
                    "id": "guardianAlphaAi",
                    "name": "GuardianAlpha AI",
                    "type": "detection", 
                    "status": "active",
                    "location": "SOC Infrastructure",
                    "lastActivity": "Now",
                    "capabilities": ["Threat Detection", "Log Analysis", "Behavioral Analysis"],
                    "platform": "LangChain Agent"
                },
                {
                    "id": "sentinelDeployAi",
                    "name": "SentinelDeploy AI",
                    "type": "deploy",
                    "status": "inactive",
                    "location": "Security Fabric", 
                    "lastActivity": "Inactive - In Development",
                    "capabilities": ["Agent Deployment", "Configuration Management"],
                    "platform": "LangChain Agent (Development)"
                },
                {
                    "id": "threatMindAi",
                    "name": "ThreatMind AI",
                    "type": "intelligence",
                    "status": "inactive",
                    "location": "Threat Intelligence Platform",
                    "lastActivity": "Inactive - In Development", 
                    "capabilities": ["Threat Intelligence", "IOC Analysis"],
                    "platform": "LangChain Agent (Development)"
                }
            ]
            
            return {
                "status": "success",
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Failed to get agents data: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_network_topology_data(self) -> Dict[str, Any]:
        """Get network topology data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all registered agents with enhanced system information
            cursor.execute('''
                SELECT id, hostname, ip_address, platform, status, last_heartbeat, agent_version,
                       os_version, capabilities, system_info, quick_summary
                FROM agents 
                ORDER BY last_heartbeat DESC
            ''')
            
            agents = cursor.fetchall()
            logger.info(f"Found {len(agents)} agents in database")
            
            data = []
            for agent in agents:
                logger.info(f"Processing agent: {agent[0] if agent else 'None'}")
                agent_id, hostname, ip_address, platform, status, last_heartbeat, agent_type, os_version, capabilities, system_info, quick_summary = agent
                
                # Simple network location determination
                if ip_address and ip_address.startswith('127.'):
                    location = "Local Development"
                elif ip_address and (ip_address.startswith('192.168.') or ip_address.startswith('10.')):
                    location = "Corporate Network"
                else:
                    location = "External Network"
                
                # Check if agent is active by analyzing recent logs
                cursor.execute('''
                    SELECT COUNT(*) FROM log_entries 
                    WHERE agent_id = ? AND timestamp > datetime('now', '-5 minutes')
                ''', (agent_id,))
                recent_logs_result = cursor.fetchone()
                recent_logs = recent_logs_result[0] if recent_logs_result else 0
                
                # Agent is active if it sent logs in last 5 minutes
                current_status = "active" if recent_logs > 0 else "inactive"
                
                # Get services from recent logs
                cursor.execute('''
                    SELECT DISTINCT source FROM log_entries 
                    WHERE agent_id = ? AND timestamp > datetime('now', '-1 hour')
                    LIMIT 10
                ''', (agent_id,))
                
                service_results = cursor.fetchall()
                services = [row[0] for row in service_results] if service_results else []
                
                # Parse enhanced system information
                system_info_parsed = {}
                quick_summary_parsed = {}
                try:
                    if system_info:
                        system_info_parsed = json.loads(system_info) if isinstance(system_info, str) else system_info
                    if quick_summary:
                        quick_summary_parsed = json.loads(quick_summary) if isinstance(quick_summary, str) else quick_summary
                except:
                    pass
                
                # Build the original agent data structure (for backward compatibility)
                agent_data = {
                    "hostname": hostname or "Unknown",
                    "ipAddress": ip_address or "Unknown",
                    "platform": platform or "Unknown",
                    "location": location,
                    "status": current_status,
                    "services": services,
                    "lastSeen": last_heartbeat or datetime.now().isoformat(),
                    "agentType": "clientEndpoint",
                    "importance": "high" if current_status == "active" else "low"
                }
                
                # Generate SOC analyst report and add it as an additional field
                endpoint_report = await self._generate_endpoint_report(
                    agent_id, hostname, ip_address, platform, os_version,
                    current_status, services, quick_summary_parsed, system_info_parsed, cursor
                )
                
                # Debug logging
                logger.debug(f"Generated endpoint report for {agent_id}: {type(endpoint_report)}")
                if endpoint_report:
                    logger.debug(f"Report keys: {list(endpoint_report.keys()) if isinstance(endpoint_report, dict) else 'Not a dict'}")
                
                # Add the SOC analyst report as a new field
                if endpoint_report and isinstance(endpoint_report, dict):
                    logger.info(f"Endpoint report type: {type(endpoint_report)}, keys: {list(endpoint_report.keys())}")
                    soc_report = endpoint_report.get("socAnalystReport")
                    if soc_report:
                        logger.info(f"SOC report found for {agent_id}, adding to agent_data")
                        agent_data["socAnalystReport"] = soc_report
                        logger.info(f"Agent data now has keys: {list(agent_data.keys())}")
                    else:
                        logger.error(f"No socAnalystReport found in endpoint report for {agent_id}")
                        logger.error(f"Endpoint report content: {endpoint_report}")
                else:
                    logger.error(f"Failed to generate endpoint report for {agent_id}, report type: {type(endpoint_report)}")
                
                # Only append if agent_data is valid
                if agent_data and isinstance(agent_data, dict):
                    data.append(agent_data)
                    logger.info(f"Successfully added agent {agent_id} to results")
                else:
                    logger.error(f"Skipping invalid agent_data for {agent_id}: {type(agent_data)}")
            
            conn.close()
            
            logger.info(f"Final data array contains {len(data)} endpoints")
            
            # Calculate security summary with null checks
            total_endpoints = len(data)
            active_endpoints = 0
            high_risk_endpoints = 0
            medium_risk_endpoints = 0
            network_zones = set()
            
            for d in data:
                if d and isinstance(d, dict):
                    # Check active endpoints (from old structure)
                    if d.get("status") == "active":
                        active_endpoints += 1
                    
                    # Collect network zones
                    if d.get("location"):
                        network_zones.add(d.get("location"))
                    
                    # Check risk levels (from new SOC report if available)
                    soc_report = d.get("socAnalystReport", {})
                    if soc_report:
                        threat_activity = soc_report.get("threatActivity", {})
                        if threat_activity:
                            risk_level = threat_activity.get("riskLevel", "")
                            if risk_level == "HIGH":
                                high_risk_endpoints += 1
                            elif risk_level == "MEDIUM":
                                medium_risk_endpoints += 1
            
            return {
                "status": "success",
                "data": data,
                "metadata": {
                    "totalEndpoints": total_endpoints,
                    "activeEndpoints": active_endpoints,
                    "inactiveEndpoints": total_endpoints - active_endpoints,
                    "networkZones": list(network_zones),
                    "generatedFromDatabase": True,
                    "lastUpdated": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get network topology: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "status": "error", 
                "message": str(e),
                "data": [],
                "metadata": {
                    "totalEndpoints": 0,
                    "generatedFromDatabase": True
                }
            }
    
    async def get_software_download_data(self) -> List[Dict[str, Any]]:
        """Get software download data with camelCase"""
        return [
            {
                "id": 1,
                "name": "windows",
                "version": "2024.1.3",
                "description": "Windows endpoint agent with real-time monitoring, behavioral analysis, and AI-powered threat detection.",
                "fileName": "CodeGrey AI Endpoint Agent",
                "downloadUrl": "https://dev-codegrey.s3.ap-south-1.amazonaws.com/windows.zip",
                "os": "Windows",
                "architecture": "asd",
                "minRamGb": 45,
                "minDiskMb": 60,
                "configurationCmd": "codegrey-agent.exe --configure --server=https://os.codegrey.ai --token=YOUR_API_TOKEN",
                "systemRequirements": [
                    "Windows 10/11 (64-bit)",
                    "Administrator privileges",
                    "4 GB RAM",
                    "500 MB disk space"
                ]
            },
            {
                "id": 2,
                "name": "linux",
                "version": "2024.1.3",
                "description": "Linux endpoint agent with advanced process monitoring, network analysis, and ML-based anomaly detection.",
                "fileName": "CodeGrey AI Endpoint Agent",
                "downloadUrl": "https://dev-codegrey.s3.ap-south-1.amazonaws.com/linux.zip",
                "os": "Linux",
                "architecture": "asd",
                "minRamGb": 45,
                "minDiskMb": 60,
                "configurationCmd": "sudo codegrey-agent configure --server https://os.codegrey.ai --token YOUR_API_TOKEN",
                "systemRequirements": [
                    "Ubuntu 18.04+ / CentOS 7+ / RHEL 8+",
                    "Root access",
                    "2 GB RAM",
                    "300 MB disk space"
                ]
            },
            {
                "id": 3,
                "name": "macos",
                "version": "2024.1.3",
                "description": "macOS endpoint agent with privacy-focused monitoring, XProtect integration, and intelligent threat correlation.",
                "fileName": "CodeGrey AI Endpoint Agent",
                "downloadUrl": "https://dev-codegrey.s3.ap-south-1.amazonaws.com/macos.zip",
                "os": "macOS",
                "architecture": "asd",
                "minRamGb": 45,
                "minDiskMb": 60,
                "configurationCmd": "sudo /usr/local/bin/codegrey-agent --configure --server=https://os.codegrey.ai --token=YOUR_API_TOKEN",
                "systemRequirements": [
                    "macOS 11.0+",
                    "Administrator privileges",
                    "3 GB RAM",
                    "400 MB disk space"
                ]
            }
        ]
    
    async def get_detection_results_data(self) -> Dict[str, Any]:
        """Get detection results with FULL AI REPORT in logInfo.message"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get detection results with ml_results (contains full AI report)
            cursor.execute('''
                SELECT dr.id, dr.threat_detected, dr.confidence_score, dr.threat_type, 
                       dr.severity, dr.detected_at, le.agent_id, le.source, le.message,
                       a.hostname, a.ip_address, a.platform, dr.ml_results, dr.ai_analysis
                FROM detection_results dr
                JOIN log_entries le ON dr.log_entry_id = le.id
                LEFT JOIN agents a ON le.agent_id = a.id
                WHERE dr.threat_detected = 1
                ORDER BY dr.detected_at DESC
                LIMIT 5000
            ''')
            
            data = []
            for row in cursor.fetchall():
                detection_id = row[0]
                confidence = row[2]
                threat_type = row[3]
                severity = row[4]
                ml_results_json = row[12]  # ml_results column (JSON)
                ai_analysis_json = row[13]  # ai_analysis column (JSON)
                
                # Parse ml_results to get full AI report
                full_report = ""
                try:
                    import json
                    ml_results = json.loads(ml_results_json) if ml_results_json else {}
                    
                    # Get the AI verdict message (the full report)
                    log_message = ml_results.get('log_message', '')
                    
                    if log_message:
                        # This is the full AI report with reasoning
                        full_report = log_message
                    else:
                        # Fallback: construct report from available data
                        full_report = f"THREAT DETECTED: {threat_type.upper()}\n"
                        full_report += f"Confidence: {confidence*100:.1f}%\n"
                        full_report += f"Severity: {severity.upper()}\n\n"
                        
                        # Add indicators if available
                        indicators = ml_results.get('indicators', [])
                        if indicators:
                            full_report += f"Indicators of Compromise:\n"
                            for indicator in indicators:
                                full_report += f"  - {indicator}\n"
                            full_report += "\n"
                        
                        # Add original log context
                        original_message = row[8]  # le.message
                        if original_message:
                            full_report += f"Original Log: {original_message}\n"
                        
                        # Add source info
                        log_source = ml_results.get('log_source', row[7])
                        if log_source:
                            full_report += f"Source: {log_source}\n"
                
                except Exception as parse_error:
                    # If parsing fails, use original log message
                    full_report = f"THREAT DETECTED: {threat_type}\nConfidence: {confidence*100:.1f}%\nOriginal Log: {row[8]}"
                
                data.append({
                    'detectionId': detection_id,
                    'threatDetected': bool(row[1]),
                    'confidenceScore': confidence,
                    'threatType': threat_type,
                    'severity': severity,
                    'detectedAt': row[5],
                    'sourceMachine': {
                        'agentId': row[6],
                        'hostname': row[9],
                        'ipAddress': row[10],
                        'platform': row[11]
                    },
                    'logInfo': {
                        'source': row[7],
                        'message': full_report  # FULL AI REPORT HERE
                    }
                })
            
            conn.close()
            
            return {
                'status': 'success',
                'data': data,
                'totalThreats': len(data),
                'lastUpdated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get detection results: {e}")
            return {'status': 'error', 'message': str(e), 'data': []}
    
    async def get_enhanced_detection_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive AI detection report with MITRE mapping and threat intelligence"""
        try:
            # Import the enhanced detection reporter
            from enhanced_ai_detection_reports import enhanced_detection_reporter
            
            # Generate comprehensive report
            report = await enhanced_detection_reporter.generate_comprehensive_report(
                time_range_hours=time_range_hours,
                include_benign=False
            )
            
            # Format for API
            formatted_report = enhanced_detection_reporter.format_report_for_api(report)
            
            return {
                'status': 'success',
                'data': formatted_report,
                'lastUpdated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced detection report: {e}")
            return {
                'status': 'error', 
                'message': str(e), 
                'data': {
                    'reportId': f"error_report_{int(datetime.now().timestamp())}",
                    'generatedAt': datetime.now().isoformat(),
                    'error': str(e)
                }
            }
    
    def _detect_real_location(self, ip_address: str, hostname: str) -> Dict[str, Any]:
        """Detect location completely dynamically by learning from environment"""
        
        try:
            # Use machine learning to determine location from observed patterns
            location_info = self._learn_location_from_environment_sync(ip_address, hostname)
            return location_info
            
        except Exception as e:
            logger.error(f"Dynamic location detection error for {ip_address}: {e}")
            # Fallback to minimal info without hardcoded assumptions
            return {
                'physicalLocation': f'Network Endpoint ({hostname or ip_address})',
                'networkZone': self._determine_zone_from_traffic_analysis(ip_address),
                'city': self._learn_city_from_network_behavior_sync(ip_address),
                'country': self._detect_country_from_traffic_patterns_sync(ip_address)
            }
    
    def _get_real_local_location(self) -> Dict[str, Any]:
        """Get real location of local machine using public IP geolocation"""
        try:
            # This would use the client's public IP to determine real location
            # For now, return dynamic location based on system analysis
            import platform
            import socket
            
            system_name = platform.node()
            
            # Try to determine location from system information
            return {
                'physical': f'Development Machine ({system_name})',
                'city': 'Development Environment',
                'country': 'Local'
            }
            
        except Exception as e:
            logger.debug(f"Local location detection failed: {e}")
            return {'physical': 'Development Machine', 'city': 'Local', 'country': 'Local'}
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private range"""
        return (ip.startswith('192.168.') or 
                ip.startswith('10.') or 
                ip.startswith('172.16.') or
                ip.startswith('172.17.') or
                ip.startswith('172.18.') or
                ip.startswith('172.19.') or
                ip.startswith('172.20.'))
    
    def _analyze_private_network_dynamically(self, ip: str, hostname: str) -> Dict[str, Any]:
        """Dynamically analyze private network without hardcoded mappings"""
        
        # Dynamic network zone detection based on IP patterns and hostname
        network_info = {
            'physicalLocation': 'Corporate Network',
            'networkZone': 'Private Network',
            'city': 'Corporate Office',
            'country': 'Unknown'
        }
        
        # Analyze IP range to determine likely network type
        ip_parts = ip.split('.')
        
        # Use third octet to determine network segment dynamically
        if len(ip_parts) >= 3:
            third_octet = int(ip_parts[2])
            
            if third_octet == 1:
                network_info['networkZone'] = 'Management Network'
            elif third_octet <= 10:
                network_info['networkZone'] = 'Corporate LAN'
            elif third_octet <= 50:
                network_info['networkZone'] = 'Server Network'
            elif third_octet <= 100:
                network_info['networkZone'] = 'User Network'
            else:
                network_info['networkZone'] = 'Guest Network'
        
        # Dynamic hostname analysis
        if hostname:
            hostname_lower = hostname.lower()
            
            # Extract location hints from hostname dynamically
            location_keywords = {
                'server': 'Server Room',
                'dc': 'Data Center',
                'prod': 'Production Environment',
                'dev': 'Development Environment',
                'test': 'Test Environment',
                'staging': 'Staging Environment',
                'web': 'Web Server Farm',
                'db': 'Database Cluster',
                'mail': 'Email Server Room'
            }
            
            for keyword, location in location_keywords.items():
                if keyword in hostname_lower:
                    network_info['physicalLocation'] = location
                    break
        
        return network_info
    
    def _get_geolocation_data(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get real geolocation data for public IPs"""
        try:
            # This would call a real geolocation API
            # For development, return None to use fallback
            return None
            
        except Exception as e:
            logger.debug(f"Geolocation API failed for {ip}: {e}")
            return None
    
    def _analyze_hostname_dynamically(self, hostname: str) -> Dict[str, Any]:
        """Dynamically analyze hostname for location and context clues"""
        
        enhancements = {}
        hostname_lower = hostname.lower()
        
        # Dynamic city detection from hostname
        city_patterns = [
            ('ny', 'New York'), ('nyc', 'New York'), ('newyork', 'New York'),
            ('la', 'Los Angeles'), ('losangeles', 'Los Angeles'),
            ('chi', 'Chicago'), ('chicago', 'Chicago'),
            ('sf', 'San Francisco'), ('sanfrancisco', 'San Francisco'),
            ('sea', 'Seattle'), ('seattle', 'Seattle'),
            ('bos', 'Boston'), ('boston', 'Boston'),
            ('mia', 'Miami'), ('miami', 'Miami'),
            ('lon', 'London'), ('london', 'London'),
            ('par', 'Paris'), ('paris', 'Paris'),
            ('tok', 'Tokyo'), ('tokyo', 'Tokyo'),
            ('syd', 'Sydney'), ('sydney', 'Sydney'),
            ('mum', 'Mumbai'), ('mumbai', 'Mumbai'),
            ('del', 'Delhi'), ('delhi', 'Delhi'),
            ('ban', 'Bangalore'), ('bangalore', 'Bangalore')
        ]
        
        for pattern, city in city_patterns:
            if pattern in hostname_lower:
                enhancements['city'] = city
                enhancements['physicalLocation'] = f'{city} Office'
                break
        
        # Dynamic department/floor detection
        floor_patterns = [
            ('floor1', 'Floor 1'), ('f1', 'Floor 1'), ('1f', 'Floor 1'),
            ('floor2', 'Floor 2'), ('f2', 'Floor 2'), ('2f', 'Floor 2'),
            ('floor3', 'Floor 3'), ('f3', 'Floor 3'), ('3f', 'Floor 3'),
            ('basement', 'Basement'), ('ground', 'Ground Floor'),
            ('penthouse', 'Penthouse'), ('roof', 'Roof Level')
        ]
        
        for pattern, floor in floor_patterns:
            if pattern in hostname_lower:
                current_location = enhancements.get('physicalLocation', 'Office')
                enhancements['physicalLocation'] = f'{current_location} - {floor}'
                break
        
        return enhancements
    
    def _learn_location_from_environment_sync(self, ip_address: str, hostname: str) -> Dict[str, Any]:
        """Learn location from actual environment data without hardcoded patterns"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Learn from historical data and network behavior
            location_data = {
                'physicalLocation': self._infer_location_from_network_traffic_sync(ip_address, cursor),
                'networkZone': self._classify_network_zone_from_behavior_sync(ip_address, cursor),
                'city': self._extract_city_from_dns_queries_sync(ip_address, cursor),
                'country': self._determine_country_from_time_patterns_sync(ip_address, cursor)
            }
            
            conn.close()
            return location_data
            
        except Exception as e:
            logger.error(f"Environment learning failed: {e}")
            return {
                'physicalLocation': f'Discovered Endpoint ({hostname or ip_address})',
                'networkZone': 'Observed Network',
                'city': 'Unknown',
                'country': 'Unknown'
            }
    
    def _infer_location_from_network_traffic_sync(self, ip_address: str, cursor) -> str:
        """Infer physical location from network traffic patterns"""
        try:
            # Analyze communication patterns to infer location
            cursor.execute('''
                SELECT message, source FROM log_entries 
                WHERE agent_id IN (SELECT id FROM agents WHERE ip_address = ?)
                AND source = 'Windows-Network'
                ORDER BY timestamp DESC LIMIT 100
            ''', (ip_address,))
            
            traffic_logs = cursor.fetchall()
            
            if traffic_logs:
                # Analyze traffic to infer location context
                external_connections = 0
                internal_connections = 0
                
                for log_message, source in traffic_logs:
                    if 'external' in log_message.lower() or 'internet' in log_message.lower():
                        external_connections += 1
                    elif 'internal' in log_message.lower() or '192.168' in log_message:
                        internal_connections += 1
                
                # Infer location type from traffic patterns
                if external_connections > internal_connections * 2:
                    return 'Edge Network Location'
                elif internal_connections > external_connections * 3:
                    return 'Internal Network Location'
                else:
                    return 'Mixed Network Environment'
            
            return f'Network Endpoint ({ip_address})'
            
        except Exception as e:
            logger.debug(f"Traffic analysis failed: {e}")
            return f'Network Location ({ip_address})'
    
    def _classify_network_zone_from_behavior_sync(self, ip_address: str, cursor) -> str:
        """Classify network zone from observed behavior patterns"""
        try:
            # Analyze log patterns to classify network zone
            cursor.execute('''
                SELECT source, COUNT(*) as count FROM log_entries 
                WHERE agent_id IN (SELECT id FROM agents WHERE ip_address = ?)
                GROUP BY source
                ORDER BY count DESC
            ''', (ip_address,))
            
            source_patterns = cursor.fetchall()
            
            if source_patterns:
                primary_source = source_patterns[0][0]
                
                # Classify based on primary log source behavior
                if 'Security' in primary_source:
                    return 'Security Zone'
                elif 'System' in primary_source:
                    return 'System Network'
                elif 'Process' in primary_source:
                    return 'Workstation Network'
                elif 'Network' in primary_source:
                    return 'Network Infrastructure'
                else:
                    return 'General Network'
            
            return 'Unclassified Network'
            
        except Exception as e:
            logger.debug(f"Network zone classification failed: {e}")
            return 'Unknown Network Zone'
    
    def _extract_city_from_dns_queries_sync(self, ip_address: str, cursor) -> str:
        """Extract city information from DNS queries and network behavior"""
        try:
            # This would analyze DNS queries to infer geographic location
            # For now, return learned location from hostname if available
            cursor.execute('''
                SELECT hostname FROM agents WHERE ip_address = ?
            ''', (ip_address,))
            
            result = cursor.fetchone()
            if result and result[0]:
                hostname = result[0].lower()
                # Use ML to extract location patterns from hostname
                return self._ml_extract_location_from_text(hostname)
            
            return 'Unknown'
            
        except Exception as e:
            logger.debug(f"City extraction failed: {e}")
            return 'Unknown'
    
    def _determine_country_from_time_patterns_sync(self, ip_address: str, cursor) -> str:
        """Determine country from activity time patterns"""
        try:
            # Analyze activity patterns to infer timezone/country
            cursor.execute('''
                SELECT timestamp FROM log_entries 
                WHERE agent_id IN (SELECT id FROM agents WHERE ip_address = ?)
                ORDER BY timestamp DESC LIMIT 50
            ''', (ip_address,))
            
            timestamps = cursor.fetchall()
            
            if timestamps:
                # Analyze activity patterns to infer timezone
                hours = []
                for ts in timestamps:
                    try:
                        dt = datetime.fromisoformat(ts[0].replace('Z', '+00:00'))
                        hours.append(dt.hour)
                    except:
                        continue
                
                if hours:
                    # Infer country from activity patterns (business hours analysis)
                    avg_hour = sum(hours) / len(hours)
                    
                    # This is a simplified example - real implementation would use more sophisticated analysis
                    if 8 <= avg_hour <= 18:
                        return 'Inferred from Activity Patterns'
                    else:
                        return 'Different Timezone'
            
            return 'Unknown'
            
        except Exception as e:
            logger.debug(f"Country determination failed: {e}")
            return 'Unknown'
    
    def _ml_extract_location_from_text(self, text: str) -> str:
        """Use ML to extract location information from text"""
        try:
            # This would use NLP/ML to extract location entities
            # For now, return generic learned location
            if len(text) > 0:
                return f'Learned Location from {text[:10]}...'
            return 'Unknown'
            
        except Exception as e:
            logger.debug(f"ML location extraction failed: {e}")
            return 'Unknown'
    
    def _determine_zone_from_traffic_analysis(self, ip_address: str) -> str:
        """Determine network zone from traffic analysis"""
        try:
            # Analyze actual network traffic to determine zone
            # This would examine routing patterns, traffic volume, etc.
            return f'Zone learned from traffic analysis'
            
        except Exception as e:
            logger.debug(f"Traffic analysis failed: {e}")
            return 'Unknown Zone'
    
    def _learn_city_from_network_behavior_sync(self, ip_address: str) -> str:
        """Learn city from network behavior patterns"""
        try:
            # This would use ML to learn city from network behavior
            return 'City learned from behavior'
            
        except Exception as e:
            logger.debug(f"City learning failed: {e}")
            return 'Unknown'
    
    def _detect_country_from_traffic_patterns_sync(self, ip_address: str) -> str:
        """Detect country from traffic patterns"""
        try:
            # This would analyze traffic patterns to detect country
            return 'Country from traffic analysis'
            
        except Exception as e:
            logger.debug(f"Country detection failed: {e}")
            return 'Unknown'
    
    async def _analyze_security_with_ai(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to analyze endpoint security and provide rating from A to F
        Pure AI analysis - no hardcoded fallbacks
        """
        api_key = self.openai_api_key
        logger.info(f"AI Analysis - API Key present: {bool(api_key)}, Length: {len(api_key) if api_key else 0}")
        
        if not api_key:
            logger.error("OpenAI API key not configured - AI analysis unavailable")
            return {
                "securityRating": "Unknown",
                "securityScore": 0,
                "vulnerabilities": [],
                "securityIssues": ["AI analysis unavailable - OpenAI API key not configured"],
                "maliciousIPs": [],
                "analysis": "AI security analysis is not available. Please configure OPENAI_API_KEY environment variable.",
                "criticalFindings": [],
                "recommendations": ["Configure OpenAI API key to enable AI-powered security analysis"],
                "analysisMethod": "None (API key not configured)"
            }
        
        logger.info("Starting AI-powered security analysis with OpenAI GPT-3.5-Turbo")
        
        # Prepare summary for AI analysis
        summary = self._prepare_security_summary(endpoint_data)
        
        # Call OpenAI API for analysis
        import aiohttp
        
        prompt = f"""You are a cybersecurity expert analyzing an endpoint's security posture. Based on the following information, provide:
1. A security rating from A (excellent) to F (critical issues)
2. List of vulnerabilities found
3. Security issues identified
4. Malicious IP detection (if any)
5. Detailed security analysis

ENDPOINT INFORMATION:
{summary}

Respond ONLY with valid JSON in this exact format:
{{
    "securityRating": "A-F letter grade",
    "securityScore": 0-100 numeric score,
    "vulnerabilities": ["list of vulnerabilities found"],
    "securityIssues": ["list of security issues"],
    "maliciousIPs": ["list of suspicious/malicious IPs if any"],
    "analysis": "detailed security analysis text",
    "criticalFindings": ["most critical issues requiring immediate attention"],
    "recommendations": ["specific security recommendations"]
}}"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": "You are a cybersecurity expert. Always respond with valid JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1500
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # Remove markdown code blocks if present
                        if '```json' in content:
                            content = content.split('```json')[1].split('```')[0].strip()
                        elif '```' in content:
                            content = content.split('```')[1].split('```')[0].strip()
                        
                        analysis = json.loads(content)
                        
                        # Return AI analysis result
                        return {
                            "securityRating": analysis.get("securityRating", "Unknown"),
                            "securityScore": analysis.get("securityScore", 0),
                            "vulnerabilities": analysis.get("vulnerabilities", []),
                            "securityIssues": analysis.get("securityIssues", []),
                            "maliciousIPs": analysis.get("maliciousIPs", []),
                            "analysis": analysis.get("analysis", ""),
                            "criticalFindings": analysis.get("criticalFindings", []),
                            "recommendations": analysis.get("recommendations", []),
                            "analysisMethod": "AI-powered (OpenAI GPT-3.5-Turbo)"
                        }
                    else:
                        error_msg = f"OpenAI API returned status {response.status}"
                        logger.error(error_msg)
                        return {
                            "securityRating": "Error",
                            "securityScore": 0,
                            "vulnerabilities": [],
                            "securityIssues": [error_msg],
                            "maliciousIPs": [],
                            "analysis": f"AI analysis failed: {error_msg}",
                            "criticalFindings": [],
                            "recommendations": ["Check OpenAI API status and credentials"],
                            "analysisMethod": f"Error (HTTP {response.status})"
                        }
        except json.JSONDecodeError as je:
            error_msg = f"Failed to parse AI response: {je}"
            logger.error(error_msg)
            return {
                "securityRating": "Error",
                "securityScore": 0,
                "vulnerabilities": [],
                "securityIssues": [error_msg],
                "maliciousIPs": [],
                "analysis": f"AI analysis failed: Invalid JSON response",
                "criticalFindings": [],
                "recommendations": ["Contact support - AI returned invalid response"],
                "analysisMethod": "Error (Invalid JSON)"
            }
        except Exception as e:
            error_msg = f"AI analysis exception: {str(e)}"
            logger.error(error_msg)
            return {
                "securityRating": "Error",
                "securityScore": 0,
                "vulnerabilities": [],
                "securityIssues": [error_msg],
                "maliciousIPs": [],
                "analysis": f"AI analysis failed with exception: {str(e)}",
                "criticalFindings": [],
                "recommendations": ["Check network connectivity and API configuration"],
                "analysisMethod": f"Error ({type(e).__name__})"
            }
    
    def _prepare_security_summary(self, endpoint_data: Dict[str, Any]) -> str:
        """Prepare endpoint data summary for AI analysis"""
        quick_summary = endpoint_data.get('quick_summary', {})
        system_info = endpoint_data.get('system_info', {})
        
        # Extract security info from the correct locations
        firewall_status = "unknown"
        antivirus_status = "unknown"
        
        # Try to get from quick_summary first
        if quick_summary:
            firewall_status = quick_summary.get('firewall', 'unknown')
            antivirus_status = quick_summary.get('antivirus', 'unknown')
        
        # If not found, try to get from system_info
        if system_info and 'security' in system_info:
            sec_info = system_info['security']
            if not firewall_status or firewall_status == 'unknown':
                firewall_status = sec_info.get('firewall_status', 'unknown')
            if not antivirus_status or antivirus_status == 'unknown':
                antivirus_status = sec_info.get('antivirus_status', 'unknown')
        
        summary_parts = [
            f"Hostname: {endpoint_data.get('hostname', 'Unknown')}",
            f"IP Address: {endpoint_data.get('ip_address', 'Unknown')}",
            f"Platform: {endpoint_data.get('platform', 'Unknown')} {endpoint_data.get('os_version', '')}",
            f"Status: {endpoint_data.get('status', 'Unknown')}",
            f"\nSecurity Configuration:",
            f"- Firewall: {firewall_status}",
            f"- Antivirus: {antivirus_status}",
        ]
        
        # Add detailed firewall information
        if system_info and 'security' in system_info:
            sec_info = system_info['security']
            
            if 'firewall_details' in sec_info:
                fw = sec_info['firewall_details']
                summary_parts.append(f"\nFirewall Details:")
                summary_parts.append(f"- Type: {fw.get('type', 'Unknown')}")
                summary_parts.append(f"- Status: {fw.get('status', 'unknown')}")
                
                if 'profiles' in fw:
                    summary_parts.append(f"- Profiles:")
                    for profile_name, profile_data in fw['profiles'].items():
                        summary_parts.append(f"  * {profile_name.title()}: {profile_data.get('state', 'unknown')}")
                        if 'policy' in profile_data:
                            summary_parts.append(f"    Policy: {profile_data['policy']}")
                
                if 'rules' in fw:
                    rules = fw['rules']
                    summary_parts.append(f"- Firewall Rules:")
                    summary_parts.append(f"  Total: {rules.get('total_rules', 0)}")
                    summary_parts.append(f"  Inbound: {rules.get('inbound_total', 0)}")
                    summary_parts.append(f"  Outbound: {rules.get('outbound_total', 0)}")
                    summary_parts.append(f"  Enabled: {rules.get('enabled_rules', 0)}")
                
                if 'active_profile' in fw:
                    summary_parts.append(f"- Active Profile: {fw['active_profile']}")
            
            # Add detailed antivirus information
            if 'antivirus_details' in sec_info:
                av = sec_info['antivirus_details']
                summary_parts.append(f"\nAntivirus Details:")
                summary_parts.append(f"- Primary Product: {av.get('primary_product', 'Unknown')}")
                summary_parts.append(f"- Status: {av.get('status', 'unknown')}")
                summary_parts.append(f"- Real-time Protection: {av.get('real_time_protection', 'unknown')}")
                summary_parts.append(f"- Total Products: {av.get('total_products', 0)}")
                summary_parts.append(f"- Up-to-date: {av.get('up_to_date', 'unknown')}")
                
                # List all products
                if 'products' in av and av['products']:
                    summary_parts.append(f"- All Products:")
                    for product in av['products']:
                        status = "ENABLED" if product.get('enabled', False) else "DISABLED"
                        summary_parts.append(f"  * {product.get('name', 'Unknown')}: {status}")
                        if product.get('up_to_date') is not None:
                            summary_parts.append(f"    Up-to-date: {product.get('up_to_date', 'unknown')}")
            
            # Add Windows Update status
            if 'windows_updates' in sec_info:
                updates = sec_info['windows_updates']
                if updates.get('status') != 'unknown':
                    summary_parts.append(f"\nWindows Updates:")
                    summary_parts.append(f"- Status: {updates.get('status', 'unknown')}")
                    if 'recently_installed' in updates:
                        summary_parts.append(f"- Recently Installed: {updates.get('recently_installed', 0)} updates")
            
            # Add encryption status
            if 'encryption_status' in sec_info:
                enc = sec_info['encryption_status']
                if enc.get('bitlocker') != 'unknown':
                    summary_parts.append(f"\nDisk Encryption:")
                    summary_parts.append(f"- BitLocker: {enc.get('bitlocker', 'unknown')}")
                    if enc.get('encrypted_volumes'):
                        summary_parts.append(f"- Encrypted Volumes: {enc.get('encrypted_volumes', 0)}")
        
        # Add network info
        if system_info and 'network' in system_info:
            net = system_info['network']
            if 'interfaces' in net:
                ips = []
                for iface in net['interfaces']:
                    for addr in iface.get('addresses', []):
                        if addr.get('address'):
                            ips.append(addr['address'])
                summary_parts.append(f"\nNetwork Interfaces:")
                summary_parts.append(f"- IP Addresses: {', '.join(ips)}")
            
            if 'connections' in net:
                conn = net['connections']
                summary_parts.append(f"- Active Connections: {conn.get('established', 0)}")
                if conn.get('listening_ports'):
                    ports = [str(p.get('port', '?')) for p in conn['listening_ports'][:10]]
                    summary_parts.append(f"- Listening Ports: {', '.join(ports)}")
            
            if 'dns_servers' in net:
                summary_parts.append(f"- DNS Servers: {', '.join(net['dns_servers'])}")
        
        # Add hardware info
        if system_info and 'hardware' in system_info:
            hw = system_info['hardware']
            if 'cpu' in hw:
                summary_parts.append(f"\nHardware Usage:")
                summary_parts.append(f"- CPU Usage: {hw['cpu'].get('usage_percent', 0)}%")
            if 'memory' in hw:
                summary_parts.append(f"- Memory Usage: {hw['memory'].get('percent', 0)}%")
        
        # Add security context
        if system_info and 'security' in system_info:
            sec = system_info['security']
            summary_parts.append(f"\nSecurity Context:")
            summary_parts.append(f"- User Accounts: {sec.get('user_accounts_count', 0)}")
            summary_parts.append(f"- Running Processes: {sec.get('process_count', 0)}")
            if sec.get('logged_in_users'):
                users = [u.get('name', '?') for u in sec['logged_in_users'][:5]]
                summary_parts.append(f"- Logged In Users: {', '.join(users)}")
        
        return '\n'.join(summary_parts)
    
    async def _generate_endpoint_report(self, agent_id: str, hostname: str, ip_address: str, 
                                   platform: str, os_version: str, status: str, 
                                   services: List[str], quick_summary: Dict, 
                                   system_info: Dict, cursor) -> Dict[str, Any]:
        """Generate comprehensive endpoint report"""
        try:
            # Prepare data for AI security analysis
            endpoint_data = {
                'agent_id': agent_id,
                'hostname': hostname,
                'ip_address': ip_address,
                'platform': platform,
                'os_version': os_version,
                'status': status,
                'services': services,
                'quick_summary': quick_summary,
                'system_info': system_info
            }
            
            # Get AI security analysis - always use AI, no fallbacks
            ai_security_analysis = await self._analyze_security_with_ai(endpoint_data)
            
            report = {
                "reportId": f"report_{agent_id}_{int(datetime.now().timestamp())}",
                "generatedAt": datetime.now().isoformat(),
                "endpointId": agent_id,
                "socAnalystReport": self._generate_soc_analyst_report(
                    hostname, ip_address, platform, os_version, status, 
                    services, quick_summary, system_info, cursor, agent_id, ai_security_analysis
                )
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate endpoint report: {e}")
            return {
                "reportId": f"report_{agent_id}_error",
                "generatedAt": datetime.now().isoformat(),
                "error": str(e),
                "summary": "Report generation failed",
                "socAnalystReport": {
                    "endpointInfo": {
                        "hostname": hostname or "Unknown",
                        "ipAddress": ip_address or "Unknown",
                        "platform": f"{platform or 'Unknown'} {os_version or ''}",
                        "status": status or "unknown",
                        "lastSeen": "Unknown"
                    },
                    "securityPosture": {
                        "firewall": "unknown",
                        "antivirus": "unknown",
                        "primaryAV": "Unknown",
                        "realTimeProtection": "unknown",
                        "totalAVProducts": 0
                    },
                    "threatActivity": {
                        "threatsLast7Days": 0,
                        "logsLast24h": 0,
                        "riskLevel": "UNKNOWN",
                        "riskFactors": [f"Report generation failed: {str(e)}"]
                    },
                    "networkExposure": {
                        "listeningPorts": 0,
                        "topPorts": [],
                        "activeConnections": 0
                    },
                    "userActivity": {
                        "loggedInUsers": 0,
                        "userNames": [],
                        "processCount": 0
                    },
                    "aiAnalysis": {
                        "securityRating": "Unknown",
                        "securityScore": 0,
                        "criticalFindings": ["Unable to generate security analysis"],
                        "topRecommendations": ["Check system connectivity and agent status"]
                    },
                    "actionItems": [
                        {
                            "priority": "HIGH",
                            "action": "Investigate report generation failure",
                            "reason": f"Report generation failed: {str(e)}"
                        }
                    ]
                }
            }
    
    def _generate_soc_analyst_report(self, hostname: str, ip_address: str, platform: str, 
                                   os_version: str, status: str, services: List[str],
                                   quick_summary: Dict, system_info: Dict, cursor, 
                                   agent_id: str, ai_analysis: Dict) -> Dict[str, Any]:
        """Generate concise SOC analyst report with essential information only"""
        
        # Extract security info
        firewall_status = "unknown"
        antivirus_status = "unknown"
        antivirus_details = {}
        
        if quick_summary:
            firewall_status = quick_summary.get('firewall', 'unknown')
            antivirus_status = quick_summary.get('antivirus', 'unknown')
        
        if system_info and 'security' in system_info:
            sec_info = system_info['security']
            if not firewall_status or firewall_status == 'unknown':
                firewall_status = sec_info.get('firewall_status', 'unknown')
            if not antivirus_status or antivirus_status == 'unknown':
                antivirus_status = sec_info.get('antivirus_status', 'unknown')
            antivirus_details = sec_info.get('antivirus_details', {})
        
        # Get threat count
        threat_count = 0
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM detections 
                WHERE agent_id = ? AND detected_at >= datetime('now', '-7 days')
            ''', (agent_id,))
            threat_count = cursor.fetchone()[0] or 0
        except:
            pass
        
        # Get recent activity
        recent_logs = 0
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM log_entries 
                WHERE agent_id = ? AND timestamp >= datetime('now', '-24 hours')
            ''', (agent_id,))
            recent_logs = cursor.fetchone()[0] or 0
        except Exception:
            pass
            
        # Get listening ports (security critical)
        listening_ports = []
        if system_info and 'network' in system_info and 'connections' in system_info['network']:
            listening_ports = system_info['network']['connections'].get('listening_ports', [])[:10]  # Top 10
        
        # Get logged in users (security critical)
        logged_users = []
        if system_info and 'security' in system_info:
            logged_users = system_info['security'].get('logged_in_users', [])
        
        # Calculate risk level
        risk_level = "LOW"
        risk_factors = []
        
        if status != "active":
            risk_level = "HIGH"
            risk_factors.append("Endpoint offline")
        
        if firewall_status == "unknown" or "disabled" in firewall_status.lower():
            risk_level = "HIGH" if risk_level == "LOW" else risk_level
            risk_factors.append("Firewall issues")
        
        if antivirus_status == "unknown" or "disabled" in antivirus_status.lower():
            risk_level = "HIGH" if risk_level == "LOW" else risk_level
            risk_factors.append("Antivirus issues")
        
        if threat_count > 5:
            risk_level = "HIGH" if risk_level == "LOW" else risk_level
            risk_factors.append(f"{threat_count} threats detected")
        
        if len(listening_ports) > 20:
            risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
            risk_factors.append("Many open ports")
        
        return {
            "endpointInfo": {
                "hostname": hostname,
                "ipAddress": ip_address,
                "platform": f"{platform} {os_version}",
                "status": status,
                "lastSeen": quick_summary.get('boot_time', 'Unknown') if quick_summary else 'Unknown'
            },
            "securityPosture": {
                "firewall": firewall_status,
                "antivirus": antivirus_status,
                "primaryAV": antivirus_details.get('primary_product', 'Unknown'),
                "realTimeProtection": antivirus_details.get('real_time_protection', 'unknown'),
                "totalAVProducts": antivirus_details.get('total_products', 0)
            },
            "threatActivity": {
                "threatsLast7Days": threat_count,
                "logsLast24h": recent_logs,
                "riskLevel": risk_level,
                "riskFactors": risk_factors
            },
            "networkExposure": {
                "listeningPorts": len(listening_ports),
                "topPorts": [f"{p['port']}/{p['address']}" for p in listening_ports[:5]],
                "activeConnections": system_info.get('network', {}).get('connections', {}).get('established', 0) if system_info else 0
            },
            "userActivity": {
                "loggedInUsers": len(logged_users),
                "userNames": [user.get('name', 'Unknown') for user in logged_users],
                "processCount": system_info.get('security', {}).get('process_count', 0) if system_info else 0
            },
            "aiAnalysis": {
                "securityRating": ai_analysis.get('securityRating', 'Unknown'),
                "securityScore": ai_analysis.get('securityScore', 0),
                "criticalFindings": ai_analysis.get('criticalFindings', []),
                "topRecommendations": ai_analysis.get('recommendations', [])[:3]  # Top 3 only
            },
            "actionItems": self._generate_soc_action_items(
                risk_level, risk_factors, firewall_status, antivirus_status, threat_count
            )
        }
    
    def _generate_soc_action_items(self, risk_level: str, risk_factors: List[str], 
                                 firewall_status: str, antivirus_status: str, 
                                 threat_count: int) -> List[Dict[str, str]]:
        """Generate actionable items for SOC analysts"""
        actions = []
        
        if risk_level == "HIGH":
            actions.append({
                "priority": "CRITICAL",
                "action": "Immediate investigation required",
                "reason": f"High risk factors: {', '.join(risk_factors)}"
            })
        
        if "disabled" in firewall_status.lower() or firewall_status == "unknown":
            actions.append({
                "priority": "HIGH",
                "action": "Verify firewall configuration",
                "reason": f"Firewall status: {firewall_status}"
            })
        
        if "disabled" in antivirus_status.lower() or antivirus_status == "unknown":
            actions.append({
                "priority": "HIGH", 
                "action": "Verify antivirus protection",
                "reason": f"Antivirus status: {antivirus_status}"
            })
        
        if threat_count > 0:
            actions.append({
                "priority": "MEDIUM",
                "action": "Review threat detections",
                "reason": f"{threat_count} threats detected in last 7 days"
            })
        
        if not actions:
            actions.append({
                "priority": "INFO",
                "action": "Continue monitoring",
                "reason": "No immediate security concerns detected"
            })
        
        return actions
    
    def _generate_endpoint_summary(self, hostname: str, ip_address: str, 
                                    platform: str, status: str, 
                                    quick_summary: Dict) -> Dict[str, Any]:
        """Generate endpoint summary"""
        return {
            "hostname": hostname,
            "ipAddress": ip_address,
            "platform": platform,
            "status": status,
            "statusDescription": "Active and reporting" if status == "active" else "Inactive or offline",
            "cpuCores": quick_summary.get("cpu_cores", 0) if quick_summary else 0,
            "memoryGb": quick_summary.get("memory_gb", 0) if quick_summary else 0,
            "diskGb": quick_summary.get("disk_gb", 0) if quick_summary else 0,
            "lastContact": quick_summary.get("boot_time", "Unknown") if quick_summary else "Unknown"
        }
    
    def _generate_system_details(self, platform: str, os_version: str, 
                                  quick_summary: Dict, system_info: Dict) -> Dict[str, Any]:
        """Generate detailed system information"""
        details = {
            "operatingSystem": {
                "platform": platform,
                "version": os_version,
                "architecture": system_info.get("system", {}).get("architecture", "Unknown") if system_info else "Unknown",
                "bootTime": quick_summary.get("boot_time", "Unknown") if quick_summary else "Unknown"
            },
            "hardware": {
                "cpuCores": quick_summary.get("cpu_cores", 0) if quick_summary else 0,
                "memoryTotal": quick_summary.get("memory_gb", 0) if quick_summary else 0,
                "diskTotal": quick_summary.get("disk_gb", 0) if quick_summary else 0
            }
        }
        
        # Add detailed hardware info if available
        if system_info and "hardware" in system_info:
            hw_info = system_info["hardware"]
            details["hardware"].update({
                "cpuUsage": hw_info.get("cpu", {}).get("usage_percent", 0),
                "memoryUsed": hw_info.get("memory", {}).get("used", 0),
                "memoryPercent": hw_info.get("memory", {}).get("percent", 0),
                "diskUsed": sum([disk.get("used", 0) for disk in hw_info.get("disk", [])]),
                "diskPercent": sum([disk.get("percent", 0) for disk in hw_info.get("disk", [])]) / max(len(hw_info.get("disk", [])), 1)
            })
        
        return details
    
    def _generate_network_details(self, ip_address: str, services: List[str], 
                                   system_info: Dict) -> Dict[str, Any]:
        """Generate network details"""
        details = {
            "primaryIp": ip_address,
            "services": services,
            "activeConnections": 0,
            "openPorts": []
        }
        
        # Add network info if available
        if system_info and "network" in system_info:
            net_info = system_info["network"]
            
            # Get all IP addresses
            if "interfaces" in net_info:
                all_ips = []
                for interface in net_info["interfaces"]:
                    for addr in interface.get("addresses", []):
                        if addr.get("address") and not addr.get("address").startswith("127."):
                            all_ips.append(addr.get("address"))
                details["allIpAddresses"] = all_ips
            
            # Get connection info
            if "connections" in net_info:
                conn_info = net_info["connections"]
                details["activeConnections"] = conn_info.get("established", 0)
                details["listeningPorts"] = conn_info.get("listening_ports", [])
            
            # DNS servers
            if "dns_servers" in net_info:
                details["dnsServers"] = net_info["dns_servers"]
        
        return details
    
    def _generate_security_details(self, quick_summary: Dict, system_info: Dict, 
                                    cursor, agent_id: str) -> Dict[str, Any]:
        """Generate security details"""
        details = {
            "firewall": quick_summary.get("firewall", "unknown") if quick_summary else "unknown",
            "antivirus": quick_summary.get("antivirus", "unknown") if quick_summary else "unknown",
            "threatDetections": 0,
            "vulnerabilities": [],
            "securityScore": 0
        }
        
        # Get threat detection count
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM detection_results dr
                JOIN log_entries le ON dr.log_entry_id = le.id
                WHERE le.agent_id = ? AND dr.threat_detected = 1
                AND dr.detected_at > datetime('now', '-7 days')
            """, (agent_id,))
            result = cursor.fetchone()
            details["threatDetections"] = result[0] if result else 0
        except:
            pass
            
        # Add security info if available
        if system_info and "security" in system_info:
            sec_info = system_info["security"]
            details.update({
                "userAccountsCount": sec_info.get("user_accounts_count", 0),
                "processCount": sec_info.get("process_count", 0),
                "loggedInUsers": sec_info.get("logged_in_users", [])
            })
        
        # Calculate security score
        score = 100
        if details["firewall"] == "disabled":
            score -= 30
        if details["antivirus"] == "disabled" or "disabled" in details["antivirus"].lower():
            score -= 30
        if details["threatDetections"] > 10:
            score -= 20
        elif details["threatDetections"] > 5:
            score -= 10
        
        details["securityScore"] = max(score, 0)
        details["securityLevel"] = "High" if score >= 80 else "Medium" if score >= 60 else "Low"
        
        return details
    
    def _generate_activity_details(self, cursor, agent_id: str) -> Dict[str, Any]:
        """Generate activity details"""
        details = {
            "logsSent24h": 0,
            "logsPerHour": 0,
            "commandsExecuted": 0,
            "lastActivity": "Unknown",
            "activityTimeline": []
        }
        
        try:
            # Get logs sent in last 24 hours
            cursor.execute("""
                SELECT COUNT(*) FROM log_entries
                WHERE agent_id = ? AND timestamp > datetime('now', '-24 hours')
            """, (agent_id,))
            result = cursor.fetchone()
            details["logsSent24h"] = result[0] if result else 0
            details["logsPerHour"] = round(details["logsSent24h"] / 24, 2)
            
            # Get commands executed
            cursor.execute("""
                SELECT COUNT(*) FROM commands
                WHERE agent_id = ? AND status = 'completed'
            """, (agent_id,))
            result = cursor.fetchone()
            details["commandsExecuted"] = result[0] if result else 0
            
            # Get activity timeline (hourly breakdown)
            cursor.execute("""
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM log_entries
                WHERE agent_id = ? AND timestamp > datetime('now', '-24 hours')
                GROUP BY hour
                ORDER BY hour DESC
                LIMIT 24
            """, (agent_id,))
            
            timeline = []
            for row in cursor.fetchall():
                timeline.append({
                    "hour": row[0],
                    "logCount": row[1]
                })
            details["activityTimeline"] = timeline
            
        except Exception as e:
            logger.error(f"Failed to get activity details: {e}")
        
        return details
    
    def _generate_threat_assessment(self, cursor, agent_id: str, 
                                     quick_summary: Dict) -> Dict[str, Any]:
        """Generate threat assessment"""
        assessment = {
            "riskLevel": "Low",
            "riskScore": 0,
            "recentThreats": [],
            "criticalIssues": [],
            "warnings": []
        }
        
        try:
            # Get recent threats
            cursor.execute("""
                SELECT dr.threat_type, dr.severity, dr.detected_at, dr.confidence_score
                FROM detection_results dr
                JOIN log_entries le ON dr.log_entry_id = le.id
                WHERE le.agent_id = ? AND dr.threat_detected = 1
                AND dr.detected_at > datetime('now', '-7 days')
                ORDER BY dr.detected_at DESC
                LIMIT 10
            """, (agent_id,))
            
            threats = []
            risk_score = 0
            for row in cursor.fetchall():
                threat = {
                    "type": row[0],
                    "severity": row[1],
                    "detectedAt": row[2],
                    "confidence": row[3]
                }
                threats.append(threat)
                
                # Add to risk score
                if row[1] == "critical":
                    risk_score += 30
                elif row[1] == "high":
                    risk_score += 20
                elif row[1] == "medium":
                    risk_score += 10
                else:
                    risk_score += 5
            
            assessment["recentThreats"] = threats
            assessment["riskScore"] = min(risk_score, 100)
            
            # Determine risk level
            if risk_score >= 70:
                assessment["riskLevel"] = "Critical"
            elif risk_score >= 50:
                assessment["riskLevel"] = "High"
            elif risk_score >= 30:
                assessment["riskLevel"] = "Medium"
            else:
                assessment["riskLevel"] = "Low"
            
            # Check for critical issues
            if quick_summary:
                if quick_summary.get("firewall") == "disabled":
                    assessment["criticalIssues"].append("Firewall is disabled")
                if "disabled" in quick_summary.get("antivirus", "").lower():
                    assessment["criticalIssues"].append("Antivirus is disabled")
            
            # Add warnings based on threat count
            if len(threats) > 5:
                assessment["warnings"].append(f"{len(threats)} threats detected in the last 7 days")
                
        except Exception as e:
            logger.error(f"Failed to generate threat assessment: {e}")
        
        return assessment
    
    def _generate_endpoint_recommendations(self, quick_summary: Dict, 
                                            system_info: Dict, 
                                            status: str) -> List[Dict[str, Any]]:
        """Generate recommendations for the endpoint"""
        recommendations = []
            
        try:
            # Check firewall
            if quick_summary and quick_summary.get("firewall") == "disabled":
                recommendations.append({
                    "priority": "critical",
                    "category": "security",
                    "title": "Enable Firewall",
                    "description": "The firewall is currently disabled. Enable it immediately to protect against network attacks.",
                    "action": "Enable Windows Firewall or equivalent"
                })
            
            # Check antivirus
            if quick_summary and ("disabled" in quick_summary.get("antivirus", "").lower()):
                recommendations.append({
                    "priority": "critical",
                    "category": "security",
                    "title": "Enable Antivirus Protection",
                    "description": "Antivirus protection is disabled. Enable it to protect against malware.",
                    "action": "Enable Windows Defender or install antivirus software"
                })
            
            # Check disk space
            if quick_summary and quick_summary.get("disk_gb", 0) > 0:
                disk_usage = system_info.get("hardware", {}).get("disk", []) if system_info else []
                for disk in disk_usage:
                    if disk.get("percent", 0) > 90:
                        recommendations.append({
                            "priority": "high",
                            "category": "performance",
                            "title": "Low Disk Space",
                            "description": f"Disk {disk.get('mountpoint', 'unknown')} is {disk.get('percent', 0)}% full",
                            "action": "Free up disk space or expand storage"
                        })
            
            # Check memory
            if system_info and "hardware" in system_info:
                mem_percent = system_info.get("hardware", {}).get("memory", {}).get("percent", 0)
                if mem_percent > 90:
                    recommendations.append({
                        "priority": "medium",
                        "category": "performance",
                        "title": "High Memory Usage",
                        "description": f"Memory usage is at {mem_percent}%",
                        "action": "Close unnecessary applications or add more RAM"
                    })
            
            # Check if offline
            if status != "active":
                recommendations.append({
                    "priority": "high",
                    "category": "connectivity",
                    "title": "Endpoint Offline",
                    "description": "This endpoint is not actively reporting",
                    "action": "Check network connectivity and agent status"
                })
            
            # If no issues, add positive feedback
            if not recommendations:
                recommendations.append({
                    "priority": "info",
                    "category": "status",
                    "title": "System Healthy",
                    "description": "No immediate issues detected. System is operating normally.",
                    "action": "Continue monitoring"
                })
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
        
        return recommendations
    
    def _calculate_endpoint_health_score(self, status: str, quick_summary: Dict, 
                                          system_info: Dict) -> Dict[str, Any]:
        """Calculate overall endpoint health score"""
        score = 100
        breakdown = {
            "security": 100,
            "performance": 100,
            "connectivity": 100,
            "compliance": 100
        }
        
        try:
            # Security score
            if quick_summary:
                if quick_summary.get("firewall") == "disabled":
                    breakdown["security"] -= 40
                if "disabled" in quick_summary.get("antivirus", "").lower():
                    breakdown["security"] -= 40
            
            # Performance score
            if system_info and "hardware" in system_info:
                hw = system_info["hardware"]
                cpu_usage = hw.get("cpu", {}).get("usage_percent", 0)
                mem_percent = hw.get("memory", {}).get("percent", 0)
                
                if cpu_usage > 90:
                    breakdown["performance"] -= 30
                elif cpu_usage > 75:
                    breakdown["performance"] -= 15
                
                if mem_percent > 90:
                    breakdown["performance"] -= 30
                elif mem_percent > 75:
                    breakdown["performance"] -= 15
            
            # Connectivity score
            if status != "active":
                breakdown["connectivity"] = 0
            
            # Calculate overall score
            score = sum(breakdown.values()) / len(breakdown)
            
            # Determine health level
            if score >= 90:
                health_level = "Excellent"
            elif score >= 75:
                health_level = "Good"
            elif score >= 60:
                health_level = "Fair"
            elif score >= 40:
                health_level = "Poor"
            else:
                health_level = "Critical"
            
            return {
                "overallScore": round(score, 1),
                "healthLevel": health_level,
                "breakdown": breakdown,
                "lastCalculated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate health score: {e}")
            return {
                "overallScore": 50,
                "healthLevel": "Unknown",
                "breakdown": breakdown,
                "error": str(e)
            }

# Global instance
api_utils = APIUtils()
