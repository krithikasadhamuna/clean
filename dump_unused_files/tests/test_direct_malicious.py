#!/usr/bin/env python3
"""
Direct malicious activity test with enhanced patterns
"""

import requests
import json
import time
from datetime import datetime

def test_specific_malicious_pattern():
    """Test a specific malicious pattern"""
    
    # Test the exact pattern that should trigger detection
    malicious_log = {
        "agent_id": "malicious-test",
        "logs": [
            {
                "timestamp": datetime.now().isoformat(),
                "source": "Windows-Process",
                "level": "CRITICAL",
                "message": "powershell.exe -enc JABhAD0AJwBoAHQAdABwADoALwAvAG0AYQBsAGkAYwBpAG8AdQBzAC4AYwBvAG0A",
                "process_info": {
                    "name": "powershell.exe",
                    "command": "powershell.exe -enc JABhAD0AJwBoAHQAdABwADoALwAvAG0AYQBsAGkAYwBpAG8AdQBzAC4AYwBvAG0A"
                }
            }
        ]
    }
    
    print(" TESTING SPECIFIC MALICIOUS PATTERN")
    print("=" * 50)
    print("Pattern: powershell.exe -enc [encoded_command]")
    print("Expected: HIGH SEVERITY THREAT")
    print()
    
    try:
        # Send the malicious log
        response = requests.post(
            'http://localhost:8080/api/logs/ingest',
            json=malicious_log,
            timeout=10
        )
        
        print(f"Log ingestion status: {response.status_code}")
        
        if response.status_code == 200:
            # Wait for processing
            time.sleep(3)
            
            # Check detection results
            detection_response = requests.get('http://localhost:8080/api/backend/detections')
            
            if detection_response.status_code == 200:
                data = detection_response.json()
                print(f"Detection API status: {data.get('status')}")
                print(f"Total threats: {data.get('total_threats', 0)}")
                
                detections = data.get('detections', [])
                if detections:
                    print("\n🚨 DETECTED THREATS:")
                    for i, detection in enumerate(detections[:3]):
                        print(f"\nThreat #{i+1}:")
                        print(f"  Type: {detection.get('threat_type')}")
                        print(f"  Severity: {detection.get('severity')}")
                        print(f"  Confidence: {detection.get('confidence_score')}")
                        print(f"  Source: {detection.get('source_machine', {}).get('hostname')}")
                        print(f"  Message: {detection.get('log_info', {}).get('message')}")
                        print(f"  Detected: {detection.get('detected_at')}")
                else:
                    print(" No detections found")
            else:
                print(f"Detection API error: {detection_response.status_code}")
                print(detection_response.text)
        else:
            print(f"Log ingestion failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Test failed: {e}")

def check_server_logs():
    """Check if server is logging detection activities"""
    print("\n Checking server logs for detection activity...")
    print("Look for messages like:")
    print("  🚨 THREAT DETECTED: [threat_type] from [agent_id]")
    print("  🚨 SECURITY ALERT: X threats detected in batch")

if __name__ == "__main__":
    test_specific_malicious_pattern()
    check_server_logs()
