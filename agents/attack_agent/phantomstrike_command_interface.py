"""
PhantomStrike AI Command Interface
Integrates PhantomStrike AI with command queue system
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ...log_forwarding.server.command_queue.command_manager import get_command_manager, CommandPriority


logger = logging.getLogger(__name__)


class PhantomStrikeCommandInterface:
    """Interface for PhantomStrike AI to queue and manage attack commands"""
    
    def __init__(self, database_manager):
        self.command_manager = get_command_manager(database_manager)
        self.db_manager = database_manager
        
        # Execution tracking
        self.active_scenarios = {}
        self.command_batches = {}
        
    async def execute_attack_scenario_with_commands(self, scenario: Dict, 
                                                  target_agents: List[str],
                                                  approved: bool = False) -> Dict:
        """Execute attack scenario by queuing commands to target agents"""
        try:
            if not approved:
                return {
                    'success': False,
                    'status': 'awaiting_approval',
                    'scenario_id': scenario.get('scenario_id'),
                    'message': 'Scenario requires approval before execution'
                }
            
            scenario_id = scenario.get('scenario_id')
            phases = scenario.get('attack_phases', [])
            
            logger.info(f"Executing scenario {scenario_id} with {len(phases)} phases")
            
            # Track scenario execution
            self.active_scenarios[scenario_id] = {
                'scenario': scenario,
                'target_agents': target_agents,
                'phases': phases,
                'current_phase': 0,
                'commands_queued': [],
                'commands_completed': [],
                'started_at': datetime.utcnow(),
                'status': 'executing'
            }
            
            # Execute phases sequentially
            execution_results = []
            
            for phase_index, phase in enumerate(phases):
                phase_result = await self._execute_attack_phase(
                    scenario_id, phase_index, phase, target_agents
                )
                execution_results.append(phase_result)
                
                # Update scenario tracking
                self.active_scenarios[scenario_id]['current_phase'] = phase_index + 1
                
                # Wait between phases
                await asyncio.sleep(5)
            
            # Mark scenario as completed
            self.active_scenarios[scenario_id]['status'] = 'completed'
            self.active_scenarios[scenario_id]['completed_at'] = datetime.utcnow()
            
            return {
                'success': True,
                'scenario_id': scenario_id,
                'execution_results': execution_results,
                'total_phases': len(phases),
                'total_commands': sum(len(phase.get('techniques', [])) * len(target_agents) for phase in phases),
                'completed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scenario execution failed: {e}")
            if scenario_id in self.active_scenarios:
                self.active_scenarios[scenario_id]['status'] = 'failed'
                self.active_scenarios[scenario_id]['error'] = str(e)
            return {'success': False, 'error': str(e)}
    
    async def _execute_attack_phase(self, scenario_id: str, phase_index: int, 
                                  phase: Dict, target_agents: List[str]) -> Dict:
        """Execute single attack phase"""
        try:
            phase_name = phase.get('name', f'phase_{phase_index}')
            techniques = phase.get('techniques', [])
            phase_targets = phase.get('targets', target_agents)
            
            logger.info(f"Executing phase '{phase_name}' with {len(techniques)} techniques")
            
            queued_commands = []
            
            # Queue commands for each technique on each target
            for technique in techniques:
                for agent_id in phase_targets:
                    # Generate command for technique
                    command_data = self._generate_technique_command(technique, phase.get('parameters', {}))
                    
                    # Queue command
                    command_id = await self.command_manager.queue_command(
                        agent_id=agent_id,
                        technique=technique,
                        command_data=command_data,
                        scenario_id=scenario_id,
                        priority=CommandPriority.HIGH,
                        parameters=phase.get('parameters', {}),
                        timeout_seconds=300
                    )
                    
                    queued_commands.append({
                        'command_id': command_id,
                        'agent_id': agent_id,
                        'technique': technique
                    })
            
            # Wait for phase completion
            await self._wait_for_phase_completion(queued_commands)
            
            # Collect results
            phase_results = await self._collect_phase_results(queued_commands)
            
            return {
                'phase_name': phase_name,
                'phase_index': phase_index,
                'techniques_executed': len(techniques),
                'targets_affected': len(phase_targets),
                'commands_queued': len(queued_commands),
                'commands_completed': len([r for r in phase_results if r.get('success')]),
                'success_rate': len([r for r in phase_results if r.get('success')]) / max(len(phase_results), 1),
                'results': phase_results,
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Phase execution failed: {e}")
            return {
                'phase_name': phase.get('name', 'unknown'),
                'phase_index': phase_index,
                'error': str(e),
                'executed_at': datetime.utcnow().isoformat()
            }
    
    def _generate_technique_command(self, technique: str, parameters: Dict) -> Dict:
        """Generate command data for MITRE technique"""
        
        # Map MITRE techniques to commands
        technique_commands = {
            'T1082': {
                'command': 'uname -a && whoami && cat /proc/version',
                'description': 'System Information Discovery',
                'platform': 'linux'
            },
            'T1083': {
                'command': 'find /home -type f -name "*.txt" | head -10',
                'description': 'File and Directory Discovery',
                'platform': 'linux'
            },
            'T1057': {
                'command': 'ps aux | head -20',
                'description': 'Process Discovery',
                'platform': 'linux'
            },
            'T1059.004': {
                'command': 'echo "PhantomStrike test execution" > /tmp/test.txt',
                'description': 'Unix Shell Execution',
                'platform': 'linux'
            },
            'T1059.001': {
                'command': 'powershell.exe -Command "Get-Process | Select-Object -First 10"',
                'description': 'PowerShell Execution',
                'platform': 'windows'
            },
            'T1005': {
                'command': 'find /home -name "*.doc" -o -name "*.pdf" | head -5',
                'description': 'Data from Local System',
                'platform': 'linux'
            }
        }
        
        base_command = technique_commands.get(technique, {
            'command': f'echo "Simulated execution of {technique}"',
            'description': f'Simulated {technique}',
            'platform': 'linux'
        })
        
        # Customize with parameters
        command_data = {
            'technique': technique,
            'command': base_command['command'],
            'description': base_command['description'],
            'platform': base_command['platform'],
            'parameters': parameters,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Apply parameter customizations
        if parameters.get('target_path'):
            command_data['command'] = command_data['command'].replace('/home', parameters['target_path'])
        
        return command_data
    
    async def _wait_for_phase_completion(self, queued_commands: List[Dict], 
                                       timeout_seconds: int = 300) -> None:
        """Wait for phase commands to complete"""
        try:
            start_time = datetime.utcnow()
            timeout_time = start_time + timedelta(seconds=timeout_seconds)
            
            while datetime.utcnow() < timeout_time:
                # Check if all commands completed
                pending_count = 0
                
                for command_info in queued_commands:
                    command_id = command_info['command_id']
                    
                    # Check command status in database
                    if not await self._is_command_completed(command_id):
                        pending_count += 1
                
                if pending_count == 0:
                    logger.info("All phase commands completed")
                    break
                
                # Wait before checking again
                await asyncio.sleep(2)
            
            if pending_count > 0:
                logger.warning(f"Phase timeout: {pending_count} commands still pending")
        
        except Exception as e:
            logger.error(f"Phase completion wait failed: {e}")
    
    async def _is_command_completed(self, command_id: str) -> bool:
        """Check if command is completed"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status FROM commands WHERE id = ?
            ''', (command_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                status = result[0]
                return status in ['completed', 'failed', 'timeout', 'cancelled']
            
            return False
            
        except Exception as e:
            logger.error(f"Command status check failed: {e}")
            return False
    
    async def _collect_phase_results(self, queued_commands: List[Dict]) -> List[Dict]:
        """Collect results from phase execution"""
        results = []
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_manager.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            for command_info in queued_commands:
                command_id = command_info['command_id']
                
                # Get command result
                cursor.execute('''
                    SELECT cr.success, cr.output, cr.error_message, cr.execution_time_ms,
                           c.technique, c.status
                    FROM command_results cr
                    JOIN commands c ON cr.command_id = c.id
                    WHERE cr.command_id = ?
                ''', (command_id,))
                
                result_row = cursor.fetchone()
                
                if result_row:
                    result = {
                        'command_id': command_id,
                        'agent_id': command_info['agent_id'],
                        'technique': result_row['technique'],
                        'success': bool(result_row['success']),
                        'output': result_row['output'],
                        'error_message': result_row['error_message'],
                        'execution_time_ms': result_row['execution_time_ms'],
                        'status': result_row['status']
                    }
                else:
                    # No result yet - command may have timed out
                    result = {
                        'command_id': command_id,
                        'agent_id': command_info['agent_id'],
                        'technique': command_info['technique'],
                        'success': False,
                        'error_message': 'No result received',
                        'status': 'timeout'
                    }
                
                results.append(result)
            
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Phase result collection failed: {e}")
            return []
    
    async def get_scenario_status(self, scenario_id: str) -> Dict:
        """Get status of executing scenario"""
        try:
            if scenario_id not in self.active_scenarios:
                return {'success': False, 'error': 'Scenario not found'}
            
            scenario_info = self.active_scenarios[scenario_id]
            
            return {
                'success': True,
                'scenario_id': scenario_id,
                'status': scenario_info['status'],
                'current_phase': scenario_info['current_phase'],
                'total_phases': len(scenario_info['phases']),
                'commands_queued': len(scenario_info['commands_queued']),
                'commands_completed': len(scenario_info['commands_completed']),
                'started_at': scenario_info['started_at'].isoformat(),
                'target_agents': scenario_info['target_agents']
            }
            
        except Exception as e:
            logger.error(f"Scenario status check failed: {e}")
            return {'success': False, 'error': str(e)}


# Global PhantomStrike command interface
phantomstrike_command_interface = None

def get_phantomstrike_interface(database_manager):
    """Get or create PhantomStrike command interface"""
    global phantomstrike_command_interface
    if phantomstrike_command_interface is None:
        phantomstrike_command_interface = PhantomStrikeCommandInterface(database_manager)
    return phantomstrike_command_interface
