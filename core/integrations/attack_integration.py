"""
Integration with attack agents for network topology-based attack planning
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.topology.network_mapper import NetworkTopologyMapper


logger = logging.getLogger(__name__)


class AttackIntegration:
    """Integration between network topology and attack agents"""
    
    def __init__(self, database_manager, topology_mapper: NetworkTopologyMapper):
        self.db_manager = database_manager
        self.topology_mapper = topology_mapper
        
        # Import your existing attack agents
        self.attack_orchestrator = None
        self.ai_attacker_brain = None
        self.dynamic_attack_generator = None
        
        self._initialize_attack_agents()
    
    def _initialize_attack_agents(self):
        """Initialize existing attack agents"""
        try:
            # Import your existing attack agents
            from ...agents.attack_agent.adaptive_attack_orchestrator import AdaptiveAttackOrchestrator
            from ...agents.attack_agent.ai_attacker_brain import AIAttackerBrain
            from ...agents.attack_agent.dynamic_attack_generator import DynamicAttackGenerator
            
            self.attack_orchestrator = AdaptiveAttackOrchestrator()
            self.ai_attacker_brain = AIAttackerBrain()
            self.dynamic_attack_generator = DynamicAttackGenerator()
            
            logger.info("Attack agents initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Some attack agents not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize attack agents: {e}")
    
    async def enhance_attack_planning_with_topology(self, attack_request: str, 
                                                  constraints: Dict = None) -> Dict:
        """Enhance attack planning with real network topology"""
        try:
            logger.info("Enhancing attack planning with network topology")
            
            # Build current network topology from logs
            topology = await self.topology_mapper.build_topology_from_logs(hours=24)
            
            # Convert topology to format expected by attack agents
            network_context = await self._convert_topology_to_attack_context(topology)
            
            # Generate attack scenario using your existing attack orchestrator
            if self.attack_orchestrator:
                scenario = await self.attack_orchestrator.generate_dynamic_scenario(
                    attack_request, network_context
                )
                
                # Enhance scenario with topology intelligence
                enhanced_scenario = await self._enhance_scenario_with_topology(
                    scenario, topology
                )
                
                return {
                    'success': True,
                    'scenario': enhanced_scenario,
                    'network_context': network_context.to_dict() if hasattr(network_context, 'to_dict') else network_context,
                    'topology_stats': {
                        'total_nodes': topology.total_nodes,
                        'high_value_targets': len(topology.high_value_targets),
                        'attack_paths': len(topology.attack_paths)
                    }
                }
            
            else:
                return {
                    'success': False,
                    'error': 'Attack orchestrator not available',
                    'network_context': network_context
                }
                
        except Exception as e:
            logger.error(f"Attack planning enhancement failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _convert_topology_to_attack_context(self, topology) -> Dict:
        """Convert network topology to attack context format"""
        try:
            # Convert to format expected by your attack agents
            network_context = {
                'domain_controllers': [
                    {
                        'id': dc_id,
                        'hostname': topology.nodes[dc_id].hostname,
                        'ip_addresses': list(topology.nodes[dc_id].ip_addresses),
                        'services': list(topology.nodes[dc_id].running_services),
                        'importance': topology.nodes[dc_id].importance
                    }
                    for dc_id in topology.domain_controllers
                    if dc_id in topology.nodes
                ],
                'endpoints': [
                    {
                        'id': agent_id,
                        'hostname': node.hostname,
                        'ip_addresses': list(node.ip_addresses),
                        'platform': node.platform,
                        'role': node.role,
                        'services': list(node.running_services),
                        'users': list(node.logged_users),
                        'admin_users': list(node.admin_users),
                        'vulnerability_score': node.vulnerability_score
                    }
                    for agent_id, node in topology.nodes.items()
                    if node.role == 'endpoint'
                ],
                'servers': [
                    {
                        'id': agent_id,
                        'hostname': node.hostname,
                        'ip_addresses': list(node.ip_addresses),
                        'platform': node.platform,
                        'role': node.role,
                        'services': list(node.running_services),
                        'importance': node.importance
                    }
                    for agent_id, node in topology.nodes.items()
                    if node.role in ['database_server', 'web_server', 'file_server', 'mail_server']
                ],
                'dmz_servers': [
                    {
                        'id': agent_id,
                        'hostname': node.hostname,
                        'ip_addresses': list(node.ip_addresses),
                        'services': list(node.running_services)
                    }
                    for agent_id, node in topology.nodes.items()
                    if node.security_zone == 'dmz'
                ],
                'firewalls': [
                    {
                        'id': agent_id,
                        'hostname': node.hostname,
                        'ip_addresses': list(node.ip_addresses)
                    }
                    for agent_id, node in topology.nodes.items()
                    if node.role == 'firewall'
                ],
                'soc_systems': [],  # SOC systems would be identified separately
                'cloud_resources': [],  # Cloud resources would be identified separately
                'security_zones': list(topology.security_zones.keys()),
                'total_agents': topology.total_nodes,
                'high_value_targets': [
                    {
                        'id': hvt_id,
                        'hostname': topology.nodes[hvt_id].hostname,
                        'role': topology.nodes[hvt_id].role,
                        'importance': topology.nodes[hvt_id].importance,
                        'services': list(topology.nodes[hvt_id].running_services)
                    }
                    for hvt_id in topology.high_value_targets
                    if hvt_id in topology.nodes
                ],
                'attack_paths': topology.attack_paths
            }
            
            return network_context
            
        except Exception as e:
            logger.error(f"Failed to convert topology to attack context: {e}")
            return {}
    
    async def _enhance_scenario_with_topology(self, scenario, topology) -> Dict:
        """Enhance attack scenario with topology-specific intelligence"""
        try:
            enhanced_scenario = scenario.copy() if isinstance(scenario, dict) else scenario.__dict__.copy()
            
            # Add topology-specific target recommendations
            enhanced_scenario['topology_recommendations'] = {
                'optimal_entry_points': self._identify_optimal_entry_points(topology),
                'lateral_movement_paths': self._identify_lateral_movement_paths(topology),
                'privilege_escalation_targets': self._identify_privilege_escalation_targets(topology),
                'data_exfiltration_targets': self._identify_data_targets(topology),
                'persistence_locations': self._identify_persistence_locations(topology)
            }
            
            # Add network-aware technique recommendations
            enhanced_scenario['network_aware_techniques'] = self._recommend_techniques_for_topology(topology)
            
            # Add timing recommendations based on network activity
            enhanced_scenario['timing_recommendations'] = await self._analyze_optimal_timing(topology)
            
            return enhanced_scenario
            
        except Exception as e:
            logger.error(f"Failed to enhance scenario with topology: {e}")
            return scenario
    
    def _identify_optimal_entry_points(self, topology) -> List[Dict]:
        """Identify best entry points for attacks"""
        entry_points = []
        
        try:
            for agent_id, node in topology.nodes.items():
                score = 0
                
                # Prefer externally accessible nodes
                if node.security_zone in ['dmz', 'external']:
                    score += 3
                
                # Prefer nodes with web services (common attack vector)
                if any(service in node.running_services for service in ['http', 'https', 'web_server']):
                    score += 2
                
                # Prefer nodes with many outbound connections (lateral movement potential)
                if len(node.outbound_connections) > 10:
                    score += 2
                
                # Avoid high-security nodes initially
                if node.importance == 'critical':
                    score -= 1
                
                if score >= 3:
                    entry_points.append({
                        'agent_id': agent_id,
                        'hostname': node.hostname,
                        'score': score,
                        'reasons': self._get_entry_point_reasons(node)
                    })
            
            # Sort by score
            entry_points.sort(key=lambda x: x['score'], reverse=True)
            return entry_points[:5]  # Top 5
            
        except Exception as e:
            logger.error(f"Failed to identify entry points: {e}")
            return []
    
    def _identify_lateral_movement_paths(self, topology) -> List[Dict]:
        """Identify lateral movement opportunities"""
        paths = []
        
        try:
            # Use existing attack paths from topology
            for path in topology.attack_paths[:10]:  # Limit to top 10
                if len(path) >= 2:
                    path_info = {
                        'path': path,
                        'length': len(path),
                        'difficulty': self._calculate_path_difficulty(path, topology),
                        'techniques': self._recommend_path_techniques(path, topology)
                    }
                    paths.append(path_info)
            
            return paths
            
        except Exception as e:
            logger.error(f"Failed to identify lateral movement paths: {e}")
            return []
    
    def _identify_privilege_escalation_targets(self, topology) -> List[Dict]:
        """Identify privilege escalation opportunities"""
        targets = []
        
        try:
            for agent_id, node in topology.nodes.items():
                # Look for nodes with admin users
                if node.admin_users:
                    targets.append({
                        'agent_id': agent_id,
                        'hostname': node.hostname,
                        'admin_users': list(node.admin_users),
                        'platform': node.platform,
                        'techniques': self._get_privesc_techniques(node)
                    })
            
            return targets
            
        except Exception as e:
            logger.error(f"Failed to identify privilege escalation targets: {e}")
            return []
    
    def _identify_data_targets(self, topology) -> List[Dict]:
        """Identify data exfiltration targets"""
        targets = []
        
        try:
            for agent_id, node in topology.nodes.items():
                if node.role in ['database_server', 'file_server'] or node.importance in ['high', 'critical']:
                    targets.append({
                        'agent_id': agent_id,
                        'hostname': node.hostname,
                        'role': node.role,
                        'services': list(node.running_services),
                        'data_value': self._assess_data_value(node)
                    })
            
            return targets
            
        except Exception as e:
            logger.error(f"Failed to identify data targets: {e}")
            return []
    
    def _identify_persistence_locations(self, topology) -> List[Dict]:
        """Identify good persistence locations"""
        locations = []
        
        try:
            for agent_id, node in topology.nodes.items():
                persistence_score = 0
                
                # Prefer endpoints over servers (less monitored)
                if node.role == 'endpoint':
                    persistence_score += 2
                
                # Prefer nodes with many connections (useful for C2)
                if len(node.outbound_connections) > 5:
                    persistence_score += 1
                
                # Prefer nodes with admin users
                if node.admin_users:
                    persistence_score += 2
                
                if persistence_score >= 2:
                    locations.append({
                        'agent_id': agent_id,
                        'hostname': node.hostname,
                        'persistence_score': persistence_score,
                        'techniques': self._get_persistence_techniques(node)
                    })
            
            return locations
            
        except Exception as e:
            logger.error(f"Failed to identify persistence locations: {e}")
            return []
    
    def _get_entry_point_reasons(self, node) -> List[str]:
        """Get reasons why node is good entry point"""
        reasons = []
        
        if node.security_zone in ['dmz', 'external']:
            reasons.append('Externally accessible')
        
        if 'http' in node.running_services or 'https' in node.running_services:
            reasons.append('Web services available')
        
        if len(node.outbound_connections) > 10:
            reasons.append('High network connectivity')
        
        if node.vulnerability_score > 0.3:
            reasons.append('Vulnerability indicators present')
        
        return reasons
    
    def _calculate_path_difficulty(self, path: List[str], topology) -> str:
        """Calculate difficulty of attack path"""
        try:
            difficulty_score = 0
            
            for agent_id in path:
                if agent_id in topology.nodes:
                    node = topology.nodes[agent_id]
                    
                    # Add difficulty based on security measures
                    if node.importance == 'critical':
                        difficulty_score += 3
                    elif node.importance == 'high':
                        difficulty_score += 2
                    
                    # Add difficulty based on platform
                    if node.platform == 'Windows':
                        difficulty_score += 1  # Generally easier to attack
                    elif node.platform == 'Linux':
                        difficulty_score += 2  # Generally harder
            
            avg_difficulty = difficulty_score / len(path) if path else 0
            
            if avg_difficulty >= 2.5:
                return 'hard'
            elif avg_difficulty >= 1.5:
                return 'medium'
            else:
                return 'easy'
                
        except Exception:
            return 'unknown'
    
    def _recommend_path_techniques(self, path: List[str], topology) -> List[str]:
        """Recommend MITRE techniques for attack path"""
        techniques = []
        
        try:
            for i, agent_id in enumerate(path):
                if agent_id in topology.nodes:
                    node = topology.nodes[agent_id]
                    
                    if i == 0:  # Initial access
                        if 'http' in node.running_services:
                            techniques.append('T1190')  # Exploit Public-Facing Application
                        if 'rdp' in node.running_services:
                            techniques.append('T1078')  # Valid Accounts
                    
                    else:  # Lateral movement
                        if node.platform == 'Windows':
                            techniques.extend(['T1021.001', 'T1550.002'])  # RDP, Pass the Hash
                        if 'smb' in node.running_services:
                            techniques.append('T1021.002')  # SMB/Windows Admin Shares
                        if 'ssh' in node.running_services:
                            techniques.append('T1021.004')  # SSH
            
            return list(set(techniques))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Failed to recommend techniques: {e}")
            return []
    
    def _get_privesc_techniques(self, node) -> List[str]:
        """Get privilege escalation techniques for node"""
        techniques = []
        
        if node.platform == 'Windows':
            techniques.extend(['T1548.002', 'T1134', 'T1055'])  # UAC Bypass, Token Manipulation, Process Injection
        elif node.platform == 'Linux':
            techniques.extend(['T1548.001', 'T1068'])  # Sudo, Exploitation for Privilege Escalation
        
        return techniques
    
    def _get_persistence_techniques(self, node) -> List[str]:
        """Get persistence techniques for node"""
        techniques = []
        
        if node.platform == 'Windows':
            techniques.extend(['T1547.001', 'T1053.005', 'T1136.001'])  # Registry Run Keys, Scheduled Tasks, Create Account
        elif node.platform == 'Linux':
            techniques.extend(['T1547.006', 'T1053.003', 'T1136.001'])  # Kernel Modules, Cron, Create Account
        
        return techniques
    
    def _assess_data_value(self, node) -> str:
        """Assess data value of node"""
        if node.role == 'database_server':
            return 'high'
        elif node.role == 'file_server':
            return 'medium'
        elif node.importance == 'critical':
            return 'high'
        elif len(node.admin_users) > 0:
            return 'medium'
        else:
            return 'low'
    
    async def _analyze_optimal_timing(self, topology) -> Dict:
        """Analyze optimal attack timing based on network activity"""
        try:
            # Analyze activity patterns from logs
            activity_analysis = await self._analyze_network_activity_patterns()
            
            return {
                'optimal_hours': activity_analysis.get('low_activity_hours', []),
                'peak_hours': activity_analysis.get('high_activity_hours', []),
                'recommended_timing': 'Execute during low activity hours to avoid detection',
                'activity_baseline': activity_analysis.get('baseline_activity', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze optimal timing: {e}")
            return {'recommended_timing': 'No timing analysis available'}
    
    async def _analyze_network_activity_patterns(self) -> Dict:
        """Analyze network activity patterns from logs"""
        try:
            # Get logs for activity analysis
            logs = await self.db_manager.get_recent_logs(hours=168)  # 7 days
            
            # Analyze activity by hour
            hourly_activity = defaultdict(int)
            
            for log_data in logs:
                try:
                    timestamp = datetime.fromisoformat(log_data['timestamp'])
                    hour = timestamp.hour
                    hourly_activity[hour] += 1
                except:
                    continue
            
            if not hourly_activity:
                return {}
            
            # Find low and high activity periods
            avg_activity = sum(hourly_activity.values()) / len(hourly_activity)
            
            low_activity_hours = [
                hour for hour, count in hourly_activity.items()
                if count < avg_activity * 0.5
            ]
            
            high_activity_hours = [
                hour for hour, count in hourly_activity.items()
                if count > avg_activity * 1.5
            ]
            
            return {
                'low_activity_hours': low_activity_hours,
                'high_activity_hours': high_activity_hours,
                'baseline_activity': avg_activity,
                'total_logs_analyzed': len(logs)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze activity patterns: {e}")
            return {}
    
    async def get_attack_targets_by_priority(self) -> Dict:
        """Get prioritized attack targets based on topology"""
        try:
            topology = await self.topology_mapper.build_topology_from_logs()
            
            # Categorize targets by attack value
            targets = {
                'critical_targets': [],
                'high_value_targets': [],
                'lateral_movement_targets': [],
                'persistence_targets': [],
                'data_targets': []
            }
            
            for agent_id, node in topology.nodes.items():
                target_info = {
                    'agent_id': agent_id,
                    'hostname': node.hostname,
                    'ip_addresses': list(node.ip_addresses),
                    'role': node.role,
                    'platform': node.platform,
                    'services': list(node.running_services),
                    'vulnerability_score': node.vulnerability_score,
                    'attack_techniques': []
                }
                
                # Categorize based on role and characteristics
                if node.role == 'domain_controller':
                    target_info['attack_techniques'] = ['T1003.006', 'T1558.003']  # DCSync, Kerberoasting
                    targets['critical_targets'].append(target_info)
                
                elif node.importance in ['high', 'critical']:
                    targets['high_value_targets'].append(target_info)
                
                elif len(node.outbound_connections) > 10:
                    target_info['attack_techniques'] = ['T1021.001', 'T1021.002']  # RDP, SMB
                    targets['lateral_movement_targets'].append(target_info)
                
                elif node.role == 'endpoint' and node.admin_users:
                    target_info['attack_techniques'] = ['T1547.001', 'T1053.005']  # Persistence
                    targets['persistence_targets'].append(target_info)
                
                elif node.role in ['database_server', 'file_server']:
                    target_info['attack_techniques'] = ['T1005', 'T1039']  # Data Collection
                    targets['data_targets'].append(target_info)
            
            return targets
            
        except Exception as e:
            logger.error(f"Failed to get attack targets: {e}")
            return {}
    
    async def update_attack_agent_context(self) -> Dict:
        """Update attack agents with latest network context"""
        try:
            # Build fresh topology
            topology = await self.topology_mapper.build_topology_from_logs()
            
            # Convert to attack context
            attack_context = await self._convert_topology_to_attack_context(topology)
            
            # Update your existing attack orchestrator with new context
            if self.attack_orchestrator:
                # This would update your attack orchestrator's network cache
                self.attack_orchestrator.network_cache['context'] = attack_context
                self.attack_orchestrator.last_network_scan = datetime.now()
                
                logger.info("Attack orchestrator context updated with topology data")
            
            return {
                'success': True,
                'context_updated': True,
                'nodes_discovered': len(topology.nodes),
                'high_value_targets': len(topology.high_value_targets),
                'attack_paths': len(topology.attack_paths)
            }
            
        except Exception as e:
            logger.error(f"Failed to update attack agent context: {e}")
            return {'success': False, 'error': str(e)}
    
    async def generate_network_aware_attack_plan(self, attack_objective: str) -> Dict:
        """Generate attack plan that's aware of actual network topology"""
        try:
            # Get current topology
            topology = await self.topology_mapper.build_topology_from_logs()
            
            # Get prioritized targets
            targets = await self.get_attack_targets_by_priority()
            
            # Generate network-aware plan
            attack_plan = {
                'objective': attack_objective,
                'phases': []
            }
            
            # Phase 1: Initial Access
            if targets['critical_targets'] or targets['high_value_targets']:
                entry_points = self._identify_optimal_entry_points(topology)
                attack_plan['phases'].append({
                    'name': 'initial_access',
                    'targets': [ep['agent_id'] for ep in entry_points[:3]],
                    'techniques': ['T1190', 'T1566.001', 'T1078'],
                    'description': 'Gain initial foothold in network'
                })
            
            # Phase 2: Lateral Movement
            if targets['lateral_movement_targets']:
                attack_plan['phases'].append({
                    'name': 'lateral_movement',
                    'targets': [t['agent_id'] for t in targets['lateral_movement_targets'][:5]],
                    'techniques': ['T1021.001', 'T1021.002', 'T1550.002'],
                    'description': 'Move laterally through network'
                })
            
            # Phase 3: Privilege Escalation
            if targets['persistence_targets']:
                attack_plan['phases'].append({
                    'name': 'privilege_escalation',
                    'targets': [t['agent_id'] for t in targets['persistence_targets'][:3]],
                    'techniques': ['T1548.002', 'T1134', 'T1055'],
                    'description': 'Escalate privileges on key systems'
                })
            
            # Phase 4: Data Collection
            if targets['data_targets']:
                attack_plan['phases'].append({
                    'name': 'data_collection',
                    'targets': [t['agent_id'] for t in targets['data_targets'][:3]],
                    'techniques': ['T1005', 'T1039', 'T1114'],
                    'description': 'Collect valuable data'
                })
            
            return {
                'success': True,
                'attack_plan': attack_plan,
                'topology_context': topology.to_dict(),
                'target_analysis': targets
            }
            
        except Exception as e:
            logger.error(f"Failed to generate network-aware attack plan: {e}")
            return {'success': False, 'error': str(e)}
