#!/usr/bin/env python3
"""
Simple test to verify AI detection on actual malicious content
"""

import requests
import json
import time
from datetime import datetime

def test_simple_malicious_detection():
    """Test simple malicious content detection"""
    print("SIMPLE MALICIOUS DETECTION TEST")
    print("=" * 50)
    
    # Send a simple log with obvious malicious content
    malicious_log = {
        'agent_id': 'simple-test',
        'logs': [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',  # INFO level but malicious content
                'source': 'TestSystem',
                'message': 'Executed nmap -sS 192.168.1.0/24 network scanning command',
                'hostname': 'test-machine',
                'platform': 'Linux'
            }
        ]
    }
    
    try:
        print("1. Sending malicious log...")
        response = requests.post(
            'http://localhost:8080/api/logs/ingest',
            json=malicious_log,
            timeout=10
        )
        
        print(f"   Log ingestion status: {response.status_code}")
        
        if response.status_code == 200:
            print("   SUCCESS: Log ingested")
            
            # Wait for processing
            print("2. Waiting for AI analysis...")
            time.sleep(2)
            
            # Check detections
            print("3. Checking for detections...")
            detection_response = requests.get('http://localhost:8080/api/backend/detections')
            
            if detection_response.status_code == 200:
                data = detection_response.json()
                detections = data.get('data', [])
                
                print(f"   Total detections: {len(detections)}")
                
                if detections:
                    print("   SUCCESS: AI DETECTED THE THREAT!")
                    latest = detections[0]
                    print(f"   Threat Type: {latest.get('threatType')}")
                    print(f"   Severity: {latest.get('severity')}")
                    print(f"   Message: {latest.get('logMessage', '')[:60]}...")
                else:
                    print("   NO DETECTIONS: AI analysis may not be running")
                    
                    # Check server logs for errors
                    print("   Checking if logs were processed...")
                    topology_response = requests.get('http://localhost:8080/api/backend/network-topology')
                    if topology_response.status_code == 200:
                        topology_data = topology_response.json()
                        endpoints = topology_data.get('data', [])
                        
                        our_endpoint = None
                        for endpoint in endpoints:
                            if 'simple-test' in endpoint.get('hostname', ''):
                                our_endpoint = endpoint
                                break
                        
                        if our_endpoint:
                            print(f"   LOGS PROCESSED: Found agent in topology")
                            print(f"   Last seen: {our_endpoint.get('lastSeen')}")
                        else:
                            print("   LOGS NOT PROCESSED: Agent not in topology")
            else:
                print(f"   Detection API error: {detection_response.status_code}")
        else:
            print(f"   FAILED: {response.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_simple_malicious_detection()
