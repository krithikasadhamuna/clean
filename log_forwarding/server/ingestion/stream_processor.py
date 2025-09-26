"""
Stream processor for real-time log processing
"""

import asyncio
import logging
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

from ...shared.models import LogEntry


logger = logging.getLogger(__name__)


class StreamProcessor:
    """Processes log streams in real-time"""
    
    def __init__(self, detection_engine=None):
        self.detection_engine = detection_engine
        self.running = False
    
    async def start(self):
        """Start stream processing"""
        self.running = True
        logger.info("Stream processor started")
    
    async def stop(self):
        """Stop stream processing"""
        self.running = False
        logger.info("Stream processor stopped")
    
    async def process_stream(self, log_stream: AsyncGenerator[LogEntry, None]):
        """Process log stream in real-time"""
        try:
            async for log_entry in log_stream:
                if not self.running:
                    break
                
                # Process individual log entry
                await self._process_log_entry(log_entry)
                
        except Exception as e:
            logger.error(f"Stream processing failed: {e}")
    
    async def _process_log_entry(self, log_entry: LogEntry):
        """Process individual log entry"""
        try:
            # Run detection if available
            if self.detection_engine:
                detection_data = {
                    'type': 'general_anomaly',
                    'data': log_entry.to_dict(),
                    'timestamp': log_entry.timestamp.isoformat()
                }
                
                context = {
                    'agent_id': log_entry.agent_id,
                    'real_time': True
                }
                
                # Run detection
                await self.detection_engine.analyze_threat_intelligently(detection_data, context)
        
        except Exception as e:
            logger.error(f"Log entry processing failed: {e}")
