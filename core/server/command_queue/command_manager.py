"""
Command Queue Management System
Manages commands from PhantomStrike AI to client agents
"""

import asyncio
import logging
import sqlite3
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from shared.models import LogEntry


logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Command execution status"""
    QUEUED = "queued"
    SENT = "sent"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class CommandPriority(Enum):
    """Command priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommandManager:
    """Manages command queue and execution tracking"""
    
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.db_path = database_manager.db_path
        
        # Command tracking
        self.pending_commands = {}
        self.executing_commands = {}
        self.command_results = {}
        
        # Configuration
        self.command_timeout = 300  # 5 minutes default
        self.max_concurrent_commands = 10
        self.cleanup_interval = 3600  # 1 hour
        
        # Statistics
        self.stats = {
            'commands_queued': 0,
            'commands_executed': 0,
            'commands_failed': 0,
            'commands_timeout': 0,
            'start_time': None
        }
        
        # Initialize database
        self._initialize_command_tables()
    
    def _initialize_command_tables(self):
        """Initialize command-related database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Commands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commands (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    scenario_id TEXT,
                    technique TEXT NOT NULL,
                    command_type TEXT DEFAULT 'attack',
                    command_data TEXT NOT NULL,
                    parameters TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'queued',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    executed_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    timeout_at TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    created_by TEXT DEFAULT 'phantomstrike_ai',
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # Command results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_results (
                    id TEXT PRIMARY KEY,
                    command_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    success BOOLEAN DEFAULT FALSE,
                    output TEXT,
                    error_message TEXT,
                    execution_time_ms INTEGER,
                    result_data TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (command_id) REFERENCES commands (id),
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_agent_status ON commands (agent_id, status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_status ON commands (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_created_at ON commands (created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_results_command_id ON command_results (command_id)')
            
            conn.commit()
            conn.close()
            
            logger.info("Command queue database tables initialized")
            
        except Exception as e:
            logger.error(f"Command table initialization failed: {e}")
            raise
    
    async def queue_command(self, agent_id: str, technique: str, command_data: Dict, 
                           scenario_id: str = None, priority: CommandPriority = CommandPriority.MEDIUM,
                           parameters: Dict = None, timeout_seconds: int = None) -> str:
        """Queue command for execution on agent"""
        try:
            command_id = f"cmd_{uuid.uuid4().hex[:12]}"
            
            if timeout_seconds is None:
                timeout_seconds = self.command_timeout
            
            timeout_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO commands (
                    id, agent_id, scenario_id, technique, command_data, parameters,
                    priority, status, timeout_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                command_id,
                agent_id,
                scenario_id,
                technique,
                json.dumps(command_data),
                json.dumps(parameters or {}),
                priority.value,
                CommandStatus.QUEUED.value,
                timeout_at.isoformat(),
                'phantomstrike_ai'
            ))
            
            conn.commit()
            conn.close()
            
            # Track in memory
            self.pending_commands[command_id] = {
                'agent_id': agent_id,
                'technique': technique,
                'status': CommandStatus.QUEUED,
                'queued_at': datetime.utcnow(),
                'timeout_at': timeout_at
            }
            
            self.stats['commands_queued'] += 1
            
            logger.info(f"Command queued: {command_id} -> {agent_id} ({technique})")
            
            return command_id
            
        except Exception as e:
            logger.error(f"Command queuing failed: {e}")
            raise
    
    async def get_pending_commands(self, agent_id: str) -> List[Dict]:
        """Get pending commands for specific agent"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get pending commands for agent
            cursor.execute('''
                SELECT id, technique, command_data, parameters, priority, created_at, timeout_at
                FROM commands 
                WHERE agent_id = ? AND status = ?
                ORDER BY priority DESC, created_at ASC
            ''', (agent_id, CommandStatus.QUEUED.value))
            
            rows = cursor.fetchall()
            conn.close()
            
            commands = []
            for row in rows:
                try:
                    command = {
                        'id': row['id'],
                        'technique': row['technique'],
                        'command_data': json.loads(row['command_data']),
                        'parameters': json.loads(row['parameters']) if row['parameters'] else {},
                        'priority': row['priority'],
                        'created_at': row['created_at'],
                        'timeout_at': row['timeout_at']
                    }
                    commands.append(command)
                    
                    # Mark as sent
                    await self._update_command_status(row['id'], CommandStatus.SENT)
                    
                except Exception as e:
                    logger.error(f"Failed to process command {row['id']}: {e}")
                    continue
            
            if commands:
                logger.info(f"Retrieved {len(commands)} pending commands for {agent_id}")
            
            return commands
            
        except Exception as e:
            logger.error(f"Get pending commands failed: {e}")
            return []
    
    async def receive_command_result(self, command_id: str, agent_id: str, 
                                   result_data: Dict) -> bool:
        """Receive command execution result from agent"""
        try:
            success = result_data.get('success', False)
            output = result_data.get('output', '')
            error_message = result_data.get('error', '')
            execution_time = result_data.get('execution_time_ms', 0)
            
            # Store result in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert result
            result_id = f"result_{uuid.uuid4().hex[:12]}"
            cursor.execute('''
                INSERT INTO command_results (
                    id, command_id, agent_id, success, output, error_message,
                    execution_time_ms, result_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result_id,
                command_id,
                agent_id,
                success,
                output,
                error_message,
                execution_time,
                json.dumps(result_data)
            ))
            
            # Update command status
            final_status = CommandStatus.COMPLETED if success else CommandStatus.FAILED
            cursor.execute('''
                UPDATE commands 
                SET status = ?, completed_at = ?
                WHERE id = ?
            ''', (final_status.value, datetime.utcnow().isoformat(), command_id))
            
            conn.commit()
            conn.close()
            
            # Update memory tracking
            if command_id in self.pending_commands:
                del self.pending_commands[command_id]
            
            if command_id in self.executing_commands:
                del self.executing_commands[command_id]
            
            self.command_results[command_id] = result_data
            
            # Update statistics
            if success:
                self.stats['commands_executed'] += 1
            else:
                self.stats['commands_failed'] += 1
            
            logger.info(f"Command result received: {command_id} -> {'SUCCESS' if success else 'FAILED'}")
            
            return True
            
        except Exception as e:
            logger.error(f"Command result processing failed: {e}")
            return False
    
    async def _update_command_status(self, command_id: str, status: CommandStatus) -> None:
        """Update command status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp_field = None
            if status == CommandStatus.SENT:
                timestamp_field = 'sent_at'
            elif status == CommandStatus.EXECUTING:
                timestamp_field = 'executed_at'
            elif status in [CommandStatus.COMPLETED, CommandStatus.FAILED]:
                timestamp_field = 'completed_at'
            
            if timestamp_field:
                cursor.execute(f'''
                    UPDATE commands 
                    SET status = ?, {timestamp_field} = ?
                    WHERE id = ?
                ''', (status.value, datetime.utcnow().isoformat(), command_id))
            else:
                cursor.execute('''
                    UPDATE commands 
                    SET status = ?
                    WHERE id = ?
                ''', (status.value, command_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Command status update failed: {e}")
    
    async def cancel_command(self, command_id: str) -> bool:
        """Cancel queued command"""
        try:
            await self._update_command_status(command_id, CommandStatus.CANCELLED)
            
            # Remove from tracking
            if command_id in self.pending_commands:
                del self.pending_commands[command_id]
            
            logger.info(f"Command cancelled: {command_id}")
            return True
            
        except Exception as e:
            logger.error(f"Command cancellation failed: {e}")
            return False
    
    async def cleanup_old_commands(self, max_age_hours: int = 24) -> Dict:
        """Clean up old completed/failed commands"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old commands
            cursor.execute('''
                DELETE FROM commands 
                WHERE status IN (?, ?, ?) AND created_at < ?
            ''', (
                CommandStatus.COMPLETED.value,
                CommandStatus.FAILED.value,
                CommandStatus.CANCELLED.value,
                cutoff_time.isoformat()
            ))
            
            deleted_commands = cursor.rowcount
            
            # Delete old results
            cursor.execute('''
                DELETE FROM command_results 
                WHERE received_at < ?
            ''', (cutoff_time.isoformat(),))
            
            deleted_results = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleanup completed: {deleted_commands} commands, {deleted_results} results")
            
            return {
                'success': True,
                'deleted_commands': deleted_commands,
                'deleted_results': deleted_results,
                'cleanup_completed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Command cleanup failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_command_statistics(self) -> Dict:
        """Get command queue statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get status counts
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM commands 
                WHERE created_at > datetime('now', '-24 hours')
                GROUP BY status
            ''')
            
            status_counts = dict(cursor.fetchall())
            
            # Get agent command counts
            cursor.execute('''
                SELECT agent_id, COUNT(*) as count
                FROM commands 
                WHERE created_at > datetime('now', '-24 hours')
                GROUP BY agent_id
                ORDER BY count DESC
                LIMIT 10
            ''')
            
            agent_counts = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'queue_statistics': {
                    'pending_commands': len(self.pending_commands),
                    'executing_commands': len(self.executing_commands),
                    'completed_results': len(self.command_results),
                    'status_distribution': status_counts,
                    'top_agents': agent_counts,
                    'total_queued': self.stats['commands_queued'],
                    'total_executed': self.stats['commands_executed'],
                    'total_failed': self.stats['commands_failed'],
                    'success_rate': (self.stats['commands_executed'] / 
                                   max(self.stats['commands_queued'], 1)) * 100
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Command statistics failed: {e}")
            return {'error': str(e)}


# Global command manager instance
command_manager = None

def get_command_manager(database_manager):
    """Get or create global command manager instance"""
    global command_manager
    if command_manager is None:
        command_manager = CommandManager(database_manager)
    return command_manager
