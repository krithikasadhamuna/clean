"""
Windows log forwarder using Windows Event Log API
"""

import asyncio
import logging
import platform
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_forwarder import BaseLogForwarder
from shared.models import LogSource, LogEntry


logger = logging.getLogger(__name__)


class WindowsLogForwarder(BaseLogForwarder):
    """Windows Event Log forwarder"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        self.event_logs = config.get('windows', {}).get('event_logs', [
            'Security', 'System', 'Application'
        ])
        
        self.wmi_enabled = config.get('windows', {}).get('wmi_enabled', False)
        
        # Check if running on Windows
        if platform.system() != "Windows":
            logger.warning("WindowsLogForwarder running on non-Windows system")
            self.event_logs = []
        
        # Import Windows-specific modules
        self._import_windows_modules()
    
    def _import_windows_modules(self):
        """Import Windows-specific modules"""
        try:
            if platform.system() == "Windows":
                # Use PowerShell for modern event log access
                import subprocess
                import json
                import wmi
                
                self.subprocess = subprocess
                self.json = json
                
                if self.wmi_enabled:
                    self.wmi_client = wmi.WMI()
                else:
                    self.wmi_client = None
                    
                # Test PowerShell availability
                try:
                    result = subprocess.run(['powershell', '-Command', 'Get-WinEvent -ListLog Security -ErrorAction SilentlyContinue'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        logger.info("PowerShell event log access available")
                    else:
                        logger.warning("PowerShell event log access may be limited")
                except Exception as e:
                    logger.warning(f"PowerShell test failed: {e}")
                    
            else:
                # Mock modules for non-Windows systems
                self.subprocess = None
                self.json = None
                self.wmi_client = None
                
        except ImportError as e:
            logger.error(f"Failed to import Windows modules: {e}")
            logger.info("Install required packages: pip install pywin32")
            self.subprocess = None
            self.json = None
            self.wmi_client = None
    
    def _get_log_source(self) -> LogSource:
        """Get log source type"""
        return LogSource.WINDOWS_SYSTEM
    
    async def _collect_logs(self) -> None:
        """Collect Windows Event Logs"""
        if not self.subprocess:
            logger.error("Windows Event Log API not available")
            return
        
        # Start collection tasks for each event log
        tasks = []
        
        for log_name in self.event_logs:
            task = asyncio.create_task(self._collect_event_log(log_name))
            tasks.append(task)
        
        # Start WMI monitoring if enabled
        if self.wmi_client:
            wmi_task = asyncio.create_task(self._collect_wmi_events())
            tasks.append(wmi_task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error collecting Windows logs: {e}")
    
    async def _collect_event_log(self, log_name: str) -> None:
        """Collect events from a specific Windows Event Log using PowerShell"""
        logger.info(f"Starting collection from {log_name} event log")
        
        # Track last processed event ID for incremental reading
        last_event_id = 0
        
        while self.running:
            try:
                # Use PowerShell Get-WinEvent for reliable access
                events = await self._get_events_powershell(log_name, last_event_id)
                
                for event in events:
                    if not self.running:
                        break
                    
                    # Convert PowerShell event to our format
                    log_data = self._convert_powershell_event(event, log_name)
                    if log_data:
                        await self.log_queue.put(log_data)
                        last_event_id = max(last_event_id, event.get('RecordId', 0))
                
                # Wait before checking for new events
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error reading {log_name} events: {e}")
                await asyncio.sleep(5)
    
    async def _get_events_powershell(self, log_name: str, last_event_id: int = 0) -> List[Dict]:
        """Get events using PowerShell Get-WinEvent"""
        try:
            # PowerShell command to get recent events
            if last_event_id > 0:
                # Get events newer than last processed ID
                cmd = f'''
                Get-WinEvent -LogName "{log_name}" -MaxEvents 100 | 
                Where-Object {{ $_.RecordId -gt {last_event_id} }} |
                Select-Object RecordId, Id, LevelDisplayName, TimeCreated, Message, LogName, ProviderName, MachineName |
                ConvertTo-Json -Depth 3
                '''
            else:
                # Get recent events (first run)
                cmd = f'''
                Get-WinEvent -LogName "{log_name}" -MaxEvents 50 |
                Select-Object RecordId, Id, LevelDisplayName, TimeCreated, Message, LogName, ProviderName, MachineName |
                ConvertTo-Json -Depth 3
                '''
            
            # Execute PowerShell command
            result = self.subprocess.run(
                ['powershell', '-Command', cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    events_data = self.json.loads(result.stdout)
                    # Handle single event vs array of events
                    if isinstance(events_data, dict):
                        return [events_data]
                    return events_data
                except self.json.JSONDecodeError as e:
                    logger.error(f"Failed to parse PowerShell output: {e}")
                    return []
            else:
                if result.stderr:
                    logger.debug(f"PowerShell stderr: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"PowerShell event collection failed: {e}")
            return []
    
    def _convert_powershell_event(self, event: Dict, log_name: str) -> Optional[Dict[str, Any]]:
        """Convert PowerShell event to our log format"""
        try:
            log_data = {
                'timestamp': event.get('TimeCreated', datetime.now().isoformat()),
                'event_id': str(event.get('Id', 'Unknown')),
                'level': event.get('LevelDisplayName', 'Information'),
                'message': event.get('Message', 'No message available'),
                'log_name': event.get('LogName', log_name),
                'source_name': event.get('ProviderName', 'Unknown'),
                'computer': event.get('MachineName', 'Unknown'),
                'record_number': event.get('RecordId', 0),
                'event_type': self._get_event_type_from_level(event.get('LevelDisplayName', 'Information')),
            }
            
            # Add security-specific parsing for Security log
            if log_name.lower() == 'security':
                log_data.update(self._parse_security_event_powershell(event))
            
            return log_data
            
        except Exception as e:
            logger.error(f"Failed to convert PowerShell event: {e}")
            return None
    
    def _convert_windows_event(self, event, log_name: str) -> Optional[Dict[str, Any]]:
        """Convert Windows event to our log format (legacy method)"""
        try:
            # Get event message
            try:
                message = self.win32evtlogutil.SafeFormatMessage(event, log_name)
            except Exception:
                message = f"Event ID {event.EventID}"
            
            log_data = {
                'timestamp': event.TimeGenerated.isoformat(),
                'event_id': str(event.EventID),
                'event_type': self._get_event_type_name(event.EventType),
                'level': self._get_event_level(event.EventType),
                'message': message,
                'log_name': log_name,
                'source_name': event.SourceName,
                'computer': event.ComputerName,
                'record_number': event.RecordNumber,
                'category': event.EventCategory,
            }
            
            # Add SID if available
            if hasattr(event, 'Sid') and event.Sid:
                log_data['user_sid'] = str(event.Sid)
            
            # Parse event data
            if hasattr(event, 'StringInserts') and event.StringInserts:
                log_data['string_inserts'] = event.StringInserts
            
            # Add security-specific fields for Security log
            if log_name.lower() == 'security':
                log_data.update(self._parse_security_event(event))
            
            return log_data
            
        except Exception as e:
            logger.error(f"Failed to convert Windows event: {e}")
            return None
    
    def _get_event_type_from_level(self, level: str) -> str:
        """Get event type from PowerShell level display name"""
        level_mapping = {
            'Critical': 'Critical',
            'Error': 'Error', 
            'Warning': 'Warning',
            'Information': 'Information',
            'Verbose': 'Verbose'
        }
        return level_mapping.get(level, 'Information')
    
    def _get_event_type_name(self, event_type: int) -> str:
        """Get event type name from numeric value"""
        type_mapping = {
            1: 'Error',
            2: 'Warning', 
            4: 'Information',
            8: 'Success Audit',
            16: 'Failure Audit'
        }
        return type_mapping.get(event_type, 'Unknown')
    
    def _get_event_level(self, event_type: int) -> str:
        """Get log level from Windows event type"""
        level_mapping = {
            1: 'error',      # Error
            2: 'warning',    # Warning
            4: 'info',       # Information
            8: 'info',       # Success Audit
            16: 'warning'    # Failure Audit
        }
        return level_mapping.get(event_type, 'info')
    
    def _parse_security_event(self, event) -> Dict[str, Any]:
        """Parse Windows Security event for additional fields"""
        security_data = {}
        
        # Map common Security event IDs
        event_id_mapping = {
            4624: 'successful_logon',
            4625: 'failed_logon',
            4634: 'logoff',
            4648: 'explicit_credentials',
            4672: 'special_privileges',
            4688: 'process_creation',
            4689: 'process_termination',
            4697: 'service_installed',
            4720: 'user_account_created',
            4726: 'user_account_deleted',
        }
        
        event_type = event_id_mapping.get(event.EventID)
        if event_type:
            security_data['security_event_type'] = event_type
        
        # Extract common security fields from string inserts
        if hasattr(event, 'StringInserts') and event.StringInserts:
            inserts = event.StringInserts
            
            if event.EventID == 4624:  # Successful logon
                if len(inserts) >= 8:
                    security_data.update({
                        'target_user': inserts[5] if len(inserts) > 5 else '',
                        'target_domain': inserts[6] if len(inserts) > 6 else '',
                        'logon_type': inserts[8] if len(inserts) > 8 else '',
                        'source_ip': inserts[18] if len(inserts) > 18 else '',
                    })
            
            elif event.EventID == 4625:  # Failed logon
                if len(inserts) >= 8:
                    security_data.update({
                        'target_user': inserts[5] if len(inserts) > 5 else '',
                        'target_domain': inserts[6] if len(inserts) > 6 else '',
                        'failure_reason': inserts[8] if len(inserts) > 8 else '',
                        'source_ip': inserts[19] if len(inserts) > 19 else '',
                    })
            
            elif event.EventID == 4688:  # Process creation
                if len(inserts) >= 8:
                    security_data.update({
                        'process_name': inserts[5] if len(inserts) > 5 else '',
                        'process_id': inserts[4] if len(inserts) > 4 else '',
                        'command_line': inserts[8] if len(inserts) > 8 else '',
                        'parent_process': inserts[13] if len(inserts) > 13 else '',
                    })
        
        return security_data
    
    def _parse_security_event_powershell(self, event: Dict) -> Dict[str, Any]:
        """Parse security-specific fields from PowerShell event"""
        security_data = {}
        
        event_id = event.get('Id', 0)
        message = event.get('Message', '')
        
        # Parse common security event types
        if event_id == 4624:  # Successful logon
            security_data['security_event_type'] = 'logon_success'
        elif event_id == 4625:  # Failed logon
            security_data['security_event_type'] = 'logon_failure'
        elif event_id == 4688:  # Process creation
            security_data['security_event_type'] = 'process_creation'
        elif event_id == 4689:  # Process termination
            security_data['security_event_type'] = 'process_termination'
        elif event_id == 4720:  # User account created
            security_data['security_event_type'] = 'user_created'
        elif event_id == 4726:  # User account deleted
            security_data['security_event_type'] = 'user_deleted'
        
        # Extract information from message using regex patterns
        import re
        
        # Extract user information
        user_match = re.search(r'Account Name:\s*([^\s]+)', message)
        if user_match:
            security_data['target_user'] = user_match.group(1)
        
        # Extract domain information
        domain_match = re.search(r'Account Domain:\s*([^\s]+)', message)
        if domain_match:
            security_data['target_domain'] = domain_match.group(1)
        
        # Extract source IP
        ip_match = re.search(r'Source Network Address:\s*([^\s]+)', message)
        if ip_match:
            security_data['source_ip'] = ip_match.group(1)
        
        # Extract logon type
        logon_type_match = re.search(r'Logon Type:\s*([^\s]+)', message)
        if logon_type_match:
            security_data['logon_type'] = logon_type_match.group(1)
        
        return security_data
    
    async def _collect_wmi_events(self) -> None:
        """Collect WMI events (if enabled)"""
        if not self.wmi_client:
            return
        
        logger.info("Starting WMI event collection")
        
        try:
            # Monitor process creation events
            process_watcher = self.wmi_client.Win32_Process.watch_for("creation")
            
            while self.running:
                try:
                    # Wait for process creation event (with timeout)
                    new_process = process_watcher(timeout_ms=1000)
                    
                    if new_process:
                        log_data = {
                            'timestamp': datetime.utcnow().isoformat(),
                            'event_type': 'wmi_process_creation',
                            'level': 'info',
                            'message': f"Process created: {new_process.Name}",
                            'process_name': new_process.Name,
                            'process_id': new_process.ProcessId,
                            'parent_process_id': new_process.ParentProcessId,
                            'command_line': new_process.CommandLine or '',
                            'creation_date': str(new_process.CreationDate) if new_process.CreationDate else '',
                        }
                        
                        await self.log_queue.put(log_data)
                
                except Exception as e:
                    if "timed out" not in str(e).lower():
                        logger.error(f"WMI event collection error: {e}")
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Failed to start WMI collection: {e}")
    
    async def _parse_structured_data(self, raw_log: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Windows-specific structured data"""
        structured_data = await super()._parse_structured_data(raw_log)
        
        # Add Windows-specific fields
        windows_fields = ['log_name', 'source_name', 'record_number', 'category',
                         'user_sid', 'security_event_type', 'logon_type', 'failure_reason']
        
        for field in windows_fields:
            if field in raw_log:
                structured_data[field] = raw_log[field]
        
        return structured_data
