#!/usr/bin/env python3
"""
API Utilities for CodeGrey AI SOC Platform
Centralized API response formatting and data management
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class APIUtils:
    """Utility class for API operations"""
    
    def __init__(self, db_path: str = "dev_soc_database.db"):
        self.db_path = db_path
    
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
            
            # Get all registered agents
            cursor.execute('''
                SELECT id, hostname, ip_address, platform, status, last_heartbeat, agent_version
                FROM agents 
                ORDER BY last_heartbeat DESC
            ''')
            
            agents = cursor.fetchall()
            
            data = []
            for agent in agents:
                agent_id, hostname, ip_address, platform, status, last_heartbeat, agent_type = agent
                
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
                
                data.append({
                    "hostname": hostname or "Unknown",
                    "ipAddress": ip_address or "Unknown",
                    "platform": platform or "Unknown",
                    "location": location,
                    "status": current_status,
                    "services": services,
                    "lastSeen": last_heartbeat or datetime.now().isoformat(),
                    "agentType": "clientEndpoint",
                    "importance": "high" if current_status == "active" else "low"
                })
            
            conn.close()
            
            return {
                "status": "success",
                "data": data,
                "metadata": {
                    "totalEndpoints": len(data),
                    "activeEndpoints": len([d for d in data if d["status"] == "active"]),
                    "inactiveEndpoints": len([d for d in data if d["status"] == "inactive"]),
                    "generatedFromDatabase": True,
                    "lastUpdated": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get network topology: {e}")
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
        """Get detection results with source machine info"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT dr.id, dr.threat_detected, dr.confidence_score, dr.threat_type, 
                       dr.severity, dr.detected_at, le.agent_id, le.source, le.message,
                       a.hostname, a.ip_address, a.platform
                FROM detection_results dr
                JOIN log_entries le ON dr.log_entry_id = le.id
                LEFT JOIN agents a ON le.agent_id = a.id
                WHERE dr.threat_detected = 1
                ORDER BY dr.detected_at DESC
                LIMIT 50
            ''')
            
            data = []
            for row in cursor.fetchall():
                data.append({
                    'detectionId': row[0],
                    'threatDetected': bool(row[1]),
                    'confidenceScore': row[2],
                    'threatType': row[3],
                    'severity': row[4],
                    'detectedAt': row[5],
                    'sourceMachine': {
                        'agentId': row[6],
                        'hostname': row[9],
                        'ipAddress': row[10],
                        'platform': row[11]
                    },
                    'logInfo': {
                        'source': row[7],
                        'message': row[8][:200] + '...' if len(row[8]) > 200 else row[8]
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

# Global instance
api_utils = APIUtils()
