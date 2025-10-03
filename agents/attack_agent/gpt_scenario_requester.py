"""
GPT-Powered Attack Scenario Requester
Allows users to request custom attack scenarios from GPT and execute them
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class GPTScenarioRequester:
    """GPT-powered attack scenario requester for custom scenarios"""
    
    def __init__(self, llm):
        self.llm = llm
        self.request_history = []
        
    async def request_custom_scenario(self, 
                                    user_request: str,
                                    network_context: Dict = None,
                                    constraints: Dict = None) -> Dict[str, Any]:
        """
        Request a custom attack scenario from GPT based on user input
        
        Args:
            user_request: User's natural language request for attack scenario
            network_context: Current network context
            constraints: Attack constraints
            
        Returns:
            GPT-generated custom attack scenario
        """
        try:
            # Build comprehensive request context
            request_context = self._build_request_context(user_request, network_context, constraints)
            
            # Generate custom scenario using GPT
            custom_scenario = await self._generate_custom_scenario_with_gpt(request_context)
            
            # Validate and enhance scenario
            validated_scenario = await self._validate_and_enhance_custom_scenario(custom_scenario, request_context)
            
            # Store in history
            self.request_history.append({
                'timestamp': datetime.utcnow(),
                'user_request': user_request,
                'scenario': validated_scenario,
                'context': request_context
            })
            
            logger.info(f"Generated custom GPT scenario: {validated_scenario.get('name', 'Unknown')}")
            
            return validated_scenario
            
        except Exception as e:
            logger.error(f"Custom scenario request failed: {e}")
            return self._get_error_scenario(user_request, str(e))
    
    def _build_request_context(self, user_request: str, network_context: Dict, constraints: Dict) -> Dict:
        """Build context for GPT scenario generation"""
        
        return {
            'user_request': user_request,
            'network_context': network_context or {},
            'constraints': constraints or {},
            'request_timestamp': datetime.utcnow().isoformat(),
            'available_techniques': [
                'Network Discovery', 'Service Enumeration', 'Vulnerability Scanning',
                'Brute Force Attacks', 'Privilege Escalation', 'Data Exfiltration',
                'Persistence Installation', 'Lateral Movement', 'Defense Evasion',
                'Command and Control', 'Credential Access', 'Discovery'
            ],
            'mitre_techniques': [
                'T1018', 'T1021', 'T1046', 'T1059.001', 'T1059.004', 'T1055',
                'T1005', 'T1041', 'T1053', 'T1021', 'T1071', 'T1003'
            ]
        }
    
    async def _generate_custom_scenario_with_gpt(self, context: Dict) -> Dict[str, Any]:
        """Generate custom scenario using GPT"""
        
        # Create comprehensive GPT prompt
        prompt = f"""
You are an expert red team operator and attack scenario planner. A user has requested a custom attack scenario with the following details:

USER REQUEST: "{context['user_request']}"
NETWORK CONTEXT: {json.dumps(context['network_context'], indent=2)}
CONSTRAINTS: {json.dumps(context['constraints'], indent=2)}
AVAILABLE TECHNIQUES: {context['available_techniques']}
MITRE TECHNIQUES: {context['mitre_techniques']}

Generate a comprehensive, realistic attack scenario that fulfills the user's request. The scenario should be:

1. **Customized to the request**: Directly address what the user asked for
2. **Technically sound**: Use real, executable techniques and tools
3. **Contextually appropriate**: Consider the network environment
4. **Realistic and executable**: All techniques should be feasible
5. **Well-structured**: Include proper attack phases and sequencing
6. **MITRE ATT&CK compliant**: Map to proper MITRE techniques
7. **Safe and controlled**: Include safety measures and constraints

