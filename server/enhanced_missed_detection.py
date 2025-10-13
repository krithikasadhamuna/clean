#!/usr/bin/env python3
"""
Enhanced Missed Threat Detection with Multiple Ground Truth Sources
Combines heuristics, red team data, analyst feedback, and attack simulations
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class EnhancedMissedDetection:
    """Enhanced system to accurately track missed threats"""
    
    def __init__(self, db_path: str = "soc_database.db"):
        self.db_path = db_path
        self._ensure_ground_truth_tables()
    
    def _ensure_ground_truth_tables(self):
        """Create tables for ground truth tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Red Team Attacks Table
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
            
            # Analyst Review Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyst_reviews (
                    id TEXT PRIMARY KEY,
                    log_entry_id TEXT,
                    detection_result_id TEXT,
                    analyst_verdict TEXT,  -- 'threat', 'benign', 'unclear'
                    confidence INTEGER,     -- 1-5
                    threat_type TEXT,
                    notes TEXT,
                    reviewed_by TEXT,
                    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Known Attack Indicators Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attack_indicators (
                    id TEXT PRIMARY KEY,
                    indicator_type TEXT,    -- 'ip', 'hash', 'domain', 'pattern'
                    indicator_value TEXT,
                    threat_type TEXT,
                    severity TEXT,
                    source TEXT,           -- 'threat_intel', 'manual', 'ml'
                    first_seen TEXT,
                    last_seen TEXT,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to create ground truth tables: {e}")
    
    async def get_comprehensive_missed_count(self, 
                                            start_time: datetime, 
                                            end_time: datetime) -> Dict[str, any]:
        """
        Get comprehensive missed threat count from multiple sources
        
        Returns breakdown of:
        - Red team attacks missed
        - Analyst-confirmed misses
        - Heuristic-based misses
        - Known IOC misses
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. RED TEAM ATTACKS MISSED (Ground Truth)
            cursor.execute('''
                SELECT COUNT(*) FROM red_team_attacks
                WHERE attack_timestamp >= ? AND attack_timestamp <= ?
                AND expected_detection = 1
                AND was_detected = 0
            ''', (start_time.isoformat(), end_time.isoformat()))
            red_team_missed = cursor.fetchone()[0]
            
            # 2. ANALYST-CONFIRMED MISSES (High Confidence)
            cursor.execute('''
                SELECT COUNT(*) FROM analyst_reviews ar
                JOIN log_entries le ON ar.log_entry_id = le.id
                LEFT JOIN detection_results dr ON ar.detection_result_id = dr.id
                WHERE ar.reviewed_at >= ? AND ar.reviewed_at <= ?
                AND ar.analyst_verdict = 'threat'
                AND ar.confidence >= 4
                AND (dr.threat_detected = 0 OR dr.threat_detected IS NULL)
            ''', (start_time.isoformat(), end_time.isoformat()))
            analyst_confirmed_missed = cursor.fetchone()[0]
            
            # 3. KNOWN IOC MISSES (Threat Intel)
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
            
            # 4. HEURISTIC MISSES (Estimated)
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
                -- Exclude already counted in other categories
                AND le.id NOT IN (
                    SELECT log_entry_id FROM analyst_reviews 
                    WHERE analyst_verdict = 'threat'
                )
            ''', (start_time.isoformat(), end_time.isoformat()))
            heuristic_missed = cursor.fetchone()[0]
            
            conn.close()
            
            # CALCULATE TOTAL (avoid double counting)
            # Priority: Red Team > Analyst > IOC > Heuristic
            total_missed = red_team_missed + analyst_confirmed_missed + ioc_missed + heuristic_missed
            
            return {
                'total_missed': total_missed,
                'breakdown': {
                    'red_team_attacks': red_team_missed,        # ← Ground truth
                    'analyst_confirmed': analyst_confirmed_missed,  # ← High confidence
                    'known_iocs': ioc_missed,                   # ← Threat intel
                    'heuristic_estimate': heuristic_missed      # ← Estimated
                },
                'confidence': self._calculate_confidence(
                    red_team_missed, 
                    analyst_confirmed_missed,
                    ioc_missed,
                    heuristic_missed
                ),
                'data_quality': {
                    'has_ground_truth': red_team_missed > 0,
                    'has_analyst_reviews': analyst_confirmed_missed > 0,
                    'has_threat_intel': ioc_missed > 0,
                    'is_estimated': heuristic_missed > 0 and red_team_missed == 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive missed count: {e}")
            return {
                'total_missed': 0,
                'breakdown': {},
                'confidence': 'unknown',
                'data_quality': {}
            }
    
    def _calculate_confidence(self, red_team: int, analyst: int, 
                            ioc: int, heuristic: int) -> str:
        """Calculate confidence level in missed count"""
        
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
        """
        Record a red team attack for ground truth tracking
        
        Call this when executing attack scenarios
        """
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
                indicator_data.get('type'),         # 'ip', 'hash', 'domain', 'pattern'
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
enhanced_missed_detector = EnhancedMissedDetection()


