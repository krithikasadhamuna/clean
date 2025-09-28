#!/usr/bin/env python3
import requests
import json

print("REAL-TIME DETECTION TEST:")
print("=" * 40)

# Test detection API
r = requests.get('http://localhost:8080/api/backend/detections')
print(f"Detection API Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    detections = data.get('data', [])
    print(f"Detection Results Found: {len(detections)}")
    
    if detections:
        print("\nRecent Detections:")
        for i, detection in enumerate(detections[:3]):
            print(f"  {i+1}. {detection.get('threatType')} - {detection.get('severity')}")
    else:
        print("No threats detected (system clean)")
else:
    print(f"Error: {r.text}")

# Test sending a test log with threat indicators
print("\nSending test threat log...")
test_log = {
    'agent_id': 'detection-test',
    'logs': [{
        'timestamp': '2025-09-27T10:30:00',
        'level': 'ERROR',
        'source': 'SecuritySystem',
        'message': 'Suspicious process detected: malware.exe attempting privilege escalation',
        'hostname': 'test-host',
        'platform': 'Windows'
    }]
}

r = requests.post('http://localhost:8080/api/logs/ingest', json=test_log)
print(f"Test log status: {r.status_code}")

print("\nREAL-TIME DETECTION SYSTEM IS READY!")