Return a JSON structure with this format:
{{
    "scenario_id": "custom_scenario_YYYYMMDD_HHMMSS",
    "name": "Descriptive scenario name based on user request",
    "description": "Detailed scenario description",
    "objective": "Clear attack objective from user request",
    "attack_type": "primary_attack_type",
    "target_agents": ["list", "of", "target", "agents"],
    "mitre_techniques": ["T1018", "T1021", "T1059.001"],
    "attack_phases": [
        {{
            "phase": "Phase Name",
            "duration": "X minutes",
            "description": "What this phase accomplishes",
            "mitre_id": "T1018",
            "techniques": ["Specific techniques used"],
            "tools": ["nmap", "PowerShell", "custom_scripts"],
            "expected_output": "What to expect from this phase",
            "success_criteria": ["How to measure success"],
            "safety_measures": ["Safety precautions"]
        }}
    ],
    "estimated_duration": "Total time estimate",
    "difficulty": "beginner|intermediate|advanced|expert",
    "stealth_level": "low|medium|high|maximum",
    "destructive": true/false,
    "detection_risk": "low|medium|high",
    "success_probability": 0.0-1.0,
    "prerequisites": ["Required conditions"],
    "success_criteria": ["Overall success metrics"],
    "cleanup_required": true/false,
    "monitoring_points": ["What to monitor"],
    "custom_notes": "Any special considerations for this scenario"
}}

Focus on creating a scenario that:
- Directly fulfills the user's request
- Is technically feasible and executable
- Considers the network context
- Includes proper safety measures
- Is well-documented and clear
- Uses realistic tools and techniques
"""

        try:
            # Use GPT to generate custom scenario
            response = await self.llm.ainvoke(prompt)
            
            # Parse GPT response
            custom_scenario = self._parse_gpt_scenario_response(response.content)
            
            return custom_scenario
            
        except Exception as e:
            logger.error(f"GPT scenario generation failed: {e}")
            return {}
    
    def _parse_gpt_scenario_response(self, response: str) -> Dict[str, Any]:
        """Parse GPT response and extract scenario"""
        try:
            # Try to extract JSON from response
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                scenario = json.loads(json_str)
                return scenario
            else:
                # If no JSON found, try to parse as text
                return self._parse_text_scenario_response(response)
                
        except Exception as e:
            logger.error(f"Failed to parse GPT scenario response: {e}")
            return {}
    
    def _parse_text_scenario_response(self, response: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        scenario = {
            'scenario_id': f"custom_scenario_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'name': 'GPT-Generated Custom Scenario',
            'description': 'Custom attack scenario generated by GPT',
            'objective': 'User-requested objective',
            'attack_type': 'custom',
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
            'monitoring_points': [],
            'custom_notes': 'Generated by GPT based on user request'
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
    
    async def _validate_and_enhance_custom_scenario(self, scenario: Dict[str, Any], context: Dict) -> Dict[str, Any]:
        """Validate and enhance GPT-generated scenario"""
        
        # Ensure required fields
        enhanced_scenario = {
            'scenario_id': scenario.get('scenario_id', f"custom_scenario_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
            'name': scenario.get('name', 'GPT-Generated Custom Scenario'),
            'description': scenario.get('description', 'Custom attack scenario generated by GPT'),
            'objective': scenario.get('objective', context['user_request']),
            'attack_type': scenario.get('attack_type', 'custom'),
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
            'custom_notes': scenario.get('custom_notes', 'Generated by GPT based on user request'),
            'gpt_generated': True,
            'user_request': context['user_request'],
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
        
        # Add user request context
        scenario['original_request'] = context['user_request']
        scenario['request_timestamp'] = context['request_timestamp']
        
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
    
    def _validate_attack_phases(self, phases: List[Dict]) -> List[Dict]:
        """Validate attack phases"""
        validated_phases = []
        
        for phase in phases:
            if isinstance(phase, dict) and 'phase' in phase:
                validated_phases.append(phase)
        
        return validated_phases
    
    def _get_error_scenario(self, user_request: str, error: str) -> Dict[str, Any]:
        """Error scenario when generation fails"""
        
        return {
            'scenario_id': f"error_scenario_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'name': f'Error: {user_request}',
            'description': f'Failed to generate scenario for: {user_request}',
            'objective': user_request,
            'attack_type': 'error',
            'target_agents': [],
            'mitre_techniques': [],
            'attack_phases': [],
            'estimated_duration': '0 minutes',
            'difficulty': 'unknown',
            'stealth_level': 'unknown',
            'destructive': False,
            'detection_risk': 'unknown',
            'success_probability': 0.0,
            'prerequisites': [],
            'success_criteria': [],
            'cleanup_required': False,
            'monitoring_points': [],
            'custom_notes': f'Error: {error}',
            'gpt_generated': False,
            'error': True,
            'error_message': error
        }
    
    async def get_scenario_suggestions(self, network_context: Dict = None) -> List[str]:
        """Get GPT-generated scenario suggestions based on network context"""
        
        try:
            prompt = f"""
