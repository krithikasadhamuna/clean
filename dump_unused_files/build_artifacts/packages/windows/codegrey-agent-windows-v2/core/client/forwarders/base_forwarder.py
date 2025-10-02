"""
Base log forwarder class
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime

from shared.models import LogEntry, LogSource, LogLevel
from shared.utils import parse_timestamp


logger = logging.getLogger(__name__)


class BaseLogForwarder(ABC):
    """Base class for all log forwarders"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.running = False
        self.log_queue = asyncio.Queue()
        
        # Statistics
        self.logs_processed = 0
        self.bytes_processed = 0
        self.errors_count = 0
        self.start_time = None
        
    async def start(self) -> None:
        """Start the log forwarder"""
        if self.running:
            return
            
        logger.info(f"Starting {self.__class__.__name__}")
        self.running = True
        self.start_time = datetime.utcnow()
        
        # Start collection tasks
        tasks = [
            asyncio.create_task(self._collect_logs()),
            asyncio.create_task(self._process_queue())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the log forwarder"""
        logger.info(f"Stopping {self.__class__.__name__}")
        self.running = False
    
    @abstractmethod
    async def _collect_logs(self) -> None:
        """Collect logs from the specific source"""
        pass
    
    async def _process_queue(self) -> None:
        """Process logs from the internal queue"""
        while self.running:
            try:
                # Get log entry from queue with timeout
                log_entry = await asyncio.wait_for(
                    self.log_queue.get(), timeout=1.0
                )
                
                # Process the log entry
                processed_entry = await self._process_log_entry(log_entry)
                if processed_entry:
                    # Store processed entry for collection
                    self.logs_processed += 1
                    self.bytes_processed += len(str(processed_entry.raw_data))
                    
                    # Forward to log forwarding system (would be implemented by subclass)
                    await self._forward_processed_log(processed_entry)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing log queue: {e}")
                self.errors_count += 1
                await asyncio.sleep(1)
    
    async def _process_log_entry(self, raw_log: Dict[str, Any]) -> Optional[LogEntry]:
        """Process raw log into LogEntry object"""
        try:
            log_entry = LogEntry()
            log_entry.agent_id = self.agent_id
            log_entry.source = self._get_log_source()
            
            # Parse timestamp
            if 'timestamp' in raw_log:
                parsed_time = parse_timestamp(raw_log['timestamp'])
                if parsed_time:
                    log_entry.timestamp = parsed_time
            
            # Set basic fields
            log_entry.message = raw_log.get('message', '')
            log_entry.raw_data = str(raw_log)
            log_entry.level = self._parse_log_level(raw_log.get('level', 'info'))
            
            # Set event information
            log_entry.event_id = raw_log.get('event_id')
            log_entry.event_type = raw_log.get('event_type')
            
            # Parse structured data
            log_entry.parsed_data = await self._parse_structured_data(raw_log)
            
            # Extract process information
            log_entry.process_info = self._extract_process_info(raw_log)
            
            # Extract network information
            log_entry.network_info = self._extract_network_info(raw_log)
            
            # Add tags
            log_entry.tags = self._generate_tags(raw_log)
            
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to process log entry: {e}")
            self.errors_count += 1
            return None
    
    @abstractmethod
    def _get_log_source(self) -> LogSource:
        """Get the log source type for this forwarder"""
        pass
    
    def _parse_log_level(self, level_str: str) -> LogLevel:
        """Parse log level string to LogLevel enum"""
        level_mapping = {
            'debug': LogLevel.DEBUG,
            'info': LogLevel.INFO,
            'information': LogLevel.INFO,
            'warn': LogLevel.WARNING,
            'warning': LogLevel.WARNING,
            'error': LogLevel.ERROR,
            'critical': LogLevel.CRITICAL,
            'fatal': LogLevel.CRITICAL,
        }
        
        return level_mapping.get(level_str.lower(), LogLevel.INFO)
    
    async def _parse_structured_data(self, raw_log: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured data from raw log"""
        # Base implementation - can be overridden
        structured_data = {}
        
        # Copy relevant fields
        for key in ['user', 'computer', 'domain', 'logon_type', 'process_name', 
                   'command_line', 'parent_process', 'source_ip', 'destination_ip']:
            if key in raw_log:
                structured_data[key] = raw_log[key]
        
        return structured_data
    
    def _extract_process_info(self, raw_log: Dict[str, Any]) -> Dict[str, Any]:
        """Extract process-related information"""
        process_info = {}
        
        process_fields = ['process_name', 'process_id', 'parent_process_id', 
                         'command_line', 'process_path', 'user', 'session_id']
        
        for field in process_fields:
            if field in raw_log:
                process_info[field] = raw_log[field]
        
        return process_info
    
    def _extract_network_info(self, raw_log: Dict[str, Any]) -> Dict[str, Any]:
        """Extract network-related information"""
        network_info = {}
        
        network_fields = ['source_ip', 'destination_ip', 'source_port', 
                         'destination_port', 'protocol', 'bytes_sent', 'bytes_received']
        
        for field in network_fields:
            if field in raw_log:
                network_info[field] = raw_log[field]
        
        return network_info
    
    def _generate_tags(self, raw_log: Dict[str, Any]) -> List[str]:
        """Generate tags for the log entry"""
        tags = []
        
        # Add source-specific tags
        tags.append(f"source:{self._get_log_source().value}")
        
        # Add level tag
        if 'level' in raw_log:
            tags.append(f"level:{raw_log['level'].lower()}")
        
        # Add event type tag
        if 'event_type' in raw_log:
            tags.append(f"event_type:{raw_log['event_type']}")
        
        # Add security-related tags
        if any(keyword in str(raw_log).lower() for keyword in 
               ['security', 'authentication', 'authorization', 'login', 'logon']):
            tags.append('security')
        
        if any(keyword in str(raw_log).lower() for keyword in 
               ['error', 'failed', 'failure', 'denied']):
            tags.append('error')
        
        if any(keyword in str(raw_log).lower() for keyword in 
               ['attack', 'malware', 'suspicious', 'threat']):
            tags.append('threat')
        
        return tags
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get forwarder statistics"""
        runtime = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'forwarder_type': self.__class__.__name__,
            'running': self.running,
            'logs_processed': self.logs_processed,
            'bytes_processed': self.bytes_processed,
            'errors_count': self.errors_count,
            'runtime_seconds': runtime,
            'logs_per_second': self.logs_processed / runtime if runtime > 0 else 0
        }
    
    async def _forward_processed_log(self, log_entry: LogEntry) -> None:
        """Forward processed log entry (to be implemented by subclasses)"""
        # Base implementation - subclasses can override
        pass
