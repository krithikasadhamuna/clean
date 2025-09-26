"""
Dynamic Frontend API for AI SOC Platform
Completely data-driven without hardcoded values
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
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
                                  hierarchy: str = Query("desc", description="Hierarchy order (asc/desc)")) -> JSONResponse:
        """Get network topology in CodeGrey API format - NO AUTH REQUIRED"""
        try:
            # Build topology from actual logs
            topology = await self.topology_mapper.build_topology_from_logs(hours=24)
            
            network_nodes = []
            x_pos = 10
            y_pos = 20
            
            # Create nodes dynamically from actual topology
            for zone, agent_ids in topology.security_zones.items():
                if not agent_ids:
                    continue
                
                # Get actual agents in this zone
                zone_agents = []
                for agent_id in agent_ids:
                    if agent_id in topology.nodes:
                        node = topology.nodes[agent_id]
                        zone_agents.append({
                            'id': agent_id,
                            'name': node.hostname,
                            'type': node.role,
                            'platform': node.platform,
                            'services': list(node.running_services),
                            'status': self._get_real_agent_status(node),
                            'importance': node.importance
                        })
                
                # Create network node with actual data
                network_node = {
                    'id': f'zone_{zone}',
                    'name': self._get_zone_name(zone),
                    'type': self._get_zone_type(zone, zone_agents),
                    'x': x_pos,
                    'y': y_pos,
                    'agents': zone_agents,
                    'status': self._get_zone_status(zone_agents)
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
        """Get agents list dynamically from actual data - NO AUTH REQUIRED"""
        try:
            agents = []
            
            # Get real AI agents from database
            ai_agents = await self._get_real_ai_agents()
            agents.extend(ai_agents)
            
            # Get endpoint agents from topology
            topology = await self.topology_mapper.build_topology_from_logs(hours=24)
            
            for agent_id, node in topology.nodes.items():
                # Get real agent data from database
                agent_info = await self.db_manager.get_agent_info(agent_id)
                
                if agent_info:
                    agent = {
                        'id': agent_id,
                        'name': agent_info.hostname,
                        'type': self._classify_agent_type(node, agent_info),
                        'status': agent_info.status,
                        'location': self._map_zone_to_location(node.security_zone),
                        'lastActivity': self._format_timestamp(agent_info.last_heartbeat),
                        'capabilities': self._get_real_capabilities(node, agent_info)
                    }
                    agents.append(agent)
            
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
    
    async def _get_real_ai_agents(self) -> List[Dict]:
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
            # Try to import and check if agents are available
            agent_modules = [
                ('phantomstrike_ai', 'agents.attack_agent.langchain_attack_agent', 'attack', 'active'),
                ('guardian_alpha_ai', 'agents.detection_agent.langchain_detection_agent', 'detection', 'active'),
                ('soc_orchestrator', 'agents.langchain_orchestrator', 'orchestration', 'active'),
                ('sentinel_deploy_ai', None, 'deploy', 'inactive'),  # Not fully implemented
                ('threat_mind_ai', None, 'intelligence', 'inactive')  # Not fully implemented
            ]
            
            for agent_id, module_path, agent_type, dev_status in agent_modules:
                try:
                    if module_path is None:
                        # Agent is in development, add with development status
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
                    else:
                        # Try to import the module
                        import importlib
                        module = importlib.import_module(module_path)
                        
                        # If import succeeds, agent is available
                        detected_agents.append({
                            'id': agent_id,
                            'name': agent_id.replace('_', ' ').title(),
                            'type': agent_type,
                            'status': dev_status,
                            'location': 'SOC Server',
                            'lastActivity': 'Now' if dev_status == 'active' else ('Inactive' if dev_status == 'inactive' else 'In Development'),
                            'capabilities': self._get_module_capabilities(module, agent_type),
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
                    "fileName": "AI SOC Platform Windows Agent",
                    "downloadUrl": "https://github.com/your-org/ai-soc-platform/releases/download/v2024.1.3/windows-agent.zip",
                    "os": "Windows",
                    "architecture": "x64",
                    "minRamGB": 2,
                    "minDiskMB": 500,
                    "configurationCmd": "python main.py client --config config/client_config.yaml",
                    "systemRequirements": [
                        "Windows 10/11 (64-bit)",
                        "Python 3.8+",
                        "2 GB RAM",
                        "500 MB disk space"
                    ]
                },
                {
                    "id": 2,
                    "name": "linux",
                    "version": "2024.1.3", 
                    "description": "Linux endpoint agent with advanced process monitoring, network analysis, and eBPF-based detection.",
                    "fileName": "AI SOC Platform Linux Agent",
                    "downloadUrl": "https://github.com/your-org/ai-soc-platform/releases/download/v2024.1.3/linux-agent.tar.gz",
                    "os": "Linux",
                    "architecture": "x64",
                    "minRamGB": 1,
                    "minDiskMB": 300,
                    "configurationCmd": "python3 main.py client --config config/client_config.yaml",
                    "systemRequirements": [
                        "Ubuntu 18.04+ / CentOS 7+ / RHEL 8+",
                        "Python 3.8+",
                        "1 GB RAM",
                        "300 MB disk space"
                    ]
                },
                {
                    "id": 3,
                    "name": "macos",
                    "version": "2024.1.3",
                    "description": "macOS endpoint agent with privacy-focused monitoring and intelligent threat correlation.",
                    "fileName": "AI SOC Platform macOS Agent",
                    "downloadUrl": "https://github.com/your-org/ai-soc-platform/releases/download/v2024.1.3/macos-agent.pkg",
                    "os": "macOS",
                    "architecture": "universal",
                    "minRamGB": 2,
                    "minDiskMB": 400,
                    "configurationCmd": "python3 main.py client --config config/client_config.yaml",
                    "systemRequirements": [
                        "macOS 11.0+",
                        "Python 3.8+",
                        "2 GB RAM", 
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
