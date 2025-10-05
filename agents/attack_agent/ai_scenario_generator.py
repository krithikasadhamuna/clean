"""
AI-Powered Dynamic Attack Scenario Generation
Generates attack scenarios dynamically using LLM based on network context and objectives
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class AIScenarioGenerator:
    """AI-powered dynamic attack scenario generation"""
    
    def __init__(self, llm):
        self.llm = llm
        self.scenario_history = []
        
    async def generate_dynamic_scenario(self, 
                                       objective: str,
                                       network_context: Dict,
                                       constraints: Dict = None) -> Dict[str, Any]:
        """
        Generate attack scenario dynamically using AI
        
        Args:
            objective: Attack objective/goal
            network_context: Network topology and target information
            constraints: Attack constraints and limitations
            
        Returns:
            Dynamically generated attack scenario
        """
        try:
            # Build comprehensive context
            context = self._build_scenario_context(objective, network_context, constraints)
            
            # Generate scenario using AI
            ai_scenario = await self._generate_scenario_with_ai(context)
            
            # Validate and enhance scenario
            validated_scenario = await self._validate_and_enhance_scenario(ai_scenario, context)
            
            # Store in history for learning
            self.scenario_history.append({
                'timestamp': datetime.utcnow(),
                'objective': objective,
                'scenario': validated_scenario,
                'context': context
            })
            
            logger.info(f"Generated AI-powered attack scenario: {validated_scenario.get('name', 'Unknown')}")
            
            return validated_scenario
            
        except Exception as e:
            logger.error(f"AI scenario generation failed: {e}")
            # NO FALLBACK - This is a 100% AI-driven SOC platform
            raise ValueError(
                f"AI scenario generation failed: {e}. "
                "This SOC platform requires AI functionality. "
                "Please check OPENAI_API_KEY environment variable and API connectivity."
            )
    
    def _build_scenario_context(self, objective: str, network_context: Dict, constraints: Dict) -> Dict:
        """Build comprehensive context for AI scenario generation"""
        
        context = {
            'objective': objective,
            'network_context': network_context,
            'constraints': constraints or {},
            'target_analysis': {
                'hosts': network_context.get('hosts', []),
                'services': network_context.get('services', []),
                'vulnerabilities': network_context.get('vulnerabilities', []),
                'defenses': network_context.get('defenses', []),
                'network_segments': network_context.get('network_segments', [])
            },
            'attack_environment': {
                'time_of_day': datetime.utcnow().hour,
                'day_of_week': datetime.utcnow().weekday(),
                'network_size': len(network_context.get('hosts', [])),
                'complexity': self._assess_network_complexity(network_context)
            },
            'historical_data': {
                'previous_attacks': network_context.get('attack_history', []),
                'detection_events': network_context.get('detection_events', []),
                'security_incidents': network_context.get('security_incidents', [])
            }
        }
        
        return context
    
    def _assess_network_complexity(self, network_context: Dict) -> str:
        """Assess network complexity for scenario planning"""
        hosts = network_context.get('hosts', [])
        services = network_context.get('services', [])
        
        if len(hosts) > 100:
            return 'enterprise'
        elif len(hosts) > 20:
            return 'medium'
        else:
            return 'small'
    
    async def _generate_scenario_with_ai(self, context: Dict) -> Dict[str, Any]:
        """Generate scenario using AI LLM"""
        
        # Create comprehensive AI prompt
        prompt = f"""
You are an expert red team operator and attack scenario planner. Generate a comprehensive, realistic attack scenario based on the following context:

OBJECTIVE: {context['objective']}
NETWORK CONTEXT: {json.dumps(context['network_context'], indent=2)}
TARGET ANALYSIS: {json.dumps(context['target_analysis'], indent=2)}
ATTACK ENVIRONMENT: {json.dumps(context['attack_environment'], indent=2)}
CONSTRAINTS: {json.dumps(context['constraints'], indent=2)}
HISTORICAL DATA: {json.dumps(context['historical_data'], indent=2)}

Generate a realistic, executable attack scenario that:

