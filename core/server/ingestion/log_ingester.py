"""
Log ingestion and processing system
"""

import asyncio
import logging
import json
import gzip
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.models import LogEntry, LogBatch, DetectionResult
from shared.utils import decompress_data, safe_json_loads


logger = logging.getLogger(__name__)


class LogIngester:
    """Handles log ingestion and initial processing"""
    
    def __init__(self, storage_manager, detection_engine=None, topology_monitor=None):
        self.storage_manager = storage_manager
        self.detection_engine = detection_engine
        self.topology_monitor = topology_monitor
        
        # Processing queues
        self.ingestion_queue = asyncio.Queue(maxsize=10000)
        self.processing_queue = asyncio.Queue(maxsize=5000)
        self.detection_queue = asyncio.Queue(maxsize=1000)
        
        # Processing state
        self.running = False
        self.workers_count = 4
        
        # Statistics
        self.stats = {
            'batches_received': 0,
            'logs_processed': 0,
            'bytes_processed': 0,
            'detection_triggered': 0,
            'processing_errors': 0,
            'start_time': None
        }
    
    async def start(self) -> None:
        """Start the log ingestion system"""
        if self.running:
            return
        
        logger.info("Starting Log Ingestion System")
        self.running = True
        self.stats['start_time'] = datetime.utcnow()
        
        # Start processing workers
        tasks = []
        
        # Ingestion workers
        for i in range(self.workers_count):
            task = asyncio.create_task(self._ingestion_worker(f"ingestion-{i}"))
            tasks.append(task)
        
        # Processing workers
        for i in range(self.workers_count):
            task = asyncio.create_task(self._processing_worker(f"processing-{i}"))
            tasks.append(task)
        
        # Detection worker (if detection engine available)
        if self.detection_engine:
            task = asyncio.create_task(self._detection_worker())
            tasks.append(task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in log ingestion system: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the log ingestion system"""
        logger.info("Stopping Log Ingestion System")
        self.running = False
    
    async def ingest_batch(self, batch_data: bytes, content_encoding: Optional[str] = None, 
                          batch_size: Optional[int] = None) -> Dict[str, Any]:
        """Ingest a batch of logs"""
        try:
            # Decompress if needed
            if content_encoding == 'gzip':
                batch_json = decompress_data(batch_data)
            else:
                batch_json = batch_data.decode('utf-8') if isinstance(batch_data, bytes) else batch_data
            
            # Parse JSON
            if isinstance(batch_json, str):
                batch_dict = safe_json_loads(batch_json, {})
            else:
                batch_dict = batch_json
            
            if not batch_dict:
                return {'status': 'error', 'message': 'Invalid batch data'}
            
            # Create LogBatch object
            log_batch = self._create_log_batch(batch_dict)
            
            # Queue for processing
            await self.ingestion_queue.put(log_batch)
            
            # Update statistics
            self.stats['batches_received'] += 1
            self.stats['bytes_processed'] += len(batch_data) if isinstance(batch_data, bytes) else len(str(batch_data))
            
            return {
                'status': 'success',
                'batch_id': log_batch.id,
                'logs_count': log_batch.batch_size,
                'queued_for_processing': True
            }
        
        except Exception as e:
            logger.error(f"Error ingesting batch: {e}")
            self.stats['processing_errors'] += 1
            return {'status': 'error', 'message': str(e)}
    
    def _create_log_batch(self, batch_dict: Dict[str, Any]) -> LogBatch:
        """Create LogBatch object from dictionary"""
        log_batch = LogBatch()
        log_batch.id = batch_dict.get('id', log_batch.id)
        log_batch.agent_id = batch_dict.get('agent_id', '')
        log_batch.created_at = datetime.fromisoformat(batch_dict.get('created_at', datetime.utcnow().isoformat()))
        log_batch.compressed = batch_dict.get('compressed', False)
        
        # Convert log entries
        logs_data = batch_dict.get('logs', [])
        log_batch.logs = []
        
        for log_data in logs_data:
            try:
                log_entry = LogEntry.from_dict(log_data)
                log_batch.logs.append(log_entry)
            except Exception as e:
                logger.error(f"Failed to parse log entry: {e}")
                continue
        
        log_batch.batch_size = len(log_batch.logs)
        return log_batch
    
    async def _ingestion_worker(self, worker_name: str) -> None:
        """Worker for initial log ingestion"""
        logger.info(f"Starting ingestion worker: {worker_name}")
        
        while self.running:
            try:
                # Get batch from ingestion queue
                log_batch = await asyncio.wait_for(
                    self.ingestion_queue.get(), timeout=1.0
                )
                
                # Process each log entry in the batch
                processed_logs = []
                for log_entry in log_batch.logs:
                    try:
                        # Enrich log entry
                        enriched_log = await self._enrich_log_entry(log_entry)
                        processed_logs.append(enriched_log)
                    except Exception as e:
                        logger.error(f"Failed to enrich log entry: {e}")
                        processed_logs.append(log_entry)  # Keep original
                
                # Update batch with processed logs
                log_batch.logs = processed_logs
                
                # Queue for further processing
                await self.processing_queue.put(log_batch)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in ingestion worker {worker_name}: {e}")
                await asyncio.sleep(1)
    
    async def _processing_worker(self, worker_name: str) -> None:
        """Worker for log processing and storage"""
        logger.info(f"Starting processing worker: {worker_name}")
        
        while self.running:
            try:
                # Get batch from processing queue
                log_batch = await asyncio.wait_for(
                    self.processing_queue.get(), timeout=1.0
                )
                
                # Store logs
                await self._store_log_batch(log_batch)
                
                # Queue for detection if detection engine available
                if self.detection_engine:
                    for log_entry in log_batch.logs:
                        if self._should_run_detection(log_entry):
                            await self.detection_queue.put(log_entry)
                
                # Update topology if topology monitor available
                if self.topology_monitor:
                    for log_entry in log_batch.logs:
                        await self.topology_monitor.process_log_entry(log_entry)
                
                # Update statistics
                self.stats['logs_processed'] += log_batch.batch_size
                
                logger.debug(f"Processed batch {log_batch.id} with {log_batch.batch_size} logs")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in processing worker {worker_name}: {e}")
                self.stats['processing_errors'] += 1
                await asyncio.sleep(1)
    
    async def _detection_worker(self) -> None:
        """Worker for real-time threat detection"""
        logger.info("Starting detection worker")
        
        while self.running:
            try:
                # Get log entry for detection
                log_entry = await asyncio.wait_for(
                    self.detection_queue.get(), timeout=1.0
                )
                
                # Run threat detection
                detection_result = await self._run_threat_detection(log_entry)
                
                if detection_result and detection_result.threat_detected:
                    # Store detection result
                    await self._store_detection_result(detection_result)
                    
                    # Trigger alert if high severity
                    if detection_result.severity in ['high', 'critical']:
                        await self._trigger_alert(log_entry, detection_result)
                
                self.stats['detection_triggered'] += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in detection worker: {e}")
                await asyncio.sleep(1)
    
    async def _enrich_log_entry(self, log_entry: LogEntry) -> LogEntry:
        """Enrich log entry with additional metadata"""
        try:
            # Set processing timestamp
            log_entry.processed_at = datetime.utcnow()
            
            # Add enrichment based on log content
            await self._add_geo_enrichment(log_entry)
            await self._add_threat_intel_enrichment(log_entry)
            await self._add_context_enrichment(log_entry)
            
            return log_entry
        
        except Exception as e:
            logger.error(f"Failed to enrich log entry: {e}")
            return log_entry
    
    async def _add_geo_enrichment(self, log_entry: LogEntry) -> None:
        """Add geographical information for IP addresses"""
        try:
            # Extract IP addresses from log entry
            ip_addresses = []
            
            if log_entry.network_info.get('source_ip'):
                ip_addresses.append(log_entry.network_info['source_ip'])
            if log_entry.network_info.get('destination_ip'):
                ip_addresses.append(log_entry.network_info['destination_ip'])
            
            # Add geo data (would integrate with GeoIP service)
            for ip in ip_addresses:
                if self._is_public_ip(ip):
                    # In production, you'd use a real GeoIP service
                    geo_data = {
                        'ip': ip,
                        'country': 'Unknown',
                        'city': 'Unknown',
                        'asn': 'Unknown'
                    }
                    log_entry.enriched_data[f'geo_{ip}'] = geo_data
        
        except Exception as e:
            logger.error(f"Geo enrichment failed: {e}")
    
    async def _add_threat_intel_enrichment(self, log_entry: LogEntry) -> None:
        """Add threat intelligence information"""
        try:
            # Check against threat intelligence feeds
            # This would integrate with your existing threat intelligence tools
            
            # Extract IOCs
            iocs = self._extract_iocs(log_entry)
            
            if iocs:
                log_entry.enriched_data['iocs'] = iocs
                
                # Check against known malicious indicators
                malicious_indicators = []
                for ioc in iocs:
                    if await self._check_threat_intel(ioc):
                        malicious_indicators.append(ioc)
                
                if malicious_indicators:
                    log_entry.enriched_data['malicious_indicators'] = malicious_indicators
                    log_entry.threat_score += 0.3  # Increase threat score
        
        except Exception as e:
            logger.error(f"Threat intel enrichment failed: {e}")
    
    async def _add_context_enrichment(self, log_entry: LogEntry) -> None:
        """Add contextual information"""
        try:
            # Add timestamp-based context
            log_entry.enriched_data['hour_of_day'] = log_entry.timestamp.hour
            log_entry.enriched_data['day_of_week'] = log_entry.timestamp.weekday()
            log_entry.enriched_data['is_weekend'] = log_entry.timestamp.weekday() >= 5
            
            # Add source-based context
            if log_entry.source:
                log_entry.enriched_data['log_source'] = log_entry.source.value
            
            # Add attack context if from attack agent
            if log_entry.attack_technique:
                log_entry.enriched_data['is_attack_simulation'] = True
                log_entry.tags.append('attack_simulation')
        
        except Exception as e:
            logger.error(f"Context enrichment failed: {e}")
    
    def _extract_iocs(self, log_entry: LogEntry) -> List[Dict[str, Any]]:
        """Extract Indicators of Compromise from log entry"""
        iocs = []
        
        try:
            import re
            
            text = f"{log_entry.message} {log_entry.raw_data}"
            
            # IP addresses
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            for ip in re.findall(ip_pattern, text):
                if self._is_valid_ip(ip):
                    iocs.append({'type': 'ip', 'value': ip})
            
            # Domain names
            domain_pattern = r'\b[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}\b'
            for domain in re.findall(domain_pattern, text):
                iocs.append({'type': 'domain', 'value': domain})
            
            # File hashes (MD5, SHA1, SHA256)
            hash_patterns = {
                'md5': r'\b[a-fA-F0-9]{32}\b',
                'sha1': r'\b[a-fA-F0-9]{40}\b', 
                'sha256': r'\b[a-fA-F0-9]{64}\b'
            }
            
            for hash_type, pattern in hash_patterns.items():
                for hash_value in re.findall(pattern, text):
                    iocs.append({'type': hash_type, 'value': hash_value})
        
        except Exception as e:
            logger.error(f"IOC extraction failed: {e}")
        
        return iocs
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if IP address is valid"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _is_public_ip(self, ip: str) -> bool:
        """Check if IP address is public"""
        try:
            import ipaddress
            return not ipaddress.ip_address(ip).is_private
        except ValueError:
            return False
    
    async def _check_threat_intel(self, ioc: Dict[str, Any]) -> bool:
        """Check IOC against threat intelligence"""
        # This would integrate with real threat intelligence services
        # For now, return False (no threat found)
        return False
    
    async def _store_log_batch(self, log_batch: LogBatch) -> None:
        """Store log batch in database"""
        try:
            await self.storage_manager.store_log_batch(log_batch)
        except Exception as e:
            logger.error(f"Failed to store log batch: {e}")
            raise
    
    def _should_run_detection(self, log_entry: LogEntry) -> bool:
        """Determine if detection should be run on this log entry"""
        # Run detection on security-relevant logs
        if 'security' in log_entry.tags:
            return True
        
        if 'threat' in log_entry.tags:
            return True
        
        if log_entry.level.value in ['warning', 'error', 'critical']:
            return True
        
        if log_entry.attack_technique:
            return True
        
        # Random sampling for other logs (to avoid overload)
        import random
        return random.random() < 0.1  # 10% sampling
    
    async def _run_threat_detection(self, log_entry: LogEntry) -> Optional[DetectionResult]:
        """Run threat detection on log entry"""
        try:
            if not self.detection_engine:
                return None
            
            # This would integrate with your existing detection agents
            detection_data = {
                'log_entry': log_entry.to_dict(),
                'context': {
                    'real_time': True,
                    'source': 'log_forwarder'
                }
            }
            
            # Call detection engine (would integrate with your AI detection agents)
            result = await self.detection_engine.analyze_threat_intelligently(
                detection_data, detection_data['context']
            )
            
            if result:
                detection_result = DetectionResult()
                detection_result.log_entry_id = log_entry.id
                detection_result.threat_detected = result.get('threat_detected', False)
                detection_result.confidence_score = result.get('confidence_score', 0.0)
                detection_result.threat_type = result.get('threat_type', '')
                detection_result.severity = result.get('severity', 'low')
                detection_result.ml_results = result.get('ml_results', {})
                detection_result.ai_analysis = result.get('ai_analysis', {})
                
                return detection_result
        
        except Exception as e:
            logger.error(f"Threat detection failed: {e}")
        
        return None
    
    async def _store_detection_result(self, detection_result: DetectionResult) -> None:
        """Store detection result"""
        try:
            await self.storage_manager.store_detection_result(detection_result)
        except Exception as e:
            logger.error(f"Failed to store detection result: {e}")
    
    async def _trigger_alert(self, log_entry: LogEntry, detection_result: DetectionResult) -> None:
        """Trigger alert for high-severity detections"""
        try:
            alert_data = {
                'alert_id': f"alert_{detection_result.id}",
                'timestamp': datetime.utcnow().isoformat(),
                'severity': detection_result.severity,
                'threat_type': detection_result.threat_type,
                'confidence': detection_result.confidence_score,
                'log_entry_id': log_entry.id,
                'agent_id': log_entry.agent_id,
                'message': log_entry.message,
                'detection_summary': detection_result.ai_analysis.get('summary', ''),
                'recommended_actions': detection_result.ai_analysis.get('recommended_actions', [])
            }
            
            logger.warning(f"SECURITY ALERT: {alert_data}")
            
            # Here you would integrate with your alerting system
            # - Send to SIEM
            # - Send email/SMS notifications
            # - Create tickets
            # - Trigger automated responses
        
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        runtime = (datetime.utcnow() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
        
        return {
            'running': self.running,
            'runtime_seconds': runtime,
            'queue_sizes': {
                'ingestion': self.ingestion_queue.qsize(),
                'processing': self.processing_queue.qsize(),
                'detection': self.detection_queue.qsize()
            },
            'statistics': {
                **self.stats,
                'logs_per_second': self.stats['logs_processed'] / runtime if runtime > 0 else 0,
                'batches_per_second': self.stats['batches_received'] / runtime if runtime > 0 else 0
            }
        }
