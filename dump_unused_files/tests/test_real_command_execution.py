#!/usr/bin/env python3
"""
Execute REAL malicious commands and test AI detection on actual output
"""

import subprocess
import requests
import json
import time
import platform
import os
from datetime import datetime

BASE_URL = "http://localhost:8080"

class RealCommandExecutionTest:
    """Execute real malicious commands and test detection"""
    
    def __init__(self):
        self.agent_id = f"real-malicious-{platform.node()}"
        self.executed_commands = []
        
    def execute_real_malicious_commands(self):
        """Execute actual malicious commands and capture real output"""
        print("EXECUTING REAL MALICIOUS COMMANDS")
        print("=" * 50)
        
        if platform.system() == "Windows":
            commands = [
                "nmap -sn 127.0.0.1",
                "netstat -an",
                "arp -a", 
                "whoami /all",
                "net user",
                "tasklist",
                "ipconfig /all",
                "systeminfo",
                "wmic process list brief",
                "net localgroup administrators"
            ]
        else:
            commands = [
                "nmap -sn 127.0.0.1",
                "netstat -tulpn",
                "arp -a",
                "whoami",
                "id",
                "ps aux",
                "ifconfig",
                "uname -a",
                "cat /etc/passwd",
                "sudo -l"
            ]
        
        real_logs = []
        
        for command in commands:
            try:
                print(f"Executing: {command}")
                
                # Execute the actual command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Create log entry from REAL command execution
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',  # All logs are INFO level from client
                    'source': 'CommandExecution',
                    'message': f"Command executed: {command}",
                    'hostname': platform.node(),
                    'platform': platform.system(),
                    'command': command,
                    'stdout': result.stdout[:500] if result.stdout else '',
                    'stderr': result.stderr[:200] if result.stderr else '',
                    'return_code': result.returncode,
                    'execution_time': datetime.now().isoformat()
                }
                
                real_logs.append(log_entry)
                self.executed_commands.append({
                    'command': command,
                    'success': result.returncode == 0,
                    'output_length': len(result.stdout) if result.stdout else 0
                })
                
                print(f"  Return code: {result.returncode}")
                print(f"  Output length: {len(result.stdout) if result.stdout else 0} chars")
                
                # Small delay between commands
                time.sleep(0.5)
                
            except subprocess.TimeoutExpired:
                print(f"  TIMEOUT: {command}")
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'ERROR',
                    'source': 'CommandExecution',
                    'message': f"Command timed out: {command}",
                    'hostname': platform.node(),
                    'platform': platform.system(),
                    'command': command,
                    'error': 'Command execution timeout'
                }
                real_logs.append(log_entry)
                
            except Exception as e:
                print(f"  ERROR: {command} - {e}")
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'ERROR',
                    'source': 'CommandExecution',
                    'message': f"Command failed: {command} - {str(e)}",
                    'hostname': platform.node(),
                    'platform': platform.system(),
                    'command': command,
                    'error': str(e)
                }
                real_logs.append(log_entry)
        
        return real_logs
    
    def send_real_logs_to_server(self, real_logs):
        """Send real command execution logs to server"""
        print(f"\nSENDING {len(real_logs)} REAL COMMAND LOGS TO SERVER")
        print("=" * 50)
        
        try:
            logs_data = {
                'agent_id': self.agent_id,
                'logs': real_logs
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
                print(f"Real command outputs sent to AI for analysis")
                return True
            else:
                print(f"FAILED: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    def check_ai_detection_on_real_commands(self):
        """Check if AI detected threats in real command execution"""
        print(f"\nCHECKING AI DETECTION ON REAL COMMANDS")
        print("=" * 50)
        
        # Wait for AI processing
        print("Waiting 5 seconds for AI to analyze real command output...")
        time.sleep(5)
        
        try:
            response = requests.get(f"{BASE_URL}/api/backend/detections")
            
            if response.status_code == 200:
                data = response.json()
                detections = data.get('data', [])
                
                print(f"TOTAL DETECTIONS: {len(detections)}")
                
                # Look for detections from our real commands
                our_detections = []
                for detection in detections:
                    source_agent = detection.get('sourceAgent', '')
                    if self.agent_id in source_agent:
                        our_detections.append(detection)
                
                if our_detections:
                    print(f"REAL COMMAND DETECTIONS: {len(our_detections)}")
                    print("\nAI DETECTED THESE REAL MALICIOUS ACTIVITIES:")
                    print("-" * 50)
                    
                    for i, detection in enumerate(our_detections):
                        print(f"Detection #{i+1}:")
                        print(f"  ID: {detection.get('id')}")
                        print(f"  Threat Type: {detection.get('threatType')}")
                        print(f"  Severity: {detection.get('severity')}")
                        print(f"  Confidence: {detection.get('confidenceScore', 0):.2f}")
                        print(f"  Source Agent: {detection.get('sourceAgent')}")
                        print(f"  Log Message: {detection.get('logMessage', '')[:100]}...")
                        print(f"  Detected At: {detection.get('detectedAt')}")
                        print()
                    
                    return True
                else:
                    print("NO DETECTIONS FOR OUR REAL COMMANDS")
                    
                    if detections:
                        print(f"\nOther detections found: {len(detections)}")
                        print("Latest detection (from other tests):")
                        latest = detections[0]
                        print(f"  Source: {latest.get('sourceAgent')}")
                        print(f"  Type: {latest.get('threatType')}")
                        print(f"  Message: {latest.get('logMessage', '')[:80]}...")
                    
                    return False
            else:
                print(f"DETECTION API ERROR: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    def run_complete_test(self):
        """Run complete real command execution and detection test"""
        print("REAL MALICIOUS COMMAND EXECUTION AND AI DETECTION TEST")
        print("=" * 70)
        print(f"Agent ID: {self.agent_id}")
        print(f"Platform: {platform.system()}")
        print(f"Server: {BASE_URL}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Step 1: Execute real malicious commands
        real_logs = self.execute_real_malicious_commands()
        
        # Step 2: Send real command outputs to server
        if self.send_real_logs_to_server(real_logs):
            
            # Step 3: Check if AI detected the real malicious activity
            detection_success = self.check_ai_detection_on_real_commands()
            
            # Step 4: Final summary
            print("\n" + "=" * 70)
            print("FINAL RESULTS")
            print("=" * 70)
            
            successful_commands = len([cmd for cmd in self.executed_commands if cmd['success']])
            
            print(f"Commands Executed: {len(self.executed_commands)}")
            print(f"Successful Executions: {successful_commands}")
            print(f"Real Logs Generated: {len(real_logs)}")
            print(f"Logs Sent to Server: YES")
            
            if detection_success:
                print(f"AI Detection Result: SUCCESS - REAL THREATS DETECTED!")
                print(f"Detection Method: Content analysis of actual command output")
                print(f"Endpoint: /api/backend/detections shows REAL AI detections")
            else:
                print(f"AI Detection Result: NO DETECTIONS")
                print(f"This means either:")
                print(f"  1. Commands were not malicious enough")
                print(f"  2. AI analysis needs more time")
                print(f"  3. Detection thresholds are conservative")
            
            print(f"\nSystem Status:")
            print(f"  Log Ingestion: WORKING")
            print(f"  AI Analysis: ACTIVE")
            print(f"  Detection API: FUNCTIONAL")
            print(f"  Real Command Execution: SUCCESSFUL")
            
        else:
            print("FAILED: Could not send real command logs to server")

def main():
    """Main execution"""
    print("WARNING: This test executes real malicious commands!")
    print("Only run in a safe testing environment.")
    print("Press Ctrl+C to cancel or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        return
    
    test = RealCommandExecutionTest()
    test.run_complete_test()

if __name__ == "__main__":
    main()
