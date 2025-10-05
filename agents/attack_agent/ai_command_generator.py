"""
AI-Powered Dynamic Command Generation
Generates attack commands dynamically using LLM instead of hardcoded templates
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import time

logger = logging.getLogger(__name__)


class AICommandGenerator:
    """AI-powered dynamic command generation for attack scenarios"""
    
    def __init__(self, llm):
        self.llm = llm
        self.command_history = []
        
    async def generate_dynamic_attack_commands(self, 
                                             attack_type: str, 
                                             platform: str, 
                                             scenario: Dict,
                                             network_context: Dict = None) -> Dict[str, Dict]:
        """
        Generate attack commands dynamically using AI based on context
        
        Args:
            attack_type: Type of attack (network_intrusion, system_compromise, etc.)
            platform: Target platform (windows, linux, macos)
            scenario: Attack scenario details
            network_context: Network topology and target information
            
        Returns:
            Dictionary of dynamically generated attack commands
        """
        try:
            # Build context for AI
            context = self._build_attack_context(attack_type, platform, scenario, network_context)
            
            # Generate commands using AI
            ai_commands = await self._generate_commands_with_ai(context)
            
            # Validate and enhance commands
            validated_commands = await self._validate_and_enhance_commands(ai_commands, platform)
            
            # Store in history for learning
            self.command_history.append({
                'timestamp': datetime.utcnow(),
                'attack_type': attack_type,
                'platform': platform,
                'commands': validated_commands,
                'context': context
            })
            
            logger.info(f"Generated {len(validated_commands)} AI-powered attack commands for {attack_type} on {platform}")
            
            return validated_commands
            
        except Exception as e:
            logger.error(f"AI command generation failed: {e}")
            
            # Log failure
            try:
                from agents.gpt_interaction_logger import gpt_logger
                await gpt_logger.log_failure(
                    interaction_type="command_generation",
                    prompt="Command generation request",
                    error_message=str(e),
                    response_time_ms=0,
                    user_request=f"{attack_type} on {platform}",
                    component="ai_command_generator"
                )
            except:
                pass
            
            # NO FALLBACK - This is a 100% AI-driven SOC platform
            raise ValueError(
                f"AI command generation failed: {e}. "
                "This SOC platform requires AI functionality. "
                "Please check OPENAI_API_KEY environment variable and API connectivity."
            )
    
    def _build_attack_context(self, attack_type: str, platform: str, scenario: Dict, network_context: Dict) -> Dict:
        """Build comprehensive context for AI command generation"""
        
        # Ensure network_context is not None
        if network_context is None:
            network_context = {}
        
        # Ensure scenario is not None
        if scenario is None:
            scenario = {}
        
        context = {
            'attack_type': attack_type,
            'platform': platform,
            'scenario': scenario,
            'network_context': network_context,
            'target_info': {
                'os': platform,
                'network_segment': network_context.get('network_segment', 'unknown'),
                'services': network_context.get('services', []),
                'vulnerabilities': network_context.get('vulnerabilities', []),
                'defenses': network_context.get('defenses', [])
            },
            'constraints': {
                'destructive': scenario.get('destructive', False),
                'stealth': scenario.get('stealth', True),
                'time_limit': scenario.get('time_limit', 300),
                'detection_avoidance': scenario.get('detection_avoidance', True)
            },
            'mitre_techniques': scenario.get('mitre_techniques', []),
            'attack_phases': scenario.get('attack_phases', [])
        }
        
        return context
    
    async def _generate_commands_with_ai(self, context: Dict) -> Dict[str, Dict]:
        """Generate commands using AI LLM"""
        
        # Create AI prompt for command generation
        prompt = f"""
You are an expert red team operator. Generate REAL, executable attack commands based on the following context:

ATTACK TYPE: {context['attack_type']}
TARGET PLATFORM: {context['platform']}
NETWORK CONTEXT: {json.dumps(context['network_context'], indent=2)}
TARGET INFO: {json.dumps(context['target_info'], indent=2)}
CONSTRAINTS: {json.dumps(context['constraints'], indent=2)}
MITRE TECHNIQUES: {context['mitre_techniques']}
ATTACK PHASES: {context['attack_phases']}

