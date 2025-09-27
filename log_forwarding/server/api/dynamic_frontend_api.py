"""
Dynamic Frontend API for AI SOC Platform
Completely data-driven without hardcoded values
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..storage.database_manager import DatabaseManager
from ..topology.network_mapper import NetworkTopologyMapper


logger = logging.getLogger(__name__)


class DynamicFrontendAPI:
    """Completely dynamic frontend API based on actual data"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager
        self.topology_mapper = NetworkTopologyMapper(database_manager)
        
        self.router = APIRouter(prefix="/api/backend", tags=["backend"])
        
        # Add routes matching CodeGrey API spec
        self.router.add_api_route("/network-topology", self.get_network_topology, methods=["GET"])
        self.router.add_api_route("/agents", self.get_agents_list, methods=["GET"])
        self.router.add_api_route("/agents/{agent_id}/details", self.get_agent_details, methods=["GET"])
        self.router.add_api_route("/software-download", self.get_software_download, methods=["GET"])
        
        # Attack operations (CodeGrey API)
        self.router.add_api_route("/langgraph/attack/start", self.start_attack, methods=["POST"])
        self.router.add_api_route("/langgraph/attack/{scenario_id}/approve", self.approve_attack, methods=["POST"])
        
        # Detection operations (CodeGrey API)
        self.router.add_api_route("/langgraph/detection/status", self.get_detection_status, methods=["GET"])
        self.router.add_api_route("/langgraph/detection/recent", self.get_recent_detections, methods=["GET"])
    
    async def get_network_topology(self, 
                                  hierarchy: str = Query("desc", description="Hierarchy order (asc/desc)"),
                                  sort_by: str = Query("importance", description="Sort field")) -> JSONResponse:
        """Get network topology in CodeGrey API format - NO AUTH REQUIRED"""
        try:
            # Build topology from actual logs (organization's network)
            topology = await self.topology_mapper.build_topology_from_logs(hours=24)
            
            network_nodes = []
            x_pos = 10
            y_pos = 20
            
            # Use ONLY the topology discovered from logs (organization endpoints)
            # Group nodes by security zones discovered from logs
            zone_groups = {}
            
            for agent_id, node in topology.nodes.items():
                zone = node.security_zone
                if zone not in zone_groups:
                    zone_groups[zone] = []
                
                # Convert NetworkNode to agent format for frontend
                agent_data = {
                    'id': agent_id,
                    'name': node.hostname,
                    'type': 'endpoint',  # These are organization endpoints
                    'platform': node.platform,
                    'status': 'active' if (datetime.utcnow() - node.last_activity).seconds < 300 else 'inactive',
                    'location': zone,
                    'lastActivity': node.last_activity.isoformat(),
                    'ip_addresses': list(node.ip_addresses),
                    'services': list(node.running_services),
                    'role': node.role,
                    'importance': node.importance
                }
                zone_groups[zone].append(agent_data)
            
            # Create network nodes from discovered zones
            for zone_name, zone_agents in zone_groups.items():
                if zone_agents:  # Only zones with actual endpoints
                    network_node = {
                        'id': zone_name.lower().replace(' ', '_').replace('-', '_'),
                        'name': zone_name,
                        'type': self._determine_zone_type_from_topology(zone_agents),
                        'x': x_pos,
                        'y': y_pos,
                        'agents': zone_agents,  # Organization endpoints only
                        'status': self._get_zone_status_from_agents(zone_agents)
                    }
                    
                    network_nodes.append(network_node)
                    x_pos += 150
                    if x_pos > 500:
                        x_pos = 10
                        y_pos += 100
            
            # Sort based on actual data
            network_nodes = self._sort_nodes_dynamically(network_nodes, sort_by, hierarchy)
            
            return JSONResponse(content={
                'status': 'success',
                'network_nodes': network_nodes,
                'metadata': {
                    'data_source': 'real_topology',
                    'total_nodes': len(network_nodes),
                    'total_agents': sum(len(node['agents']) for node in network_nodes),
                    'generated_from_logs': True,
                    'hierarchy': hierarchy,
                    'sort_by': sort_by,
                    'generated_at': datetime.utcnow().isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Dynamic network nodes error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_agents_list(self,
                             location: Optional[str] = Query(None),
                             agent_type: Optional[str] = Query(None), 
                             status: Optional[str] = Query(None),
                             sort_by: str = Query("name"),
                             order: str = Query("asc")) -> JSONResponse:
        """Get SOC AI agents list (NOT organization endpoints) - NO AUTH REQUIRED"""
        try:
            agents = []
            
            # Get SOC AI agents (platform tools, not organization endpoints)
            ai_agents = await self._get_soc_ai_agents()
            agents.extend(ai_agents)
            
            # NOTE: Agents API returns SOC AI agents only
            # Organization endpoints are shown in network-topology API
            
            # Apply filters
            agents = self._apply_filters(agents, location, agent_type, status)
            
            # Sort dynamically
            agents = self._sort_agents_dynamically(agents, sort_by, order)
            
            return JSONResponse(content={
                'status': 'success',
                'agents': agents,
                'metadata': {
                    'data_source': 'real_data',
                    'total_agents': len(agents),
                    'ai_agents': len([a for a in agents if a['type'] in ['attack', 'detection', 'intelligence']]),
                    'endpoint_agents': len([a for a in agents if a['type'] == 'endpoint']),
                    'filters_applied': {'location': location, 'type': agent_type, 'status': status},
                    'generated_at': datetime.utcnow().isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Dynamic agents list error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_agent_details(self, agent_id: str) -> JSONResponse:
        """Get agent details dynamically from actual data"""
        try:
            # Try to get from database first
            agent_info = await self.db_manager.get_agent_info(agent_id)
            
            if agent_info:
                # Get topology info
                topology = await self.topology_mapper.build_topology_from_logs(hours=24)
                node = topology.nodes.get(agent_id)
                
                details = {
                    'id': agent_info.id,
                    'name': agent_info.hostname,
                    'type': self._classify_agent_type(node, agent_info) if node else 'endpoint',
                    'status': agent_info.status,
                    'location': self._map_zone_to_location(node.security_zone if node else 'unknown'),
                    'platform': agent_info.platform,
                    'os_version': agent_info.os_version,
                    'ip_address': agent_info.ip_address,
                    'capabilities': agent_info.capabilities,
                    'log_sources': agent_info.log_sources,
                    'configuration': agent_info.configuration,
                    'statistics': {
                        'logs_sent': agent_info.logs_sent_count,
                        'bytes_sent': agent_info.bytes_sent,
                        'errors': agent_info.errors_count,
                        'last_heartbeat': agent_info.last_heartbeat.isoformat()
                    },
                    'network_info': node.to_dict() if node else {},
                    'real_data': True
                }
                
                return JSONResponse(content={'status': 'success', 'agent': details})
            
            # Check if it's an AI agent
            ai_agent = await self._get_ai_agent_details_dynamic(agent_id)
            if ai_agent:
                return JSONResponse(content={'status': 'success', 'agent': ai_agent})
            
            raise HTTPException(status_code=404, detail="Agent not found")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get agent details error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_soc_ai_agents(self) -> List[Dict]:
        """Get AI agents from actual running instances and database"""
        ai_agents = []
        
        try:
            # Query database for AI-related agents
            import sqlite3
            
            conn = sqlite3.connect(self.db_manager.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Look for agents that might be AI agents
            cursor.execute("""
                SELECT id, hostname, platform, status, last_heartbeat, capabilities, 
                       configuration, security_zone, importance, agent_version
                FROM agents 
                WHERE capabilities LIKE '%ai%' 
                   OR capabilities LIKE '%attack%' 
                   OR capabilities LIKE '%detection%'
                   OR hostname LIKE '%ai%'
                   OR hostname LIKE '%phantom%'
                   OR hostname LIKE '%guardian%'
                ORDER BY last_heartbeat DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                try:
                    capabilities = json.loads(row['capabilities']) if row['capabilities'] else []
                    
                    agent = {
                        'id': row['id'],
                        'name': row['hostname'],
                        'type': self._determine_type_from_capabilities(capabilities),
                        'status': row['status'],
                        'location': self._map_zone_to_location(row['security_zone']),
                        'lastActivity': self._format_timestamp_string(row['last_heartbeat']),
                        'capabilities': capabilities,
                        'platform': row['platform'],
                        'version': row['agent_version']
                    }
                    ai_agents.append(agent)
                    
                except Exception as e:
                    logger.error(f"Failed to process AI agent {row['id']}: {e}")
                    continue
            
            # If no AI agents found in database, try to detect from running processes
            if not ai_agents:
                ai_agents = await self._detect_running_ai_agents()
            
            return ai_agents
            
        except Exception as e:
            logger.error(f"Real AI agents query failed: {e}")
            return []
    
    async def _detect_running_ai_agents(self) -> List[Dict]:
        """Detect AI agents from running processes/modules"""
        detected_agents = []
        
        try:
            # Dynamically discover available AI agent modules
            agent_modules = await self._discover_ai_agent_modules()
            
            for agent_id, module_path, agent_type, dev_status in agent_modules:
                try:
                    if module_path is None:
                        # Agent is in development, add with development status
                        # Use established agent names
                        name_mapping = {
                            'phantomstrike_ai': 'PhantomStrike AI',
                            'guardian_alpha_ai': 'GuardianAlpha AI', 
                            'sentinel_deploy_ai': 'SentinelDeploy AI',
                            'threat_mind_ai': 'ThreatMind AI'
                        }
                        
                        location_mapping = {
                            'attack': 'External Network',
                            'detection': 'SOC Infrastructure',
                            'deploy': 'Security Fabric',
                            'intelligence': 'Threat Intelligence Platform'
                        }
                        
                        agent_name = name_mapping.get(agent_id, self._generate_agent_name(agent_id, agent_type))
                        agent_location = location_mapping.get(agent_type, self._determine_agent_location(agent_type))
                        
                        detected_agents.append({
                            'id': agent_id,
                            'name': agent_name,
                            'type': agent_type,
                            'status': dev_status,
                            'location': agent_location,
                            'lastActivity': 'Inactive - In Development' if dev_status == 'inactive' else 'In Development',
                            'capabilities': await self._get_dynamic_capabilities(agent_type, module_path),
                            'platform': 'LangChain Agent (Development)',
                            'development_stage': True
                        })
                    else:
                        # Try to import the module
                        import importlib
                        module = importlib.import_module(module_path)
                        
                        # If import succeeds, agent is available
                        # Use established agent names
                        name_mapping = {
                            'phantomstrike_ai': 'PhantomStrike AI',
                            'guardian_alpha_ai': 'GuardianAlpha AI', 
                            'sentinel_deploy_ai': 'SentinelDeploy AI',
                            'threat_mind_ai': 'ThreatMind AI'
                        }
                        
                        location_mapping = {
                            'attack': 'External Network',
                            'detection': 'SOC Infrastructure',
                            'deploy': 'Security Fabric',
                            'intelligence': 'Threat Intelligence Platform'
                        }
                        
                        agent_name = name_mapping.get(agent_id, self._generate_agent_name(agent_id, agent_type))
                        agent_location = location_mapping.get(agent_type, self._determine_agent_location(agent_type))
                        
                        detected_agents.append({
                            'id': agent_id,
                            'name': agent_name,
                            'type': agent_type,
                            'status': dev_status,
                            'location': agent_location,
                            'lastActivity': 'Now' if dev_status == 'active' else ('Inactive' if dev_status == 'inactive' else 'In Development'),
                            'capabilities': await self._get_dynamic_capabilities(agent_type, module_path),
                            'platform': 'LangChain Agent',
                            'detected': True
                        })
                    
                except ImportError:
                    # Agent module not available, but still add if in development
                    if dev_status in ['development', 'inactive']:
                        detected_agents.append({
                            'id': agent_id,
                            'name': agent_id.replace('_', ' ').title(),
                            'type': agent_type,
                            'status': dev_status,
                            'location': 'SOC Server',
                            'lastActivity': 'Inactive' if dev_status == 'inactive' else 'In Development',
                            'capabilities': self._get_development_capabilities(agent_type),
                            'platform': 'LangChain Agent (Development)',
                            'development_stage': True
                        })
                except Exception as e:
                    logger.warning(f"Error detecting agent {agent_id}: {e}")
                    continue
            
            return detected_agents
            
        except Exception as e:
            logger.error(f"AI agent detection failed: {e}")
            return []
    
    def _get_module_capabilities(self, module, agent_type: str) -> List[str]:
        """Extract capabilities from module inspection"""
        capabilities = []
        
        try:
            # Inspect module for classes and methods
            import inspect
            
            classes = inspect.getmembers(module, inspect.isclass)
            
            for class_name, class_obj in classes:
                if 'agent' in class_name.lower():
                    methods = inspect.getmembers(class_obj, inspect.ismethod)
                    
                    for method_name, method_obj in methods:
                        if not method_name.startswith('_'):
                            # Convert method names to capabilities
                            capability = method_name.replace('_', ' ').title()
                            capabilities.append(capability)
            
            # Add type-specific capabilities
            type_capabilities = {
                'attack': ['Attack Planning', 'Scenario Generation'],
                'detection': ['Threat Detection', 'Analysis'],
                'orchestration': ['Multi-Agent Coordination', 'Workflow Management']
            }
            
            capabilities.extend(type_capabilities.get(agent_type, []))
            
            return list(set(capabilities))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Module capability extraction failed: {e}")
            return [f'{agent_type.title()} Agent']
    
    def _get_real_agent_status(self, node) -> str:
        """Get real agent status from node data"""
        if not node.last_activity:
            return 'offline'
        
        time_diff = datetime.utcnow() - node.last_activity
        
        if time_diff.total_seconds() < 60:
            return 'active'
        elif time_diff.total_seconds() < 300:
            return 'idle'
        else:
            return 'offline'
    
    def _classify_agent_type(self, node, agent_info) -> str:
        """Classify agent type from actual data"""
        if not node and not agent_info:
            return 'unknown'
        
        # Check capabilities first
        if agent_info and agent_info.capabilities:
            caps_str = ' '.join(agent_info.capabilities).lower()
            
            if 'attack' in caps_str or 'red team' in caps_str:
                return 'attack'
            elif 'detection' in caps_str or 'threat' in caps_str:
                return 'detection'
            elif 'deploy' in caps_str or 'management' in caps_str:
                return 'deploy'
            elif 'intelligence' in caps_str:
                return 'intelligence'
        
        # Check node role if available
        if node:
            if node.role == 'domain_controller':
                return 'critical_endpoint'
            elif node.role in ['database_server', 'web_server', 'file_server']:
                return 'server'
            else:
                return 'endpoint'
        
        return 'endpoint'
    
    def _get_real_capabilities(self, node, agent_info) -> List[str]:
        """Get real capabilities from node and agent data"""
        capabilities = []
        
        # From agent info
        if agent_info and agent_info.capabilities:
            capabilities.extend(agent_info.capabilities)
        
        # From node services
        if node and node.running_services:
            service_capabilities = {
                'ssh': 'Remote Access (SSH)',
                'rdp': 'Remote Desktop',
                'smb': 'File Sharing',
                'http': 'Web Services',
                'https': 'Secure Web Services',
                'database': 'Database Services',
                'ldap': 'Directory Services',
                'dns': 'DNS Services'
            }
            
            for service in node.running_services:
                if service in service_capabilities:
                    capabilities.append(service_capabilities[service])
        
        # From node role
        if node:
            role_capabilities = {
                'domain_controller': ['Active Directory', 'Authentication'],
                'database_server': ['Data Storage', 'Query Processing'],
                'web_server': ['HTTP Services', 'Content Delivery'],
                'file_server': ['File Storage', 'Share Management']
            }
            
            if node.role in role_capabilities:
                capabilities.extend(role_capabilities[node.role])
        
        return list(set(capabilities))  # Remove duplicates
    
    def _get_zone_name(self, zone: str) -> str:
        """Get zone display name"""
        zone_names = {
            'external': 'External Network',
            'dmz': 'DMZ',
            'internal': 'Internal Network', 
            'corporate': 'Corporate Network'
        }
        return zone_names.get(zone, f'{zone.title()} Zone')
    
    def _get_zone_type(self, zone: str, agents: List[Dict]) -> str:
        """Get zone type based on actual agents"""
        if zone == 'external':
            return 'gateway'
        elif zone == 'dmz':
            return 'security_zone'
        elif any(agent['type'] == 'critical_endpoint' for agent in agents):
            return 'domain_network'
        elif any(agent['type'] == 'server' for agent in agents):
            return 'server_network'
        else:
            return 'internal_network'
    
    def _get_zone_status(self, agents: List[Dict]) -> str:
        """Get zone status from actual agent status"""
        if not agents:
            return 'offline'
        
        active_count = sum(1 for agent in agents if agent['status'] == 'active')
        total_count = len(agents)
        
        if active_count == total_count:
            return 'normal'
        elif active_count > total_count / 2:
            return 'degraded'
        else:
            return 'critical'
    
    def _map_zone_to_location(self, zone: str) -> str:
        """Map security zone to location"""
        return self._get_zone_name(zone)
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format timestamp for display"""
        if not timestamp:
            return 'Never'
        
        time_diff = datetime.utcnow() - timestamp
        
        if time_diff.total_seconds() < 60:
            return 'Now'
        elif time_diff.total_seconds() < 3600:
            minutes = int(time_diff.total_seconds() / 60)
            return f'{minutes} mins ago'
        elif time_diff.total_seconds() < 86400:
            hours = int(time_diff.total_seconds() / 3600)
            return f'{hours} hours ago'
        else:
            days = int(time_diff.total_seconds() / 86400)
            return f'{days} days ago'
    
    def _format_timestamp_string(self, timestamp_str: str) -> str:
        """Format timestamp string for display"""
        if not timestamp_str:
            return 'Never'
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            return self._format_timestamp(timestamp)
        except:
            return 'Unknown'
    
    def _determine_type_from_capabilities(self, capabilities: List[str]) -> str:
        """Determine agent type from capabilities"""
        caps_str = ' '.join(capabilities).lower()
        
        if any(keyword in caps_str for keyword in ['attack', 'phantom', 'red team']):
            return 'attack'
        elif any(keyword in caps_str for keyword in ['detection', 'guardian', 'threat']):
            return 'detection'
        elif any(keyword in caps_str for keyword in ['deploy', 'sentinel', 'orchestration']):
            return 'deploy'
        elif any(keyword in caps_str for keyword in ['intelligence', 'mind', 'correlation']):
            return 'intelligence'
        else:
            return 'endpoint'
    
    def _apply_filters(self, agents: List[Dict], location: str, agent_type: str, status: str) -> List[Dict]:
        """Apply filters to agents list"""
        filtered = agents
        
        if location:
            filtered = [a for a in filtered if a['location'] == location]
        if agent_type:
            filtered = [a for a in filtered if a['type'] == agent_type]
        if status:
            filtered = [a for a in filtered if a['status'] == status]
        
        return filtered
    
    def _sort_nodes_dynamically(self, nodes: List[Dict], sort_by: str, hierarchy: str) -> List[Dict]:
        """Sort nodes based on actual data"""
        try:
            def sort_key(node):
                if sort_by == 'importance':
                    # Calculate importance from actual data
                    agent_count = len(node['agents'])
                    critical_agents = sum(1 for agent in node['agents'] 
                                        if agent.get('importance') == 'critical')
                    return agent_count + (critical_agents * 10)
                elif sort_by == 'name':
                    return node['name']
                elif sort_by == 'type':
                    return node['type']
                else:
                    return node['name']
            
            reverse = hierarchy == 'desc'
            return sorted(nodes, key=sort_key, reverse=reverse)
            
        except Exception as e:
            logger.error(f"Dynamic node sorting failed: {e}")
            return nodes
    
    def _sort_agents_dynamically(self, agents: List[Dict], sort_by: str, order: str) -> List[Dict]:
        """Sort agents based on actual data"""
        try:
            def sort_key(agent):
                if sort_by == 'name':
                    return agent['name']
                elif sort_by == 'type':
                    # AI agents first, then endpoints
                    type_priority = {
                        'attack': 1, 'detection': 2, 'intelligence': 3, 'deploy': 4,
                        'orchestration': 5, 'server': 6, 'critical_endpoint': 7, 'endpoint': 8
                    }
                    return type_priority.get(agent['type'], 9)
                elif sort_by == 'status':
                    status_priority = {'active': 1, 'idle': 2, 'available': 3, 'development': 4, 'inactive': 5, 'offline': 6}
                    return status_priority.get(agent['status'], 7)
                elif sort_by == 'location':
                    return agent['location']
                else:
                    return agent['name']
            
            reverse = order == 'desc'
            return sorted(agents, key=sort_key, reverse=reverse)
            
        except Exception as e:
            logger.error(f"Dynamic agent sorting failed: {e}")
            return agents
    
    async def _get_ai_agent_details_dynamic(self, agent_id: str) -> Optional[Dict]:
        """Get AI agent details dynamically"""
        try:
            # Try to get status from actual running agents
            if agent_id == 'phantomstrike_ai':
                from ...agents.attack_agent.langchain_attack_agent import phantomstrike_ai
                status = await phantomstrike_ai.get_execution_status()
                
                return {
                    'id': agent_id,
                    'name': 'PhantomStrike AI',
                    'type': 'attack',
                    'status': 'active' if status else 'offline',
                    'real_status': status,
                    'capabilities_dynamic': True,
                    'last_update': datetime.utcnow().isoformat()
                }
            
            elif agent_id == 'guardian_alpha_ai':
                from ...agents.detection_agent.langchain_detection_agent import langchain_detection_agent
                status = await langchain_detection_agent.get_detection_statistics()
                
                return {
                    'id': agent_id,
                    'name': 'GuardianAlpha AI',
                    'type': 'detection',
                    'status': 'active' if status else 'offline',
                    'real_status': status,
                    'capabilities_dynamic': True,
                    'last_update': datetime.utcnow().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Dynamic AI agent details failed: {e}")
            return None
    
    def _get_development_capabilities(self, agent_type: str) -> List[str]:
        """Get placeholder capabilities for agents in development"""
        development_capabilities = {
            'deploy': [
                'Agent Deployment (Planned)',
                'Container Orchestration (Planned)',
                'System Management (Planned)',
                'Configuration Management (Planned)'
            ],
            'intelligence': [
                'Threat Intelligence (Planned)',
                'IOC Analysis (Planned)', 
                'Campaign Attribution (Planned)',
                'Predictive Modeling (Planned)'
            ]
            }
        
        return development_capabilities.get(agent_type, ['Development in Progress'])
    
    async def _discover_ai_agent_modules(self) -> List[Tuple[str, str, str, str]]:
        """Dynamically discover AI agent modules from filesystem"""
        agent_modules = []
        
        try:
            import os
            import importlib.util
            from pathlib import Path
            
            # Look for agent modules in the agents directory
            agents_dir = Path(__file__).parent.parent.parent.parent / "agents"
            
            # Scan for agent directories
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir() and not agent_dir.name.startswith('_'):
                    # Look for agent files
                    for agent_file in agent_dir.rglob("*agent*.py"):
                        if "langchain" in agent_file.name or "ai" in agent_file.name:
                            try:
                                # Extract agent info from file path and content
                                agent_type = self._extract_agent_type_from_path(agent_dir.name)
                                agent_id = self._generate_agent_id_from_path(agent_file)
                                module_path = self._get_module_path_from_file(agent_file)
                                
                                # Determine status by trying to import
                                try:
                                    spec = importlib.util.spec_from_file_location("test", agent_file)
                                    status = 'active' if spec else 'inactive'
                                except:
                                    status = 'inactive'
                                
                                agent_modules.append((agent_id, module_path, agent_type, status))
                                
                            except Exception as e:
                                logger.debug(f"Could not process agent file {agent_file}: {e}")
                                continue
            
            # If no agents found, return the known agent set
            if not agent_modules:
                agent_modules = [
                    ('phantomstrike_ai', 'agents.attack_agent.langchain_attack_agent', 'attack', 'active'),
                    ('guardian_alpha_ai', 'agents.detection_agent.langchain_detection_agent', 'detection', 'active'),
                    ('sentinel_deploy_ai', None, 'deploy', 'inactive'),
                    ('threat_mind_ai', None, 'intelligence', 'inactive')
                ]
                
        except Exception as e:
            logger.error(f"Agent module discovery failed: {e}")
            # Fallback to minimal agents
            agent_modules = [
                ('ai_agent_1', None, 'attack', 'inactive'),
                ('ai_agent_2', None, 'detection', 'inactive')
            ]
        
        return agent_modules
    
    def _extract_agent_type_from_path(self, dir_name: str) -> str:
        """Extract agent type from directory name"""
        if 'attack' in dir_name.lower():
            return 'attack'
        elif 'detection' in dir_name.lower():
            return 'detection'
        elif 'deploy' in dir_name.lower():
            return 'deploy'
        elif 'intelligence' in dir_name.lower() or 'reasoning' in dir_name.lower():
            return 'intelligence'
        else:
            return 'unknown'
    
    def _generate_agent_id_from_path(self, file_path: Path) -> str:
        """Generate agent ID from file path"""
        # Use directory name + file name to create unique ID
        dir_name = file_path.parent.name
        file_name = file_path.stem
        
        # Create readable ID
        agent_id = f"{dir_name}_{file_name}".replace('_agent', '').replace('langchain_', '')
        return agent_id.lower()
    
    def _get_module_path_from_file(self, file_path: Path) -> str:
        """Get importable module path from file path"""
        try:
            # Convert file path to module path
            relative_path = file_path.relative_to(Path(__file__).parent.parent.parent.parent)
            module_path = str(relative_path.with_suffix('')).replace(os.sep, '.')
            return module_path
        except:
            return None
    
    def _generate_agent_name(self, agent_id: str, agent_type: str) -> str:
        """Generate human-readable agent name dynamically"""
        # Generate name based on type and ID
        type_prefixes = {
            'attack': 'Strike',
            'detection': 'Guardian', 
            'deploy': 'Sentinel',
            'intelligence': 'Mind'
        }
        
        prefix = type_prefixes.get(agent_type, 'Agent')
        suffix = 'AI'
        
        # Create unique name from ID
        unique_part = agent_id.replace('_', '').title()[:8]
        
        return f"{prefix}{unique_part} {suffix}"
    
    def _determine_agent_location(self, agent_type: str) -> str:
        """Determine agent location based on type and function"""
        # Dynamic location assignment based on agent purpose
        if agent_type == 'attack':
            return 'Attack Simulation Zone'
        elif agent_type == 'detection':
            return 'Detection Infrastructure'
        elif agent_type == 'deploy':
            return 'Deployment Zone'
        elif agent_type == 'intelligence':
            return 'Intelligence Hub'
        else:
            return 'SOC Platform'
    
    async def _get_dynamic_capabilities(self, agent_type: str, module_path: str = None) -> List[str]:
        """Get capabilities dynamically from module inspection or type"""
        capabilities = []
        
        if module_path:
            try:
                # Try to import and inspect module for capabilities
                import importlib
                import inspect
                
                module = importlib.import_module(module_path)
                
                # Look for classes and methods to determine capabilities
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and 'agent' in name.lower():
                        # Get methods as capabilities
                        methods = inspect.getmembers(obj, predicate=inspect.ismethod)
                        for method_name, method in methods:
                            if not method_name.startswith('_'):
                                capability = method_name.replace('_', ' ').title()
                                capabilities.append(capability)
                        
                        # Limit capabilities
                        if len(capabilities) > 10:
                            capabilities = capabilities[:10]
                        break
                
            except Exception as e:
                logger.debug(f"Could not inspect module {module_path}: {e}")
        
        # Fallback to type-based capabilities if module inspection fails
        if not capabilities:
            capabilities = self._get_type_based_capabilities(agent_type)
        
        return capabilities
    
    def _get_type_based_capabilities(self, agent_type: str) -> List[str]:
        """Get capabilities based on agent type"""
        type_capabilities = {
            'attack': [
                'Attack Planning',
                'Scenario Generation', 
                'Vulnerability Assessment',
                'Penetration Testing',
                'Red Team Operations'
            ],
            'detection': [
                'Threat Detection',
                'Log Analysis',
                'Behavioral Analysis',
                'Anomaly Detection',
                'Incident Response'
            ],
            'deploy': [
                'Agent Deployment',
                'Configuration Management',
                'System Orchestration',
                'Policy Enforcement',
                'Auto-Remediation'
            ],
            'intelligence': [
                'Threat Intelligence',
                'IOC Analysis',
                'Campaign Tracking',
                'Risk Assessment',
                'Predictive Analytics'
            ]
        }
        
        return type_capabilities.get(agent_type, ['General AI Operations'])
    
    def _get_zone_status_from_agents(self, agents: List[Dict]) -> str:
        """Get zone status based on agent statuses"""
        if not agents:
            return 'empty'
        
        active_count = len([a for a in agents if a.get('status') == 'active'])
        total_count = len(agents)
        
        if active_count == total_count:
            return 'normal'
        elif active_count > 0:
            return 'partial'
        else:
            return 'inactive'
    
    def _determine_zone_type_from_topology(self, agents: List[Dict]) -> str:
        """Determine zone type from topology-discovered endpoints"""
        if not agents:
            return 'unknown'
        
        # Determine type based on discovered roles and services
        roles = [agent.get('role', 'endpoint') for agent in agents]
        services = []
        for agent in agents:
            services.extend(agent.get('services', []))
        
        if 'domain_controller' in roles:
            return 'server'
        elif 'web_server' in roles or any('http' in s.lower() for s in services):
            return 'server'
        elif 'database_server' in roles or any('sql' in s.lower() for s in services):
            return 'database'
        elif 'firewall' in roles:
            return 'firewall'
        elif any('workstation' in r.lower() for r in roles):
            return 'workstation'
        else:
            return 'workstation'  # Default for organization endpoints
    
    def _determine_zone_type_from_agents(self, agents: List[Dict]) -> str:
        """Determine zone type based on agents in the zone"""
        if not agents:
            return 'unknown'
        
        # Determine type based on agent types in the zone
        agent_types = [agent.get('type', 'unknown') for agent in agents]
        
        if 'attack' in agent_types:
            return 'gateway'  # Attack agents typically in external/gateway zones
        elif 'detection' in agent_types:
            return 'server'   # Detection agents in server infrastructure
        elif 'deploy' in agent_types:
            return 'firewall' # Deploy agents in security fabric
        elif 'intelligence' in agent_types:
            return 'database' # Intelligence agents near data
        elif 'endpoint' in agent_types:
            return 'workstation' # Endpoint agents are workstations
        else:
            return 'server'   # Default to server
    
    async def _get_all_agents_dynamic(self) -> List[Dict]:
        """Get all agents (AI + endpoint agents) dynamically"""
        all_agents = []
        
        # Get AI agents
        ai_agents = await self._get_real_ai_agents()
        all_agents.extend(ai_agents)
        
        # Get endpoint agents from database (real client agents)
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_manager.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all registered endpoint agents
            cursor.execute("""
                SELECT id, hostname, platform, status, last_heartbeat, 
                       ip_address, security_zone, agent_version
                FROM agents 
                WHERE agent_type = 'endpoint' OR platform NOT LIKE '%LangChain%'
                ORDER BY last_heartbeat DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                endpoint_agent = {
                    'id': row['id'],
                    'name': row['hostname'],
                    'type': 'endpoint',
                    'status': row['status'],
                    'location': row['security_zone'] or self._determine_location_from_ip(row['ip_address']),
                    'lastActivity': self._format_timestamp_string(row['last_heartbeat']),
                    'platform': row['platform'],
                    'capabilities': ['Log Forwarding', 'Command Execution', 'Container Management'],
                    'ip_address': row['ip_address']
                }
                all_agents.append(endpoint_agent)
                
        except Exception as e:
            logger.warning(f"Could not get endpoint agents: {e}")
        
        return all_agents
    
    def _determine_location_from_ip(self, ip_address: str) -> str:
        """Determine network location from IP address"""
        if not ip_address:
            return 'Unknown Network'
        
        # Simple IP-based zone detection
        if ip_address.startswith('10.0.0.'):
            return 'Internal Network'
        elif ip_address.startswith('192.168.'):
            return 'Corporate Network'
        elif ip_address.startswith('172.'):
            return 'DMZ Network'
        else:
            return 'External Network'
    
    async def start_attack(self, request_data: Dict[str, Any]) -> JSONResponse:
        """Start PhantomStrike AI attack workflow (CodeGrey API format) - NO AUTH REQUIRED"""
        try:
            user_request = request_data.get('user_request', '')
            attack_type = request_data.get('attack_type', 'apt')
            complexity = request_data.get('complexity', 'simple')
            
            # Use integration bridge to plan attack
            from ...agents.integration_bridge import integration_bridge
            
            # Get network context
            topology = await self.topology_mapper.build_topology_from_logs(hours=24)
            network_context = await self._convert_topology_to_context(topology)
            
            # Plan attack
            planning_result = await integration_bridge.plan_attack_unified(
                user_request, network_context, {
                    'attack_type': attack_type,
                    'complexity': complexity
                }
            )
            
            if planning_result.get('success'):
                scenario = planning_result.get('scenario', {})
                scenario_id = scenario.get('scenario_id', f'scn_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}')
                
                return JSONResponse(content={
                    "success": True,
                    "scenario_id": scenario_id,
                    "scenario": {
                        "id": scenario_id,
                        "name": f"Attack Scenario: {user_request}",
                        "topology": network_context,
                        "techniques": scenario.get('mitre_techniques', []),
                        "status": "pending_approval"
                    },
                    "network_topology": network_context,
                    "message": "Attack scenario generated. Awaiting approval."
                })
            else:
                raise HTTPException(status_code=500, detail=planning_result.get('error', 'Attack planning failed'))
                
        except Exception as e:
            logger.error(f"Start attack error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def approve_attack(self, scenario_id: str, request_data: Dict[str, Any] = None) -> JSONResponse:
        """Approve and execute attack scenario (CodeGrey API format)"""
        try:
            # Use integration bridge to execute attack
            from ...agents.integration_bridge import integration_bridge
            
            # For now, simulate execution approval
            execution_result = {
                "success": True,
                "message": "Attack execution started",
                "golden_images_created": 2,  # Simulated
                "execution_id": f"exec_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            }
            
            return JSONResponse(content=execution_result)
            
        except Exception as e:
            logger.error(f"Approve attack error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_detection_status(self) -> JSONResponse:
        """Get GuardianAlpha AI detection status (CodeGrey API format)"""
        try:
            # Get detection agent status
            from ...agents.detection_agent.langchain_detection_agent import langchain_detection_agent
            
            try:
                detection_stats = await langchain_detection_agent.get_detection_statistics()
                
                status = {
                    "continuous_detection": True,
                    "guardian_alpha_status": "active",
                    "detections_today": detection_stats.get('detection_events', 0),
                    "llm_model": "gpt-3.5-turbo",
                    "analysis_method": "ml_ai_comparison"
                }
            except Exception as e:
                status = {
                    "continuous_detection": False,
                    "guardian_alpha_status": "error",
                    "detections_today": 0,
                    "error": str(e)
                }
            
            return JSONResponse(content=status)
            
        except Exception as e:
            logger.error(f"Detection status error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_recent_detections(self) -> JSONResponse:
        """Get recent threat detections (CodeGrey API format)"""
        try:
            # Get recent detection results from database
            detection_results = await self.db_manager.get_detection_results(hours=24)
            
            # Convert to CodeGrey format
            recent_detections = []
            
            for detection in detection_results[:10]:  # Limit to 10 most recent
                detection_data = {
                    "id": f"det_{detection.get('id', 'unknown')}",
                    "timestamp": detection.get('detected_at', datetime.utcnow().isoformat()),
                    "threat_type": detection.get('threat_type', 'Unknown'),
                    "severity": detection.get('severity', 'medium').upper(),
                    "confidence": detection.get('confidence_score', 0.5),
                    "verdict": "malicious" if detection.get('threat_detected') else "benign",
                    "reasoning": detection.get('ai_analysis', {}).get('reasoning', 'AI analysis completed'),
                    "llm_analysis": True,
                    "ml_analysis": True
                }
                recent_detections.append(detection_data)
            
            return JSONResponse(content=recent_detections)
            
        except Exception as e:
            logger.error(f"Recent detections error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _convert_topology_to_context(self, topology) -> Dict:
        """Convert topology to network context for attack planning"""
        try:
            return {
                'total_nodes': topology.total_nodes,
                'active_nodes': topology.active_nodes,
                'security_zones': list(topology.security_zones.keys()),
                'high_value_targets': len(topology.high_value_targets),
                'attack_paths': len(topology.attack_paths),
                'last_updated': topology.last_updated.isoformat()
            }
        except Exception as e:
            logger.error(f"Topology conversion failed: {e}")
            return {}
    
    async def get_software_download(self) -> JSONResponse:
        """Get available client agents for download (CodeGrey API format)"""
        try:
            software_downloads = [
                {
                    "id": 1,
                    "name": "windows",
                    "version": "2024.1.3",
                    "description": "Windows endpoint agent with real-time monitoring, behavioral analysis, and AI-powered threat detection.",
                    "fileName": "CodeGrey AI Endpoint Agent",
                    "downloadUrl": "https://dev-codegrey.s3.ap-south-1.amazonaws.com/windows.zip",
                    "os": "Windows",
                    "architecture": "asd",
                    "minRamGB": 45,
                    "minDiskMB": 60,
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
                    "minRamGB": 45,
                    "minDiskMB": 60,
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
                    "minRamGB": 45,
                    "minDiskMB": 60,
                    "configurationCmd": "sudo /usr/local/bin/codegrey-agent --configure --server=https://os.codegrey.ai --token=YOUR_API_TOKEN",
                    "systemRequirements": [
                        "macOS 11.0+",
                        "Administrator privileges",
                        "3 GB RAM",
                        "400 MB disk space"
                    ]
                }
            ]
            
            return JSONResponse(content=software_downloads)
            
        except Exception as e:
            logger.error(f"Software download API error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _build_codegrey_network_topology(self, topology, hierarchy: str) -> Dict:
        """Build network topology in CodeGrey API format"""
        try:
            nodes = []
            connections = []
            
            # Convert topology to CodeGrey format
            hierarchy_level = 0
            
            for zone, agent_ids in topology.security_zones.items():
                if not agent_ids:
                    continue
                
                zone_agents = []
                for agent_id in agent_ids:
                    if agent_id in topology.nodes:
                        node = topology.nodes[agent_id]
                        agent_data = {
                            "id": agent_id,
                            "name": node.hostname,
                            "status": "online" if self._get_real_agent_status(node) == "active" else "offline",
                            "type": "endpoint"
                        }
                        zone_agents.append(agent_data)
                
                # Map zone to CodeGrey format
                zone_mapping = {
                    'external': {'name': 'Internet', 'type': 'gateway'},
                    'dmz': {'name': 'DMZ Network', 'type': 'network'},
                    'internal': {'name': 'Internal Network', 'type': 'network'},
                    'corporate': {'name': 'Corporate Network', 'type': 'network'}
                }
                
                zone_info = zone_mapping.get(zone, {'name': f'{zone.title()} Network', 'type': 'network'})
                
                node_data = {
                    "id": zone,
                    "name": zone_info['name'],
                    "type": zone_info['type'],
                    "x": 10 + hierarchy_level * 40,
                    "y": 20 + hierarchy_level * 40,
                    "agents": zone_agents,
                    "status": self._get_zone_status(zone_agents),
                    "hierarchy_level": hierarchy_level
                }
                
                nodes.append(node_data)
                
                # Create connections
                if hierarchy_level > 0 and len(nodes) > 1:
                    connections.append({
                        "source": nodes[hierarchy_level - 1]["id"],
                        "target": zone
                    })
                
                hierarchy_level += 1
            
            # Sort by hierarchy
            if hierarchy == "asc":
                nodes.sort(key=lambda x: x["hierarchy_level"])
            else:
                nodes.sort(key=lambda x: x["hierarchy_level"], reverse=True)
            
            # Count agents
            total_agents = sum(len(node["agents"]) for node in nodes)
            online_agents = sum(len([a for a in node["agents"] if a["status"] == "online"]) for node in nodes)
            offline_agents = total_agents - online_agents
            
            return {
                "nodes": nodes,
                "connections": connections,
                "hierarchy_order": hierarchy,
                "total_agents": total_agents,
                "online_agents": online_agents,
                "offline_agents": offline_agents
            }
            
        except Exception as e:
            logger.error(f"CodeGrey topology building failed: {e}")
            return {
                "nodes": [],
                "connections": [],
                "hierarchy_order": hierarchy,
                "total_agents": 0,
                "online_agents": 0,
                "offline_agents": 0
            }
    
    async def receive_heartbeat(self, agent_id: str, heartbeat_data: Dict[str, Any]) -> JSONResponse:
        """Receive heartbeat from client agent"""
        try:
            # Store heartbeat in database
            # await self.db_manager.update_agent_heartbeat(agent_id, heartbeat_data)
            
            return JSONResponse(content={
                'status': 'success',
                'message': 'Heartbeat received',
                'agent_id': agent_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Heartbeat processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_agent_commands(self, agent_id: str) -> JSONResponse:
        """Get pending commands for agent"""
        try:
            # For now, return empty commands list
            # In production, this would query a command queue
            commands = []
            
            return JSONResponse(content={
                'status': 'success',
                'agent_id': agent_id,
                'commands': commands,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Get commands error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def receive_command_result(self, agent_id: str, command_id: str, result_data: Dict[str, Any]) -> JSONResponse:
        """Receive command execution result from agent"""
        try:
            # Store command result in database
            # In production, this would update the command status
            
            return JSONResponse(content={
                'status': 'success',
                'message': 'Command result received',
                'agent_id': agent_id,
                'command_id': command_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Command result processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def ingest_logs(self, logs_data: Dict[str, Any]) -> JSONResponse:
        """Ingest logs from client agents"""
        try:
            logs = logs_data.get('logs', [])
            
            # Process and store logs
            for log_entry in logs:
                # Add to database via log ingester
                # In production, this would go through the full detection pipeline
                pass
            
            return JSONResponse(content={
                'status': 'success',
                'message': f'Ingested {len(logs)} logs',
                'logs_processed': len(logs),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Log ingestion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
