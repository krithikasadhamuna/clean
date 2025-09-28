#!/usr/bin/env python3
"""
Check if malicious test logs are in database
"""

import sqlite3

def check_malicious_logs():
    """Check malicious logs in database"""
    try:
        conn = sqlite3.connect('dev_soc_database.db')
        cursor = conn.cursor()
        
        # Check for malicious test logs
        cursor.execute('SELECT COUNT(*) FROM log_entries WHERE agent_id = ?', ('malicious-test',))
        malicious_count = cursor.fetchone()[0]
        print(f"Malicious test logs: {malicious_count}")
        
        if malicious_count > 0:
            cursor.execute('''
                SELECT message, source, level, timestamp 
                FROM log_entries 
                WHERE agent_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 5
            ''', ('malicious-test',))
            
            print("\nRecent malicious logs:")
            for row in cursor.fetchall():
                print(f"  Message: {row[0][:100]}...")
                print(f"  Source: {row[1]}")
                print(f"  Level: {row[2]}")
                print(f"  Time: {row[3]}")
                print()
        
        # Check total recent logs
        cursor.execute('SELECT COUNT(*) FROM log_entries WHERE timestamp > datetime("now", "-1 hour")')
        recent_count = cursor.fetchone()[0]
        print(f"Total recent logs (last hour): {recent_count}")
        
        # Check detection results for malicious test
        cursor.execute('SELECT COUNT(*) FROM detection_results WHERE detected_at > datetime("now", "-1 hour")')
        recent_detections = cursor.fetchone()[0]
        print(f"Recent detections (last hour): {recent_detections}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_malicious_logs()