1. **Aligns with the objective**: The scenario should directly support achieving the stated objective
2. **Is contextually appropriate**: Uses techniques appropriate for the network environment
3. **Is realistic and executable**: All techniques should be technically feasible
4. **Considers constraints**: Respects any limitations (time, resources, stealth, etc.)
5. **Uses MITRE ATT&CK framework**: Maps techniques to proper MITRE ATT&CK techniques
6. **Is adaptive**: Considers the network complexity and environment
7. **Includes proper sequencing**: Attack phases should be logically ordered
8. **Has realistic timing**: Phase durations should be realistic
9. **Considers detection**: Includes stealth and evasion considerations
10. **Is comprehensive**: Covers reconnaissance, initial access, execution, persistence, etc.

Return a JSON structure with this EXACT format:
{{
    "scenario_id": "unique_scenario_id",
    "name": "Descriptive scenario name",
    "description": "Detailed scenario description",
    "objective": "Clear attack objective",
    "attack_type": "primary_attack_type",
    "target_agents": ["list", "of", "target", "agents"],
    "mitre_techniques": ["T1018", "T1021", "T1059.001"],
    "attack_phases": [
        {{
            "phase": "Reconnaissance",
            "duration": "10 minutes",
            "description": "Network discovery and enumeration",
            "mitre_id": "T1018",
            "techniques": ["Network scanning", "Service enumeration"],
            "tools": ["nmap", "nslookup"],
            "expected_output": "Network topology map"
        }},
        {{
            "phase": "Initial Access",
            "duration": "15 minutes",
            "description": "Gaining initial access to target systems",
            "mitre_id": "T1078",
            "techniques": ["Valid accounts", "Default accounts"],
            "tools": ["hydra", "medusa"],
            "expected_output": "Successful authentication"
        }}
    ],
    "estimated_duration": "45 minutes",
    "difficulty": "intermediate",
    "stealth_level": "medium",
    "destructive": false,
    "detection_risk": "medium",
    "success_probability": 0.75,
    "prerequisites": ["Network access", "Target enumeration"],
    "success_criteria": ["Successful network access", "Data exfiltration"],
    "cleanup_required": true,
    "monitoring_points": ["Network traffic", "System logs", "User activity"]
}}

Focus on creating a scenario that is:
- Technically sound and executable
- Contextually appropriate for the network
- Realistic in terms of timing and complexity
- Properly sequenced with logical attack flow
- Stealthy and evasive if required
- Non-destructive if specified
- Comprehensive in coverage

