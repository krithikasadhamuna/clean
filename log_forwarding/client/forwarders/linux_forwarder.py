"""
Linux log forwarder using file tailing and auditd
"""

import asyncio
import logging
import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_forwarder import BaseLogForwarder
from ...shared.models import LogSource
from ...shared.utils import parse_timestamp


logger = logging.getLogger(__name__)


class LinuxLogForwarder(BaseLogForwarder):
    """Linux system log forwarder"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        self.log_files = config.get('linux', {}).get('log_files', [
            '/var/log/syslog',
            '/var/log/auth.log',
            '/var/log/kern.log'
        ])
        
        self.auditd_enabled = config.get('linux', {}).get('auditd_enabled', True)
        self.audit_log_path = '/var/log/audit/audit.log'
        
        # Check if running on Linux
        if platform.system() != "Linux":
            logger.warning("LinuxLogForwarder running on non-Linux system")
            self.log_files = []
        
        # File watchers
        self.file_watchers = {}
        self.file_positions = {}
    
    def _get_log_source(self) -> LogSource:
        """Get log source type"""
        return LogSource.LINUX_SYSTEM
    
    async def _collect_logs(self) -> None:
        """Collect Linux system logs"""
        tasks = []
        
        # Start file tailing tasks
        for log_file in self.log_files:
            if os.path.exists(log_file) and os.access(log_file, os.R_OK):
                task = asyncio.create_task(self._tail_log_file(log_file))
                tasks.append(task)
            else:
                logger.warning(f"Log file not accessible: {log_file}")
        
        # Start auditd monitoring if enabled
        if self.auditd_enabled and os.path.exists(self.audit_log_path):
            audit_task = asyncio.create_task(self._tail_audit_log())
            tasks.append(audit_task)
        
        # Start journal monitoring (systemd)
        if self._has_systemd():
            journal_task = asyncio.create_task(self._collect_journal_logs())
            tasks.append(journal_task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error collecting Linux logs: {e}")
    
    async def _tail_log_file(self, log_file_path: str) -> None:
        """Tail a log file for new entries"""
        logger.info(f"Starting to tail {log_file_path}")
        
        try:
            # Get initial file position (end of file)
            file_path = Path(log_file_path)
            if log_file_path not in self.file_positions:
                self.file_positions[log_file_path] = file_path.stat().st_size
            
            while self.running:
                try:
                    current_size = file_path.stat().st_size
                    last_position = self.file_positions[log_file_path]
                    
                    if current_size > last_position:
                        # Read new content
                        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            
                            for line in new_lines:
                                if not self.running:
                                    break
                                
                                line = line.strip()
                                if line:
                                    log_data = self._parse_syslog_line(line, log_file_path)
                                    if log_data:
                                        await self.log_queue.put(log_data)
                            
                            # Update position
                            self.file_positions[log_file_path] = f.tell()
                    
                    elif current_size < last_position:
                        # File was rotated, start from beginning
                        logger.info(f"Log rotation detected for {log_file_path}")
                        self.file_positions[log_file_path] = 0
                    
                    await asyncio.sleep(1)
                    
                except FileNotFoundError:
                    logger.warning(f"Log file disappeared: {log_file_path}")
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Error tailing {log_file_path}: {e}")
                    await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f"Failed to tail {log_file_path}: {e}")
    
    def _parse_syslog_line(self, line: str, source_file: str) -> Optional[Dict[str, Any]]:
        """Parse a syslog format line"""
        try:
            # Basic syslog format: timestamp hostname process[pid]: message
            import re
            
            # Try to match standard syslog format
            syslog_pattern = r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:\[\s]+)(?:\[(\d+)\])?:\s*(.*)$'
            match = re.match(syslog_pattern, line)
            
            if match:
                timestamp_str, hostname, process, pid, message = match.groups()
                
                # Parse timestamp (add current year)
                current_year = datetime.now().year
                full_timestamp = f"{current_year} {timestamp_str}"
                parsed_time = parse_timestamp(full_timestamp)
                
                log_data = {
                    'timestamp': parsed_time.isoformat() if parsed_time else datetime.utcnow().isoformat(),
                    'hostname': hostname,
                    'process_name': process,
                    'process_id': pid,
                    'message': message,
                    'raw_line': line,
                    'source_file': source_file,
                    'level': self._determine_log_level(message, source_file),
                }
                
                # Add facility/priority info if available
                if source_file.endswith('auth.log'):
                    log_data['facility'] = 'auth'
                elif source_file.endswith('kern.log'):
                    log_data['facility'] = 'kernel'
                elif source_file.endswith('syslog'):
                    log_data['facility'] = 'system'
                
                # Parse authentication events
                if 'auth.log' in source_file:
                    log_data.update(self._parse_auth_log(message))
                
                return log_data
            
            else:
                # Fallback for non-standard format
                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': line,
                    'raw_line': line,
                    'source_file': source_file,
                    'level': 'info',
                }
        
        except Exception as e:
            logger.error(f"Failed to parse syslog line: {e}")
            return None
    
    def _determine_log_level(self, message: str, source_file: str) -> str:
        """Determine log level from message content"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['error', 'failed', 'failure', 'denied', 'invalid']):
            return 'error'
        elif any(word in message_lower for word in ['warning', 'warn', 'deprecated']):
            return 'warning'
        elif any(word in message_lower for word in ['critical', 'fatal', 'panic']):
            return 'critical'
        elif 'auth.log' in source_file and any(word in message_lower for word in ['accepted', 'opened', 'closed']):
            return 'info'
        else:
            return 'info'
    
    def _parse_auth_log(self, message: str) -> Dict[str, Any]:
        """Parse authentication-related log messages"""
        auth_data = {}
        
        # SSH login patterns
        if 'ssh' in message.lower():
            import re
            
            # Successful SSH login
            ssh_success = re.search(r'Accepted (\w+) for (\w+) from ([\d.]+) port (\d+)', message)
            if ssh_success:
                auth_method, user, source_ip, port = ssh_success.groups()
                auth_data.update({
                    'auth_type': 'ssh_success',
                    'auth_method': auth_method,
                    'user': user,
                    'source_ip': source_ip,
                    'source_port': port
                })
            
            # Failed SSH login
            ssh_failed = re.search(r'Failed password for (?:invalid user )?(\w+) from ([\d.]+) port (\d+)', message)
            if ssh_failed:
                user, source_ip, port = ssh_failed.groups()
                auth_data.update({
                    'auth_type': 'ssh_failure',
                    'user': user,
                    'source_ip': source_ip,
                    'source_port': port
                })
        
        # Sudo usage
        if 'sudo' in message.lower():
            sudo_pattern = re.search(r'(\w+) : TTY=(\S+) ; PWD=(\S+) ; USER=(\w+) ; COMMAND=(.+)', message)
            if sudo_pattern:
                user, tty, pwd, target_user, command = sudo_pattern.groups()
                auth_data.update({
                    'auth_type': 'sudo',
                    'user': user,
                    'target_user': target_user,
                    'command': command,
                    'working_directory': pwd,
                    'tty': tty
                })
        
        return auth_data
    
    async def _tail_audit_log(self) -> None:
        """Tail auditd log file"""
        logger.info("Starting auditd log collection")
        
        try:
            await self._tail_log_file(self.audit_log_path)
        except Exception as e:
            logger.error(f"Failed to tail audit log: {e}")
    
    def _has_systemd(self) -> bool:
        """Check if systemd is available"""
        return os.path.exists('/run/systemd/system')
    
    async def _collect_journal_logs(self) -> None:
        """Collect systemd journal logs"""
        try:
            import systemd.journal
            
            logger.info("Starting systemd journal collection")
            
            # Create journal reader
            j = systemd.journal.Reader()
            j.seek_tail()
            j.get_previous()  # Move to last entry
            
            while self.running:
                try:
                    # Wait for new entries
                    j.wait(timeout=1)
                    
                    for entry in j:
                        if not self.running:
                            break
                        
                        log_data = self._convert_journal_entry(entry)
                        if log_data:
                            await self.log_queue.put(log_data)
                
                except Exception as e:
                    logger.error(f"Error reading journal: {e}")
                    await asyncio.sleep(5)
        
        except ImportError:
            logger.info("systemd-python not available, skipping journal collection")
        except Exception as e:
            logger.error(f"Failed to collect journal logs: {e}")
    
    def _convert_journal_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Convert systemd journal entry to our format"""
        try:
            log_data = {
                'timestamp': entry.get('__REALTIME_TIMESTAMP', datetime.utcnow()).isoformat(),
                'hostname': entry.get('_HOSTNAME', 'unknown'),
                'process_name': entry.get('_COMM', entry.get('SYSLOG_IDENTIFIER', 'unknown')),
                'process_id': str(entry.get('_PID', '')),
                'message': entry.get('MESSAGE', ''),
                'unit': entry.get('_SYSTEMD_UNIT', ''),
                'priority': str(entry.get('PRIORITY', 6)),
                'facility': str(entry.get('SYSLOG_FACILITY', 16)),
                'source': 'systemd_journal'
            }
            
            # Convert priority to log level
            priority_map = {
                '0': 'critical',  # Emergency
                '1': 'critical',  # Alert
                '2': 'critical',  # Critical
                '3': 'error',     # Error
                '4': 'warning',   # Warning
                '5': 'info',      # Notice
                '6': 'info',      # Info
                '7': 'debug'      # Debug
            }
            
            log_data['level'] = priority_map.get(log_data['priority'], 'info')
            
            return log_data
        
        except Exception as e:
            logger.error(f"Failed to convert journal entry: {e}")
            return None
    
    async def _parse_structured_data(self, raw_log: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Linux-specific structured data"""
        structured_data = await super()._parse_structured_data(raw_log)
        
        # Add Linux-specific fields
        linux_fields = ['hostname', 'facility', 'source_file', 'unit', 'priority',
                       'auth_type', 'auth_method', 'target_user', 'source_ip', 'source_port',
                       'working_directory', 'tty']
        
        for field in linux_fields:
            if field in raw_log:
                structured_data[field] = raw_log[field]
        
        return structured_data
