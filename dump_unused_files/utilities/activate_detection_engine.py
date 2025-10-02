#!/usr/bin/env python3
"""
Activate the threat detection engine to process stored logs
"""

import asyncio
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def activate_detection_engine():
    """Activate detection engine to process all stored logs"""
    try:
        logger.info(" ACTIVATING THREAT DETECTION ENGINE")
        logger.info("=" * 50)
        
        # Import detection components
        from agents.detection_agent.real_threat_detector import real_threat_detector
        from agents.detection_agent.langchain_detection_agent import LangChainDetectionAgent
        
        # Initialize detection agent
        detection_agent = LangChainDetectionAgent()
        
        # Get all unprocessed logs from database
        conn = sqlite3.connect('dev_soc_database.db')
        cursor = conn.cursor()
        
        # Get logs that haven't been processed for detection
        cursor.execute('''
            SELECT le.id, le.agent_id, le.source, le.timestamp, le.message, 
                   le.level, le.raw_data, le.parsed_data, le.enriched_data
            FROM log_entries le
            LEFT JOIN detection_results dr ON le.id = dr.log_entry_id
            WHERE dr.id IS NULL
            ORDER BY le.timestamp DESC
            LIMIT 100
        ''')
        
        unprocessed_logs = cursor.fetchall()
        logger.info(f" Found {len(unprocessed_logs)} unprocessed logs")
        
        if not unprocessed_logs:
            logger.info(" All logs already processed")
            return
        
        # Process each log through detection engine
        detections_found = 0
        for i, log_row in enumerate(unprocessed_logs):
            log_id, agent_id, source, timestamp, message, level, raw_data, parsed_data, enriched_data = log_row
            
            # Convert to detection format
            log_entry = {
                'id': log_id,
                'agent_id': agent_id or 'unknown',
                'source': source,
                'timestamp': timestamp,
                'message': message,
                'level': level,
                'raw_data': raw_data,
                'parsed_data': json.loads(parsed_data) if parsed_data else {},
                'enriched_data': json.loads(enriched_data) if enriched_data else {}
            }
            
            # Run threat detection
            try:
                detection_data = detection_agent._convert_log_to_detection_data(log_entry)
                result = await detection_agent.analyze_threat(detection_data)
                
                # Store detection result
                if result:
                    threat_detected = result.threat_score > 0.5
                    
                    # Generate unique detection ID
                    import uuid
                    detection_id = str(uuid.uuid4())
                    
                    # Store in detection_results table
                    cursor.execute('''
                        INSERT INTO detection_results (
                            id, log_entry_id, threat_detected, confidence_score, 
                            threat_type, severity, ml_results, ai_analysis,
                            detected_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        detection_id,
                        log_id,
                        threat_detected,
                        result.threat_score,
                        result.threat_type or 'unknown',
                        result.severity,
                        json.dumps(result.ml_results) if hasattr(result, 'ml_results') else '{}',
                        json.dumps({
                            'reasoning': result.reasoning,
                            'recommendations': result.recommendations,
                            'indicators': result.indicators
                        }),
                        datetime.now().isoformat()
                    ))
                    
                    if threat_detected:
                        detections_found += 1
                        logger.info(f"🚨 THREAT DETECTED: {result.threat_type} (Score: {result.threat_score:.2f})")
                        logger.info(f"   Source: {source}")
                        logger.info(f"   Message: {message[:100]}...")
                        logger.info(f"   Severity: {result.severity}")
                        logger.info(f"   Reasoning: {result.reasoning}")
                        
                # Progress indicator
                if (i + 1) % 20 == 0:
                    logger.info(f"📈 Processed {i + 1}/{len(unprocessed_logs)} logs...")
                    
            except Exception as e:
                logger.error(f"Detection failed for log {log_id}: {e}")
                continue
        
        # Commit all detection results
        conn.commit()
        conn.close()
        
        logger.info(" DETECTION ENGINE ACTIVATION COMPLETE")
        logger.info("=" * 50)
        logger.info(f" Processed: {len(unprocessed_logs)} logs")
        logger.info(f"🚨 Threats found: {detections_found}")
        logger.info(f" Benign logs: {len(unprocessed_logs) - detections_found}")
        
        if detections_found > 0:
            logger.info("🚨 SECURITY ALERTS GENERATED - Check detection_results table")
        else:
            logger.info(" No immediate threats detected in recent logs")
            
        return detections_found
        
    except Exception as e:
        logger.error(f" Detection engine activation failed: {e}")
        return 0

async def setup_continuous_detection():
    """Setup continuous detection for new logs"""
    logger.info(" Setting up continuous detection pipeline...")
    
    try:
        from agents.detection_agent.langchain_detection_agent import LangChainDetectionAgent
        
        detection_agent = LangChainDetectionAgent()
        
        # Create a simple log stream from database polling
        async def log_stream_generator():
            """Generate log stream from database"""
            last_processed_time = datetime.now()
            
            while True:
                try:
                    conn = sqlite3.connect('dev_soc_database.db')
                    cursor = conn.cursor()
                    
                    # Get new logs since last check
                    cursor.execute('''
                        SELECT le.id, le.agent_id, le.source, le.timestamp, le.message, 
                               le.level, le.raw_data, le.parsed_data, le.enriched_data
                        FROM log_entries le
                        LEFT JOIN detection_results dr ON le.id = dr.log_entry_id
                        WHERE dr.id IS NULL AND le.timestamp > ?
                        ORDER BY le.timestamp ASC
                        LIMIT 50
                    ''', (last_processed_time.isoformat(),))
                    
                    new_logs = cursor.fetchall()
                    conn.close()
                    
                    if new_logs:
                        # Convert to log format
                        log_batch = []
                        for log_row in new_logs:
                            log_id, agent_id, source, timestamp, message, level, raw_data, parsed_data, enriched_data = log_row
                            log_batch.append({
                                'id': log_id,
                                'agent_id': agent_id or 'unknown',
                                'source': source,
                                'timestamp': timestamp,
                                'message': message,
                                'level': level,
                                'raw_data': raw_data,
                                'parsed_data': json.loads(parsed_data) if parsed_data else {},
                                'enriched_data': json.loads(enriched_data) if enriched_data else {}
                            })
                        
                        yield log_batch
                        last_processed_time = datetime.now()
                    
                    # Wait before next check
                    await asyncio.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    logger.error(f"Log stream error: {e}")
                    await asyncio.sleep(30)
        
        # Start continuous detection
        logger.info(" Starting continuous threat detection pipeline")
        await detection_agent.continuous_detection_pipeline(log_stream_generator())
        
    except Exception as e:
        logger.error(f"Continuous detection setup failed: {e}")

if __name__ == "__main__":
    # Run activation
    detections = asyncio.run(activate_detection_engine())
    
    if detections > 0:
        print(f"\n🚨 SECURITY ALERT: {detections} threats detected!")
        print("Run the following to see threat details:")
        print("python check_database.py")
    else:
        print("\n System appears secure - no immediate threats detected")
        print("Continuous monitoring is now active")
