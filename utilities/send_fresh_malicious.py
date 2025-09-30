#!/usr/bin/env python3
"""
Send a fresh malicious log to trigger real-time detection
"""

import requests
import json
from datetime import datetime

def send_malicious_log():
    """Send a single malicious log"""
    
    malicious_payload = {
        "agent_id": "realtime-test",
        "logs": [
            {
                "timestamp": datetime.now().isoformat(),
                "source": "Windows-Process",
                "level": "CRITICAL",
                "message": "powershell.exe -enc MALICIOUS_ENCODED_COMMAND_DETECTED_BY_AI_SOC",
                "process_info": {
                    "name": "powershell.exe",
                    "pid": 9999,
                    "command": "powershell.exe -enc MALICIOUS_ENCODED_COMMAND"
                }
            }
        ]
    }
    
    print("🚨 SENDING FRESH MALICIOUS LOG")
    print("=" * 40)
    print("Expected: IMMEDIATE threat detection")
    print("Pattern: powershell.exe -enc")
    print("Level: CRITICAL")
    print("Source: Windows-Process")
    print()
    
    try:
        response = requests.post(
            'http://localhost:8080/api/logs/ingest',
            json=malicious_payload,
            timeout=10
        )
        
        print(f" Log sent - Status: {response.status_code}")
        
        if response.status_code == 200:
            print(" Server accepted the log")
            print("🔍 Check your server terminal for:")
            print("   🚨 THREAT DETECTED: malicious_processes from realtime-test")
            print("   🚨 SECURITY ALERT: 1 threats detected in batch")
        else:
            print(f" Server error: {response.text}")
            
    except Exception as e:
        print(f" Error: {e}")

if __name__ == "__main__":
    send_malicious_log()
