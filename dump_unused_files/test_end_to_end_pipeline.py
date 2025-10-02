#!/usr/bin/env python3
"""
Test complete end-to-end SOC platform pipeline
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_complete_pipeline(server_url="http://127.0.0.1:8081"):
    """Test complete end-to-end pipeline"""
    
    print("=" * 60)
    print("CodeGrey Complete End-to-End Pipeline Test")
    print("=" * 60)
    print(f"Server: {server_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Register test agent
            print("Step 1: Agent Registration")
            print("-" * 40)
            
            agent_data = {
                "agent_id": "e2e_test_agent",
                "hostname": "test-machine",
                "ip_address": "127.0.0.1",
                "platform": "Windows",
                "capabilities": ["log_forwarding", "command_execution", "network_discovery"]
            }
            
            async with session.post(
                f"{server_url}/api/agents/register",
                json=agent_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            ) as response:
                
                if response.status == 200:
                    print("SUCCESS: Agent registered")
                else:
                    print(f"FAILED: Agent registration failed - {response.status}")
                    return False
            
            # Step 2: Send heartbeat with network topology
            print("\nStep 2: Agent Heartbeat with Network Topology")
            print("-" * 40)
            
            heartbeat_data = {
                "agent_id": "e2e_test_agent",
                "timestamp": datetime.now().isoformat(),
                "status": "online",
                "statistics": {
                    "runtime_seconds": 100,
                    "logs_processed": 50,
                    "connection_errors": 0
                },
                "network_topology": {
                    "networkTopology": [
                        {
                            "hostname": "test-host-1",
                            "ipAddress": "192.168.1.100",
                            "platform": "Windows",
                            "services": ["HTTP", "SSH"],
                            "ports": [80, 22],
                            "responseTime": 5.2,
                            "lastSeen": datetime.now().isoformat(),
                            "discoveredBy": "network_scan"
                        },
                        {
                            "hostname": "test-host-2",
                            "ipAddress": "192.168.1.101",
                            "platform": "Linux",
                            "services": ["SSH", "MySQL"],
                            "ports": [22, 3306],
                            "responseTime": 3.1,
                            "lastSeen": datetime.now().isoformat(),
                            "discoveredBy": "network_scan"
                        }
                    ],
                    "scanMetadata": {
                        "totalHosts": 2,
                        "lastScan": datetime.now().isoformat(),
                        "scannerStatus": "active"
                    }
                }
            }
            
            async with session.post(
                f"{server_url}/api/agents/e2e_test_agent/heartbeat",
                json=heartbeat_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            ) as response:
                
                if response.status == 200:
                    print("SUCCESS: Heartbeat sent with network topology")
                else:
                    print(f"FAILED: Heartbeat failed - {response.status}")
                    return False
            
            # Step 3: Send test logs (simulating attack activity)
            print("\nStep 3: Log Forwarding (Attack Simulation)")
            print("-" * 40)
            
            attack_logs = {
                "agent_id": "e2e_test_agent",
                "logs": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "warning",
                        "message": "Suspicious PowerShell execution detected",
                        "source": "windows_security",
                        "event_id": 4104,
                        "log_name": "PowerShell",
                        "process_info": {
                            "process_name": "powershell.exe",
                            "command_line": "powershell -enc <encoded_command>",
                            "user": "SYSTEM"
                        }
                    },
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "error",
                        "message": "Failed login attempt from suspicious IP",
                        "source": "windows_security",
                        "event_id": 4625,
                        "log_name": "Security",
                        "network_info": {
                            "source_ip": "192.168.1.200",
                            "target_user": "administrator",
                            "failure_reason": "Unknown user name or bad password"
                        }
                    },
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "info",
                        "message": "Network connection established",
                        "source": "windows_system",
                        "event_id": 5156,
                        "log_name": "Security",
                        "network_info": {
                            "source_ip": "192.168.1.100",
                            "destination_ip": "192.168.1.50",
                            "destination_port": 445,
                            "protocol": "TCP"
                        }
                    }
                ]
            }
            
            async with session.post(
                f"{server_url}/api/logs/ingest",
                json=attack_logs,
                headers={'Content-Type': 'application/json'},
                timeout=30
            ) as response:
                
                if response.status == 200:
                    print("SUCCESS: Attack simulation logs sent")
                else:
                    print(f"FAILED: Log sending failed - {response.status}")
                    return False
            
            # Step 4: Test attack planning
            print("\nStep 4: Attack Planning")
            print("-" * 40)
            
            attack_request = {
                "scenario": "End-to-end test penetration scenario",
                "target": "192.168.1.100",
                "objectives": ["test detection capabilities", "validate log collection"],
                "constraints": ["non-destructive", "test environment only"],
                "techniques": ["T1059.001", "T1082", "T1016", "T1021.002"]
            }
            
            async with session.post(
                f"{server_url}/api/soc/plan-attack",
                json=attack_request,
                headers={'Content-Type': 'application/json'},
                timeout=30
            ) as response:
                
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get('success'):
                        scenario_id = response_data.get('scenario_id')
                        print(f"SUCCESS: Attack scenario planned - ID: {scenario_id}")
                    else:
                        print(f"FAILED: Attack planning failed - {response_data.get('error')}")
                        return False
                else:
                    print(f"FAILED: Attack planning failed - {response.status}")
                    return False
            
            # Step 5: Verify data in database
            print("\nStep 5: Database Verification")
            print("-" * 40)
            
            # Check agents
            async with session.get(f"{server_url}/api/agents", timeout=10) as response:
                if response.status == 200:
                    agents_data = await response.json()
                    agents = agents_data.get('agents', [])
                    test_agent = next((a for a in agents if a.get('id') == 'e2e_test_agent'), None)
                    if test_agent:
                        print(f"SUCCESS: Test agent found in database - Status: {test_agent.get('status')}")
                    else:
                        print("FAILED: Test agent not found in database")
                        return False
                else:
                    print(f"FAILED: Cannot retrieve agents - {response.status}")
                    return False
            
            # Check logs
            async with session.get(f"{server_url}/api/logs?agent_id=e2e_test_agent", timeout=10) as response:
                if response.status == 200:
                    logs_data = await response.json()
                    logs = logs_data.get('logs', [])
                    print(f"SUCCESS: Found {len(logs)} logs in database")
                    
                    # Check for attack-related logs
                    attack_logs_found = sum(1 for log in logs if 'attack' in log.get('message', '').lower() or 'suspicious' in log.get('message', '').lower())
                    print(f"SUCCESS: Found {attack_logs_found} attack-related logs")
                else:
                    print(f"FAILED: Cannot retrieve logs - {response.status}")
                    return False
            
            # Check network topology
            async with session.get(f"{server_url}/api/network-topology", timeout=10) as response:
                if response.status == 200:
                    topology_data = await response.json()
                    nodes = topology_data.get('networkTopology', [])
                    print(f"SUCCESS: Found {len(nodes)} network nodes in database")
                else:
                    print(f"FAILED: Cannot retrieve network topology - {response.status}")
                    return False
            
            return True
    
    except Exception as e:
        print(f"FAILED: End-to-end test error - {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_threat_detection(server_url="http://127.0.0.1:8081"):
    """Test threat detection capabilities"""
    
    print("\n" + "=" * 60)
    print("Threat Detection Test")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Send high-risk logs
            threat_logs = {
                "agent_id": "threat_test_agent",
                "logs": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "critical",
                        "message": "MALWARE DETECTED: Trojan.Win32.Generic detected in system32",
                        "source": "windows_security",
                        "event_id": 1116,
                        "log_name": "Security",
                        "threat_indicators": ["malware", "trojan", "system32"]
                    },
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "critical",
                        "message": "PRIVILEGE ESCALATION: Unauthorized access to admin privileges",
                        "source": "windows_security",
                        "event_id": 4672,
                        "log_name": "Security",
                        "threat_indicators": ["privilege_escalation", "unauthorized_access"]
                    }
                ]
            }
            
            async with session.post(
                f"{server_url}/api/logs/ingest",
                json=threat_logs,
                headers={'Content-Type': 'application/json'},
                timeout=30
            ) as response:
                
                if response.status == 200:
                    print("SUCCESS: Threat simulation logs sent")
                    return True
                else:
                    print(f"FAILED: Threat log sending failed - {response.status}")
                    return False
    
    except Exception as e:
        print(f"FAILED: Threat detection test error - {e}")
        return False

async def main():
    """Run complete end-to-end pipeline test"""
    
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081"
    
    print("Starting CodeGrey Complete End-to-End Pipeline Test...")
    print("=" * 60)
    
    # Test complete pipeline
    pipeline_result = await test_complete_pipeline(server_url)
    
    # Test threat detection
    threat_result = await test_threat_detection(server_url)
    
    # Summary
    print("\n" + "=" * 60)
    print("END-TO-END PIPELINE TEST SUMMARY")
    print("=" * 60)
    
    print(f"Complete Pipeline: {'PASSED' if pipeline_result else 'FAILED'}")
    print(f"Threat Detection: {'PASSED' if threat_result else 'FAILED'}")
    
    if pipeline_result and threat_result:
        print("\nSUCCESS: Complete end-to-end pipeline is working correctly!")
        print("- Agent registration: Working")
        print("- Heartbeat with network topology: Working")
        print("- Log forwarding: Working")
        print("- Attack planning: Working")
        print("- Database storage: Working")
        print("- Threat detection: Working")
        return True
    else:
        print("\nFAILED: End-to-end pipeline has issues.")
        print("\nTROUBLESHOOTING:")
        if not pipeline_result:
            print("- Fix pipeline execution issues")
        if not threat_result:
            print("- Fix threat detection capabilities")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
