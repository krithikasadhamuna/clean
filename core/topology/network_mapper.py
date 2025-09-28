"""
Network Topology Mapper - Builds network topology from collected logs
Provides network intelligence for attack planning and threat analysis
"""

import asyncio
import logging
import sqlite3
import json
import ipaddress
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, field

from shared.models import LogEntry
from shared.utils import get_system_info


logger = logging.getLogger(__name__)


@dataclass
class NetworkNode:
    """Represents a network node (agent/endpoint)"""
    agent_id: str
    hostname: str
    ip_addresses: Set[str] = field(default_factory=set)
    mac_addresses: Set[str] = field(default_factory=set)
    platform: str = "unknown"
    os_version: str = "unknown"
    
    # Network characteristics
    subnet: Optional[str] = None
    domain: Optional[str] = None
    security_zone: str = "unknown"
    
    # Discovered services
    open_ports: Set[int] = field(default_factory=set)
    running_services: Set[str] = field(default_factory=set)
    
    # Role classification
    role: str = "endpoint"  # endpoint, server, domain_controller, firewall, etc.
    importance: str = "medium"  # low, medium, high, critical
    
    # Network connections
    outbound_connections: Set[str] = field(default_factory=set)
    inbound_connections: Set[str] = field(default_factory=set)
    
    # User context
    logged_users: Set[str] = field(default_factory=set)
    admin_users: Set[str] = field(default_factory=set)
    
    # Vulnerability indicators
    vulnerability_score: float = 0.0
    exposed_services: List[str] = field(default_factory=list)
    
    # Last seen
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'hostname': self.hostname,
            'ip_addresses': list(self.ip_addresses),
            'mac_addresses': list(self.mac_addresses),
            'platform': self.platform,
            'os_version': self.os_version,
            'subnet': self.subnet,
            'domain': self.domain,
            'security_zone': self.security_zone,
            'open_ports': list(self.open_ports),
            'running_services': list(self.running_services),
            'role': self.role,
            'importance': self.importance,
            'outbound_connections': list(self.outbound_connections),
            'inbound_connections': list(self.inbound_connections),
            'logged_users': list(self.logged_users),
            'admin_users': list(self.admin_users),
            'vulnerability_score': self.vulnerability_score,
            'exposed_services': self.exposed_services,
            'last_activity': self.last_activity.isoformat()
        }


@dataclass
class NetworkTopology:
    """Complete network topology"""
    nodes: Dict[str, NetworkNode] = field(default_factory=dict)
    subnets: Dict[str, List[str]] = field(default_factory=dict)
    domains: Dict[str, List[str]] = field(default_factory=dict)
    security_zones: Dict[str, List[str]] = field(default_factory=dict)
    
    # Network relationships
    trust_relationships: List[Tuple[str, str]] = field(default_factory=list)
    attack_paths: List[List[str]] = field(default_factory=list)
    
    # High-value targets
    domain_controllers: List[str] = field(default_factory=list)
    servers: List[str] = field(default_factory=list)
    high_value_targets: List[str] = field(default_factory=list)
    
    # Network statistics
    total_nodes: int = 0
    active_nodes: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'nodes': {k: v.to_dict() for k, v in self.nodes.items()},
            'subnets': self.subnets,
            'domains': self.domains,
            'security_zones': self.security_zones,
            'trust_relationships': self.trust_relationships,
            'attack_paths': self.attack_paths,
            'domain_controllers': self.domain_controllers,
            'servers': self.servers,
            'high_value_targets': self.high_value_targets,
            'total_nodes': self.total_nodes,
            'active_nodes': self.active_nodes,
            'last_updated': self.last_updated.isoformat()
        }