Generate REAL, executable commands that:
1. Are appropriate for the target platform ({context['platform']})
2. Match the attack type ({context['attack_type']})
3. Respect the constraints (destructive: {context['constraints']['destructive']}, stealth: {context['constraints']['stealth']})
4. Use actual tools and techniques (nmap, PowerShell, bash, etc.)
5. Are contextually appropriate for the network environment
6. Include proper error handling and logging

Return a JSON structure with this format:
{{
    "technique_id": {{
        "technique": "Human readable technique name",
        "script": "Actual executable command/script",
        "description": "What this command does",
        "mitre_technique": "MITRE ATT&CK technique ID",
        "destructive": true/false,
        "real_attack": true,
        "platform": "{context['platform']}",
        "dependencies": ["required tools"],
        "expected_output": "What output to expect",
        "error_handling": "How to handle errors"
    }}
}}

Focus on generating commands that are:
- Contextually relevant to the network environment
- Platform-appropriate
- Realistic and executable
- Stealthy if required
- Non-destructive if specified
"""

        try:
            from agents.gpt_interaction_logger import gpt_logger
            
            start_time = time.time()
            
            # Use LLM to generate commands
            response = await self.llm.ainvoke(prompt)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse AI response
            ai_commands = self._parse_ai_response(response.content)
            
            # Log success
            await gpt_logger.log_success(
                interaction_type="command_generation",
                prompt=prompt,
                response=response.content,
                response_time_ms=response_time_ms,
                user_request=f"{context['attack_type']} on {context['platform']}",
                result_summary=f"Generated {len(ai_commands)} commands",
                component="ai_command_generator",
                tokens_used=2000
            )
            
            return ai_commands
            
        except Exception as e:
            logger.error(f"AI command generation failed: {e}")
            return {}
    
    def _parse_ai_response(self, response: str) -> Dict[str, Dict]:
        """Parse AI response and extract commands"""
        try:
            # Try to extract JSON from response
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                commands = json.loads(json_str)
                return commands
            else:
                # If no JSON found, try to parse as text
                return self._parse_text_response(response)
                
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {}
    
    def _parse_text_response(self, response: str) -> Dict[str, Dict]:
        """Parse text response when JSON parsing fails"""
        commands = {}
        lines = response.split('\n')
        current_technique = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('T') and '.' in line:  # MITRE technique
                current_technique = line
                commands[current_technique] = {
                    'technique': line,
                    'script': '',
                    'description': '',
                    'mitre_technique': line,
                    'destructive': True,
                    'real_attack': True,
                    'platform': 'unknown'
                }
            elif line.startswith('Script:') and current_technique:
                commands[current_technique]['script'] = line.replace('Script:', '').strip()
            elif line.startswith('Description:') and current_technique:
                commands[current_technique]['description'] = line.replace('Description:', '').strip()
        
        return commands
    
    async def _validate_and_enhance_commands(self, commands: Dict[str, Dict], platform: str) -> Dict[str, Dict]:
        """Validate and enhance AI-generated commands"""
        enhanced_commands = {}
        
        for technique_id, command in commands.items():
            try:
                # Validate command structure
                if not command.get('script'):
                    logger.warning(f"No script found for technique {technique_id}")
                    continue
                
                # Enhance with platform-specific details
                enhanced_command = {
                    'technique': command.get('technique', technique_id),
                    'script': command.get('script', ''),
                    'description': command.get('description', 'AI-generated attack command'),
                    'mitre_technique': command.get('mitre_technique', technique_id),
                    'destructive': command.get('destructive', True),
                    'real_attack': True,
                    'platform': platform,
                    'dependencies': command.get('dependencies', []),
                    'expected_output': command.get('expected_output', ''),
                    'error_handling': command.get('error_handling', ''),
                    'ai_generated': True,
                    'generated_at': datetime.utcnow().isoformat()
                }
                
                # Add platform-specific enhancements
                enhanced_command = self._enhance_for_platform(enhanced_command, platform)
                
                enhanced_commands[technique_id] = enhanced_command
                
            except Exception as e:
                logger.error(f"Failed to enhance command {technique_id}: {e}")
                continue
        
        return enhanced_commands
    
    def _enhance_for_platform(self, command: Dict, platform: str) -> Dict:
        """Enhance command for specific platform"""
        
        if platform.lower() == 'windows':
            # Add PowerShell-specific enhancements
            if 'powershell' in command['script'].lower():
                command['execution_policy'] = 'bypass'
                command['output_format'] = 'json'
            
            # Add Windows-specific error handling
            command['error_handling'] += '; if ($LASTEXITCODE -ne 0) { Write-Error "Command failed" }'
            
        elif platform.lower() == 'linux':
            # Add bash-specific enhancements
            if 'bash' in command['script'].lower() or command['script'].startswith('#'):
                command['shell'] = '/bin/bash'
                command['error_handling'] += '; if [ $? -ne 0 ]; then echo "Command failed"; fi'
        
        return command
    
    # REMOVED: _get_fallback_commands() 
    # This SOC platform is 100% AI-driven - no hardcoded fallbacks
    
    async def learn_from_execution(self, command_id: str, execution_result: Dict):
        """Learn from command execution results to improve future generation"""
        try:
            # Store execution results for learning
            learning_data = {
                'command_id': command_id,
                'execution_result': execution_result,
                'timestamp': datetime.utcnow(),
                'success': execution_result.get('success', False),
                'output': execution_result.get('output', ''),
                'error': execution_result.get('error', '')
            }
            
            # Add to learning history
            self.command_history.append(learning_data)
            
            # Analyze patterns for improvement
            await self._analyze_execution_patterns()
            
        except Exception as e:
            logger.error(f"Learning from execution failed: {e}")
    
    async def _analyze_execution_patterns(self):
        """Analyze execution patterns to improve command generation"""
        try:
            # Analyze success/failure patterns
            successful_commands = [cmd for cmd in self.command_history if cmd.get('success', False)]
            failed_commands = [cmd for cmd in self.command_history if not cmd.get('success', False)]
            
            # Extract patterns
            success_patterns = self._extract_patterns(successful_commands)
            failure_patterns = self._extract_patterns(failed_commands)
            
            # Store patterns for future use
            self.success_patterns = success_patterns
            self.failure_patterns = failure_patterns
            
            logger.info(f"Analyzed {len(successful_commands)} successful and {len(failed_commands)} failed commands")
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
    
    def _extract_patterns(self, commands: List[Dict]) -> Dict:
        """Extract patterns from command execution history"""
        patterns = {
            'common_techniques': {},
            'platform_success_rates': {},
            'error_types': {},
            'execution_times': []
        }
        
        for cmd in commands:
            # Extract technique patterns
            technique = cmd.get('technique', 'unknown')
            patterns['common_techniques'][technique] = patterns['common_techniques'].get(technique, 0) + 1
            
            # Extract platform patterns
            platform = cmd.get('platform', 'unknown')
            patterns['platform_success_rates'][platform] = patterns['platform_success_rates'].get(platform, 0) + 1
            
            # Extract error patterns
            if cmd.get('error'):
                error_type = type(cmd['error']).__name__
                patterns['error_types'][error_type] = patterns['error_types'].get(error_type, 0) + 1
        
        return patterns


# Integration function for existing attack agent
async def generate_ai_commands(attack_type: str, platform: str, scenario: Dict, 
                            network_context: Dict = None, llm = None) -> Dict[str, Dict]:
    """
    Generate AI-powered attack commands
    
    Args:
        attack_type: Type of attack
        platform: Target platform
        scenario: Attack scenario
        network_context: Network context
        llm: Language model instance
        
    Returns:
        Dictionary of AI-generated attack commands
    """
    if not llm:
        # Use default LLM with API key from environment
        import os
        from langchain_openai import ChatOpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            return {}
            
        llm = ChatOpenAI(
            model='gpt-3.5-turbo', 
            temperature=0.7,
            api_key=api_key
        )
    
    generator = AICommandGenerator(llm)
    return await generator.generate_dynamic_attack_commands(
        attack_type, platform, scenario, network_context
    )
