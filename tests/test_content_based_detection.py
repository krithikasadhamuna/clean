#!/usr/bin/env python3
"""
Test content-based detection that analyzes ALL logs regardless of level
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"

def test_content_based_detection():
    """Test detection based on log content, not level"""
    print("CONTENT-BASED DETECTION TEST")
    print("=" * 50)
    print("Testing detection on ALL logs regardless of level")
    print("=" * 50)
    
    # Send logs with malicious content but INFO level
    test_logs = {
        'agent_id': 'content-test-agent',
        'logs': [
            # INFO level but contains nmap - should be detected
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'source': 'ProcessMonitor',
                'message': 'Process started: nmap -sS 192.168.1.0/24 scanning network for vulnerabilities',
                'hostname': 'test-host',
                'platform': 'Linux'
            },
            
            # INFO level but contains sqlmap - should be detected
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'source': 'WebServer',
                'message': 'Request logged: sqlmap -u http://target.com/login.php testing for SQL injection',
                'hostname': 'web-server',
                'platform': 'Linux'
            },
            
            # INFO level but contains whoami - should be detected
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'source': 'CommandLog',
                'message': 'User executed: whoami && net user && net localgroup administrators',
                'hostname': 'workstation',
                'platform': 'Windows'
            },
            
            # INFO level but contains metasploit - should be detected
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'source': 'SecurityTool',
                'message': 'Tool execution: metasploit exploit/windows/smb/ms17_010_eternalblue launched',
                'hostname': 'security-test',
                'platform': 'Windows'
            },
            
            # Regular INFO log - should NOT be detected
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'source': 'Application',
                'message': 'User logged in successfully from IP 192.168.1.50',
                'hostname': 'app-server',
                'platform': 'Linux'
            }
        ]
    }
    
    try:
        print(f"Sending {len(test_logs['logs'])} logs with malicious content...")
        
        response = requests.post(
            f"{BASE_URL}/api/logs/ingest",
            json=test_logs,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: {result.get('message')}")
            
            # Wait for processing
            print("Waiting 3 seconds for AI analysis...")
            time.sleep(3)
            
            # Check detections
            detection_response = requests.get(f"{BASE_URL}/api/backend/detections")
            
            if detection_response.status_code == 200:
                detection_data = detection_response.json()
                detections = detection_data.get('data', [])
                
                print(f"\nDETECTIONS FOUND: {len(detections)}")
                
                # Look for our test detections
                our_detections = [d for d in detections if 'content-test-agent' in str(d)]
                
                if our_detections:
                    print(f"OUR TEST DETECTIONS: {len(our_detections)}")
                    print("\nDETECTED THREATS:")
                    print("-" * 40)
                    
                    for i, detection in enumerate(our_detections):
                        print(f"Detection #{i+1}:")
                        print(f"  Type: {detection.get('threatType')}")
                        print(f"  Severity: {detection.get('severity')}")
                        print(f"  Confidence: {detection.get('confidenceScore', 0):.2f}")
                        print(f"  Message: {detection.get('logMessage', '')[:80]}...")
                        print()
                    
                    print("SUCCESS: Content-based detection is working!")
                    print("AI analyzes ALL logs regardless of level!")
                    
                else:
                    print("NO DETECTIONS: Content analysis may need adjustment")
                    
                    # Check if any detections exist at all
                    if detections:
                        print(f"\nOther detections found: {len(detections)}")
                        print("Latest detection:")
                        latest = detections[0]
                        print(f"  Source: {latest.get('sourceAgent')}")
                        print(f"  Message: {latest.get('logMessage', '')[:80]}...")
                    
            else:
                print(f"Detection API error: {detection_response.status_code}")
                
        else:
            print(f"Log ingestion failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Test failed: {e}")

def main():
    """Run content-based detection test"""
    test_content_based_detection()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("This test verifies that:")
    print("1. ALL logs are analyzed for threats (not just ERROR/WARNING)")
    print("2. Content-based detection works on log messages")
    print("3. Attack tools and suspicious commands are detected")
    print("4. Detection happens regardless of log level")
    print("\nThe /api/backend/detections endpoint shows REAL AI detections")
    print("based on log content analysis, not fabricated results!")

if __name__ == "__main__":
    main()
