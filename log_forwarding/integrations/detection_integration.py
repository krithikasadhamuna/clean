"""
Integration with existing detection agents
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..shared.models import LogEntry, DetectionResult


logger = logging.getLogger(__name__)


class DetectionIntegration:
    """Integration with existing AI detection agents"""
    
    def __init__(self):
        # Import your existing detection agents
        self.ai_enhanced_detector = None
        self.ai_threat_analyzer = None
        self.real_threat_detector = None
        self.langgraph_detection_agent = None
        
        self._initialize_detection_agents()
    
    def _initialize_detection_agents(self):
        """Initialize existing detection agents"""
        try:
            # Import your existing detection agents
            from ..agents.detection_agent.ai_enhanced_detector import AIEnhancedThreatDetector
            from ..agents.detection_agent.ai_threat_analyzer import AIThreatAnalyzer
            from ..agents.detection_agent.real_threat_detector import RealThreatDetector
            from ..agents.detection_agent.langgraph_detection_agent import LangGraphDetectionAgent
            
            # Initialize agents
            self.ai_enhanced_detector = AIEnhancedThreatDetector()
            self.ai_threat_analyzer = AIThreatAnalyzer()
            self.real_threat_detector = RealThreatDetector()
            self.langgraph_detection_agent = LangGraphDetectionAgent()
            
            logger.info("Detection agents initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Some detection agents not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize detection agents: {e}")
    
    async def analyze_log_entry(self, log_entry: LogEntry, context: Dict[str, Any] = None) -> Optional[DetectionResult]:
        """Analyze log entry using existing detection agents"""
        try:
            if not context:
                context = {'real_time': True, 'source': 'log_forwarder'}
            
            # Convert log entry to detection data format
            detection_data = self._convert_log_to_detection_data(log_entry)
            
            # Run through AI Enhanced Detector first
            if self.ai_enhanced_detector:
                result = await self._run_ai_enhanced_detection(detection_data, context)
                if result and result.threat_detected:
                    return result
            
            # Run through Real Threat Detector
            if self.real_threat_detector:
                result = await self._run_real_threat_detection(detection_data, context)
                if result and result.threat_detected:
                    return result
            
            # For high-priority logs, run through LangGraph detection workflow
            if self._should_run_advanced_detection(log_entry):
                if self.langgraph_detection_agent:
                    result = await self._run_langgraph_detection(detection_data, context)
                    if result:
                        return result
            
            return None
            
        except Exception as e:
            logger.error(f"Detection analysis failed: {e}")
            return None
    
    def _convert_log_to_detection_data(self, log_entry: LogEntry) -> Dict[str, Any]:
        """Convert LogEntry to format expected by detection agents"""
        return {
            'timestamp': log_entry.timestamp.isoformat(),
            'agent_id': log_entry.agent_id,
            'source': log_entry.source.value,
            'message': log_entry.message,
            'raw_data': log_entry.raw_data,
            'level': log_entry.level.value,
            'event_id': log_entry.event_id,
            'event_type': log_entry.event_type,
            'process_info': log_entry.process_info,
            'network_info': log_entry.network_info,
            'parsed_data': log_entry.parsed_data,
            'enriched_data': log_entry.enriched_data,
            'attack_technique': log_entry.attack_technique,
            'attack_command': log_entry.attack_command,
            'attack_result': log_entry.attack_result,
            'tags': log_entry.tags,
            'metadata': log_entry.metadata
        }
    
    async def _run_ai_enhanced_detection(self, detection_data: Dict[str, Any], 
                                       context: Dict[str, Any]) -> Optional[DetectionResult]:
        """Run AI Enhanced Threat Detector"""
        try:
            result = await self.ai_enhanced_detector.analyze_threat_intelligently(
                detection_data, context
            )
            
            if result:
                return self._convert_detection_result(result, 'ai_enhanced')
            
        except Exception as e:
            logger.error(f"AI Enhanced Detection failed: {e}")
        
        return None
    
    async def _run_real_threat_detection(self, detection_data: Dict[str, Any], 
                                       context: Dict[str, Any]) -> Optional[DetectionResult]:
        """Run Real Threat Detector"""
        try:
            # Convert to format expected by real threat detector
            if detection_data.get('process_info'):
                process_result = self.real_threat_detector.detect_process_anomaly(
                    detection_data['process_info']
                )
                if process_result.get('threat_detected'):
                    return self._convert_detection_result(process_result, 'real_threat')
            
            if detection_data.get('network_info'):
                # Network detection would go here
                pass
            
            # File-based detection
            if 'file' in detection_data.get('event_type', '').lower():
                file_data = {
                    'path': detection_data.get('parsed_data', {}).get('file_path', ''),
                    'hash': detection_data.get('parsed_data', {}).get('file_hash', ''),
                    'size': detection_data.get('parsed_data', {}).get('file_size', 0)
                }
                
                if file_data['path']:
                    file_result = self.real_threat_detector.detect_file_threat(file_data)
                    if file_result.get('threat_detected'):
                        return self._convert_detection_result(file_result, 'real_threat')
        
        except Exception as e:
            logger.error(f"Real Threat Detection failed: {e}")
        
        return None
    
    async def _run_langgraph_detection(self, detection_data: Dict[str, Any], 
                                     context: Dict[str, Any]) -> Optional[DetectionResult]:
        """Run LangGraph Detection Workflow"""
        try:
            # This would integrate with your LangGraph detection workflow
            # For now, we'll create a placeholder
            
            # You would call your existing LangGraph detection workflow here:
            # result = await self.langgraph_detection_agent.run_detection_workflow(detection_data)
            
            # Placeholder implementation
            workflow_result = {
                'threat_detected': False,
                'confidence_score': 0.0,
                'threat_type': 'unknown',
                'severity': 'low',
                'analysis': 'LangGraph analysis placeholder'
            }
            
            if workflow_result.get('threat_detected'):
                return self._convert_detection_result(workflow_result, 'langgraph')
        
        except Exception as e:
            logger.error(f"LangGraph Detection failed: {e}")
        
        return None
    
    def _convert_detection_result(self, result: Dict[str, Any], detector_type: str) -> DetectionResult:
        """Convert detection result to DetectionResult object"""
        detection_result = DetectionResult()
        detection_result.threat_detected = result.get('threat_detected', False)
        detection_result.confidence_score = result.get('confidence_score', 0.0)
        detection_result.threat_type = result.get('threat_type', 'unknown')
        detection_result.severity = result.get('severity', 'low')
        
        # Store results by detector type
        if detector_type == 'ai_enhanced':
            detection_result.ai_analysis = result
        elif detector_type == 'real_threat':
            detection_result.ml_results = result
        elif detector_type == 'langgraph':
            detection_result.ai_analysis = result
        
        # Extract MITRE techniques if available
        if 'mitre_techniques' in result:
            detection_result.mitre_techniques = result['mitre_techniques']
        
        if 'tactics' in result:
            detection_result.tactics = result['tactics']
        
        # Add metadata
        detection_result.metadata = {
            'detector_type': detector_type,
            'detection_timestamp': datetime.utcnow().isoformat()
        }
        
        return detection_result
    
    def _should_run_advanced_detection(self, log_entry: LogEntry) -> bool:
        """Determine if advanced (LangGraph) detection should be run"""
        # Run advanced detection for high-priority logs
        if log_entry.threat_score > 0.5:
            return True
        
        if log_entry.level.value in ['error', 'critical']:
            return True
        
        if 'security' in log_entry.tags or 'threat' in log_entry.tags:
            return True
        
        if log_entry.attack_technique:
            return True
        
        # Run for certain event types
        high_priority_events = [
            'process_creation', 'network_connection', 'file_creation',
            'registry_modification', 'authentication_failure'
        ]
        
        if log_entry.event_type in high_priority_events:
            return True
        
        return False
    
    async def run_correlation_analysis(self, log_entries: List[LogEntry], 
                                     time_window: int = 3600) -> List[DetectionResult]:
        """Run correlation analysis across multiple log entries"""
        try:
            if not self.ai_threat_analyzer:
                return []
            
            # Convert log entries to threat events
            threat_events = []
            for log_entry in log_entries:
                if log_entry.threat_score > 0.1:  # Only include potentially suspicious events
                    event = {
                        'timestamp': log_entry.timestamp.isoformat(),
                        'agent_id': log_entry.agent_id,
                        'event_type': log_entry.event_type,
                        'message': log_entry.message,
                        'threat_score': log_entry.threat_score,
                        'process_info': log_entry.process_info,
                        'network_info': log_entry.network_info
                    }
                    threat_events.append(event)
            
            if not threat_events:
                return []
            
            # Run correlation analysis
            correlation_result = await self.ai_threat_analyzer.correlate_threats_with_ai(
                threat_events, time_window
            )
            
            if correlation_result.get('correlation_found'):
                # Create detection result for the correlation
                detection_result = DetectionResult()
                detection_result.threat_detected = True
                detection_result.confidence_score = correlation_result.get('confidence', 0.0)
                detection_result.threat_type = 'correlated_attack'
                detection_result.severity = correlation_result.get('severity', 'medium')
                detection_result.ai_analysis = correlation_result
                
                return [detection_result]
            
            return []
            
        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            return []
    
    async def generate_threat_intelligence(self, detection_result: DetectionResult) -> Dict[str, Any]:
        """Generate threat intelligence for detected threats"""
        try:
            if not self.ai_threat_analyzer:
                return {}
            
            threat_data = {
                'threat_type': detection_result.threat_type,
                'confidence': detection_result.confidence_score,
                'severity': detection_result.severity,
                'mitre_techniques': detection_result.mitre_techniques,
                'tactics': detection_result.tactics,
                'ml_results': detection_result.ml_results,
                'ai_analysis': detection_result.ai_analysis
            }
            
            intelligence = await self.ai_threat_analyzer.generate_threat_intelligence(threat_data)
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Threat intelligence generation failed: {e}")
            return {}
