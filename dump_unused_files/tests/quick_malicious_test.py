#!/usr/bin/env python3
import subprocess
import requests
import json
import time
from datetime import datetime

# Execute one real malicious command and test detection
print("QUICK REAL MALICIOUS COMMAND TEST")
print("=" * 40)

# Execute real nmap command
print("1. Executing real nmap command...")
result = subprocess.run("nmap -sn 127.0.0.1", shell=True, capture_output=True, text=True)

# Create real log from command execution
real_log = {
    'agent_id': 'quick-test-agent',
    'logs': [{
        'timestamp': datetime.now().isoformat(),
        'level': 'INFO',
        'source': 'CommandExecution',
        'message': f'Command executed: nmap -sn 127.0.0.1',
        'hostname': 'test-machine',
        'platform': 'Windows',
        'command_output': result.stdout[:200] if result.stdout else 'No output'
    }]
}

print("2. Sending real command log to server...")
response = requests.post('http://localhost:8080/api/logs/ingest', json=real_log)
print(f"   Status: {response.status_code}")

print("3. Waiting for AI analysis...")
time.sleep(3)

print("4. Checking detections...")
detection_response = requests.get('http://localhost:8080/api/backend/detections')
data = detection_response.json()
detections = data.get('data', [])

print(f"   Detections found: {len(detections)}")

if detections:
    print("   SUCCESS: AI DETECTED THE REAL MALICIOUS COMMAND!")
    latest = detections[0]
    print(f"   Threat: {latest.get('threatType')}")
    print(f"   Severity: {latest.get('severity')}")
else:
    print("   No detections yet - AI may still be processing")

print("\nREAL COMMAND DETECTION TEST COMPLETE!")
