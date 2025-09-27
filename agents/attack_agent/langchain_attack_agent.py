"""
LangChain-Based PhantomStrike AI Attack Agent
Fully integrated with LangChain for attack planning and execution
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool, tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

from .adaptive_attack_orchestrator import adaptive_orchestrator
from .dynamic_attack_generator import DynamicAttackGenerator


logger = logging.getLogger(__name__)


class AttackPlanningInput(BaseModel):
    """Input schema for attack planning"""
    attack_objective: str = Field(description="Attack objective or scenario description")
    network_context: Dict = Field(description="Current network topology and context")
    constraints: Dict = Field(default_factory=dict, description="Attack constraints and limitations")


class AttackScenario(BaseModel):
    """Attack scenario model"""
    scenario_id: str = Field(description="Unique scenario identifier")
    name: str = Field(description="Scenario name")
    description: str = Field(description="Detailed scenario description")
    attack_type: str = Field(description="Type of attack (apt, ransomware, etc.)")
    target_agents: List[str] = Field(description="Target agent IDs")
    mitre_techniques: List[str] = Field(description="MITRE ATT&CK techniques to use")
    attack_phases: List[Dict] = Field(description="Ordered attack phases")
    estimated_duration: str = Field(description="Estimated execution time")
    risk_level: str = Field(description="Risk level (low, medium, high)")
    requires_approval: bool = Field(default=True, description="Whether human approval is required")


class AttackCallbackHandler(AsyncCallbackHandler):
    """Callback handler for attack agent events"""
    
    def __init__(self):
        self.attack_events = []
        self.user_interactions = []
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when tool starts"""
        self.attack_events.append({
            'event': 'tool_start',
            'tool': serialized.get('name', 'unknown'),
            'input': input_str[:200],  # Truncate
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def on_agent_action(self, action, **kwargs) -> None:
        """Called when agent takes action"""
        if 'approval' in str(action).lower():
            self.user_interactions.append({
                'event': 'approval_request',
                'action': str(action),
                'timestamp': datetime.utcnow().isoformat()
            })


@tool
def network_discovery_tool(network_context: Dict) -> Dict:
    """
    Discover and analyze network topology for attack planning
    
    Args:
        network_context: Current network context from topology mapper
    
    Returns:
        Network analysis results for attack planning
    """
    try:
        # Analyze network context for attack opportunities
        endpoints = network_context.get('endpoints', [])
        servers = network_context.get('servers', [])
        domain_controllers = network_context.get('domain_controllers', [])
        high_value_targets = network_context.get('high_value_targets', [])
        
        analysis = {
            'network_analysis_complete': True,
            'total_endpoints': len(endpoints),
            'total_servers': len(servers),
            'domain_controllers': len(domain_controllers),
            'high_value_targets': len(high_value_targets),
            'attack_surface': {
                'web_servers': len([s for s in servers if 'web' in s.get('role', '')]),
                'database_servers': len([s for s in servers if 'database' in s.get('role', '')]),
                'file_servers': len([s for s in servers if 'file' in s.get('role', '')]),
                'admin_endpoints': len([e for e in endpoints if e.get('admin_users', [])])
            },
            'security_zones': list(network_context.get('security_zones', [])),
            'attack_paths_available': len(network_context.get('attack_paths', [])),
            'optimal_entry_points': network_context.get('attack_intelligence', {}).get('optimal_entry_points', []),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Network discovery tool failed: {e}")
        return {
            'network_analysis_complete': False,
            'error': str(e)
        }


@tool
def attack_scenario_generator_tool(attack_objective: str, network_analysis: Dict, constraints: Dict) -> Dict:
    """
    Generate attack scenarios based on objective and network analysis
    
    Args:
        attack_objective: What the attack should accomplish
        network_analysis: Results from network discovery
        constraints: Attack constraints and limitations
    
    Returns:
        Generated attack scenarios
    """
    try:
        # Use existing dynamic attack generator
        generator = DynamicAttackGenerator()
        
        # Generate scenarios based on network context
        scenarios = []
        
        # Determine attack type from objective
        objective_lower = attack_objective.lower()
        
        if any(term in objective_lower for term in ['apt', 'advanced', 'persistent']):
            attack_type = 'apt_simulation'
        elif any(term in objective_lower for term in ['ransomware', 'crypto', 'encrypt']):
            attack_type = 'ransomware_simulation'
        elif any(term in objective_lower for term in ['data', 'exfil', 'steal']):
            attack_type = 'data_exfiltration'
        else:
            attack_type = 'general_assessment'
        
        # Generate scenario based on available targets
        scenario = {
            'scenario_id': f"scenario_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'name': f"PhantomStrike {attack_type.replace('_', ' ').title()}",
            'description': f"AI-generated attack scenario: {attack_objective}",
            'attack_type': attack_type,
            'target_agents': network_analysis.get('optimal_entry_points', [])[:3],
            'mitre_techniques': _get_techniques_for_attack_type(attack_type),
            'attack_phases': _generate_attack_phases(attack_type, network_analysis),
            'estimated_duration': _estimate_duration(attack_type),
            'risk_level': _assess_risk_level(attack_type, network_analysis),
            'requires_approval': True,
            'network_context': network_analysis,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return {
            'scenario_generation_complete': True,
            'scenarios': [scenario],
            'primary_scenario': scenario,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Attack scenario generation failed: {e}")
        return {
            'scenario_generation_complete': False,
            'error': str(e)
        }


@tool
def golden_image_management_tool(action: str, container_ids: List[str], snapshot_name: str = None) -> Dict:
    """
    Manage golden images for attack containers
    
    Args:
        action: Action to perform (create, restore, list)
        container_ids: Container IDs to operate on
        snapshot_name: Name for snapshot (for create/restore actions)
    
    Returns:
        Golden image operation results
    """
    try:
        # This would integrate with your existing golden image tools
        from ..langgraph.tools.golden_image_tools import GoldenImageTool
        
        golden_tool = GoldenImageTool()
        
        if action == 'create':
            results = []
            for container_id in container_ids:
                result = golden_tool.create_golden_image(
                    container_id, 
                    'container_snapshot',
                    {'snapshot_name': snapshot_name or f'snapshot_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}'}
                )
                results.append(result)
            
            return {
                'golden_image_operation_complete': True,
                'action': action,
                'results': results,
                'snapshots_created': len([r for r in results if r.get('success')]),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        elif action == 'restore':
            results = []
            for container_id in container_ids:
                result = golden_tool.restore_golden_image(container_id, snapshot_name)
                results.append(result)
            
            return {
                'golden_image_operation_complete': True,
                'action': action,
                'results': results,
                'restorations_completed': len([r for r in results if r.get('success')]),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        else:
            return {
                'golden_image_operation_complete': False,
                'error': f'Unknown action: {action}'
            }
            
    except Exception as e:
        logger.error(f"Golden image management failed: {e}")
        return {
            'golden_image_operation_complete': False,
            'error': str(e)
        }


@tool
def attack_execution_tool(scenario: Dict, approved: bool = False) -> Dict:
    """
    Execute attack scenario (requires approval)
    
    Args:
        scenario: Attack scenario to execute
        approved: Whether the attack has been approved by user
    
    Returns:
        Attack execution results
    """
    try:
        if not approved:
            return {
                'execution_complete': False,
                'status': 'awaiting_approval',
                'message': 'Attack scenario requires user approval before execution',
                'scenario_summary': {
                    'name': scenario.get('name'),
                    'attack_type': scenario.get('attack_type'),
                    'target_count': len(scenario.get('target_agents', [])),
                    'technique_count': len(scenario.get('mitre_techniques', [])),
                    'estimated_duration': scenario.get('estimated_duration')
                }
            }
        
        # Execute attack using existing orchestrator
        execution_result = asyncio.run(
            adaptive_orchestrator.execute_dynamic_scenario(scenario)
        )
        
        return {
            'execution_complete': True,
            'execution_result': execution_result,
            'scenario_id': scenario.get('scenario_id'),
            'executed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Attack execution failed: {e}")
        return {
            'execution_complete': False,
            'error': str(e)
        }


def _get_techniques_for_attack_type(attack_type: str) -> List[str]:
    """Get MITRE techniques for attack type"""
    technique_mapping = {
        'apt_simulation': ['T1566.001', 'T1055', 'T1003', 'T1021.001', 'T1041'],
        'ransomware_simulation': ['T1486', 'T1490', 'T1489', 'T1083', 'T1057'],
        'data_exfiltration': ['T1005', 'T1039', 'T1114', 'T1020', 'T1041'],
        'general_assessment': ['T1082', 'T1083', 'T1018', 'T1033', 'T1016']
    }
    
    return technique_mapping.get(attack_type, ['T1082', 'T1083'])


def _generate_attack_phases(attack_type: str, network_analysis: Dict) -> List[Dict]:
    """Generate attack phases based on type and network"""
    optimal_targets = network_analysis.get('optimal_entry_points', [])
    hvts = network_analysis.get('high_value_targets', 0)
    
    if attack_type == 'apt_simulation':
        return [
            {
                'name': 'initial_access',
                'description': 'Gain initial foothold in network',
                'targets': optimal_targets[:1],
                'techniques': ['T1566.001'],
                'duration': '30 minutes'
            },
            {
                'name': 'execution',
                'description': 'Execute malicious code',
                'targets': optimal_targets[:1],
                'techniques': ['T1055'],
                'duration': '15 minutes'
            },
            {
                'name': 'persistence',
                'description': 'Establish persistence mechanisms',
                'targets': optimal_targets[:2],
                'techniques': ['T1547.001'],
                'duration': '20 minutes'
            },
            {
                'name': 'lateral_movement',
                'description': 'Move laterally through network',
                'targets': optimal_targets,
                'techniques': ['T1021.001'],
                'duration': '45 minutes'
            },
            {
                'name': 'collection',
                'description': 'Collect valuable data',
                'targets': optimal_targets[-2:] if len(optimal_targets) >= 2 else optimal_targets,
                'techniques': ['T1003', 'T1005'],
                'duration': '30 minutes'
            }
        ]
    
    elif attack_type == 'ransomware_simulation':
        return [
            {
                'name': 'initial_access',
                'description': 'Initial compromise',
                'targets': optimal_targets[:1],
                'techniques': ['T1566.001'],
                'duration': '15 minutes'
            },
            {
                'name': 'discovery',
                'description': 'Discover network and files',
                'targets': optimal_targets,
                'techniques': ['T1083', 'T1057'],
                'duration': '20 minutes'
            },
            {
                'name': 'lateral_movement',
                'description': 'Spread across network',
                'targets': optimal_targets,
                'techniques': ['T1021.002'],
                'duration': '30 minutes'
            },
            {
                'name': 'impact',
                'description': 'Encrypt files (simulated)',
                'targets': optimal_targets,
                'techniques': ['T1486', 'T1490'],
                'duration': '25 minutes'
            }
        ]
    
    else:  # Default phases
        return [
            {
                'name': 'reconnaissance',
                'description': 'Gather system information',
                'targets': optimal_targets[:1],
                'techniques': ['T1082', 'T1083'],
                'duration': '20 minutes'
            },
            {
                'name': 'execution',
                'description': 'Execute test commands',
                'targets': optimal_targets,
                'techniques': ['T1059.001'],
                'duration': '15 minutes'
            }
        ]


def _estimate_duration(attack_type: str) -> str:
    """Estimate attack duration"""
    duration_mapping = {
        'apt_simulation': '2-3 hours',
        'ransomware_simulation': '1-2 hours',
        'data_exfiltration': '1.5-2.5 hours',
        'general_assessment': '30-60 minutes'
    }
    
    return duration_mapping.get(attack_type, '1-2 hours')


def _assess_risk_level(attack_type: str, network_analysis: Dict) -> str:
    """Assess risk level of attack"""
    if attack_type in ['ransomware_simulation', 'apt_simulation']:
        return 'high'
    elif network_analysis.get('high_value_targets', 0) > 0:
        return 'medium'
    else:
        return 'low'


class LangChainAttackAgent:
    """LangChain-based PhantomStrike AI attack agent"""
    
    def __init__(self, llm_config: Dict = None):
        self.llm_config = llm_config or self._default_llm_config()
        
        # Initialize LLM (prefer OpenAI as configured)
        try:
            from langchain_openai import ChatOpenAI
            
            # Use OpenAI GPT-3.5-turbo as primary (as configured in server_config.yaml)
            self.llm = ChatOpenAI(
                model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                temperature=self.llm_config.get('temperature', 0.7),
                max_tokens=self.llm_config.get('max_tokens', 2048),
                openai_api_key=self.llm_config.get('api_key')
            )
            logger.info("Using OpenAI GPT-3.5-turbo for PhantomStrike AI")
            
        except Exception as e:
            logger.warning(f"OpenAI not available, falling back to Ollama: {e}")
            
            # Fallback to Ollama if OpenAI fails
            self.llm = ChatOllama(
                model=self.llm_config.get('model', 'llama2'),
                base_url=self.llm_config.get('endpoint', 'http://localhost:11434'),
                temperature=self.llm_config.get('temperature', 0.7)
            )
        
        # Initialize memory for conversation context
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize callback handler
        self.callback_handler = AttackCallbackHandler()
        
        # Create attack planning tools
        self.tools = [
            network_discovery_tool,
            attack_scenario_generator_tool,
            golden_image_management_tool,
            attack_execution_tool
        ]
        
        # Create attack planning prompt
        self.attack_prompt = self._create_attack_prompt()
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.attack_prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            callbacks=[self.callback_handler],
            verbose=True,
            max_iterations=10,
            early_stopping_method="generate"
        )
        
        # State tracking
        self.pending_approvals = {}
        self.active_executions = {}
        
        logger.info("LangChain PhantomStrike AI Attack Agent initialized")
    
    def _default_llm_config(self) -> Dict:
        """Load LLM configuration dynamically"""
        try:
            # Try to load from server config
            import sys
            from pathlib import Path
            server_path = Path(__file__).parent.parent.parent / "log_forwarding"
            sys.path.insert(0, str(server_path))
            
            from shared.config import config
            server_config = config.load_server_config()
            llm_config = server_config.get('llm', {})
            
            if llm_config:
                return {
                    'model': llm_config.get('model', 'gpt-3.5-turbo'),
                    'temperature': llm_config.get('temperature', 0.7),
                    'max_tokens': llm_config.get('max_tokens', 2048),
                    'api_key': llm_config.get('api_key', ''),
                    'provider': llm_config.get('provider', 'openai')
                }
        except Exception as e:
            logger.debug(f"Could not load server config: {e}")
        
        # Fallback to auto-detected config
        return self._generate_dynamic_llm_config()
    
    def _generate_dynamic_llm_config(self) -> Dict:
        """Generate dynamic LLM configuration"""
        # Test if Ollama is available
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=3)
            ollama_available = response.status_code == 200
        except:
            ollama_available = False
        
        # Always prefer OpenAI GPT-3.5-turbo (as configured)
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            return {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'max_tokens': 2048,
                'api_key': openai_key,
                'provider': 'openai'
            }
        elif ollama_available:
            return {
                'endpoint': 'http://localhost:11434',
                'model': 'llama2',
                'temperature': 0.7,
                'max_tokens': 2048,
                'provider': 'ollama'
            }
        else:
            # Mock fallback
            return {
                'model': 'mock-llm',
                'temperature': 0.7,
                'max_tokens': 2048,
                'provider': 'mock'
            }
    
    def _create_attack_prompt(self) -> ChatPromptTemplate:
        """Create attack planning prompt template"""
        system_message = """You are PhantomStrike AI, an elite red team attack planning specialist.

Your role is to plan and orchestrate sophisticated attack scenarios for security testing.

You have access to these tools:
- network_discovery_tool: Analyze network topology and identify attack opportunities
- attack_scenario_generator_tool: Generate detailed attack scenarios
- golden_image_management_tool: Manage system snapshots for safe restoration
- attack_execution_tool: Execute approved attack scenarios

ATTACK PLANNING PROCESS:
1. Analyze the network topology and identify optimal targets
2. Generate detailed attack scenarios based on the objective
3. Create golden image snapshots before any execution
4. Present scenarios to user for approval
5. Execute approved scenarios with full monitoring
6. Restore systems from golden images after completion

IMPORTANT RULES:
- NEVER execute attacks without explicit user approval
- ALWAYS create golden images before execution
- Focus on realistic attack paths based on actual network topology
- Map all techniques to MITRE ATT&CK framework
- Consider detection evasion and stealth
- Prioritize high-value targets and lateral movement opportunities

SCENARIO QUALITY:
- Base scenarios on real network topology
- Use appropriate techniques for target platforms
- Consider timing and operational security
- Plan for detection and response scenarios
- Include cleanup and restoration procedures"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    async def plan_attack_scenario(self, attack_request: str, 
                                 network_context: Dict, 
                                 constraints: Dict = None) -> AttackScenario:
        """Plan attack scenario using LangChain agent"""
        try:
            if not constraints:
                constraints = {}
            
            # Prepare input for agent
            planning_input = {
                "input": f"""
Plan an attack scenario based on this request:

ATTACK REQUEST: {attack_request}

NETWORK CONTEXT: 
{network_context}

CONSTRAINTS:
{constraints}

Please follow the complete planning process:
1. Analyze the network topology
2. Generate appropriate attack scenarios
3. Plan golden image creation
4. Present scenario for approval

Focus on creating realistic, network-aware attack scenarios that leverage the actual topology.
""",
                "chat_history": self.memory.chat_memory.messages
            }
            
            # Run agent planning
            result = await self.agent_executor.ainvoke(planning_input)
            
            # Parse result into AttackScenario
            scenario = self._parse_attack_scenario(result, attack_request)
            
            # Store for approval tracking
            self.pending_approvals[scenario.scenario_id] = {
                'scenario': scenario,
                'created_at': datetime.utcnow(),
                'status': 'pending_approval'
            }
            
            return scenario
            
        except Exception as e:
            logger.error(f"Attack scenario planning failed: {e}")
            return self._create_fallback_scenario(attack_request, network_context)
    
    async def execute_approved_scenario(self, scenario_id: str, 
                                      user_approval: bool) -> Dict[str, Any]:
        """Execute attack scenario after user approval"""
        try:
            if scenario_id not in self.pending_approvals:
                return {'success': False, 'error': 'Scenario not found'}
            
            approval_info = self.pending_approvals[scenario_id]
            scenario = approval_info['scenario']
            
            if not user_approval:
                # User rejected scenario
                approval_info['status'] = 'rejected'
                return {
                    'success': False,
                    'status': 'rejected',
                    'message': 'Attack scenario rejected by user'
                }
            
            # User approved - execute scenario
            approval_info['status'] = 'approved'
            approval_info['approved_at'] = datetime.utcnow()
            
            execution_input = {
                "input": f"""
Execute the approved attack scenario:

SCENARIO: {scenario.dict()}

APPROVAL: User has approved this scenario for execution

Please:
1. Create golden images for all target systems
2. Execute the attack phases in sequence
3. Monitor execution and collect results
4. Restore systems from golden images after completion

Proceed with execution now that approval is confirmed.
""",
                "chat_history": self.memory.chat_memory.messages
            }
            
            # Execute via agent
            execution_result = await self.agent_executor.ainvoke(execution_input)
            
            # Track execution
            self.active_executions[scenario_id] = {
                'scenario': scenario,
                'execution_result': execution_result,
                'started_at': datetime.utcnow(),
                'status': 'executing'
            }
            
            return {
                'success': True,
                'scenario_id': scenario_id,
                'execution_started': True,
                'execution_result': execution_result
            }
            
        except Exception as e:
            logger.error(f"Attack execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _parse_attack_scenario(self, agent_result: Dict, attack_request: str) -> AttackScenario:
        """Parse agent result into AttackScenario object"""
        try:
            output = agent_result.get('output', '')
            
            # Extract scenario information from agent output
            # This is simplified - in production you'd use more sophisticated parsing
            
            scenario_id = f"phantomstrike_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Determine attack type from request
            request_lower = attack_request.lower()
            if 'apt' in request_lower:
                attack_type = 'apt_simulation'
            elif 'ransomware' in request_lower:
                attack_type = 'ransomware_simulation'
            elif 'data' in request_lower:
                attack_type = 'data_exfiltration'
            else:
                attack_type = 'general_assessment'
            
            # Extract MITRE techniques from output
            import re
            mitre_techniques = re.findall(r'T\d{4}(?:\.\d{3})?', output)
            if not mitre_techniques:
                mitre_techniques = _get_techniques_for_attack_type(attack_type)
            
            return AttackScenario(
                scenario_id=scenario_id,
                name=f"PhantomStrike {attack_type.replace('_', ' ').title()}",
                description=f"AI-generated scenario: {attack_request}",
                attack_type=attack_type,
                target_agents=[],  # Would be populated from network analysis
                mitre_techniques=mitre_techniques,
                attack_phases=_generate_attack_phases(attack_type, {}),
                estimated_duration=_estimate_duration(attack_type),
                risk_level=_assess_risk_level(attack_type, {}),
                requires_approval=True
            )
            
        except Exception as e:
            logger.error(f"Scenario parsing failed: {e}")
            return self._create_fallback_scenario(attack_request, {})
    
    def _create_fallback_scenario(self, attack_request: str, network_context: Dict) -> AttackScenario:
        """Create fallback scenario when parsing fails"""
        return AttackScenario(
            scenario_id=f"fallback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name="Fallback Attack Scenario",
            description=f"Fallback scenario for: {attack_request}",
            attack_type="general_assessment",
            target_agents=[],
            mitre_techniques=['T1082', 'T1083'],
            attack_phases=[],
            estimated_duration="1 hour",
            risk_level="low",
            requires_approval=True
        )
    
    async def get_pending_approvals(self) -> List[Dict]:
        """Get scenarios pending user approval"""
        try:
            pending = []
            
            for scenario_id, approval_info in self.pending_approvals.items():
                if approval_info['status'] == 'pending_approval':
                    scenario = approval_info['scenario']
                    pending.append({
                        'scenario_id': scenario_id,
                        'scenario_name': scenario.name,
                        'attack_type': scenario.attack_type,
                        'target_count': len(scenario.target_agents),
                        'risk_level': scenario.risk_level,
                        'estimated_duration': scenario.estimated_duration,
                        'created_at': approval_info['created_at'].isoformat(),
                        'techniques': scenario.mitre_techniques
                    })
            
            return pending
            
        except Exception as e:
            logger.error(f"Get pending approvals failed: {e}")
            return []
    
    async def get_execution_status(self) -> Dict[str, Any]:
        """Get status of active executions"""
        try:
            active_executions = []
            
            for scenario_id, execution_info in self.active_executions.items():
                scenario = execution_info['scenario']
                active_executions.append({
                    'scenario_id': scenario_id,
                    'scenario_name': scenario.name,
                    'attack_type': scenario.attack_type,
                    'status': execution_info['status'],
                    'started_at': execution_info['started_at'].isoformat(),
                    'progress': self._calculate_execution_progress(execution_info)
                })
            
            return {
                'active_executions': active_executions,
                'pending_approvals': len([a for a in self.pending_approvals.values() 
                                        if a['status'] == 'pending_approval']),
                'agent_status': 'operational',
                'last_update': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Execution status check failed: {e}")
            return {'error': str(e)}
    
    def _calculate_execution_progress(self, execution_info: Dict) -> str:
        """Calculate execution progress"""
        # Simplified progress calculation
        start_time = execution_info['started_at']
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        if elapsed < 300:  # 5 minutes
            return 'initializing'
        elif elapsed < 1800:  # 30 minutes
            return 'in_progress'
        else:
            return 'completing'


# Global LangChain attack agent instance
phantomstrike_ai = LangChainAttackAgent()
