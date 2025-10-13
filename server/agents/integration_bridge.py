"""
Integration Bridge between LangChain Agents and Existing Infrastructure
Connects new LangChain-based agents with existing detection and attack components
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .detection_agent.langchain_detection_agent import langchain_detection_agent
from .attack_agent.langchain_attack_agent import phantomstrike_ai
from .langchain_orchestrator import soc_orchestrator

# Import existing agents
from .detection_agent.ai_enhanced_detector import ai_enhanced_detector
from .detection_agent.ai_threat_analyzer import ai_threat_analyzer
from .detection_agent.real_threat_detector import real_threat_detector
from .attack_agent.adaptive_attack_orchestrator import adaptive_orchestrator
from .attack_agent.dynamic_attack_generator import DynamicAttackGenerator


logger = logging.getLogger(__name__)


class AgentIntegrationBridge:
    """Bridge between LangChain agents and existing infrastructure"""
    
    def __init__(self):
        # LangChain agents
        self.langchain_detection = langchain_detection_agent
        self.langchain_attack = phantomstrike_ai
        self.langchain_orchestrator = soc_orchestrator
        
        # Existing agents
        self.existing_detection = ai_enhanced_detector
        self.existing_threat_analyzer = ai_threat_analyzer
        self.existing_real_detector = real_threat_detector
        self.existing_attack_orchestrator = adaptive_orchestrator
        self.existing_attack_generator = DynamicAttackGenerator()
        
        # Bridge state
        self.bridge_active = True
        self.routing_preferences = {
            'detection': 'langchain',  # Use LangChain by default
            'attack': 'langchain',     # Use LangChain by default
            'fallback_enabled': True
        }
        
        logger.info("Agent Integration Bridge initialized")
    
    async def detect_threat_unified(self, detection_data: Dict, context: Dict = None) -> Dict:
        """Unified threat detection using both LangChain and existing agents"""
        try:
            results = {}
            
            # Try LangChain detection first
            if self.routing_preferences['detection'] == 'langchain':
                try:
                    langchain_result = await self.langchain_detection.analyze_threat(detection_data, context)
                    results['langchain'] = {
                        'success': True,
                        'result': langchain_result.dict() if hasattr(langchain_result, 'dict') else langchain_result,
                        'method': 'langchain_agent'
                    }
                except Exception as e:
                    logger.error(f"LangChain detection failed: {e}")
                    results['langchain'] = {'success': False, 'error': str(e)}
                    
                    # Fallback to existing detection if enabled
                    if self.routing_preferences['fallback_enabled']:
                        results['existing'] = await self._run_existing_detection(detection_data, context)
            
            else:
                # Use existing detection primarily
                results['existing'] = await self._run_existing_detection(detection_data, context)
            
            # Combine results
            final_result = self._combine_detection_results(results)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Unified threat detection failed: {e}")
            return {'success': False, 'error': str(e), 'method': 'bridge_error'}
    
    async def plan_attack_unified(self, attack_request: str, network_context: Dict, 
                                constraints: Dict = None) -> Dict:
        """Unified attack planning using both LangChain and existing agents"""
        try:
            results = {}
            
            # Try LangChain attack planning first
            if self.routing_preferences['attack'] == 'langchain':
                try:
                    langchain_scenario = await self.langchain_attack.plan_attack_scenario(
                        attack_request, network_context, constraints
                    )
                    results['langchain'] = {
                        'success': True,
                        'scenario': langchain_scenario.dict() if hasattr(langchain_scenario, 'dict') else langchain_scenario,
                        'method': 'langchain_agent'
                    }
                except Exception as e:
                    logger.error(f"LangChain attack planning failed: {e}")
                    results['langchain'] = {'success': False, 'error': str(e)}
                    
                    # Fallback to existing attack orchestrator
                    if self.routing_preferences['fallback_enabled']:
                        results['existing'] = await self._run_existing_attack_planning(
                            attack_request, network_context
                        )
            else:
                # Use existing attack planning primarily
                results['existing'] = await self._run_existing_attack_planning(
                    attack_request, network_context
                )
            
            # Return best result
            final_result = self._select_best_attack_result(results)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Unified attack planning failed: {e}")
            return {'success': False, 'error': str(e), 'method': 'bridge_error'}
    
    async def _run_existing_detection(self, detection_data: Dict, context: Dict) -> Dict:
        """Run detection using existing agents"""
        try:
            # Use existing AI enhanced detector
            result = await self.existing_detection.analyze_threat_intelligently(detection_data, context)
            
            return {
                'success': True,
                'result': result,
                'method': 'existing_ai_enhanced'
            }
            
        except Exception as e:
            logger.error(f"Existing detection failed: {e}")
            
            # Fallback to basic real detector
            try:
                basic_result = self._run_basic_detection(detection_data)
                return {
                    'success': True,
                    'result': basic_result,
                    'method': 'existing_basic'
                }
            except Exception as e2:
                logger.error(f"Basic detection also failed: {e2}")
                return {'success': False, 'error': str(e)}
    
    def _run_basic_detection(self, detection_data: Dict) -> Dict:
        """Run basic detection using real threat detector"""
        data_type = detection_data.get('type', 'unknown')
        data = detection_data.get('data', {})
        
        if data_type == 'process_anomaly':
            return self.existing_real_detector.detect_process_anomaly(data)
        elif data_type == 'file_threat':
            return self.existing_real_detector.detect_file_threat(data)
        elif data_type == 'network_anomaly':
            return self.existing_real_detector.detect_network_anomaly(data)
        elif data_type == 'command_injection':
            return self.existing_real_detector.detect_command_injection(data)
        else:
            return {'threat_detected': False, 'reason': 'Unknown data type'}
    
    async def _run_existing_attack_planning(self, attack_request: str, network_context: Dict) -> Dict:
        """Run attack planning using existing orchestrator"""
        try:
            # Convert network context to format expected by existing orchestrator
            legacy_context = self._convert_to_legacy_network_context(network_context)
            
            # Use existing attack orchestrator
            scenario = await self.existing_attack_orchestrator.generate_dynamic_scenario(
                attack_request, legacy_context
            )
            
            return {
                'success': True,
                'scenario': scenario.__dict__ if hasattr(scenario, '__dict__') else scenario,
                'method': 'existing_orchestrator'
            }
            
        except Exception as e:
            logger.error(f"Existing attack planning failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _convert_to_legacy_network_context(self, network_context: Dict) -> Any:
        """Convert new network context to legacy format"""
        try:
            # Import the legacy NetworkContext class
            from .attack_agent.adaptive_attack_orchestrator import NetworkContext
            
            # Extract data from new format
            endpoints = network_context.get('endpoints', [])
            servers = network_context.get('servers', [])
            domain_controllers = network_context.get('domain_controllers', [])
            
            # Convert to legacy format
            legacy_context = NetworkContext(
                domain_controllers=[self._convert_endpoint_to_legacy(dc) for dc in domain_controllers],
                endpoints=[self._convert_endpoint_to_legacy(ep) for ep in endpoints],
                dmz_servers=[self._convert_endpoint_to_legacy(srv) for srv in servers if 'dmz' in str(srv)],
                firewalls=[],  # Would need to be populated if available
                soc_systems=[],  # Would need to be populated if available
                cloud_resources=[],  # Would need to be populated if available
                security_zones=network_context.get('security_zones', []),
                total_agents=len(endpoints) + len(servers) + len(domain_controllers),
                high_value_targets=[self._convert_endpoint_to_legacy(hvt) for hvt in network_context.get('high_value_targets', [])],
                attack_paths=network_context.get('attack_paths', [])
            )
            
            return legacy_context
            
        except Exception as e:
            logger.error(f"Legacy context conversion failed: {e}")
            return network_context  # Return as-is if conversion fails
    
    def _convert_endpoint_to_legacy(self, endpoint: Dict) -> Dict:
        """Convert endpoint format to legacy format"""
        return {
            'id': endpoint.get('id', ''),
            'hostname': endpoint.get('hostname', ''),
            'ip_address': endpoint.get('ip_addresses', [''])[0] if endpoint.get('ip_addresses') else '',
            'platform': endpoint.get('platform', ''),
            'role': endpoint.get('role', ''),
            'services': endpoint.get('services', []),
            'importance': endpoint.get('importance', 'medium')
        }
    
    def _combine_detection_results(self, results: Dict) -> Dict:
        """Combine results from different detection methods"""
        try:
            # Prefer LangChain results if available and successful
            if 'langchain' in results and results['langchain'].get('success'):
                langchain_result = results['langchain']['result']
                
                # Enhance with existing results if available
                if 'existing' in results and results['existing'].get('success'):
                    existing_result = results['existing']['result']
                    
                    # Combine confidence scores
                    langchain_confidence = getattr(langchain_result, 'confidence_score', 0.5)
                    existing_confidence = existing_result.get('combined_confidence', 0.5)
                    
                    combined_confidence = (langchain_confidence * 0.7) + (existing_confidence * 0.3)
                    
                    return {
                        'success': True,
                        'method': 'combined',
                        'threat_detected': getattr(langchain_result, 'threat_detected', False),
                        'confidence_score': combined_confidence,
                        'threat_type': getattr(langchain_result, 'threat_type', 'unknown'),
                        'severity': getattr(langchain_result, 'severity', 'medium'),
                        'langchain_analysis': langchain_result,
                        'existing_analysis': existing_result,
                        'reasoning': getattr(langchain_result, 'reasoning', 'LangChain analysis'),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                
                else:
                    # Only LangChain result available
                    return {
                        'success': True,
                        'method': 'langchain_only',
                        'threat_detected': getattr(langchain_result, 'threat_detected', False),
                        'confidence_score': getattr(langchain_result, 'confidence_score', 0.5),
                        'threat_type': getattr(langchain_result, 'threat_type', 'unknown'),
                        'severity': getattr(langchain_result, 'severity', 'medium'),
                        'analysis': langchain_result,
                        'reasoning': getattr(langchain_result, 'reasoning', 'LangChain analysis'),
                        'timestamp': datetime.utcnow().isoformat()
                    }
            
            # Fallback to existing results
            elif 'existing' in results and results['existing'].get('success'):
                existing_result = results['existing']['result']
                return {
                    'success': True,
                    'method': 'existing_fallback',
                    'threat_detected': existing_result.get('final_threat_detected', False),
                    'confidence_score': existing_result.get('combined_confidence', 0.5),
                    'threat_type': existing_result.get('threat_classification', 'unknown'),
                    'severity': existing_result.get('threat_severity', 'medium'),
                    'analysis': existing_result,
                    'reasoning': existing_result.get('ai_reasoning', 'Existing agent analysis'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            else:
                # Both failed
                return {
                    'success': False,
                    'method': 'all_failed',
                    'langchain_error': results.get('langchain', {}).get('error'),
                    'existing_error': results.get('existing', {}).get('error'),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Result combination failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _select_best_attack_result(self, results: Dict) -> Dict:
        """Select best attack planning result"""
        try:
            # Prefer LangChain results
            if 'langchain' in results and results['langchain'].get('success'):
                return {
                    'success': True,
                    'method': 'langchain_preferred',
                    'scenario': results['langchain']['scenario'],
                    'source': 'langchain_agent'
                }
            
            # Fallback to existing
            elif 'existing' in results and results['existing'].get('success'):
                return {
                    'success': True,
                    'method': 'existing_fallback',
                    'scenario': results['existing']['scenario'],
                    'source': 'existing_orchestrator'
                }
            
            else:
                return {
                    'success': False,
                    'method': 'all_failed',
                    'errors': {
                        'langchain': results.get('langchain', {}).get('error'),
                        'existing': results.get('existing', {}).get('error')
                    }
                }
                
        except Exception as e:
            logger.error(f"Attack result selection failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def execute_attack_unified(self, scenario: Dict, approved: bool = False) -> Dict:
        """Unified attack execution using both systems"""
        try:
            # Determine which system to use for execution
            scenario_source = scenario.get('source', 'unknown')
            
            if scenario_source == 'langchain_agent' or self.routing_preferences['attack'] == 'langchain':
                # Use LangChain execution
                try:
                    result = await self.langchain_attack.execute_approved_scenario(
                        scenario.get('scenario_id', 'unknown'), approved
                    )
                    
                    return {
                        'success': result.get('success', False),
                        'execution_method': 'langchain',
                        'result': result
                    }
                    
                except Exception as e:
                    logger.error(f"LangChain execution failed: {e}")
                    
                    # Fallback to existing system
                    if self.routing_preferences['fallback_enabled']:
                        return await self._execute_with_existing_system(scenario, approved)
                    else:
                        return {'success': False, 'error': str(e)}
            
            else:
                # Use existing execution system
                return await self._execute_with_existing_system(scenario, approved)
                
        except Exception as e:
            logger.error(f"Unified attack execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_with_existing_system(self, scenario: Dict, approved: bool) -> Dict:
        """Execute attack using existing system"""
        try:
            if not approved:
                return {
                    'success': False,
                    'status': 'awaiting_approval',
                    'message': 'Attack requires approval'
                }
            
            # Convert scenario to existing format
            legacy_scenario = self._convert_scenario_to_legacy(scenario)
            
            # Execute using existing orchestrator
            execution_result = await self.existing_attack_orchestrator.execute_dynamic_scenario(legacy_scenario)
            
            return {
                'success': True,
                'execution_method': 'existing_orchestrator',
                'result': execution_result
            }
            
        except Exception as e:
            logger.error(f"Existing system execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _convert_scenario_to_legacy(self, scenario: Dict) -> Any:
        """Convert scenario to legacy format"""
        try:
            # Import legacy scenario class if available
            from .attack_agent.adaptive_attack_orchestrator import AttackScenario
            
            # Convert to legacy format
            legacy_scenario = AttackScenario(
                id=scenario.get('scenario_id', 'unknown'),
                name=scenario.get('name', 'Converted Scenario'),
                description=scenario.get('description', ''),
                attack_type=scenario.get('attack_type', 'general'),
                complexity='intermediate',
                estimated_duration=60,  # Default to 60 minutes
                target_elements=scenario.get('target_agents', []),
                attack_path=[],
                mitre_techniques=scenario.get('mitre_techniques', []),
                success_criteria={},
                risk_level=scenario.get('risk_level', 'medium'),
                prerequisites=[],
                generated_at=datetime.utcnow().isoformat(),
                confidence_score=0.8
            )
            
            return legacy_scenario
            
        except Exception as e:
            logger.error(f"Legacy scenario conversion failed: {e}")
            return scenario  # Return as-is if conversion fails
    
    async def process_log_entry_unified(self, log_entry: Dict) -> Dict:
        """Process ALL log entries through unified detection pipeline"""
        try:
            # Convert log entry to detection data
            detection_data = {
                'type': self._determine_detection_type(log_entry),
                'data': log_entry,
                'timestamp': log_entry.get('timestamp', datetime.utcnow().isoformat())
            }
            
            context = {
                'agent_id': log_entry.get('agent_id'),
                'source': 'log_forwarding',
                'real_time': True,
                'analyze_all_logs': True  # Flag to analyze ALL logs
            }
            
            # Run unified detection on ALL logs (not just suspicious ones)
            result = await self.detect_threat_unified(detection_data, context)
            
            # Store ALL results (threats and benign) for learning
            await self._store_detection_result(result, log_entry)
            
            return result
            
        except Exception as e:
            logger.error(f"Unified log processing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _determine_detection_type(self, log_entry: Dict) -> str:
        """Determine detection type from log entry"""
        event_type = log_entry.get('event_type', '').lower()
        message = log_entry.get('message', '').lower()
        
        if 'process' in event_type or 'process' in message:
            return 'process_anomaly'
        elif 'file' in event_type or 'file' in message:
            return 'file_threat'
        elif 'network' in event_type or 'connection' in message:
            return 'network_anomaly'
        elif 'command' in event_type or 'cmd' in message or 'powershell' in message:
            return 'command_injection'
        else:
            return 'general_anomaly'
    
    async def _store_detection_result(self, result: Dict, log_entry: Dict) -> None:
        """Store ALL detection results (threats and benign) for learning"""
        try:
            # Store ALL results, not just threats
            detection_record = {
                'threat_detected': result.get('threat_detected', False),
                'confidence_score': result.get('confidence_score', 0.0),
                'threat_type': result.get('threat_type', 'benign'),
                'severity': result.get('severity', 'low'),
                'method': result.get('method', 'unified'),
                'analysis': result.get('analysis', {}),
                'reasoning': result.get('reasoning', ''),
                'ml_analysis': result.get('langchain_analysis', {}).get('ml_results', {}) if result.get('langchain_analysis') else {},
                'ai_analysis': result.get('langchain_analysis', {}).get('ai_analysis', {}) if result.get('langchain_analysis') else {},
                'llm_model': 'gpt-3.5-turbo',
                'analyzed_all_logs': True,
                'timestamp': result.get('timestamp', datetime.utcnow().isoformat())
            }
            
            # Store using existing detector
            self.existing_real_detector.store_detection(
                detection_record, 
                log_entry.get('agent_id', 'unknown')
            )
            
            # Log storage for tracking
            if result.get('threat_detected'):
                logger.info(f"Threat result stored: {result.get('threat_type')} (confidence: {result.get('confidence_score')})")
            else:
                logger.debug(f"Benign result stored for log: {log_entry.get('message', '')[:30]}...")
            
        except Exception as e:
            logger.error(f"Detection result storage failed: {e}")
    
    def set_routing_preference(self, component: str, preference: str) -> None:
        """Set routing preference for components"""
        if component in ['detection', 'attack']:
            self.routing_preferences[component] = preference
            logger.info(f"Routing preference set: {component} -> {preference}")
    
    def enable_fallback(self) -> None:
        """Enable fallback to existing systems"""
        self.routing_preferences['fallback_enabled'] = True
        logger.info("Fallback to existing systems enabled")
    
    def disable_fallback(self) -> None:
        """Disable fallback to existing systems"""
        self.routing_preferences['fallback_enabled'] = False
        logger.info("Fallback to existing systems disabled")
    
    def get_bridge_status(self) -> Dict:
        """Get integration bridge status"""
        return {
            'bridge_active': self.bridge_active,
            'routing_preferences': self.routing_preferences,
            'langchain_agents': {
                'detection': 'available',
                'attack': 'available',
                'orchestrator': 'available'
            },
            'existing_agents': {
                'ai_enhanced_detector': 'available',
                'threat_analyzer': 'available', 
                'real_detector': 'available',
                'attack_orchestrator': 'available'
            },
            'last_update': datetime.utcnow().isoformat()
        }


# Global integration bridge instance
integration_bridge = AgentIntegrationBridge()
