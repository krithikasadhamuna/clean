#!/usr/bin/env python3
"""
AI Detection Results Monitor for CodeGrey SOC Platform
Real-time detection statistics and accuracy tracking
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DetectionStats:
    """Real-time detection statistics"""
    total_detections: int
    threats_detected: int
    threats_missed: int
    false_positives: int
    true_positives: int
    detection_accuracy: float
    false_positive_rate: float
    detection_rate: float
    time_range_hours: int
    last_updated: datetime


class AIDetectionMonitor:
    """Monitor and track AI detection performance in real-time"""
    
    def __init__(self, db_path: str = "soc_database.db"):
        self.db_path = db_path
        self._ensure_ground_truth_tables()
    
    def _ensure_ground_truth_tables(self):
        """Create tables for ground truth tracking (best approach)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Red Team Attacks Table (Ground Truth)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS red_team_attacks (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT,
                    attack_type TEXT,
                    target_agent_id TEXT,
                    attack_timestamp TEXT,
                    expected_detection BOOLEAN DEFAULT 1,
                    was_detected BOOLEAN DEFAULT 0,
                    detection_id TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Analyst Review Table (High Confidence)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyst_reviews (
                    id TEXT PRIMARY KEY,
                    log_entry_id TEXT,
                    detection_result_id TEXT,
                    analyst_verdict TEXT,
                    confidence INTEGER,
                    threat_type TEXT,
                    notes TEXT,
                    reviewed_by TEXT,
                    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Known Attack Indicators Table (Threat Intel)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attack_indicators (
                    id TEXT PRIMARY KEY,
                    indicator_type TEXT,
                    indicator_value TEXT,
                    threat_type TEXT,
                    severity TEXT,
                    source TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to create ground truth tables: {e}")
    
    async def get_detection_stats(self, time_range_hours: int = 24) -> DetectionStats:
        """Get real-time detection statistics"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total detections processed
            cursor.execute('''
                SELECT COUNT(*) FROM detection_results
                WHERE detected_at >= ? AND detected_at <= ?
            ''', (start_time.isoformat(), end_time.isoformat()))
            total_detections = cursor.fetchone()[0]
            
            # Get threats detected (threat_detected = 1)
            cursor.execute('''
                SELECT COUNT(*) FROM detection_results
                WHERE threat_detected = 1 
                AND detected_at >= ? AND detected_at <= ?
            ''', (start_time.isoformat(), end_time.isoformat()))
            threats_detected = cursor.fetchone()[0]
            
            # Get false positives (marked as false_positive = 1)
            cursor.execute('''
                SELECT COUNT(*) FROM detection_results
                WHERE threat_detected = 1 AND false_positive = 1
                AND detected_at >= ? AND detected_at <= ?
            ''', (start_time.isoformat(), end_time.isoformat()))
            false_positives = cursor.fetchone()[0]
            
            # Get true positives (verified = 1)
            cursor.execute('''
                SELECT COUNT(*) FROM detection_results
                WHERE threat_detected = 1 AND verified = 1
                AND detected_at >= ? AND detected_at <= ?
            ''', (start_time.isoformat(), end_time.isoformat()))
            true_positives = cursor.fetchone()[0]
            
            # Calculate threats missed using BEST APPROACH (multi-source)
            # 1. Red Team Attacks Missed (Ground Truth - BEST)
            cursor.execute('''
                SELECT COUNT(*) FROM red_team_attacks
                WHERE attack_timestamp >= ? AND attack_timestamp <= ?
                AND expected_detection = 1
                AND was_detected = 0
            ''', (start_time.isoformat(), end_time.isoformat()))
            red_team_missed = cursor.fetchone()[0]
            
            # 2. Analyst-Confirmed Misses (High Confidence)
            cursor.execute('''
                SELECT COUNT(*) FROM analyst_reviews ar
                JOIN log_entries le ON ar.log_entry_id = le.id
                LEFT JOIN detection_results dr ON ar.detection_result_id = dr.id
                WHERE ar.reviewed_at >= ? AND ar.reviewed_at <= ?
                AND ar.analyst_verdict = 'threat'
                AND ar.confidence >= 4
                AND (dr.threat_detected = 0 OR dr.threat_detected IS NULL)
            ''', (start_time.isoformat(), end_time.isoformat()))
            analyst_missed = cursor.fetchone()[0]
            
            # 3. Known IOC Misses (Threat Intel)
            cursor.execute('''
                SELECT COUNT(DISTINCT le.id) FROM log_entries le
                JOIN attack_indicators ai ON (
                    le.message LIKE '%' || ai.indicator_value || '%'
                )
                LEFT JOIN detection_results dr ON le.id = dr.log_entry_id
                WHERE le.timestamp >= ? AND le.timestamp <= ?
                AND ai.active = 1
                AND (dr.threat_detected = 0 OR dr.threat_detected IS NULL)
            ''', (start_time.isoformat(), end_time.isoformat()))
            ioc_missed = cursor.fetchone()[0]
            
            # 4. Heuristic Misses (Baseline Estimate)
            cursor.execute('''
                SELECT COUNT(*) FROM log_entries le
                LEFT JOIN detection_results dr ON le.id = dr.log_entry_id
                WHERE le.timestamp >= ? AND le.timestamp <= ?
                AND (dr.threat_detected = 0 OR dr.threat_detected IS NULL)
                AND le.level IN ('error', 'critical', 'warning')
                AND (
                    le.message LIKE '%failed%' OR
                    le.message LIKE '%error%' OR
                    le.message LIKE '%attack%' OR
                    le.message LIKE '%malicious%' OR
                    le.message LIKE '%suspicious%' OR
                    le.message LIKE '%breach%' OR
                    le.message LIKE '%unauthorized%' OR
                    le.message LIKE '%exploit%' OR
                    le.message LIKE '%intrusion%'
                )
                AND le.id NOT IN (
                    SELECT log_entry_id FROM analyst_reviews 
                    WHERE analyst_verdict = 'threat' AND reviewed_at >= ? AND reviewed_at <= ?
                )
            ''', (start_time.isoformat(), end_time.isoformat(), start_time.isoformat(), end_time.isoformat()))
            heuristic_missed = cursor.fetchone()[0]
            
            # Total missed (prioritize ground truth sources)
            threats_missed = red_team_missed + analyst_missed + ioc_missed + heuristic_missed
            
            # Store breakdown for detailed reporting
            missed_breakdown = {
                'red_team': red_team_missed,
                'analyst_confirmed': analyst_missed,
                'known_iocs': ioc_missed,
                'heuristic': heuristic_missed,
                'confidence': self._calculate_confidence_level(
                    red_team_missed, analyst_missed, ioc_missed, heuristic_missed
                )
            }
            
            conn.close()
            
            # Calculate metrics
            detection_accuracy = self._calculate_accuracy(
                true_positives, false_positives, threats_missed
            )
            
            false_positive_rate = self._calculate_fp_rate(
                false_positives, threats_detected
            )
            
            detection_rate = self._calculate_detection_rate(
                threats_detected, threats_missed
            )
            
            return DetectionStats(
                total_detections=total_detections,
                threats_detected=threats_detected,
                threats_missed=threats_missed,
                false_positives=false_positives,
                true_positives=true_positives,
                detection_accuracy=detection_accuracy,
                false_positive_rate=false_positive_rate,
                detection_rate=detection_rate,
                time_range_hours=time_range_hours,
                last_updated=end_time
            )
            
        except Exception as e:
            logger.error(f"Failed to get detection stats: {e}")
            return DetectionStats(
                total_detections=0,
                threats_detected=0,
                threats_missed=0,
                false_positives=0,
                true_positives=0,
                detection_accuracy=0.0,
                false_positive_rate=0.0,
                detection_rate=0.0,
                time_range_hours=time_range_hours,
                last_updated=end_time
            )
    
    def _calculate_accuracy(self, true_positives: int, false_positives: int, 
                          false_negatives: int) -> float:
        """Calculate detection accuracy"""
        total = true_positives + false_positives + false_negatives
        if total == 0:
            return 100.0
        
        accuracy = (true_positives / total) * 100
        return round(accuracy, 2)
    
    def _calculate_fp_rate(self, false_positives: int, total_detections: int) -> float:
        """Calculate false positive rate"""
        if total_detections == 0:
            return 0.0
        
        fp_rate = (false_positives / total_detections) * 100
        return round(fp_rate, 2)
    
    def _calculate_detection_rate(self, detected: int, missed: int) -> float:
        """Calculate detection rate (recall)"""
        total = detected + missed
        if total == 0:
            return 100.0
        
        detection_rate = (detected / total) * 100
        return round(detection_rate, 2)
    
    async def get_hourly_detection_trend(self, time_range_hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly detection trend for charting"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m-%d %H:00:00', detected_at) as hour,
                    COUNT(*) as total,
                    SUM(CASE WHEN threat_detected = 1 THEN 1 ELSE 0 END) as detected,
                    SUM(CASE WHEN threat_detected = 1 AND false_positive = 1 THEN 1 ELSE 0 END) as false_positives
                FROM detection_results
                WHERE detected_at >= ? AND detected_at <= ?
                GROUP BY hour
                ORDER BY hour
            ''', (start_time.isoformat(), end_time.isoformat()))
            
            trend_data = []
            for row in cursor.fetchall():
                trend_data.append({
                    'hour': row[0],
                    'total': row[1],
                    'detected': row[2],
                    'false_positives': row[3]
                })
            
            conn.close()
            return trend_data
            
        except Exception as e:
            logger.error(f"Failed to get hourly trend: {e}")
            return []
    
    async def get_detection_breakdown_by_type(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get detection breakdown by threat type"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    threat_type,
                    COUNT(*) as count,
                    AVG(confidence_score) as avg_confidence,
                    SUM(CASE WHEN false_positive = 1 THEN 1 ELSE 0 END) as false_positives
                FROM detection_results
                WHERE threat_detected = 1
                AND detected_at >= ? AND detected_at <= ?
                GROUP BY threat_type
                ORDER BY count DESC
            ''', (start_time.isoformat(), end_time.isoformat()))
            
            breakdown = {}
            for row in cursor.fetchall():
                breakdown[row[0]] = {
                    'count': row[1],
                    'avg_confidence': round(row[2] * 100, 1) if row[2] else 0,
                    'false_positives': row[3]
                }
            
            conn.close()
            return breakdown
            
        except Exception as e:
            logger.error(f"Failed to get detection breakdown: {e}")
            return {}
    
    async def get_detection_breakdown_by_severity(self, time_range_hours: int = 24) -> Dict[str, int]:
        """Get detection breakdown by severity"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    severity,
                    COUNT(*) as count
                FROM detection_results
                WHERE threat_detected = 1
                AND detected_at >= ? AND detected_at <= ?
                GROUP BY severity
            ''', (start_time.isoformat(), end_time.isoformat()))
            
            severity_breakdown = {}
            for row in cursor.fetchall():
                severity_breakdown[row[0]] = row[1]
            
            conn.close()
            return severity_breakdown
            
        except Exception as e:
            logger.error(f"Failed to get severity breakdown: {e}")
            return {}
    
    async def get_recent_detections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent detections"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    dr.id,
                    dr.threat_type,
                    dr.severity,
                    dr.confidence_score,
                    dr.detected_at,
                    le.source,
                    le.message,
                    a.hostname,
                    dr.false_positive,
                    dr.verified
                FROM detection_results dr
                JOIN log_entries le ON dr.log_entry_id = le.id
                LEFT JOIN agents a ON le.agent_id = a.id
                WHERE dr.threat_detected = 1
                ORDER BY dr.detected_at DESC
                LIMIT ?
            ''', (limit,))
            
            recent_detections = []
            for row in cursor.fetchall():
                recent_detections.append({
                    'id': row[0],
                    'threat_type': row[1],
                    'severity': row[2],
                    'confidence': round(row[3] * 100, 1),
                    'detected_at': row[4],
                    'source': row[5],
                    'message': row[6][:100] if row[6] else '',  # Truncate
                    'hostname': row[7],
                    'status': 'False Positive' if row[8] else ('Verified' if row[9] else 'Pending Review')
                })
            
            conn.close()
            return recent_detections
            
        except Exception as e:
            logger.error(f"Failed to get recent detections: {e}")
            return []
    
    def format_for_api(self, stats: DetectionStats) -> Dict[str, Any]:
        """Format detection stats for API response"""
        
        # Determine overall status
        if stats.threats_missed > 10:
            status = 'warning'
            status_message = f'{stats.threats_missed} threats potentially missed'
        elif stats.false_positive_rate > 20:
            status = 'warning'
            status_message = f'High false positive rate: {stats.false_positive_rate}%'
        elif stats.detection_accuracy >= 95:
            status = 'excellent'
            status_message = 'Detection system performing excellently'
        elif stats.detection_accuracy >= 85:
            status = 'good'
            status_message = 'Detection system performing well'
        else:
            status = 'needs_improvement'
            status_message = 'Detection system needs tuning'
        
        return {
            'status': 'success',
            'detectionStats': {
                'summary': {
                    'detected': stats.threats_detected,
                    'missed': stats.threats_missed,
                    'totalProcessed': stats.total_detections,
                    'accuracy': stats.detection_accuracy,
                    'detectionRate': stats.detection_rate,
                    'falsePositiveRate': stats.false_positive_rate
                },
                'breakdown': {
                    'truePositives': stats.true_positives,
                    'falsePositives': stats.false_positives,
                    'falseNegatives': stats.threats_missed,
                    'benign': stats.total_detections - stats.threats_detected
                },
                'performance': {
                    'status': status,
                    'statusMessage': status_message,
                    'accuracy': stats.detection_accuracy,
                    'precision': self._calculate_precision(stats.true_positives, stats.false_positives),
                    'recall': stats.detection_rate,
                    'f1Score': self._calculate_f1_score(stats.true_positives, stats.false_positives, stats.threats_missed)
                },
                'timeRange': {
                    'hours': stats.time_range_hours,
                    'lastUpdated': stats.last_updated.isoformat()
                }
            }
        }
    
    def _calculate_precision(self, true_positives: int, false_positives: int) -> float:
        """Calculate precision"""
        total = true_positives + false_positives
        if total == 0:
            return 100.0
        
        precision = (true_positives / total) * 100
        return round(precision, 2)
    
    def _calculate_f1_score(self, true_positives: int, false_positives: int, false_negatives: int) -> float:
        """Calculate F1 score"""
        precision_denominator = true_positives + false_positives
        recall_denominator = true_positives + false_negatives
        
        if precision_denominator == 0 or recall_denominator == 0:
            return 0.0
        
        precision = true_positives / precision_denominator
        recall = true_positives / recall_denominator
        
        if precision + recall == 0:
            return 0.0
        
        f1 = 2 * (precision * recall) / (precision + recall)
        return round(f1 * 100, 2)
    
    def _calculate_confidence_level(self, red_team: int, analyst: int, ioc: int, heuristic: int) -> str:
        """Calculate confidence level in missed count based on data sources"""
        if red_team > 0:
            return 'very_high'  # Ground truth from actual attacks
        elif analyst > 0:
            return 'high'       # Analyst confirmed
        elif ioc > 0:
            return 'medium'     # Known threats
        elif heuristic > 0:
            return 'low'        # Heuristic estimate
        else:
            return 'unknown'
    
    async def record_red_team_attack(self, attack_data: Dict) -> str:
        """Record a red team attack for ground truth tracking"""
        try:
            import uuid
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            attack_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO red_team_attacks (
                    id, scenario_id, attack_type, target_agent_id,
                    attack_timestamp, expected_detection, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                attack_id,
                attack_data.get('scenario_id'),
                attack_data.get('attack_type'),
                attack_data.get('target_agent_id'),
                attack_data.get('timestamp', datetime.now().isoformat()),
                attack_data.get('expected_detection', True),
                attack_data.get('notes', '')
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded red team attack: {attack_id}")
            return attack_id
            
        except Exception as e:
            logger.error(f"Failed to record red team attack: {e}")
            return None
    
    async def mark_attack_detected(self, attack_id: str, detection_id: str):
        """Mark a red team attack as detected"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE red_team_attacks
                SET was_detected = 1, detection_id = ?
                WHERE id = ?
            ''', (detection_id, attack_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Marked attack {attack_id} as detected")
            
        except Exception as e:
            logger.error(f"Failed to mark attack as detected: {e}")
    
    async def record_analyst_review(self, review_data: Dict) -> str:
        """Record analyst review of a log entry"""
        try:
            import uuid
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            review_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO analyst_reviews (
                    id, log_entry_id, detection_result_id,
                    analyst_verdict, confidence, threat_type,
                    notes, reviewed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                review_id,
                review_data.get('log_entry_id'),
                review_data.get('detection_result_id'),
                review_data.get('verdict'),  # 'threat', 'benign', 'unclear'
                review_data.get('confidence', 3),  # 1-5
                review_data.get('threat_type'),
                review_data.get('notes', ''),
                review_data.get('analyst_name')
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded analyst review: {review_id}")
            return review_id
            
        except Exception as e:
            logger.error(f"Failed to record analyst review: {e}")
            return None
    
    async def add_attack_indicator(self, indicator_data: Dict) -> str:
        """Add known attack indicator for detection"""
        try:
            import uuid
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            indicator_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO attack_indicators (
                    id, indicator_type, indicator_value,
                    threat_type, severity, source,
                    first_seen, last_seen, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                indicator_id,
                indicator_data.get('type'),
                indicator_data.get('value'),
                indicator_data.get('threat_type'),
                indicator_data.get('severity', 'medium'),
                indicator_data.get('source', 'manual'),
                now,
                now,
                True
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added attack indicator: {indicator_id}")
            return indicator_id
            
        except Exception as e:
            logger.error(f"Failed to add attack indicator: {e}")
            return None


# Global instance
detection_monitor = AIDetectionMonitor()

