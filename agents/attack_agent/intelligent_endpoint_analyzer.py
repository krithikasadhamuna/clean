#!/usr/bin/env python3
"""
Intelligent Endpoint Analyzer
AI-powered analysis of endpoints to determine roles, capabilities, and attack potential
"""

import logging
import platform
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IntelligentEndpointAnalyzer:
    """
    AI analyzes endpoints to determine:
    - Executive vs normal users
    - SMTP/FTP/Web server capabilities  
    - Database servers
    - High-value targets
    - Attack vector possibilities
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.analysis_cache = {}
        
    async def analyze_endpoint_capabilities(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI determines what this endpoint can do
        
        Returns:
            {
                'can_be_smtp': bool,
                'can_be_ftp': bool,
                'can_be_web_server': bool,
                'can_be_database': bool,
                'is_executive': bool,
                'is_admin': bool,
                'attack_potential': float,
                'recommended_roles': List[str]
            }
        """
        try:
            endpoint_id = endpoint.get('id', 'unknown')
            
            # Check cache first
            if endpoint_id in self.analysis_cache:
                cached = self.analysis_cache[endpoint_id]
                if (datetime.utcnow() - cached['timestamp']).seconds < 300:  # 5 min cache
                    return cached['analysis']
            
            # Get endpoint information
            hostname = endpoint.get('hostname', '').lower()
            platform_info = endpoint.get('platform', '').lower()
            network_role = endpoint.get('network_role', '').lower()
            detected_services = endpoint.get('detected_services', '').lower()
            open_ports = endpoint.get('open_ports', '')
            
            # Parse open ports
            ports = []
            if open_ports:
                try:
                    ports = json.loads(open_ports) if isinstance(open_ports, str) else open_ports
                except:
                    ports = []
            
            # Analyze capabilities
            analysis = {
                'endpoint_id': endpoint_id,
                'hostname': hostname,
                'platform': platform_info,
                
                # Server capabilities
                'can_be_smtp': self._check_smtp_capability(endpoint, ports, detected_services),
                'can_be_ftp': self._check_ftp_capability(endpoint, ports, detected_services),
                'can_be_web_server': self._check_web_capability(endpoint, ports, detected_services),
                'can_be_database': self._check_database_capability(endpoint, ports, detected_services),
                
                # User classification
                'is_executive': self._check_executive_user(endpoint, hostname, network_role),
                'is_admin': self._check_admin_user(endpoint, hostname, network_role),
                'is_domain_controller': 'domain' in hostname or 'dc' in hostname,
                
                # Attack potential
                'attack_surface_score': self._calculate_attack_surface(endpoint, ports),
                'value_score': self._calculate_value_score(endpoint, hostname, network_role),
                
                # Recommendations
                'recommended_roles': [],
                'attack_vectors': []
            }
            
            # Determine recommended roles
            analysis['recommended_roles'] = self._determine_recommended_roles(analysis)
            
            # Identify attack vectors
            analysis['attack_vectors'] = self._identify_attack_vectors(analysis, endpoint)
            
            # Cache the analysis
            self.analysis_cache[endpoint_id] = {
                'analysis': analysis,
                'timestamp': datetime.utcnow()
            }
            
            logger.info(f"Analyzed endpoint {endpoint_id}: {len(analysis['recommended_roles'])} roles, "
                       f"{len(analysis['attack_vectors'])} attack vectors")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Endpoint analysis failed: {e}")
            return {
                'endpoint_id': endpoint.get('id', 'unknown'),
                'can_be_smtp': False,
                'can_be_ftp': False,
                'can_be_web_server': False,
                'can_be_database': False,
                'is_executive': False,
                'is_admin': False,
                'attack_surface_score': 0,
                'value_score': 0,
                'recommended_roles': [],
                'attack_vectors': []
            }
    
    def _check_smtp_capability(self, endpoint: Dict, ports: List, services: str) -> bool:
        """Check if endpoint can be used as SMTP server"""
        # Check for existing SMTP
        if 'smtp' in services or 'mail' in services:
            return True
        
        # Check if port 25, 587, or 465 is available
        if any(p in ports for p in [25, 587, 465]):
            return True
        
        # Linux servers are good SMTP candidates
        platform_info = endpoint.get('platform', '').lower()
        if 'linux' in platform_info:
            return True
        
        return False
    
    def _check_ftp_capability(self, endpoint: Dict, ports: List, services: str) -> bool:
        """Check if endpoint can be used as FTP server"""
        # Check for existing FTP
        if 'ftp' in services:
            return True
        
        # Check if port 21 or 22 (SFTP) is available
        if any(p in ports for p in [21, 22]):
            return True
        
        # Servers are good FTP candidates
        platform_info = endpoint.get('platform', '').lower()
        if 'linux' in platform_info or 'server' in platform_info:
            return True
        
        return False
    
    def _check_web_capability(self, endpoint: Dict, ports: List, services: str) -> bool:
        """Check if endpoint can be used as web server"""
        # Check for existing web server
        if any(term in services for term in ['http', 'apache', 'nginx', 'iis', 'web']):
            return True
        
        # Check if port 80 or 443 is available
        if any(p in ports for p in [80, 443, 8080, 8443]):
            return True
        
        return False
    
    def _check_database_capability(self, endpoint: Dict, ports: List, services: str) -> bool:
        """Check if endpoint can be used as database server"""
        # Check for existing database
        if any(term in services for term in ['mysql', 'postgres', 'mssql', 'oracle', 'mongodb', 'database']):
            return True
        
        # Check for database ports
        if any(p in ports for p in [3306, 5432, 1433, 1521, 27017]):
            return True
        
        return False
    
    def _check_executive_user(self, endpoint: Dict, hostname: str, network_role: str) -> bool:
        """Check if this is an executive/high-value user endpoint"""
        # Check hostname for executive indicators
        executive_keywords = ['ceo', 'cfo', 'cto', 'president', 'executive', 'director', 'vp', 'chief']
        if any(keyword in hostname for keyword in executive_keywords):
            return True
        
        # Check network role
        if 'executive' in network_role or 'c-level' in network_role:
            return True
        
        return False
    
    def _check_admin_user(self, endpoint: Dict, hostname: str, network_role: str) -> bool:
        """Check if this is an admin user endpoint"""
        # Check hostname for admin indicators
        admin_keywords = ['admin', 'sysadmin', 'administrator', 'root']
        if any(keyword in hostname for keyword in admin_keywords):
            return True
        
        # Check network role
        if 'admin' in network_role:
            return True
        
        return False
    
    def _calculate_attack_surface(self, endpoint: Dict, ports: List) -> float:
        """Calculate attack surface score (0-100)"""
        score = 0
        
        # More open ports = larger attack surface
        score += min(len(ports) * 5, 30)
        
        # Privileged ports increase score
        privileged_ports = [21, 22, 23, 25, 80, 443, 445, 3389]
        score += len([p for p in ports if p in privileged_ports]) * 10
        
        # Network exposure
        security_zone = endpoint.get('security_zone', '').lower()
        if 'dmz' in security_zone or 'external' in security_zone:
            score += 20
        
        return min(score, 100)
    
    def _calculate_value_score(self, endpoint: Dict, hostname: str, network_role: str) -> float:
        """Calculate target value score (0-100)"""
        score = 0
        
        # Executive/admin endpoints are high value
        if self._check_executive_user(endpoint, hostname, network_role):
            score += 50
        if self._check_admin_user(endpoint, hostname, network_role):
            score += 40
        
        # Domain controllers are extremely valuable
        if 'domain' in hostname or 'dc' in hostname:
            score += 60
        
        # Servers are more valuable than endpoints
        if 'server' in endpoint.get('network_element_type', '').lower():
            score += 30
        
        # Database servers are high value
        if 'database' in endpoint.get('network_role', '').lower():
            score += 40
        
        return min(score, 100)
    
    def _determine_recommended_roles(self, analysis: Dict) -> List[str]:
        """Determine what roles this endpoint should play in attacks"""
        roles = []
        
        # Attack infrastructure roles
        if analysis['can_be_smtp']:
            roles.append('smtp_server')
        if analysis['can_be_ftp']:
            roles.append('ftp_server')
        if analysis['can_be_web_server']:
            roles.append('web_server')
        if analysis['can_be_database']:
            roles.append('database_server')
        
        # Target roles
        if analysis['is_executive']:
            roles.append('executive_target')
        if analysis['is_admin']:
            roles.append('admin_target')
        if analysis['is_domain_controller']:
            roles.append('domain_controller_target')
        
        # Attack roles
        if analysis['attack_surface_score'] > 50:
            roles.append('entry_point')
        if analysis['value_score'] > 60:
            roles.append('high_value_target')
        
        return roles
    
    def _identify_attack_vectors(self, analysis: Dict, endpoint: Dict) -> List[str]:
        """Identify possible attack vectors for this endpoint"""
        vectors = []
        
        # Phishing vectors
        if analysis['is_executive'] or analysis['is_admin']:
            vectors.append('spear_phishing')
            vectors.append('credential_harvesting')
        
        # Network vectors
        if analysis['attack_surface_score'] > 40:
            vectors.append('network_exploitation')
            vectors.append('service_exploitation')
        
        # Lateral movement vectors
        if analysis['is_domain_controller']:
            vectors.append('privilege_escalation')
            vectors.append('credential_dumping')
        
        # Data exfiltration vectors
        if analysis['can_be_database'] or analysis['value_score'] > 50:
            vectors.append('data_exfiltration')
        
        return vectors
    
    async def identify_executive_endpoints(self, endpoints: List[Dict]) -> List[Dict]:
        """Find endpoints with executive/high-value users"""
        executive_endpoints = []
        
        for endpoint in endpoints:
            analysis = await self.analyze_endpoint_capabilities(endpoint)
            if analysis['is_executive'] or analysis['value_score'] > 60:
                executive_endpoints.append({
                    **endpoint,
                    'analysis': analysis
                })
        
        logger.info(f"Identified {len(executive_endpoints)} executive endpoints")
        return executive_endpoints
    
    async def find_smtp_capable_endpoints(self, endpoints: List[Dict]) -> List[Dict]:
        """Find endpoints that can be SMTP servers"""
        smtp_capable = []
        
        for endpoint in endpoints:
            analysis = await self.analyze_endpoint_capabilities(endpoint)
            if analysis['can_be_smtp']:
                smtp_capable.append({
                    **endpoint,
                    'analysis': analysis
                })
        
        logger.info(f"Found {len(smtp_capable)} SMTP-capable endpoints")
        return smtp_capable
    
    async def find_ftp_capable_endpoints(self, endpoints: List[Dict]) -> List[Dict]:
        """Find endpoints that can be FTP servers"""
        ftp_capable = []
        
        for endpoint in endpoints:
            analysis = await self.analyze_endpoint_capabilities(endpoint)
            if analysis['can_be_ftp']:
                ftp_capable.append({
                    **endpoint,
                    'analysis': analysis
                })
        
        logger.info(f"Found {len(ftp_capable)} FTP-capable endpoints")
        return ftp_capable
    
    async def find_web_server_endpoints(self, endpoints: List[Dict]) -> List[Dict]:
        """Find endpoints that can be web servers"""
        web_capable = []
        
        for endpoint in endpoints:
            analysis = await self.analyze_endpoint_capabilities(endpoint)
            if analysis['can_be_web_server']:
                web_capable.append({
                    **endpoint,
                    'analysis': analysis
                })
        
        logger.info(f"Found {len(web_capable)} web server capable endpoints")
        return web_capable
    
    async def find_database_endpoints(self, endpoints: List[Dict]) -> List[Dict]:
        """Find database server endpoints"""
        database_endpoints = []
        
        for endpoint in endpoints:
            analysis = await self.analyze_endpoint_capabilities(endpoint)
            if analysis['can_be_database'] or 'database' in endpoint.get('network_role', '').lower():
                database_endpoints.append({
                    **endpoint,
                    'analysis': analysis
                })
        
        logger.info(f"Found {len(database_endpoints)} database endpoints")
        return database_endpoints
    
    async def find_attack_infrastructure_candidates(self, endpoints: List[Dict], 
                                                   resource_type: str) -> List[Dict]:
        """
        Find endpoints that can host attack infrastructure
        
        Args:
            endpoints: List of all endpoints
            resource_type: Type of infrastructure needed (smtp, ftp, web, database)
        
        Returns:
            List of suitable endpoints, sorted by suitability
        """
        candidates = []
        
        for endpoint in endpoints:
            analysis = await self.analyze_endpoint_capabilities(endpoint)
            
            # Check if endpoint can host this resource type
            capability_key = f'can_be_{resource_type}'
            if analysis.get(capability_key, False):
                candidates.append({
                    **endpoint,
                    'analysis': analysis,
                    'suitability_score': self._calculate_suitability_score(analysis, resource_type)
                })
        
        # Sort by suitability score
        candidates.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        logger.info(f"Found {len(candidates)} candidates for {resource_type}")
        return candidates
    
    def _calculate_suitability_score(self, analysis: Dict, resource_type: str) -> float:
        """Calculate how suitable an endpoint is for hosting infrastructure"""
        score = 0
        
        # Prefer servers over endpoints
        if 'server' in analysis.get('platform', '').lower():
            score += 30
        
        # Prefer Linux for most services
        if 'linux' in analysis.get('platform', '').lower():
            score += 20
        
        # Lower attack surface is better for infrastructure
        score += (100 - analysis.get('attack_surface_score', 50)) * 0.3
        
        # Don't use high-value targets for infrastructure
        if analysis.get('is_executive') or analysis.get('is_admin'):
            score -= 50
        
        return max(score, 0)
    
    async def get_network_attack_graph(self, endpoints: List[Dict]) -> Dict[str, Any]:
        """
        Generate attack graph showing possible attack paths
        
        Returns:
            {
                'nodes': List of endpoints with analysis,
                'edges': Possible attack paths between endpoints,
                'entry_points': Best entry points for attacks,
                'high_value_targets': Most valuable targets
            }
        """
        nodes = []
        edges = []
        entry_points = []
        high_value_targets = []
        
        # Analyze all endpoints
        for endpoint in endpoints:
            analysis = await self.analyze_endpoint_capabilities(endpoint)
            node = {
                **endpoint,
                'analysis': analysis
            }
            nodes.append(node)
            
            # Identify entry points
            if analysis['attack_surface_score'] > 50:
                entry_points.append(node)
            
            # Identify high-value targets
            if analysis['value_score'] > 60:
                high_value_targets.append(node)
        
        # Generate attack edges (possible paths)
        for source in nodes:
            for target in nodes:
                if source['id'] != target['id']:
                    # Check if attack path is possible
                    if self._is_attack_path_possible(source, target):
                        edges.append({
                            'source': source['id'],
                            'target': target['id'],
                            'techniques': self._get_path_techniques(source, target)
                        })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'entry_points': entry_points,
            'high_value_targets': high_value_targets,
            'graph_metrics': {
                'total_endpoints': len(nodes),
                'entry_points': len(entry_points),
                'high_value_targets': len(high_value_targets),
                'possible_paths': len(edges)
            }
        }
    
    def _is_attack_path_possible(self, source: Dict, target: Dict) -> bool:
        """Check if attack path from source to target is possible"""
        # Same security zone = easier path
        if source.get('security_zone') == target.get('security_zone'):
            return True
        
        # DMZ to internal is possible
        if source.get('security_zone') == 'dmz' and target.get('security_zone') == 'internal':
            return True
        
        return False
    
    def _get_path_techniques(self, source: Dict, target: Dict) -> List[str]:
        """Get MITRE techniques for attack path"""
        techniques = []
        
        # Initial access
        if source.get('security_zone') == 'dmz':
            techniques.append('T1190')  # Exploit Public-Facing Application
        
        # Lateral movement
        techniques.append('T1021.001')  # Remote Desktop Protocol
        techniques.append('T1021.002')  # SMB/Windows Admin Shares
        
        # Privilege escalation if targeting admin/exec
        target_analysis = target.get('analysis', {})
        if target_analysis.get('is_admin') or target_analysis.get('is_executive'):
            techniques.append('T1078')  # Valid Accounts
        
        return techniques


# Global instance
endpoint_analyzer = IntelligentEndpointAnalyzer()

