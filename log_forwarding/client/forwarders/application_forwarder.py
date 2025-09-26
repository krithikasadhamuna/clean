"""
Application log forwarder for attack agent and custom applications
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .base_forwarder import BaseLogForwarder
from ...shared.models import LogSource


logger = logging.getLogger(__name__)


class ApplicationLogForwarder(BaseLogForwarder):
    """Forwarder for application logs, especially attack agent logs"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        # Attack agent integration
        self.attack_agent_enabled = config.get('attack_agent', {}).get('execution_logging', True)
        self.attack_command_queue = asyncio.Queue() if self.attack_agent_enabled else None
        
        # Application log files to monitor
        self.app_log_files = [
            'attack_execution.log',
            'threat_detection.log', 
            'ai_reasoning.log',
            'application.log'
        ]
        
        # File positions for tailing
        self.file_positions = {}
    
    def _get_log_source(self) -> LogSource:
        """Get log source type"""
        return LogSource.APPLICATION
    
    async def _collect_logs(self) -> None:
        """Collect application logs"""
        tasks = []
        
        # Monitor application log files
        for log_file in self.app_log_files:
            if Path(log_file).exists():
                task = asyncio.create_task(self._tail_app_log(log_file))
                tasks.append(task)
        
        # Monitor attack agent if enabled
        if self.attack_agent_enabled:
            attack_task = asyncio.create_task(self._monitor_attack_agent())
            tasks.append(attack_task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error collecting application logs: {e}")
    
    async def _tail_app_log(self, log_file: str) -> None:
        """Tail application log file"""
        logger.info(f"Tailing application log: {log_file}")
        
        try:
            file_path = Path(log_file)
            
            # Initialize file position
            if log_file not in self.file_positions:
                if file_path.exists():
                    self.file_positions[log_file] = file_path.stat().st_size
                else:
                    self.file_positions[log_file] = 0
            
            while self.running:
                try:
                    if not file_path.exists():
                        await asyncio.sleep(5)
                        continue
                    
                    current_size = file_path.stat().st_size
                    last_position = self.file_positions[log_file]
                    
                    if current_size > last_position:
                        # Read new content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            
                            for line in new_lines:
                                if not self.running:
                                    break
                                
                                line = line.strip()
                                if line:
                                    log_data = self._parse_app_log_line(line, log_file)
                                    if log_data:
                                        await self.log_queue.put(log_data)
                            
                            self.file_positions[log_file] = f.tell()
                    
                    elif current_size < last_position:
                        # File was rotated
                        self.file_positions[log_file] = 0
                    
                    await asyncio.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error tailing {log_file}: {e}")
                    await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f"Failed to tail {log_file}: {e}")
    
    def _parse_app_log_line(self, line: str, source_file: str) -> Optional[Dict[str, Any]]:
        """Parse application log line"""
        try:
            # Try to parse as JSON first (structured logging)
            try:
                json_data = json.loads(line)
                return self._convert_json_log(json_data, source_file)
            except json.JSONDecodeError:
                pass
            
            # Parse as standard log format
            import re
            
            # Pattern: timestamp - logger - level - message
            log_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d{3})?)\s*-\s*([^-]+)\s*-\s*(\w+)\s*-\s*(.+)$'
            match = re.match(log_pattern, line)
            
            if match:
                timestamp_str, logger_name, level, message = match.groups()
                
                log_data = {
                    'timestamp': timestamp_str.replace(',', '.'),  # Fix millisecond separator
                    'logger_name': logger_name.strip(),
                    'level': level.lower(),
                    'message': message,
                    'source_file': source_file,
                    'raw_line': line
                }
                
                # Add attack-specific parsing
                if 'attack' in source_file.lower():
                    log_data.update(self._parse_attack_log(message))
                
                return log_data
            
            else:
                # Fallback - treat as plain message
                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': line,
                    'source_file': source_file,
                    'level': 'info',
                    'raw_line': line
                }
        
        except Exception as e:
            logger.error(f"Failed to parse app log line: {e}")
            return None
    
    def _convert_json_log(self, json_data: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """Convert JSON log entry to our format"""
        log_data = {
            'timestamp': json_data.get('timestamp', datetime.utcnow().isoformat()),
            'level': json_data.get('level', 'info').lower(),
            'message': json_data.get('message', ''),
            'logger_name': json_data.get('logger', json_data.get('name', 'unknown')),
            'source_file': source_file,
        }
        
        # Copy additional structured fields
        for key, value in json_data.items():
            if key not in ['timestamp', 'level', 'message', 'logger', 'name']:
                log_data[key] = value
        
        return log_data
    
    def _parse_attack_log(self, message: str) -> Dict[str, Any]:
        """Parse attack execution log messages"""
        attack_data = {}
        
        try:
            # Look for attack technique patterns
            import re
            
            # MITRE technique pattern
            technique_pattern = r'T\d{4}(?:\.\d{3})?'
            techniques = re.findall(technique_pattern, message)
            if techniques:
                attack_data['mitre_techniques'] = techniques
            
            # Command execution pattern
            if 'executing command' in message.lower():
                cmd_match = re.search(r'executing command[:\s]+(.+)', message, re.IGNORECASE)
                if cmd_match:
                    attack_data['attack_command'] = cmd_match.group(1)
            
            # Target information
            if 'target' in message.lower():
                target_match = re.search(r'target[:\s]+([^\s]+)', message, re.IGNORECASE)
                if target_match:
                    attack_data['target'] = target_match.group(1)
            
            # Success/failure indication
            if any(word in message.lower() for word in ['success', 'successful', 'completed']):
                attack_data['attack_result'] = 'success'
            elif any(word in message.lower() for word in ['failed', 'failure', 'error']):
                attack_data['attack_result'] = 'failure'
            
            # Process information
            if 'process' in message.lower():
                proc_match = re.search(r'process[:\s]+([^\s]+)', message, re.IGNORECASE)
                if proc_match:
                    attack_data['process_name'] = proc_match.group(1)
        
        except Exception as e:
            logger.error(f"Failed to parse attack log: {e}")
        
        return attack_data
    
    async def _monitor_attack_agent(self) -> None:
        """Monitor attack agent execution in real-time"""
        logger.info("Starting attack agent monitoring")
        
        # This would integrate with your existing attack agents
        # For now, we'll simulate monitoring the attack execution queue
        
        while self.running:
            try:
                # Check if there are any attack executions to monitor
                # This would integrate with your existing attack orchestrator
                await self._check_attack_executions()
                
                await asyncio.sleep(2)
            
            except Exception as e:
                logger.error(f"Error monitoring attack agent: {e}")
                await asyncio.sleep(5)
    
    async def _check_attack_executions(self) -> None:
        """Check for active attack executions and log them"""
        try:
            # This would integrate with your existing attack orchestrator
            # For demonstration, we'll check a hypothetical attack status
            
            # You would replace this with actual integration to your attack agents:
            # - agents.attack_agent.adaptive_attack_orchestrator
            # - agents.attack_agent.ai_attacker_brain
            # - agents.attack_agent.dynamic_attack_generator
            
            # Example integration point:
            # from agents.attack_agent.adaptive_attack_orchestrator import adaptive_orchestrator
            # active_executions = await adaptive_orchestrator.get_active_executions()
            
            # For now, we'll create a placeholder
            # In real implementation, you'd get this from your attack orchestrator
            active_executions = []  # Replace with actual attack status
            
            for execution in active_executions:
                log_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'event_type': 'attack_execution',
                    'level': 'info',
                    'message': f"Attack execution: {execution.get('scenario_name', 'unknown')}",
                    'attack_id': execution.get('id'),
                    'attack_scenario': execution.get('scenario_name'),
                    'attack_phase': execution.get('current_phase'),
                    'target_agents': execution.get('target_agents', []),
                    'techniques_executed': execution.get('techniques_executed', []),
                    'commands_sent': execution.get('commands_sent', 0),
                    'success_rate': execution.get('success_rate', 0.0)
                }
                
                await self.log_queue.put(log_data)
        
        except Exception as e:
            logger.error(f"Failed to check attack executions: {e}")
    
    def log_attack_execution(self, execution_data: Dict[str, Any]) -> None:
        """Public method to log attack execution data"""
        if not self.attack_agent_enabled or not self.running:
            return
        
        try:
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'attack_execution',
                'level': 'info',
                'message': f"Attack technique executed: {execution_data.get('technique', 'unknown')}",
                'source': 'attack_agent',
                **execution_data  # Include all execution data
            }
            
            # Queue the log entry (non-blocking)
            if self.attack_command_queue:
                try:
                    self.attack_command_queue.put_nowait(log_data)
                except asyncio.QueueFull:
                    logger.warning("Attack command queue is full, dropping log entry")
        
        except Exception as e:
            logger.error(f"Failed to log attack execution: {e}")
    
    async def _parse_structured_data(self, raw_log: Dict[str, Any]) -> Dict[str, Any]:
        """Parse application-specific structured data"""
        structured_data = await super()._parse_structured_data(raw_log)
        
        # Add application-specific fields
        app_fields = ['logger_name', 'source_file', 'attack_id', 'attack_scenario',
                     'attack_phase', 'target_agents', 'techniques_executed', 
                     'commands_sent', 'success_rate', 'attack_result']
        
        for field in app_fields:
            if field in raw_log:
                structured_data[field] = raw_log[field]
        
        return structured_data
