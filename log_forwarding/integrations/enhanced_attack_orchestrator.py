"""
Enhanced Attack Orchestrator with Log-Based Network Topology
Integrates with log forwarding system for real-time network intelligence
"""

import asyncio
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..server.topology.network_mapper import NetworkTopologyMapper
from .attack_integration import AttackIntegration


logger = logging.getLogger(__name__)


class EnhancedAttackOrchestrator:
    """Enhanced attack orchestrator with log-based network intelligence"""
    
    def __init__(self, database_manager, server_endpoint: str = "http://localhost:8080"):
        self.db_manager = database_manager
        self.server_endpoint = server_endpoint
        
        # Network topology components
        self.topology_mapper = NetworkTopologyMapper(database_manager)
        self.attack_integration = AttackIntegration(database_manager, self.topology_mapper)
        
        # Cache for network topology
        self.topology_cache = None
        self.cache_ttl = 300  # 5 minutes
        self.last_topology_update = None
        
        # Import your existing attack orchestrator
        self.base_orchestrator = None
        self._initialize_base_orchestrator()
    
    def _initialize_base_orchestrator(self):
        """Initialize your existing attack orchestrator"""
        try:
            from ...agents.attack_agent.adaptive_attack_orchestrator import AdaptiveAttackOrchestrator
            self.base_orchestrator = AdaptiveAttackOrchestrator()
            logger.info("Base attack orchestrator initialized")
        except ImportError as e:
            logger.warning(f"Base attack orchestrator not available: {e}")
    
    async def get_enhanced_network_context(self, force_refresh: bool = False) -> Dict:
        """Get network context enhanced with log-based topology"""
        try:
            # Check cache
            if (not force_refresh and 
                self.topology_cache and 
                self.last_topology_update and
                (datetime.utcnow() - self.last_topology_update).seconds < self.cache_ttl):
                return self.topology_cache
            
            logger.info("Building enhanced network context from logs...")
            
            # Build topology from logs
            topology = await self.topology_mapper.build_topology_from_logs(hours=24)
            
            # Convert to attack context format
            attack_context = await self.attack_integration._convert_topology_to_attack_context(topology)
            
            # Enhance with additional intelligence
            enhanced_context = {
                **attack_context,
                'topology_metadata': {
                    'source': 'log_analysis',
                    'analysis_period_hours': 24,
                    'confidence': 'high',
                    'last_updated': topology.last_updated.isoformat(),
                    'data_freshness': 'real_time'
                },
                'attack_intelligence': {
                    'optimal_entry_points': self.attack_integration._identify_optimal_entry_points(topology),
                    'lateral_movement_paths': self.attack_integration._identify_lateral_movement_paths(topology),
                    'privilege_escalation_targets': self.attack_integration._identify_privilege_escalation_targets(topology),
                    'data_exfiltration_targets': self.attack_integration._identify_data_targets(topology),
                    'persistence_opportunities': self.attack_integration._identify_persistence_locations(topology)
                },
                'network_vulnerabilities': await self._assess_network_vulnerabilities(topology),
                'timing_recommendations': await self.attack_integration._analyze_optimal_timing(topology)
            }
            
            # Cache the result
            self.topology_cache = enhanced_context
            self.last_topology_update = datetime.utcnow()
            
            logger.info(f"Enhanced network context built: {len(topology.nodes)} nodes, "
                       f"{len(topology.high_value_targets)} HVTs, "
                       f"{len(topology.attack_paths)} attack paths")
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Failed to get enhanced network context: {e}")
            return {}
    
    async def generate_log_informed_attack_scenario(self, attack_request: str, 
                                                  scenario_type: str = None) -> Dict:
        """Generate attack scenario informed by log-based network topology"""
        try:
            logger.info(f"Generating log-informed attack scenario: {attack_request[:50]}...")
            
            # Get enhanced network context
            network_context = await self.get_enhanced_network_context()
            
            if not network_context:
                return {'success': False, 'error': 'No network context available'}
            
            # Use your existing attack orchestrator with enhanced context
            if self.base_orchestrator:
                # Update base orchestrator's network cache with our enhanced data
                self.base_orchestrator.network_cache = {
                    'context': self._convert_to_legacy_format(network_context),
                    'timestamp': datetime.utcnow()
                }
                self.base_orchestrator.last_network_scan = datetime.utcnow()
                
                # Generate scenario using base orchestrator
                scenario = await self.base_orchestrator.generate_dynamic_scenario(
                    attack_request, self.base_orchestrator.network_cache['context']
                )
                
                # Enhance scenario with log-based intelligence
                enhanced_scenario = await self._enhance_scenario_with_log_intelligence(
                    scenario, network_context
                )
                
                return {
                    'success': True,
                    'scenario': enhanced_scenario,
                    'network_intelligence': {
                        'topology_source': 'real_time_logs',
                        'nodes_analyzed': len(network_context.get('endpoints', [])),
                        'high_value_targets': len(network_context.get('high_value_targets', [])),
                        'attack_paths_available': len(network_context.get('attack_paths', []))
                    }
                }
            
            else:
                # Fallback: create scenario without base orchestrator
                scenario = await self._create_fallback_scenario(attack_request, network_context)
                return {'success': True, 'scenario': scenario}
                
        except Exception as e:
            logger.error(f"Log-informed scenario generation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _convert_to_legacy_format(self, enhanced_context: Dict) -> Any:
        """Convert enhanced context to format expected by existing attack orchestrator"""
        try:
            # This would convert to your existing NetworkContext format
            # You'd need to import your NetworkContext class
            
            # For now, return the enhanced context as-is
            # In real implementation, you'd do:
            # from ...agents.attack_agent.adaptive_attack_orchestrator import NetworkContext
            # return NetworkContext(...)
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Legacy format conversion failed: {e}")
            return enhanced_context
    
    async def _enhance_scenario_with_log_intelligence(self, scenario, network_context: Dict) -> Dict:
        """Enhance attack scenario with log-based intelligence"""
        try:
            enhanced = scenario.__dict__.copy() if hasattr(scenario, '__dict__') else scenario.copy()
            
            # Add real-time network intelligence
            enhanced['network_intelligence'] = {
                'real_time_topology': True,
                'nodes_discovered': len(network_context.get('endpoints', [])),
                'services_mapped': sum(len(ep.get('services', [])) for ep in network_context.get('endpoints', [])),
                'vulnerability_hotspots': [
                    ep for ep in network_context.get('endpoints', [])
                    if ep.get('vulnerability_score', 0) > 0.5
                ],
                'optimal_targets': network_context.get('attack_intelligence', {}).get('optimal_entry_points', []),
                'lateral_movement_opportunities': network_context.get('attack_intelligence', {}).get('lateral_movement_paths', [])
            }
            
            # Enhance target selection with log-based data
            if 'target_elements' in enhanced:
                enhanced['recommended_targets'] = self._select_optimal_targets(
                    enhanced['target_elements'], network_context
                )
            
            # Add timing recommendations
            timing = network_context.get('timing_recommendations', {})
            if timing:
                enhanced['optimal_execution_time'] = timing
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Scenario enhancement failed: {e}")
            return scenario
    
    def _select_optimal_targets(self, target_elements: List[str], network_context: Dict) -> List[Dict]:
        """Select optimal targets based on log-derived network intelligence"""
        optimal_targets = []
        
        try:
            endpoints = network_context.get('endpoints', [])
            servers = network_context.get('servers', [])
            hvts = network_context.get('high_value_targets', [])
            
            # Prioritize targets based on attack intelligence
            for target_type in target_elements:
                if target_type == 'endpoint':
                    # Select endpoints with highest vulnerability scores
                    sorted_endpoints = sorted(
                        endpoints, 
                        key=lambda x: x.get('vulnerability_score', 0), 
                        reverse=True
                    )
                    optimal_targets.extend(sorted_endpoints[:3])
                
                elif target_type == 'server':
                    # Select servers with valuable services
                    valuable_servers = [
                        s for s in servers 
                        if any(svc in s.get('services', []) for svc in ['database', 'web_server', 'file_server'])
                    ]
                    optimal_targets.extend(valuable_servers[:2])
                
                elif target_type == 'domain_controller':
                    # Select domain controllers
                    dcs = network_context.get('domain_controllers', [])
                    optimal_targets.extend(dcs)
            
            return optimal_targets
            
        except Exception as e:
            logger.error(f"Target selection failed: {e}")
            return []
    
    async def _create_fallback_scenario(self, attack_request: str, network_context: Dict) -> Dict:
        """Create fallback scenario when base orchestrator unavailable"""
        try:
            # Analyze attack request
            request_lower = attack_request.lower()
            
            # Determine scenario type
            if any(term in request_lower for term in ['apt', 'advanced', 'persistent']):
                scenario_type = 'apt_simulation'
            elif any(term in request_lower for term in ['ransomware', 'crypto', 'encrypt']):
                scenario_type = 'ransomware_simulation'
            elif any(term in request_lower for term in ['data', 'exfil', 'steal']):
                scenario_type = 'data_exfiltration'
            else:
                scenario_type = 'general_assessment'
            
            # Select targets based on available nodes
            targets = []
            if network_context.get('endpoints'):
                targets.extend([ep['id'] for ep in network_context['endpoints'][:3]])
            if network_context.get('high_value_targets'):
                targets.extend([hvt['id'] for hvt in network_context['high_value_targets'][:2]])
            
            scenario = {
                'id': f"scenario_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'name': f"Log-Informed {scenario_type.replace('_', ' ').title()}",
                'description': f"Attack scenario generated from real-time log analysis: {attack_request}",
                'type': scenario_type,
                'targets': targets,
                'techniques': self._get_techniques_for_scenario_type(scenario_type),
                'phases': self._generate_attack_phases(scenario_type, targets),
                'estimated_duration': '2-4 hours',
                'confidence': 0.8,
                'network_intelligence': network_context.get('attack_intelligence', {}),
                'generated_at': datetime.utcnow().isoformat(),
                'source': 'log_based_topology'
            }
            
            return scenario
            
        except Exception as e:
            logger.error(f"Fallback scenario creation failed: {e}")
            return {}
    
    def _get_techniques_for_scenario_type(self, scenario_type: str) -> List[str]:
        """Get MITRE techniques for scenario type"""
        technique_mapping = {
            'apt_simulation': ['T1566.001', 'T1055', 'T1003', 'T1021.001', 'T1041'],
            'ransomware_simulation': ['T1486', 'T1490', 'T1489', 'T1083', 'T1057'],
            'data_exfiltration': ['T1005', 'T1039', 'T1114', 'T1020', 'T1041'],
            'general_assessment': ['T1082', 'T1083', 'T1018', 'T1033', 'T1016']
        }
        
        return technique_mapping.get(scenario_type, ['T1082', 'T1083'])
    
    def _generate_attack_phases(self, scenario_type: str, targets: List[str]) -> List[Dict]:
        """Generate attack phases based on scenario type and targets"""
        if scenario_type == 'apt_simulation':
            return [
                {'name': 'initial_access', 'targets': targets[:1], 'techniques': ['T1566.001']},
                {'name': 'execution', 'targets': targets[:1], 'techniques': ['T1055']},
                {'name': 'persistence', 'targets': targets[:2], 'techniques': ['T1547.001']},
                {'name': 'lateral_movement', 'targets': targets, 'techniques': ['T1021.001']},
                {'name': 'collection', 'targets': targets[-2:], 'techniques': ['T1003', 'T1005']}
            ]
        
        elif scenario_type == 'ransomware_simulation':
            return [
                {'name': 'initial_access', 'targets': targets[:1], 'techniques': ['T1566.001']},
                {'name': 'discovery', 'targets': targets, 'techniques': ['T1083', 'T1057']},
                {'name': 'lateral_movement', 'targets': targets, 'techniques': ['T1021.002']},
                {'name': 'impact', 'targets': targets, 'techniques': ['T1486', 'T1490']}
            ]
        
        else:  # Default phases
            return [
                {'name': 'reconnaissance', 'targets': targets[:1], 'techniques': ['T1082', 'T1083']},
                {'name': 'execution', 'targets': targets, 'techniques': ['T1059.001']},
                {'name': 'collection', 'targets': targets, 'techniques': ['T1005']}
            ]
    
    async def _assess_network_vulnerabilities(self, topology) -> Dict:
        """Assess network vulnerabilities from topology"""
        try:
            vulnerabilities = {
                'high_risk_nodes': [],
                'exposed_services': [],
                'weak_authentication': [],
                'network_segmentation_issues': []
            }
            
            for agent_id, node in topology.nodes.items():
                # High vulnerability score nodes
                if node.vulnerability_score > 0.5:
                    vulnerabilities['high_risk_nodes'].append({
                        'agent_id': agent_id,
                        'hostname': node.hostname,
                        'vulnerability_score': node.vulnerability_score,
                        'exposed_services': node.exposed_services
                    })
                
                # Exposed dangerous services
                dangerous_services = ['rdp', 'ssh', 'smb', 'winrm']
                exposed = [svc for svc in node.running_services if svc in dangerous_services]
                if exposed:
                    vulnerabilities['exposed_services'].append({
                        'agent_id': agent_id,
                        'hostname': node.hostname,
                        'services': exposed
                    })
                
                # Weak authentication indicators
                if not node.admin_users and 'administrator' in node.logged_users:
                    vulnerabilities['weak_authentication'].append({
                        'agent_id': agent_id,
                        'hostname': node.hostname,
                        'issue': 'Default admin account active'
                    })
            
            # Network segmentation issues
            for subnet, nodes in topology.subnets.items():
                if len(nodes) > 50:  # Large flat network
                    vulnerabilities['network_segmentation_issues'].append({
                        'subnet': subnet,
                        'nodes_count': len(nodes),
                        'issue': 'Large flat network segment'
                    })
            
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Vulnerability assessment failed: {e}")
            return {}
    
    async def execute_topology_aware_attack(self, scenario: Dict, 
                                          approval_required: bool = True) -> Dict:
        """Execute attack with topology awareness"""
        try:
            logger.info(f"Executing topology-aware attack: {scenario.get('name', 'Unknown')}")
            
            # Get fresh network context
            network_context = await self.get_enhanced_network_context(force_refresh=True)
            
            # Validate targets still exist and are reachable
            validated_targets = await self._validate_attack_targets(scenario, network_context)
            
            if not validated_targets:
                return {
                    'success': False,
                    'error': 'No valid targets found in current network topology'
                }
            
            # Update scenario with validated targets
            scenario['validated_targets'] = validated_targets
            
            # Execute using base orchestrator if available
            if self.base_orchestrator:
                execution_result = await self.base_orchestrator.execute_dynamic_scenario(
                    scenario, validated_targets
                )
                
                # Enhance result with topology context
                enhanced_result = {
                    **execution_result,
                    'topology_context': network_context,
                    'network_intelligence_used': True,
                    'targets_validated': len(validated_targets)
                }
                
                return enhanced_result
            
            else:
                # Fallback execution (simulation only)
                return await self._simulate_topology_aware_execution(scenario, network_context)
                
        except Exception as e:
            logger.error(f"Topology-aware attack execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _validate_attack_targets(self, scenario: Dict, network_context: Dict) -> List[str]:
        """Validate that attack targets are still valid and reachable"""
        try:
            valid_targets = []
            scenario_targets = scenario.get('targets', [])
            
            # Get all available nodes
            all_nodes = []
            all_nodes.extend(network_context.get('endpoints', []))
            all_nodes.extend(network_context.get('servers', []))
            all_nodes.extend(network_context.get('domain_controllers', []))
            
            available_node_ids = [node['id'] for node in all_nodes]
            
            for target_id in scenario_targets:
                if target_id in available_node_ids:
                    valid_targets.append(target_id)
                else:
                    logger.warning(f"Target {target_id} no longer available in network")
            
            # If no original targets are valid, select new ones based on scenario type
            if not valid_targets and scenario.get('type'):
                valid_targets = await self._select_alternative_targets(
                    scenario['type'], network_context
                )
            
            return valid_targets
            
        except Exception as e:
            logger.error(f"Target validation failed: {e}")
            return []
    
    async def _select_alternative_targets(self, scenario_type: str, network_context: Dict) -> List[str]:
        """Select alternative targets when original targets unavailable"""
        try:
            targets = []
            
            if scenario_type == 'apt_simulation':
                # For APT, prefer high-value targets
                hvts = network_context.get('high_value_targets', [])
                targets.extend([hvt['id'] for hvt in hvts[:2]])
                
                # Add some endpoints for lateral movement
                endpoints = network_context.get('endpoints', [])
                targets.extend([ep['id'] for ep in endpoints[:2]])
            
            elif scenario_type == 'ransomware_simulation':
                # For ransomware, target as many endpoints as possible
                endpoints = network_context.get('endpoints', [])
                targets.extend([ep['id'] for ep in endpoints[:5]])
                
                # Add file servers
                servers = [s for s in network_context.get('servers', []) 
                          if 'file_server' in s.get('role', '')]
                targets.extend([s['id'] for s in servers])
            
            elif scenario_type == 'data_exfiltration':
                # For data exfil, target database and file servers
                servers = network_context.get('servers', [])
                data_servers = [s for s in servers 
                              if s.get('role') in ['database_server', 'file_server']]
                targets.extend([s['id'] for s in data_servers])
            
            return targets[:5]  # Limit to 5 targets
            
        except Exception as e:
            logger.error(f"Alternative target selection failed: {e}")
            return []
    
    async def _simulate_topology_aware_execution(self, scenario: Dict, network_context: Dict) -> Dict:
        """Simulate attack execution with topology awareness"""
        try:
            execution_result = {
                'execution_id': f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'scenario_id': scenario.get('id'),
                'status': 'simulated',
                'start_time': datetime.utcnow().isoformat(),
                'phases_executed': [],
                'commands_sent': 0,
                'targets_affected': len(scenario.get('validated_targets', [])),
                'network_context': network_context,
                'simulation_results': {
                    'detection_likelihood': 'medium',
                    'success_probability': 0.75,
                    'estimated_impact': 'moderate'
                }
            }
            
            # Simulate each phase
            for phase in scenario.get('phases', []):
                phase_result = {
                    'phase_name': phase['name'],
                    'targets': phase['targets'],
                    'techniques': phase['techniques'],
                    'simulated_at': datetime.utcnow().isoformat(),
                    'success': True,
                    'detection_risk': 'low'
                }
                
                execution_result['phases_executed'].append(phase_result)
                execution_result['commands_sent'] += len(phase['techniques']) * len(phase['targets'])
            
            execution_result['end_time'] = datetime.utcnow().isoformat()
            
            return {'success': True, 'execution': execution_result}
            
        except Exception as e:
            logger.error(f"Simulated execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_real_time_network_status(self) -> Dict:
        """Get real-time network status for attack planning"""
        try:
            # Get topology from recent logs (last hour for real-time status)
            topology = await self.topology_mapper.build_topology_from_logs(hours=1)
            
            status = {
                'network_status': 'active',
                'active_nodes': topology.active_nodes,
                'total_nodes': topology.total_nodes,
                'availability_rate': topology.active_nodes / topology.total_nodes if topology.total_nodes > 0 else 0,
                'high_value_targets_online': len([
                    hvt for hvt in topology.high_value_targets
                    if hvt in topology.nodes and 
                    (datetime.utcnow() - topology.nodes[hvt].last_activity).seconds < 3600
                ]),
                'security_zones': {
                    zone: len(nodes) for zone, nodes in topology.security_zones.items()
                },
                'last_updated': topology.last_updated.isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Real-time network status failed: {e}")
            return {'network_status': 'unknown', 'error': str(e)}