CRITICAL: The attack_phases must be an array of objects (dictionaries), NOT strings. Each phase must have the structure shown in the example above with phase, duration, description, mitre_id, techniques, tools, and expected_output fields.
"""

        try:
            # Use LLM to generate scenario
            response = await self.llm.ainvoke(prompt)
            
            # Debug: Log the raw response
            logger.info(f"Raw AI response: {response.content[:500]}...")
            
            # Parse AI response
            ai_scenario = self._parse_ai_scenario_response(response.content)
            
            # Debug: Log the parsed scenario
            logger.info(f"Parsed scenario attack_phases: {ai_scenario.get('attack_phases', [])}")
            
            return ai_scenario
            
        except Exception as e:
            logger.error(f"AI scenario generation failed: {e}")
            return {}
    
    def _parse_ai_scenario_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and extract scenario"""
        try:
            # Try to extract JSON from response
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                logger.info(f"Extracted JSON: {json_str[:200]}...")
                scenario = json.loads(json_str)
                logger.info(f"Parsed scenario keys: {list(scenario.keys())}")
                return scenario
            else:
                # If no JSON found, try to parse as text
                logger.warning("No JSON found in response, using text parser")
                return self._parse_text_scenario_response(response)
                
        except Exception as e:
            logger.error(f"Failed to parse AI scenario response: {e}")
            return {}
    
    def _parse_text_scenario_response(self, response: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        scenario = {
            'scenario_id': f"ai_scenario_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'name': 'AI-Generated Attack Scenario',
            'description': 'Dynamically generated attack scenario',
            'attack_type': 'general_assessment',
            'target_agents': [],
            'mitre_techniques': [],
            'attack_phases': [],
            'estimated_duration': '30 minutes',
            'difficulty': 'intermediate',
            'stealth_level': 'medium',
            'destructive': False,
            'detection_risk': 'medium',
            'success_probability': 0.7,
            'prerequisites': [],
            'success_criteria': [],
            'cleanup_required': True,
            'monitoring_points': []
        }
        
        # Try to extract information from text
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Name:') or line.startswith('Scenario:'):
                scenario['name'] = line.split(':', 1)[1].strip()
            elif line.startswith('Description:'):
                scenario['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('Duration:'):
                scenario['estimated_duration'] = line.split(':', 1)[1].strip()
        
        return scenario
    
    async def _validate_and_enhance_scenario(self, scenario: Dict[str, Any], context: Dict) -> Dict[str, Any]:
        """Validate and enhance AI-generated scenario"""
        
        # Ensure required fields
        enhanced_scenario = {
            'scenario_id': scenario.get('scenario_id', f"ai_scenario_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
            'name': scenario.get('name', 'AI-Generated Attack Scenario'),
            'description': scenario.get('description', 'Dynamically generated attack scenario'),
            'objective': scenario.get('objective', context['objective']),
            'attack_type': scenario.get('attack_type', 'general_assessment'),
            'target_agents': scenario.get('target_agents', []),
            'mitre_techniques': scenario.get('mitre_techniques', []),
            'attack_phases': scenario.get('attack_phases', []),
            'estimated_duration': scenario.get('estimated_duration', '30 minutes'),
            'difficulty': scenario.get('difficulty', 'intermediate'),
            'stealth_level': scenario.get('stealth_level', 'medium'),
            'destructive': scenario.get('destructive', False),
            'detection_risk': scenario.get('detection_risk', 'medium'),
            'success_probability': scenario.get('success_probability', 0.7),
            'prerequisites': scenario.get('prerequisites', []),
            'success_criteria': scenario.get('success_criteria', []),
            'cleanup_required': scenario.get('cleanup_required', True),
            'monitoring_points': scenario.get('monitoring_points', []),
            'ai_generated': True,
            'generated_at': datetime.utcnow().isoformat(),
            'context_used': context
        }
        
        # Enhance with network context
        enhanced_scenario = self._enhance_with_network_context(enhanced_scenario, context)
        
        # Validate MITRE techniques
        enhanced_scenario['mitre_techniques'] = self._validate_mitre_techniques(enhanced_scenario['mitre_techniques'])
        
        # Validate attack phases
        enhanced_scenario['attack_phases'] = self._validate_attack_phases(enhanced_scenario['attack_phases'])
        
        return enhanced_scenario
    
    def _enhance_with_network_context(self, scenario: Dict, context: Dict) -> Dict:
        """Enhance scenario with network context information"""
        
        # Add network-specific details
        if context['network_context'].get('hosts'):
            scenario['target_hosts'] = context['network_context']['hosts']
        
        if context['network_context'].get('services'):
            scenario['target_services'] = context['network_context']['services']
        
        if context['network_context'].get('vulnerabilities'):
            scenario['known_vulnerabilities'] = context['network_context']['vulnerabilities']
        
        # Add complexity assessment
        scenario['network_complexity'] = context['attack_environment']['complexity']
        
        # Add timing considerations
        scenario['time_context'] = {
            'generated_at': datetime.utcnow().isoformat(),
            'time_of_day': context['attack_environment']['time_of_day'],
            'day_of_week': context['attack_environment']['day_of_week']
        }
        
        return scenario
    
    def _validate_mitre_techniques(self, techniques: List[str]) -> List[str]:
        """Validate MITRE ATT&CK techniques"""
        valid_techniques = []
        
        for technique in techniques:
            if technique.startswith('T') and '.' in technique:
                valid_techniques.append(technique)
            elif technique.startswith('T') and len(technique) == 5:
                valid_techniques.append(technique)
        
        return valid_techniques
    
    def _validate_attack_phases(self, phases: List) -> List[Dict]:
        """Validate attack phases - convert strings to proper format if needed"""
        validated_phases = []
        
        for phase in phases:
            if isinstance(phase, dict) and 'phase' in phase:
                validated_phases.append(phase)
            elif isinstance(phase, str):
                # Convert string to proper phase format
                validated_phases.append({
                    'phase': phase,
                    'duration': '10 minutes',
                    'description': f'{phase} phase of the attack',
                    'mitre_id': 'T1082',
                    'techniques': [phase],
                    'tools': ['nmap', 'netstat'],
                    'expected_output': f'{phase} completed'
                })
        
        return validated_phases
    
    # REMOVED: _get_fallback_scenario()
    # This SOC platform is 100% AI-driven - no hardcoded fallbacks
    
    async def learn_from_scenario_execution(self, scenario_id: str, execution_result: Dict):
        """Learn from scenario execution to improve future generation"""
        try:
            # Store execution results for learning
            learning_data = {
                'scenario_id': scenario_id,
                'execution_result': execution_result,
                'timestamp': datetime.utcnow(),
                'success': execution_result.get('success', False),
                'effectiveness': execution_result.get('effectiveness', 0.0),
                'detection_events': execution_result.get('detection_events', []),
                'lessons_learned': execution_result.get('lessons_learned', [])
            }
            
            # Add to learning history
            self.scenario_history.append(learning_data)
            
            # Analyze patterns for improvement
            await self._analyze_scenario_patterns()
            
        except Exception as e:
            logger.error(f"Learning from scenario execution failed: {e}")
    
    async def _analyze_scenario_patterns(self):
        """Analyze scenario patterns to improve future generation"""
        try:
            # Analyze success/failure patterns
            successful_scenarios = [s for s in self.scenario_history if s.get('success', False)]
            failed_scenarios = [s for s in self.scenario_history if not s.get('success', False)]
            
            # Extract patterns
            success_patterns = self._extract_scenario_patterns(successful_scenarios)
            failure_patterns = self._extract_scenario_patterns(failed_scenarios)
            
            # Store patterns for future use
            self.success_patterns = success_patterns
            self.failure_patterns = failure_patterns
            
            logger.info(f"Analyzed {len(successful_scenarios)} successful and {len(failed_scenarios)} failed scenarios")
            
        except Exception as e:
            logger.error(f"Scenario pattern analysis failed: {e}")
    
    def _extract_scenario_patterns(self, scenarios: List[Dict]) -> Dict:
        """Extract patterns from scenario execution history"""
        patterns = {
            'common_techniques': {},
            'effective_phases': {},
            'detection_events': {},
            'success_factors': {}
        }
        
        for scenario in scenarios:
            # Extract technique patterns
            techniques = scenario.get('mitre_techniques', [])
            for technique in techniques:
                patterns['common_techniques'][technique] = patterns['common_techniques'].get(technique, 0) + 1
            
            # Extract phase patterns
            phases = scenario.get('attack_phases', [])
            for phase in phases:
                phase_name = phase.get('phase', 'unknown')
                patterns['effective_phases'][phase_name] = patterns['effective_phases'].get(phase_name, 0) + 1
            
            # Extract detection patterns
            detection_events = scenario.get('detection_events', [])
            for event in detection_events:
                event_type = event.get('type', 'unknown')
                patterns['detection_events'][event_type] = patterns['detection_events'].get(event_type, 0) + 1
        
        return patterns


# Integration function for existing attack agent
async def generate_ai_scenario(objective: str, network_context: Dict, 
                             constraints: Dict = None, llm = None) -> Dict[str, Any]:
    """
    Generate AI-powered attack scenario
    
    Args:
        objective: Attack objective
        network_context: Network context
        constraints: Attack constraints
        llm: Language model instance
        
    Returns:
        AI-generated attack scenario
    """
    if not llm:
        # Use default LLM if none provided
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)
    
    generator = AIScenarioGenerator(llm)
    return await generator.generate_dynamic_scenario(objective, network_context, constraints)
