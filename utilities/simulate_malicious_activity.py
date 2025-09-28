#!/usr/bin/env python3
"""
Simulate malicious activity to test threat detection
"""

import requests
import json
import time
from datetime import datetime

def simulate_malicious_logs():
    """Send malicious log samples to test detection"""
    
    malicious_scenarios = [
        {
            "name": "PowerShell Encoded Command",
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": "Windows-Process",
                    "level": "WARNING",
                    "message": "Process powershell.exe executed with arguments: -enc JABhAD0AJwBoAHQAdABwADoALwAvAG0AYQBsAGkAYwBpAG8AdQBzAC4AYwBvAG0A",
                    "process_info": {
                        "name": "powershell.exe",
                        "pid": 1234,
                        "command": "powershell.exe -enc JABhAD0AJwBoAHQAdABwADoALwAvAG0AYQBsAGkAYwBpAG8AdQBzAC4AYwBvAG0A"
                    }
                }
            ]
        },
        {
            "name": "Suspicious User Creation",
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": "Windows-Security",
                    "level": "ERROR",
                    "message": "Command executed: net user hacker P@ssw0rd /add",
                    "process_info": {
                        "name": "cmd.exe",
                        "command": "net user hacker P@ssw0rd /add"
                    }
                }
            ]
        },
        {
            "name": "Registry Modification",
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": "Windows-System",
                    "level": "CRITICAL",
                    "message": "Registry modification: reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v malware /d C:\\temp\\evil.exe",
                    "registry_info": {
                        "key": "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                        "value": "malware",
                        "data": "C:\\temp\\evil.exe"
                    }
                }
            ]
        },
        {
            "name": "Suspicious File Download",
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": "Windows-Network",
                    "level": "WARNING",
                    "message": "File download via certutil: certutil -decode c:\\temp\\encoded.txt c:\\temp\\malware.exe",
                    "network_info": {
                        "source_ip": "192.168.1.100",
                        "destination": "malicious.com",
                        "protocol": "HTTPS"
                    }
                }
            ]
        },
        {
            "name": "Scheduled Task Creation",
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": "Windows-System",
                    "level": "ERROR",
                    "message": "Scheduled task created: schtasks /create /tn 'BackdoorTask' /tr 'C:\\temp\\backdoor.exe' /sc minute /mo 5",
                    "task_info": {
                        "name": "BackdoorTask",
                        "command": "C:\\temp\\backdoor.exe",
                        "schedule": "every 5 minutes"
                    }
                }
            ]
        },
        {
            "name": "WMIC Process Creation",
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": "Windows-Process",
                    "level": "CRITICAL",
                    "message": "Remote process creation: wmic process call create 'cmd.exe /c whoami > c:\\temp\\info.txt'",
                    "process_info": {
                        "method": "wmic",
                        "command": "cmd.exe /c whoami > c:\\temp\\info.txt",
                        "remote": True
                    }
                }
            ]
        }
    ]
    
    print("🚨 SIMULATING MALICIOUS ACTIVITY")
    print("=" * 50)
    
    for scenario in malicious_scenarios:
        print(f"\n🎯 Testing: {scenario['name']}")
        
        # Send malicious logs to server
        payload = {
            "agent_id": "test-malicious-agent",
            "logs": scenario["logs"]
        }
        
        try:
            response = requests.post(
                'http://localhost:8080/api/logs/ingest',
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ Sent malicious logs")
                
                # Wait a moment for processing
                time.sleep(2)
                
                # Check for detections
                detection_response = requests.get('http://localhost:8080/api/backend/detections')
                if detection_response.status_code == 200:
                    detection_data = detection_response.json()
                    threat_count = detection_data.get('total_threats', 0)
                    
                    if threat_count > 0:
                        print(f"   🚨 THREAT DETECTED! Total threats: {threat_count}")
                        
                        # Show latest detection
                        detections = detection_data.get('detections', [])
                        if detections:
                            latest = detections[0]
                            print(f"      Type: {latest.get('threat_type')}")
                            print(f"      Severity: {latest.get('severity')}")
                            print(f"      Confidence: {latest.get('confidence_score'):.2f}")
                    else:
                        print(f"   ⚠️ No threat detected yet")
                else:
                    print(f"   ❌ Detection API error: {detection_response.status_code}")
            else:
                print(f"   ❌ Failed to send logs: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Small delay between scenarios
        time.sleep(3)
    
    print(f"\n🎯 SIMULATION COMPLETE")
    print("Check the detection results API for all detected threats")

if __name__ == "__main__":
    simulate_malicious_logs()