class NetworkTopologyMapper:
    """Maps network topology from log data"""
    
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.topology = NetworkTopology()
        
        # Pattern matchers for log analysis
        self.service_patterns = {
            'ssh': [r':22\b', r'ssh', r'sshd'],
            'rdp': [r':3389\b', r'rdp', r'terminal.*server'],
            'smb': [r':445\b', r':139\b', r'smb', r'cifs'],
            'http': [r':80\b', r'http(?!s)', r'apache', r'nginx'],
            'https': [r':443\b', r'https', r'ssl', r'tls'],
            'dns': [r':53\b', r'dns', r'named'],
            'dhcp': [r':67\b', r':68\b', r'dhcp'],
            'ldap': [r':389\b', r':636\b', r'ldap', r'active.*directory'],
            'kerberos': [r':88\b', r'kerberos', r'krb'],
            'winrm': [r':5985\b', r':5986\b', r'winrm'],
            'database': [r':1433\b', r':3306\b', r':5432\b', r'sql', r'mysql', r'postgres'],
            'web_server': [r'iis', r'apache', r'nginx', r'tomcat']
        }
        
        self.role_indicators = {
            'domain_controller': [
                r'domain.*controller', r'active.*directory', r'ldap', r'kerberos',
                r'group.*policy', r'sysvol', r'netlogon'
            ],
            'file_server': [
                r'file.*server', r'smb', r'cifs', r'shares', r'dfs'
            ],
            'web_server': [
                r'web.*server', r'http', r'apache', r'nginx', r'iis'
            ],
            'database_server': [
                r'database', r'sql.*server', r'mysql', r'postgres', r'oracle'
            ],
            'mail_server': [
                r'mail.*server', r'exchange', r'smtp', r'imap', r'pop3'
            ],
            'firewall': [
                r'firewall', r'pfsense', r'fortigate', r'checkpoint'
            ]
        }
    
    async def build_topology_from_logs(self, hours: int = 24) -> NetworkTopology:
        """Build network topology from recent logs"""
        logger.info(f"Building network topology from logs (last {hours} hours)")
        
        try:
            # Get recent logs
            logs = await self.db_manager.get_recent_logs(hours=hours, limit=50000)
            
            # Reset topology
            self.topology = NetworkTopology()
            
            # Process logs to extract network information
            for log_data in logs:
                await self._process_log_for_topology(log_data)
            
            # Analyze and classify nodes
            await self._analyze_network_nodes()
            
            # Discover network relationships
            await self._discover_relationships()
            
            # Calculate attack paths
            await self._calculate_attack_paths()
            
            # Update statistics
            self._update_topology_statistics()
            
            logger.info(f"Topology built: {self.topology.total_nodes} nodes, "
                       f"{len(self.topology.subnets)} subnets, "
                       f"{len(self.topology.domain_controllers)} DCs")
            
            return self.topology
            
        except Exception as e:
            logger.error(f"Failed to build network topology: {e}")
            return self.topology
    
    async def _process_log_for_topology(self, log_data: Dict) -> None:
        """Process individual log entry for topology information"""
        try:
            agent_id = log_data.get('agent_id')
            if not agent_id:
                return
            
            # Get or create network node
            if agent_id not in self.topology.nodes:
                self.topology.nodes[agent_id] = NetworkNode(
                    agent_id=agent_id,
                    hostname=log_data.get('parsed_data', {}).get('hostname', f'agent-{agent_id}')
                )
            
            node = self.topology.nodes[agent_id]
            
            # Update last activity
            if log_data.get('timestamp'):
                try:
                    node.last_activity = datetime.fromisoformat(log_data['timestamp'])
                except:
                    pass
            
            # Extract network information from different log sources
            await self._extract_system_info(node, log_data)
            await self._extract_network_connections(node, log_data)
            await self._extract_service_info(node, log_data)
            await self._extract_user_info(node, log_data)
            await self._extract_security_context(node, log_data)
            
        except Exception as e:
            logger.error(f"Failed to process log for topology: {e}")
    
    async def _extract_system_info(self, node: NetworkNode, log_data: Dict) -> None:
        """Extract system information from logs"""
        try:
            parsed_data = log_data.get('parsed_data', {})
            enriched_data = log_data.get('enriched_data', {})
            network_info = log_data.get('network_info', {})
            
            # Platform information
            if 'platform' in enriched_data:
                node.platform = enriched_data['platform']
            elif 'windows' in log_data.get('source', '').lower():
                node.platform = 'Windows'
            elif 'linux' in log_data.get('source', '').lower():
                node.platform = 'Linux'
            
            # IP addresses
            if network_info.get('source_ip'):
                node.ip_addresses.add(network_info['source_ip'])
            if network_info.get('destination_ip'):
                node.ip_addresses.add(network_info['destination_ip'])
            
            # Extract IPs from message content
            import re
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            message = log_data.get('message', '')
            for ip in re.findall(ip_pattern, message):
                if self._is_valid_ip(ip) and not ip.startswith(('127.', '0.')):
                    node.ip_addresses.add(ip)
            
            # Hostname from various sources
            for field in ['hostname', 'computer', 'computer_name']:
                if field in parsed_data:
                    node.hostname = parsed_data[field]
                    break
            
            # Domain information
            if 'domain' in parsed_data:
                node.domain = parsed_data['domain']
            
            # Determine subnet
            for ip in node.ip_addresses:
                if self._is_private_ip(ip):
                    subnet = self._get_subnet(ip)
                    if subnet:
                        node.subnet = subnet
                        break
            
        except Exception as e:
            logger.error(f"Failed to extract system info: {e}")
    
    async def _extract_network_connections(self, node: NetworkNode, log_data: Dict) -> None:
        """Extract network connection information"""
        try:
            network_info = log_data.get('network_info', {})
            message = log_data.get('message', '').lower()
            
            # Extract port information
            import re
            port_pattern = r':(\d+)\b'
            for port_match in re.finditer(port_pattern, log_data.get('raw_data', '')):
                try:
                    port = int(port_match.group(1))
                    if 1 <= port <= 65535:
                        node.open_ports.add(port)
                except ValueError:
                    continue
            
            # Network connections from parsed data
            if network_info.get('source_ip') and network_info.get('destination_ip'):
                source_ip = network_info['source_ip']
                dest_ip = network_info['destination_ip']
                
                # Determine if this is outbound or inbound
                if any(source_ip.startswith(ip) for ip in node.ip_addresses):
                    node.outbound_connections.add(dest_ip)
                else:
                    node.inbound_connections.add(source_ip)
            
            # Extract connections from log messages
            connection_patterns = [
                r'connect(?:ed|ion).*?to\s+([0-9.]+)',
                r'from\s+([0-9.]+).*?to\s+([0-9.]+)',
                r'established.*?([0-9.]+):(\d+)',
                r'listening.*?on\s+([0-9.]+):(\d+)'
            ]
            
            for pattern in connection_patterns:
                matches = re.finditer(pattern, message)
                for match in matches:
                    for group in match.groups():
                        if self._is_valid_ip(group):
                            if not self._is_private_ip(group):
                                node.outbound_connections.add(group)
            
        except Exception as e:
            logger.error(f"Failed to extract network connections: {e}")
    
    async def _extract_service_info(self, node: NetworkNode, log_data: Dict) -> None:
        """Extract running services information"""
        try:
            message = log_data.get('message', '').lower()
            raw_data = log_data.get('raw_data', '').lower()
            source = log_data.get('source', '').lower()
            
            # Check for service patterns
            for service, patterns in self.service_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, message) or re.search(pattern, raw_data):
                        node.running_services.add(service)
            
            # Extract from Windows service logs
            if 'windows' in source and log_data.get('event_type') == 'service':
                service_name = log_data.get('parsed_data', {}).get('service_name')
                if service_name:
                    node.running_services.add(service_name.lower())
            
            # Extract from Linux systemd logs
            if 'linux' in source and 'systemd' in message:
                systemd_match = re.search(r'(\w+)\.service', message)
                if systemd_match:
                    node.running_services.add(systemd_match.group(1))
            
        except Exception as e:
            logger.error(f"Failed to extract service info: {e}")
    
    async def _extract_user_info(self, node: NetworkNode, log_data: Dict) -> None:
        """Extract user and authentication information"""
        try:
            parsed_data = log_data.get('parsed_data', {})
            message = log_data.get('message', '').lower()
            
            # Extract usernames
            user_fields = ['user', 'username', 'target_user', 'logon_user']
            for field in user_fields:
                if field in parsed_data:
                    username = parsed_data[field]
                    if username and username not in ['system', 'anonymous', '$']:
                        node.logged_users.add(username)
                        
                        # Check if admin user
                        if any(admin_term in username.lower() for admin_term in 
                              ['admin', 'administrator', 'root', 'sa']):
                            node.admin_users.add(username)
            
            # Extract from authentication logs
            if 'authentication' in message or 'logon' in message:
                auth_patterns = [
                    r'user[:\s]+(\w+)',
                    r'logon[:\s]+(\w+)',
                    r'login[:\s]+(\w+)',
                    r'for\s+user\s+(\w+)'
                ]
                
                for pattern in auth_patterns:
                    match = re.search(pattern, message)
                    if match:
                        username = match.group(1)
                        if len(username) > 2:  # Avoid single chars
                            node.logged_users.add(username)
            
        except Exception as e:
            logger.error(f"Failed to extract user info: {e}")
    
    async def _extract_security_context(self, node: NetworkNode, log_data: Dict) -> None:
        """Extract security context and zone information"""
        try:
            # Determine security zone based on IP ranges
            for ip in node.ip_addresses:
                if ip.startswith('192.168.'):
                    node.security_zone = 'internal'
                elif ip.startswith('10.'):
                    node.security_zone = 'corporate'
                elif ip.startswith('172.'):
                    node.security_zone = 'dmz'
                elif not self._is_private_ip(ip):
                    node.security_zone = 'external'
            
            # Check for vulnerability indicators
            message = log_data.get('message', '').lower()
            vuln_indicators = [
                'failed', 'error', 'denied', 'blocked', 'suspicious',
                'malware', 'virus', 'trojan', 'backdoor', 'exploit'
            ]
            
            vuln_count = sum(1 for indicator in vuln_indicators if indicator in message)
            if vuln_count > 0:
                node.vulnerability_score += vuln_count * 0.1
                node.vulnerability_score = min(node.vulnerability_score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to extract security context: {e}")
    
    async def _analyze_network_nodes(self) -> None:
        """Analyze and classify network nodes"""
        try:
            for agent_id, node in self.topology.nodes.items():
                # Classify node role
                await self._classify_node_role(node)
                
                # Determine importance
                await self._assess_node_importance(node)
                
                # Group by subnets
                if node.subnet:
                    if node.subnet not in self.topology.subnets:
                        self.topology.subnets[node.subnet] = []
                    self.topology.subnets[node.subnet].append(agent_id)
                
                # Group by domains
                if node.domain:
                    if node.domain not in self.topology.domains:
                        self.topology.domains[node.domain] = []
                    self.topology.domains[node.domain].append(agent_id)
                
                # Group by security zones
                if node.security_zone not in self.topology.security_zones:
                    self.topology.security_zones[node.security_zone] = []
                self.topology.security_zones[node.security_zone].append(agent_id)
            
        except Exception as e:
            logger.error(f"Failed to analyze network nodes: {e}")
    
    async def _classify_node_role(self, node: NetworkNode) -> None:
        """Classify node role based on services and characteristics"""
        try:
            services = node.running_services
            hostname = node.hostname.lower()
            
            # Check role indicators
            for role, patterns in self.role_indicators.items():
                score = 0
                for pattern in patterns:
                    if any(re.search(pattern, service) for service in services):
                        score += 2
                    if re.search(pattern, hostname):
                        score += 1
                
                if score >= 2:
                    node.role = role
                    break
            
            # Special classifications
            if 'ldap' in services or 'kerberos' in services:
                node.role = 'domain_controller'
                self.topology.domain_controllers.append(node.agent_id)
            elif any(svc in services for svc in ['database', 'sql', 'mysql']):
                node.role = 'database_server'
                self.topology.servers.append(node.agent_id)
            elif any(svc in services for svc in ['http', 'https', 'web_server']):
                node.role = 'web_server'
                self.topology.servers.append(node.agent_id)
            
        except Exception as e:
            logger.error(f"Failed to classify node role: {e}")
    
    async def _assess_node_importance(self, node: NetworkNode) -> None:
        """Assess node importance for attack planning"""
        try:
            importance_score = 0
            
            # Role-based scoring
            role_scores = {
                'domain_controller': 10,
                'database_server': 8,
                'file_server': 6,
                'web_server': 5,
                'mail_server': 5,
                'endpoint': 1
            }
            importance_score += role_scores.get(node.role, 1)
            
            # Service-based scoring
            high_value_services = ['ldap', 'kerberos', 'database', 'smb', 'rdp']
            importance_score += len([s for s in node.running_services if s in high_value_services])
            
            # Admin user presence
            importance_score += len(node.admin_users) * 2
            
            # Network connectivity (more connections = more important)
            total_connections = len(node.outbound_connections) + len(node.inbound_connections)
            if total_connections > 50:
                importance_score += 3
            elif total_connections > 20:
                importance_score += 2
            elif total_connections > 10:
                importance_score += 1
            
            # Determine importance level
            if importance_score >= 15:
                node.importance = 'critical'
                self.topology.high_value_targets.append(node.agent_id)
            elif importance_score >= 10:
                node.importance = 'high'
                self.topology.high_value_targets.append(node.agent_id)
            elif importance_score >= 5:
                node.importance = 'medium'
            else:
                node.importance = 'low'
            
        except Exception as e:
            logger.error(f"Failed to assess node importance: {e}")
    
    async def _discover_relationships(self) -> None:
        """Discover trust relationships and network paths"""
        try:
            # Analyze domain relationships
            for domain, nodes in self.topology.domains.items():
                # Nodes in same domain have trust relationships
                for i, node1 in enumerate(nodes):
                    for node2 in nodes[i+1:]:
                        self.topology.trust_relationships.append((node1, node2))
            
            # Analyze network connectivity patterns
            for agent_id, node in self.topology.nodes.items():
                # Find nodes that this node connects to
                for target_ip in node.outbound_connections:
                    target_node = self._find_node_by_ip(target_ip)
                    if target_node and target_node != agent_id:
                        self.topology.trust_relationships.append((agent_id, target_node))
            
        except Exception as e:
            logger.error(f"Failed to discover relationships: {e}")
    
    async def _calculate_attack_paths(self) -> None:
        """Calculate potential attack paths through the network"""
        try:
            # Simple attack path calculation
            # From external -> DMZ -> internal -> domain controllers
            
            external_nodes = self.topology.security_zones.get('external', [])
            dmz_nodes = self.topology.security_zones.get('dmz', [])
            internal_nodes = self.topology.security_zones.get('internal', [])
            domain_controllers = self.topology.domain_controllers
            
            # Generate attack paths
            for ext_node in external_nodes[:3]:  # Limit to avoid explosion
                for dmz_node in dmz_nodes[:3]:
                    for int_node in internal_nodes[:3]:
                        for dc_node in domain_controllers[:2]:
                            path = [ext_node, dmz_node, int_node, dc_node]
                            self.topology.attack_paths.append(path)
            
            # Also create direct paths to high-value targets
            for hvt in self.topology.high_value_targets[:5]:
                # Simple path: any endpoint -> HVT
                endpoints = [n for n, node in self.topology.nodes.items() 
                           if node.role == 'endpoint'][:3]
                for endpoint in endpoints:
                    if endpoint != hvt:
                        self.topology.attack_paths.append([endpoint, hvt])
            
        except Exception as e:
            logger.error(f"Failed to calculate attack paths: {e}")
    
    def _update_topology_statistics(self) -> None:
        """Update topology statistics"""
        self.topology.total_nodes = len(self.topology.nodes)
        
        # Count active nodes (activity in last hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self.topology.active_nodes = sum(
            1 for node in self.topology.nodes.values()
            if node.last_activity > cutoff_time
        )
        
        self.topology.last_updated = datetime.utcnow()
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if string is valid IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is private/internal"""
        try:
            return ipaddress.ip_address(ip).is_private
        except ValueError:
            return False
    
    def _get_subnet(self, ip: str) -> Optional[str]:
        """Get subnet for IP address"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                # Return /24 subnet
                octets = ip.split('.')
                return f"{octets[0]}.{octets[1]}.{octets[2]}.0/24"
        except ValueError:
            pass
        return None
    
    def _find_node_by_ip(self, ip: str) -> Optional[str]:
        """Find node by IP address"""
        for agent_id, node in self.topology.nodes.items():
            if ip in node.ip_addresses:
                return agent_id
        return None
    
    async def get_attack_context_for_agent(self, agent_id: str) -> Dict:
        """Get attack context for specific agent (for attack agent use)"""
        try:
            if agent_id not in self.topology.nodes:
                return {'error': 'Agent not found in topology'}
            
            node = self.topology.nodes[agent_id]
            
            # Find potential targets
            same_subnet_targets = []
            if node.subnet and node.subnet in self.topology.subnets:
                same_subnet_targets = [
                    aid for aid in self.topology.subnets[node.subnet] 
                    if aid != agent_id
                ]
            
            # Find high-value targets in reach
            reachable_hvts = []
            for hvt_id in self.topology.high_value_targets:
                hvt_node = self.topology.nodes.get(hvt_id)
                if hvt_node and (hvt_node.subnet == node.subnet or 
                               hvt_id in node.outbound_connections):
                    reachable_hvts.append(hvt_id)
            
            return {
                'agent_context': node.to_dict(),
                'same_subnet_targets': same_subnet_targets,
                'reachable_high_value_targets': reachable_hvts,
                'domain_controllers': self.topology.domain_controllers,
                'attack_paths': [
                    path for path in self.topology.attack_paths 
                    if agent_id in path
                ],
                'trust_relationships': [
                    rel for rel in self.topology.trust_relationships 
                    if agent_id in rel
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get attack context: {e}")
            return {'error': str(e)}
    
    async def export_topology_for_attack_planning(self) -> Dict:
        """Export topology in format suitable for attack planning"""
        try:
            return {
                'network_topology': self.topology.to_dict(),
                'attack_intelligence': {
                    'high_value_targets': [
                        {
                            'agent_id': hvt_id,
                            'details': self.topology.nodes[hvt_id].to_dict()
                        }
                        for hvt_id in self.topology.high_value_targets
                        if hvt_id in self.topology.nodes
                    ],
                    'domain_controllers': [
                        {
                            'agent_id': dc_id,
                            'details': self.topology.nodes[dc_id].to_dict()
                        }
                        for dc_id in self.topology.domain_controllers
                        if dc_id in self.topology.nodes
                    ],
                    'attack_paths': self.topology.attack_paths,
                    'vulnerable_services': [
                        {
                            'agent_id': agent_id,
                            'services': list(node.running_services),
                            'vulnerability_score': node.vulnerability_score
                        }
                        for agent_id, node in self.topology.nodes.items()
                        if node.vulnerability_score > 0.3
                    ]
                },
                'network_statistics': {
                    'total_nodes': self.topology.total_nodes,
                    'active_nodes': self.topology.active_nodes,
                    'subnets_count': len(self.topology.subnets),
                    'domains_count': len(self.topology.domains),
                    'high_value_targets_count': len(self.topology.high_value_targets),
                    'last_updated': self.topology.last_updated.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to export topology: {e}")
            return {'error': str(e)}