Based on this network context, suggest 5 interesting attack scenarios:

NETWORK CONTEXT: {json.dumps(network_context or {}, indent=2)}

Suggest 5 creative, realistic attack scenarios that would be interesting to test. Each suggestion should be:
1. Technically feasible
2. Educational and informative
3. Safe to execute
4. Relevant to the network context
5. Creative and engaging

Return as a JSON array of scenario suggestions:
[
    "Scenario 1: [Brief description]",
    "Scenario 2: [Brief description]",
    "Scenario 3: [Brief description]",
    "Scenario 4: [Brief description]",
    "Scenario 5: [Brief description]"
]
"""

            response = await self.llm.ainvoke(prompt)
            
            # Parse suggestions
            suggestions = self._parse_suggestions_response(response.content)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Scenario suggestions failed: {e}")
            return [
                "Network reconnaissance and service enumeration",
                "Privilege escalation simulation",
                "Data exfiltration testing",
                "Persistence mechanism installation",
                "Defense evasion techniques"
            ]
    
    def _parse_suggestions_response(self, response: str) -> List[str]:
        """Parse GPT suggestions response"""
        try:
            import re
            
            # Look for JSON array in response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                suggestions = json.loads(json_str)
                return suggestions
            else:
                # Fallback to text parsing
                lines = response.split('\n')
                suggestions = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('*'):
                        suggestions.append(line)
                return suggestions[:5]  # Limit to 5 suggestions
                
        except Exception as e:
            logger.error(f"Failed to parse suggestions: {e}")
            return [
                "Network reconnaissance and service enumeration",
                "Privilege escalation simulation", 
                "Data exfiltration testing",
                "Persistence mechanism installation",
                "Defense evasion techniques"
            ]


# Integration function for easy use
async def request_gpt_scenario(user_request: str, 
                              network_context: Dict = None, 
                              constraints: Dict = None, 
                              llm = None) -> Dict[str, Any]:
    """
    Request a custom attack scenario from GPT
    
    Args:
        user_request: Natural language request for attack scenario
        network_context: Network context information
        constraints: Attack constraints
        llm: Language model instance
        
    Returns:
        GPT-generated custom attack scenario
    """
    if not llm:
        # Use default LLM if none provided
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)
    
    requester = GPTScenarioRequester(llm)
    return await requester.request_custom_scenario(user_request, network_context, constraints)


# Example usage function
async def example_gpt_scenario_requests():
    """Example of how to request custom scenarios from GPT"""
    
    # Initialize GPT requester
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)
    requester = GPTScenarioRequester(llm)
    
    # Example 1: Simple request
    scenario1 = await requester.request_custom_scenario(
        "I want to test if I can steal data from the finance department without being detected"
    )
    
    # Example 2: Complex request with context
    scenario2 = await requester.request_custom_scenario(
        "Create an APT simulation that targets the CEO's computer and exfiltrates sensitive documents",
        network_context={
            "hosts": ["10.0.1.100", "10.0.1.101"],
            "services": ["RDP", "SSH", "HTTP"],
            "vulnerabilities": ["Weak passwords", "Outdated software"]
        },
        constraints={
            "destructive": False,
            "stealth": True,
            "time_limit": 3600
        }
    )
    
    # Example 3: Get suggestions
    suggestions = await requester.get_scenario_suggestions({
        "hosts": ["192.168.1.100", "192.168.1.101"],
        "services": ["SSH", "HTTP", "MySQL"]
    })
    
    return {
        "scenario1": scenario1,
        "scenario2": scenario2,
        "suggestions": suggestions
    }
