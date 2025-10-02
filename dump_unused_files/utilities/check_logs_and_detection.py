#!/usr/bin/env python3
"""
Check if logs are constantly sent and detection is happening
"""

import sqlite3
import time
from datetime import datetime

def check_logs_and_detection():
    """Check log activity and detection status"""
    
    print("CHECKING LOGS AND DETECTION ACTIVITY")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('dev_soc_database.db')
        cursor = conn.cursor()
        
        # Check log activity over time
        print("\n1. LOG ACTIVITY CHECK")
        print("-" * 30)
        
        # Get initial log count
        cursor.execute("SELECT COUNT(*) FROM log_entries")
        initial_count = cursor.fetchone()[0]
        print(f"   Initial log count: {initial_count}")
        
        # Wait and check again
        print("   Waiting 10 seconds to check for new logs...")
        time.sleep(10)
        
        cursor.execute("SELECT COUNT(*) FROM log_entries")
        final_count = cursor.fetchone()[0]
        print(f"   Final log count: {final_count}")
        
        new_logs = final_count - initial_count
        print(f"   New logs in 10 seconds: {new_logs}")
        print(f"   Log ingestion rate: {'ACTIVE' if new_logs > 0 else 'INACTIVE'}")
        
        # Check recent log sources
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM log_entries 
            WHERE timestamp > datetime('now', '-10 minutes')
            GROUP BY source
            ORDER BY count DESC
        """)
        
        recent_sources = cursor.fetchall()
        print(f"\n   Recent log sources (last 10 minutes):")
        for source, count in recent_sources:
            print(f"      {source}: {count} logs")
        
        # Check detection activity
        print("\n2. DETECTION ACTIVITY CHECK")
        print("-" * 30)
        
        # Get detection count
        cursor.execute("SELECT COUNT(*) FROM detection_results")
        total_detections = cursor.fetchone()[0]
        print(f"   Total detections: {total_detections}")
        
        # Check recent detections
        cursor.execute("""
            SELECT COUNT(*) FROM detection_results 
            WHERE detected_at > datetime('now', '-1 hour')
        """)
        
        recent_detections = cursor.fetchone()[0]
        print(f"   Recent detections (1 hour): {recent_detections}")
        
        # Check threat types
        cursor.execute("""
            SELECT threat_type, COUNT(*) as count
            FROM detection_results
            WHERE threat_detected = 1
            GROUP BY threat_type
            ORDER BY count DESC
        """)
        
        threat_types = cursor.fetchall()
        print(f"   Detected threat types:")
        for threat_type, count in threat_types:
            print(f"      {threat_type}: {count} detections")
        
        # Check agent activity
        print("\n3. AGENT ACTIVITY CHECK")
        print("-" * 30)
        
        cursor.execute("""
            SELECT id, hostname, ip_address, status, last_heartbeat
            FROM agents
            ORDER BY last_heartbeat DESC
        """)
        
        agents = cursor.fetchall()
        print(f"   Registered agents: {len(agents)}")
        
        for agent in agents:
            agent_id, hostname, ip_address, status, last_heartbeat = agent
            print(f"      {hostname} ({ip_address}): {status}")
            print(f"         Last heartbeat: {last_heartbeat}")
        
        conn.close()
        
        # Summary
        print(f"\n4. ACTIVITY SUMMARY")
        print("-" * 30)
        print(f"   Log ingestion: {'ACTIVE' if new_logs > 0 else 'INACTIVE'}")
        print(f"   Detection engine: {'ACTIVE' if total_detections > 0 else 'INACTIVE'}")
        print(f"   Agent communication: {'ACTIVE' if len(agents) > 0 else 'INACTIVE'}")
        
        if new_logs > 0:
            print(f"   System is actively processing {new_logs} logs every 10 seconds")
        else:
            print(f"   No new logs detected - client agents may not be running")
            
    except Exception as e:
        print(f"Check failed: {e}")

if __name__ == "__main__":
    check_logs_and_detection()
