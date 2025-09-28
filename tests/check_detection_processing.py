#!/usr/bin/env python3
"""
Check if detection processing is working by examining the database directly
"""

import sqlite3
import json
from datetime import datetime

def check_database_detections():
    """Check database for detection results"""
    print("CHECKING DATABASE FOR DETECTIONS")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = sqlite3.connect('soc_database.db')
        cursor = conn.cursor()
        
        # Check if detection_results table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detection_results'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("Detection results table: EXISTS")
            
            # Get all detection results
            cursor.execute("SELECT * FROM detection_results ORDER BY detected_at DESC LIMIT 10")
            detections = cursor.fetchall()
            
            print(f"Total detections in database: {len(detections)}")
            
            if detections:
                print("\nRECENT DETECTIONS:")
                print("-" * 40)
                
                # Get column names
                cursor.execute("PRAGMA table_info(detection_results)")
                columns = [col[1] for col in cursor.fetchall()]
                
                for detection in detections:
                    detection_dict = dict(zip(columns, detection))
                    print(f"Detection ID: {detection_dict.get('id')}")
                    print(f"  Threat Detected: {detection_dict.get('threat_detected')}")
                    print(f"  Confidence Score: {detection_dict.get('confidence_score')}")
                    print(f"  Threat Type: {detection_dict.get('threat_type')}")
                    print(f"  Severity: {detection_dict.get('severity')}")
                    print(f"  Detected At: {detection_dict.get('detected_at')}")
                    print()
            else:
                print("No detections found in database")
        else:
            print("Detection results table: DOES NOT EXIST")
        
        # Check log entries
        cursor.execute("SELECT COUNT(*) FROM log_entries WHERE agent_id LIKE '%malicious%' OR agent_id LIKE '%guaranteed%'")
        malicious_logs = cursor.fetchone()[0]
        print(f"\nMalicious test logs in database: {malicious_logs}")
        
        if malicious_logs > 0:
            cursor.execute("""
                SELECT agent_id, level, source, message, timestamp 
                FROM log_entries 
                WHERE agent_id LIKE '%malicious%' OR agent_id LIKE '%guaranteed%'
                ORDER BY timestamp DESC LIMIT 5
            """)
            recent_logs = cursor.fetchall()
            
            print("\nRECENT MALICIOUS LOGS:")
            print("-" * 40)
            for log in recent_logs:
                print(f"Agent: {log[0]}")
                print(f"  Level: {log[1]}")
                print(f"  Source: {log[2]}")
                print(f"  Message: {log[3][:80]}...")
                print(f"  Time: {log[4]}")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

def test_detection_api_format():
    """Test the detection API response format"""
    print("\nTESTING DETECTION API FORMAT")
    print("=" * 50)
    
    try:
        import requests
        response = requests.get('http://localhost:8080/api/backend/detections')
        
        print(f"API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response structure: {list(data.keys())}")
            
            if 'data' in data:
                detections = data['data']
                print(f"Detections array length: {len(detections)}")
                
                if detections:
                    print("\nFirst detection structure:")
                    print(json.dumps(detections[0], indent=2))
                else:
                    print("Detections array is empty")
            else:
                print("No 'data' field in response")
                print("Full response:")
                print(json.dumps(data, indent=2))
        else:
            print(f"API Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

def main():
    """Main check"""
    check_database_detections()
    test_detection_api_format()
    
    print("\n" + "=" * 60)
    print("DETECTION SYSTEM ANALYSIS")
    print("=" * 60)
    print("1. Check if logs are being stored in database")
    print("2. Check if detection_results table has entries")
    print("3. Verify API response format")
    print("4. Confirm real-time detection is processing logs")

if __name__ == "__main__":
    main()
