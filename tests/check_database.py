#!/usr/bin/env python3
"""
Check database status and detection results
"""

import sqlite3
from datetime import datetime

def check_database():
    """Check database contents and detection status"""
    try:
        conn = sqlite3.connect('dev_soc_database.db')
        cursor = conn.cursor()
        
        print("🔍 DATABASE STATUS CHECK")
        print("=" * 50)
        
        # Check log entries
        cursor.execute('SELECT COUNT(*) FROM log_entries')
        log_count = cursor.fetchone()[0]
        print(f"📊 Total log entries: {log_count}")
        
        # Check agents
        cursor.execute('SELECT COUNT(*) FROM agents')
        agent_count = cursor.fetchone()[0]
        print(f"🤖 Total agents: {agent_count}")
        
        # Show recent agents
        cursor.execute('''
            SELECT id, hostname, ip_address, status, last_heartbeat 
            FROM agents 
            ORDER BY last_heartbeat DESC 
            LIMIT 5
        ''')
        
        print(f"\n👥 REGISTERED AGENTS:")
        agents = cursor.fetchall()
        if agents:
            for row in agents:
                print(f"  • ID: {row[0]}")
                print(f"    Hostname: {row[1]}")
                print(f"    IP: {row[2]}")
                print(f"    Status: {row[3]}")
                print(f"    Last Heartbeat: {row[4]}")
                print()
        else:
            print("  No agents registered yet")
        
        # Check recent logs
        cursor.execute('''
            SELECT agent_id, source, level, message, timestamp 
            FROM log_entries 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        
        print(f"\n📝 RECENT LOGS (Last 10):")
        logs = cursor.fetchall()
        if logs:
            for row in logs:
                print(f"  • Agent: {row[0] or 'unknown'}")
                print(f"    Source: {row[1]}")
                print(f"    Level: {row[2]}")
                print(f"    Message: {row[3][:60]}...")
                print(f"    Time: {row[4]}")
                print()
        else:
            print("  No logs found")
        
        # Check detection results
        cursor.execute('SELECT COUNT(*) FROM detection_results')
        detection_count = cursor.fetchone()[0]
        print(f"🛡️  Detection results: {detection_count}")
        
        if detection_count > 0:
            cursor.execute('''
                SELECT threat_detected, threat_type, severity, confidence_score 
                FROM detection_results 
                ORDER BY detected_at DESC 
                LIMIT 5
            ''')
            
            print(f"\n🚨 RECENT DETECTIONS:")
            for row in cursor.fetchall():
                print(f"  • Threat: {row[0]}")
                print(f"    Type: {row[1]}")
                print(f"    Severity: {row[2]}")
                print(f"    Confidence: {row[3]}")
                print()
        else:
            print("  No threat detections yet")
        
        conn.close()
        
        # Analysis
        print("🎯 ANALYSIS:")
        print("-" * 30)
        if agent_count == 0:
            print("❌ No agents registered - heartbeat data not being stored")
        else:
            print("✅ Agents are being registered")
            
        if log_count == 0:
            print("❌ No logs stored - log ingestion not working")
        else:
            print(f"✅ {log_count} logs stored - ingestion working")
            
        if detection_count == 0:
            print("⚠️  No threat detections - detection engine may not be running")
        else:
            print(f"✅ {detection_count} detections - threat detection active")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_database()
