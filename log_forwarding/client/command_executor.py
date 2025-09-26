"""
Command Execution Engine for Client Agents
Executes commands received from PhantomStrike AI attack agent
"""

import asyncio
import logging
import subprocess
import platform
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp

from ..shared.models import LogEntry
from ..shared.utils import safe_json_loads


logger = logging.getLogger(__name__)


class CommandExecutionEngine:
    """Executes attack commands received from server"""
    
    def __init__(self, agent_id: str, server_endpoint: str, api_key: str = None):
        self.agent_id = agent_id
        self.server_endpoint = server_endpoint
        self.api_key = api_key
        
        # Execution state
        self.running = False
        self.command_queue = asyncio.Queue()
        self.execution_log = []
        
        # Security settings
        self.execution_enabled = True
        self.allowed_techniques = set()  # Empty = allow all
        self.blocked_techniques = set()
        
        # Statistics
        self.stats = {
            'commands_received': 0,
            'commands_executed': 0,
            'commands_failed': 0,
            'techniques_executed': set(),
            'start_time': None
        }
        
        # HTTP session
        self.session = None
    
    async def start(self) -> None:
        """Start command execution engine"""
        if self.running:
            return
        
        logger.info(f"🚀 Starting Command Execution Engine (Agent: {self.agent_id})")
        self.running = True
        self.stats['start_time'] = datetime.utcnow()
        
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Start main tasks
        tasks = [
            asyncio.create_task(self._command_poller()),
            asyncio.create_task(self._command_executor())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Command execution engine error: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop command execution engine"""
        logger.info("⏹️ Stopping Command Execution Engine")
        self.running = False
        
        if self.session:
            await self.session.close()
    
    async def _command_poller(self) -> None:
        """Poll server for pending commands"""
        logger.info("📡 Starting command poller")
        
        while self.running:
            try:
                # Poll for commands
                commands = await self._get_pending_commands()
                
                for command in commands:
                    await self.command_queue.put(command)
                    self.stats['commands_received'] += 1
                
                # Wait before next poll
                await asyncio.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                logger.error(f"Command polling error: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _get_pending_commands(self) -> List[Dict[str, Any]]:
        """Get pending commands from server"""
        try:
            if not self.session:
                return []
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            async with self.session.get(
                f"{self.server_endpoint}/api/agents/{self.agent_id}/commands",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    commands = data.get('commands', [])
                    
                    if commands:
                        logger.info(f"Retrieved {len(commands)} pending commands")
                    
                    return commands
                elif response.status == 404:
                    # No commands available
                    return []
                else:
                    logger.warning(f"Command polling failed: {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Failed to get pending commands: {e}")
            return []
    
    async def _command_executor(self) -> None:
        """Execute commands from queue"""
        logger.info("⚡ Starting command executor")
        
        while self.running:
            try:
                # Get command from queue
                command = await asyncio.wait_for(
                    self.command_queue.get(), timeout=1.0
                )
                
                # Execute command
                start_time = datetime.utcnow()
                result = await self._execute_command(command)
                end_time = datetime.utcnow()
                
                # Add execution timing
                result['execution_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
                
                # Report result back to server
                await self._report_command_result(command, result)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Command executor error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual command"""
        try:
            command_id = command.get('id', 'unknown')
            technique = command.get('technique', 'unknown')
            parameters = command.get('parameters', {})
            
            logger.info(f"🎯 Executing command {command_id}: {technique}")
            
            # Security check
            if not self._is_command_allowed(technique):
                return {
                    'success': False,
                    'error': f'Technique {technique} not allowed',
                    'executed_at': datetime.utcnow().isoformat()
                }
            
            # Execute based on technique
            if technique.startswith('T1059'):  # Command and Scripting Interpreter
                result = await self._execute_command_interpreter(parameters)
            elif technique.startswith('T1055'):  # Process Injection
                result = await self._execute_process_injection(parameters)
            elif technique.startswith('T1003'):  # OS Credential Dumping
                result = await self._execute_credential_dumping(parameters)
            elif technique.startswith('T1021'):  # Remote Services
                result = await self._execute_remote_services(parameters)
            elif technique.startswith('T1082'):  # System Information Discovery
                result = await self._execute_system_discovery(parameters)
            else:
                result = await self._execute_generic_technique(technique, parameters)
            
            # Update statistics
            if result.get('success'):
                self.stats['commands_executed'] += 1
                self.stats['techniques_executed'].add(technique)
            else:
                self.stats['commands_failed'] += 1
            
            # Log execution
            execution_log = {
                'command_id': command_id,
                'technique': technique,
                'parameters': parameters,
                'result': result,
                'executed_at': datetime.utcnow().isoformat()
            }
            self.execution_log.append(execution_log)
            
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'executed_at': datetime.utcnow().isoformat()
            }
    
    def _is_command_allowed(self, technique: str) -> bool:
        """Check if command execution is allowed"""
        if not self.execution_enabled:
            return False
        
        if self.blocked_techniques and technique in self.blocked_techniques:
            return False
        
        if self.allowed_techniques and technique not in self.allowed_techniques:
            return False
        
        return True
    
    async def _execute_command_interpreter(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute T1059 - Command and Scripting Interpreter"""
        try:
            command = parameters.get('command', '')
            if not command:
                return {'success': False, 'error': 'No command specified'}
            
            # Execute command based on platform
            if platform.system() == "Windows":
                if parameters.get('interpreter') == 'powershell':
                    result = await self._run_powershell_command(command)
                else:
                    result = await self._run_cmd_command(command)
            else:
                result = await self._run_bash_command(command)
            
            return {
                'success': True,
                'technique': 'T1059',
                'output': result.get('stdout', ''),
                'error_output': result.get('stderr', ''),
                'return_code': result.get('returncode', 0),
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_process_injection(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute T1055 - Process Injection (Simulated)"""
        try:
            target_process = parameters.get('target_process', 'notepad.exe')
            payload = parameters.get('payload', 'test_payload')
            
            # SIMULATION ONLY - Real implementation would do actual injection
            logger.info(f"SIMULATING process injection into {target_process}")
            
            return {
                'success': True,
                'technique': 'T1055',
                'simulation': True,
                'target_process': target_process,
                'payload_size': len(payload),
                'message': f'Simulated injection into {target_process}',
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_credential_dumping(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute T1003 - OS Credential Dumping (Simulated)"""
        try:
            dump_type = parameters.get('type', 'lsass')
            
            # SIMULATION ONLY - Real implementation would dump credentials
            logger.info(f"SIMULATING credential dumping: {dump_type}")
            
            # Simulate finding credentials
            simulated_creds = [
                {'username': 'admin', 'hash': 'aad3b435b51404eeaad3b435b51404ee'},
                {'username': 'user1', 'hash': 'b4b9b02e6f09a9bd760f388b67351e2b'}
            ]
            
            return {
                'success': True,
                'technique': 'T1003',
                'simulation': True,
                'dump_type': dump_type,
                'credentials_found': len(simulated_creds),
                'message': f'Simulated credential dump: {len(simulated_creds)} credentials',
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_system_discovery(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute T1082 - System Information Discovery"""
        try:
            discovery_type = parameters.get('type', 'basic')
            
            # Get real system information
            if platform.system() == "Windows":
                result = await self._run_cmd_command('systeminfo')
            else:
                result = await self._run_bash_command('uname -a && cat /proc/version')
            
            return {
                'success': True,
                'technique': 'T1082',
                'discovery_type': discovery_type,
                'system_info': result.get('stdout', ''),
                'platform': platform.system(),
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _run_powershell_command(self, command: str) -> Dict[str, Any]:
        """Run PowerShell command"""
        try:
            process = await asyncio.create_subprocess_exec(
                'powershell.exe', '-Command', command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'returncode': process.returncode
            }
            
        except Exception as e:
            logger.error(f"PowerShell execution failed: {e}")
            return {'stdout': '', 'stderr': str(e), 'returncode': 1}
    
    async def _run_cmd_command(self, command: str) -> Dict[str, Any]:
        """Run CMD command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'returncode': process.returncode
            }
            
        except Exception as e:
            logger.error(f"CMD execution failed: {e}")
            return {'stdout': '', 'stderr': str(e), 'returncode': 1}
    
    async def _run_bash_command(self, command: str) -> Dict[str, Any]:
        """Run Bash command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'returncode': process.returncode
            }
            
        except Exception as e:
            logger.error(f"Bash execution failed: {e}")
            return {'stdout': '', 'stderr': str(e), 'returncode': 1}
    
    async def _execute_generic_technique(self, technique: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic MITRE technique"""
        try:
            # For techniques we don't have specific implementations
            logger.info(f"Executing generic technique: {technique}")
            
            # Get technique-specific command from parameters
            command = parameters.get('command')
            if command:
                if platform.system() == "Windows":
                    result = await self._run_cmd_command(command)
                else:
                    result = await self._run_bash_command(command)
                
                return {
                    'success': True,
                    'technique': technique,
                    'output': result.get('stdout', ''),
                    'executed_at': datetime.utcnow().isoformat()
                }
            else:
                # Simulate execution
                return {
                    'success': True,
                    'technique': technique,
                    'simulation': True,
                    'message': f'Simulated execution of {technique}',
                    'executed_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _report_command_result(self, command: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Report command execution result back to server"""
        try:
            if not self.session:
                return
            
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            report_data = {
                'agent_id': self.agent_id,
                'command_id': command.get('id'),
                'technique': command.get('technique'),
                'result': result,
                'reported_at': datetime.utcnow().isoformat()
            }
            
            async with self.session.post(
                f"{self.server_endpoint}/api/agents/{self.agent_id}/command-results",
                json=report_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    logger.debug(f"Command result reported: {command.get('id')}")
                else:
                    logger.warning(f"Failed to report result: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to report command result: {e}")
    
    def enable_execution(self) -> None:
        """Enable command execution"""
        self.execution_enabled = True
        logger.info("✅ Command execution enabled")
    
    def disable_execution(self) -> None:
        """Disable command execution"""
        self.execution_enabled = False
        logger.warning("🚫 Command execution disabled")
    
    def set_allowed_techniques(self, techniques: List[str]) -> None:
        """Set allowed MITRE techniques"""
        self.allowed_techniques = set(techniques)
        logger.info(f"✅ Allowed techniques: {len(techniques)}")
    
    def set_blocked_techniques(self, techniques: List[str]) -> None:
        """Set blocked MITRE techniques"""
        self.blocked_techniques = set(techniques)
        logger.info(f"🚫 Blocked techniques: {len(techniques)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        runtime = (datetime.utcnow() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
        
        return {
            'execution_enabled': self.execution_enabled,
            'running': self.running,
            'runtime_seconds': runtime,
            'commands_received': self.stats['commands_received'],
            'commands_executed': self.stats['commands_executed'],
            'commands_failed': self.stats['commands_failed'],
            'success_rate': (self.stats['commands_executed'] / max(self.stats['commands_received'], 1)) * 100,
            'techniques_executed': list(self.stats['techniques_executed']),
            'queue_size': self.command_queue.qsize(),
            'allowed_techniques_count': len(self.allowed_techniques),
            'blocked_techniques_count': len(self.blocked_techniques)
        }
