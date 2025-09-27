#!/usr/bin/env python3
"""
Dynamic Threat Analyzer v2.0
Real-time threat analysis that learns from environment without hardcoded patterns
"""

import logging
import json
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DynamicThreatAnalyzer:
    """Dynamic threat analyzer that learns from environment"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.baseline_behavior = {}
        self.threat_indicators = []
        self.learning_enabled = config.get('real_time_detection', {}).get('ml_analysis', True)
        
        # Initialize baseline
        self._establish_baseline()
        
        logger.info("Dynamic Threat Analyzer v2.0 initialized")
    
    def _establish_baseline(self):
        """Establish baseline behavior dynamically"""
        try:
            # Learn normal system behavior
            self.baseline_behavior = {
                'normal_cpu_range': self._learn_normal_cpu_usage(),
                'normal_memory_range': self._learn_normal_memory_usage(),
                'normal_process_count': self._learn_normal_process_count(),
                'normal_network_connections': self._learn_normal_network_activity(),
                'established_at': datetime.now().isoformat()
            }
            
            logger.info("Baseline behavior established from environment")
            
        except Exception as e:
            logger.error(f"Baseline establishment failed: {e}")
    
    def _learn_normal_cpu_usage(self) -> Dict[str, float]:
        """Learn normal CPU usage patterns"""
        try:
            # Sample CPU usage over time to establish normal range
            samples = []
            for _ in range(10):
                samples.append(psutil.cpu_percent(interval=0.1))
            
            return {
                'min': min(samples),
                'max': max(samples),
                'avg': sum(samples) / len(samples),
                'samples': len(samples)
            }
        except:
            return {'min': 0, 'max': 100, 'avg': 50, 'samples': 0}
    
    def _learn_normal_memory_usage(self) -> Dict[str, float]:
        """Learn normal memory usage patterns"""
        try:
            memory = psutil.virtual_memory()
            return {
                'normal_percent': memory.percent,
                'normal_available': memory.available,
                'total': memory.total
            }
        except:
            return {'normal_percent': 50, 'normal_available': 0, 'total': 0}
    
    def _learn_normal_process_count(self) -> Dict[str, int]:
        """Learn normal process count patterns"""
        try:
            processes = list(psutil.process_iter())
            return {
                'normal_count': len(processes),
                'sampled_at': datetime.now().isoformat()
            }
        except:
            return {'normal_count': 50, 'sampled_at': datetime.now().isoformat()}
    
    def _learn_normal_network_activity(self) -> Dict[str, int]:
        """Learn normal network activity patterns"""
        try:
            connections = psutil.net_connections()
            return {
                'normal_connections': len(connections),
                'established_connections': len([c for c in connections if c.status == 'ESTABLISHED']),
                'sampled_at': datetime.now().isoformat()
            }
        except:
            return {'normal_connections': 10, 'established_connections': 5, 'sampled_at': datetime.now().isoformat()}
    
    def analyze_current_state(self) -> Dict[str, Any]:
        """Analyze current system state for threats using learned baselines"""
        
        analysis_results = {
            'threats_found': 0,
            'anomalies_detected': [],
            'behavioral_changes': [],
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_method': 'dynamic_learning'
        }
        
        try:
            # 1. CPU anomaly detection
            cpu_anomaly = self._detect_cpu_anomaly()
            if cpu_anomaly:
                analysis_results['anomalies_detected'].append(cpu_anomaly)
                analysis_results['threats_found'] += 1
            
            # 2. Memory anomaly detection
            memory_anomaly = self._detect_memory_anomaly()
            if memory_anomaly:
                analysis_results['anomalies_detected'].append(memory_anomaly)
                analysis_results['threats_found'] += 1
            
            # 3. Process anomaly detection
            process_anomaly = self._detect_process_anomaly()
            if process_anomaly:
                analysis_results['anomalies_detected'].append(process_anomaly)
                analysis_results['threats_found'] += 1
            
            # 4. Network anomaly detection
            network_anomaly = self._detect_network_anomaly()
            if network_anomaly:
                analysis_results['anomalies_detected'].append(network_anomaly)
                analysis_results['threats_found'] += 1
            
            # 5. Behavioral change detection
            behavioral_changes = self._detect_behavioral_changes()
            analysis_results['behavioral_changes'] = behavioral_changes
            
        except Exception as e:
            logger.error(f"Threat analysis failed: {e}")
            analysis_results['error'] = str(e)
        
        return analysis_results
    
    def _detect_cpu_anomaly(self) -> Optional[Dict[str, Any]]:
        """Detect CPU usage anomalies compared to learned baseline"""
        try:
            current_cpu = psutil.cpu_percent(interval=1)
            baseline = self.baseline_behavior.get('normal_cpu_range', {})
            
            normal_max = baseline.get('max', 100)
            normal_avg = baseline.get('avg', 50)
            
            # Dynamic threshold based on learned behavior
            anomaly_threshold = normal_avg + (normal_max - normal_avg) * 1.5
            
            if current_cpu > anomaly_threshold:
                return {
                    'type': 'cpu_anomaly',
                    'severity': 'medium' if current_cpu > anomaly_threshold * 1.2 else 'low',
                    'current_value': current_cpu,
                    'baseline_max': normal_max,
                    'threshold_exceeded_by': current_cpu - anomaly_threshold,
                    'description': f'CPU usage {current_cpu}% exceeds learned baseline'
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"CPU anomaly detection failed: {e}")
            return None
    
    def _detect_memory_anomaly(self) -> Optional[Dict[str, Any]]:
        """Detect memory usage anomalies"""
        try:
            current_memory = psutil.virtual_memory()
            baseline = self.baseline_behavior.get('normal_memory_range', {})
            
            normal_percent = baseline.get('normal_percent', 50)
            anomaly_threshold = normal_percent * 1.3  # 30% above normal
            
            if current_memory.percent > anomaly_threshold:
                return {
                    'type': 'memory_anomaly',
                    'severity': 'high' if current_memory.percent > 90 else 'medium',
                    'current_percent': current_memory.percent,
                    'baseline_percent': normal_percent,
                    'available_mb': current_memory.available / 1024 / 1024,
                    'description': f'Memory usage {current_memory.percent}% exceeds learned baseline'
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Memory anomaly detection failed: {e}")
            return None
    
    def _detect_process_anomaly(self) -> Optional[Dict[str, Any]]:
        """Detect process count anomalies"""
        try:
            current_processes = list(psutil.process_iter())
            current_count = len(current_processes)
            
            baseline = self.baseline_behavior.get('normal_process_count', {})
            normal_count = baseline.get('normal_count', 50)
            
            # Dynamic threshold - significant deviation from baseline
            deviation_threshold = normal_count * 0.3  # 30% deviation
            
            if abs(current_count - normal_count) > deviation_threshold:
                return {
                    'type': 'process_anomaly',
                    'severity': 'medium',
                    'current_count': current_count,
                    'baseline_count': normal_count,
                    'deviation': current_count - normal_count,
                    'description': f'Process count {current_count} deviates significantly from baseline {normal_count}'
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Process anomaly detection failed: {e}")
            return None
    
    def _detect_network_anomaly(self) -> Optional[Dict[str, Any]]:
        """Detect network activity anomalies"""
        try:
            connections = psutil.net_connections()
            current_connections = len(connections)
            
            baseline = self.baseline_behavior.get('normal_network_connections', {})
            normal_connections = baseline.get('normal_connections', 10)
            
            # Dynamic threshold based on learned patterns
            anomaly_threshold = normal_connections * 2  # Double normal activity
            
            if current_connections > anomaly_threshold:
                return {
                    'type': 'network_anomaly',
                    'severity': 'high' if current_connections > anomaly_threshold * 2 else 'medium',
                    'current_connections': current_connections,
                    'baseline_connections': normal_connections,
                    'threshold_exceeded': current_connections - anomaly_threshold,
                    'description': f'Network connections {current_connections} exceed learned baseline'
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Network anomaly detection failed: {e}")
            return None
    
    def _detect_behavioral_changes(self) -> List[Dict[str, Any]]:
        """Detect behavioral changes from established patterns"""
        
        changes = []
        
        try:
            # Compare current behavior to baseline
            current_time = datetime.now()
            baseline_time = datetime.fromisoformat(self.baseline_behavior.get('established_at', current_time.isoformat()))
            
            time_since_baseline = (current_time - baseline_time).total_seconds()
            
            # If baseline is old, suggest re-establishing
            if time_since_baseline > 86400:  # 24 hours
                changes.append({
                    'type': 'baseline_aging',
                    'description': 'Baseline behavior patterns are aging, consider re-establishment',
                    'age_hours': time_since_baseline / 3600,
                    'recommendation': 'Update baseline'
                })
            
            # Detect if system behavior has fundamentally changed
            current_cpu = psutil.cpu_percent()
            baseline_cpu = self.baseline_behavior.get('normal_cpu_range', {}).get('avg', 50)
            
            if abs(current_cpu - baseline_cpu) > 20:  # Significant CPU behavior change
                changes.append({
                    'type': 'cpu_behavior_shift',
                    'description': f'CPU usage pattern has shifted significantly',
                    'current': current_cpu,
                    'baseline': baseline_cpu,
                    'recommendation': 'Monitor for system changes'
                })
            
        except Exception as e:
            logger.debug(f"Behavioral change detection failed: {e}")
        
        return changes
    
    def update_baseline(self):
        """Update baseline behavior patterns"""
        try:
            self._establish_baseline()
            logger.info("Baseline behavior patterns updated")
        except Exception as e:
            logger.error(f"Baseline update failed: {e}")
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get summary of threat analysis capabilities"""
        return {
            'analyzer_version': '2.0.0',
            'learning_enabled': self.learning_enabled,
            'baseline_established': bool(self.baseline_behavior),
            'analysis_methods': [
                'Dynamic CPU Anomaly Detection',
                'Memory Usage Pattern Analysis', 
                'Process Count Deviation Detection',
                'Network Activity Anomaly Detection',
                'Behavioral Change Analysis'
            ],
            'threat_indicators_learned': len(self.threat_indicators),
            'last_baseline_update': self.baseline_behavior.get('established_at', 'Never')
        }
