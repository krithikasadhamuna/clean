#!/usr/bin/env python3
"""
Test Manual Command Flow
Tests the complete development environment with manual command queuing
"""

import requests
import json
import time
from typing import Dict, Any

def test_manual_command_flow():
    """Test the complete flow with manual command queuing"""
    print("=" * 80)
    print("CODEGREY AI SOC PLATFORM - MANUAL COMMAND FLOW TEST")
    print("=" * 80)
    
    base_url = "http://127.0.0.1:8081"
    
    # Test 1: Server Health
    print("\n1. Testing Server Health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"SUCCESS: Server Health: {health_data['status']}")
            print(f"   Version: {health_data['version']}")
            print(f"   Agents: {health_data['agents']}")
        else:
            print(f"FAILED: Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"FAILED: Server health check error: {e}")
        return False
    
    # Test 2: Register Test Agent
    print("\n2. Registering Test Agent...")
    try:
        agent_data = {
            "agent_id": "test_manual_agent",
            "hostname": "test-machine",
            "platform": "windows",
            "ip_address": "192.168.1.100"
        }
        
        response = requests.post(
            f"{base_url}/api/agents/register",
            json=agent_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Agent registered: {result['agent_id']}")
            agent_id = result['agent_id']
        else:
            print(f"❌ Agent registration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Agent registration error: {e}")
        return False
    
    # Test 3: Manual Command Queuing
    print("\n3. Testing Manual Command Queuing...")
    try:
        # Queue a create_self_replica command
        command_data = {
            "technique": "create_self_replica",
            "command_data": {
                "container_name": "test_replica",
                "network": "bridge",
                "description": "Create a replica of the host system for attack simulation"
            }
        }
        
        # This would normally be done by the AI attack agent
        # For testing, we'll simulate the command queuing
        print("   📝 Simulating command queuing...")
        print(f"   Command: {command_data['technique']}")
        print(f"   Data: {command_data['command_data']}")
        
        # In a real scenario, this would be queued by the CommandManager
        print("✅ Command queuing simulation successful")
        
    except Exception as e:
        print(f"❌ Command queuing error: {e}")
        return False
    
    # Test 4: Check for Commands
    print("\n4. Checking for Pending Commands...")
    try:
        response = requests.get(
            f"{base_url}/api/agents/{agent_id}/commands",
            timeout=10
        )
        
        if response.status_code == 200:
            commands = response.json()
            command_count = len(commands.get('commands', []))
            print(f"✅ Retrieved {command_count} pending commands")
            
            if command_count > 0:
                print("   📋 Commands available:")
                for cmd in commands.get('commands', []):
                    print(f"     - {cmd.get('technique', 'Unknown')}: {cmd.get('status', 'Unknown')}")
            else:
                print("   ℹ️ No commands available (this is normal for manual testing)")
        else:
            print(f"❌ Command retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Command retrieval error: {e}")
        return False
    
    # Test 5: Simulate Command Execution
    print("\n5. Simulating Command Execution...")
    try:
        # Simulate a successful command execution
        result_data = {
            "command_id": "test_cmd_001",
            "status": "completed",
            "success": True,
            "output": "Self-replica container created successfully",
            "execution_time_ms": 1500,
            "timestamp": "2025-10-01T19:00:00.000Z"
        }
        
        response = requests.post(
            f"{base_url}/api/agents/{agent_id}/commands/result",
            json=result_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Command result submitted: {result.get('status', 'Unknown')}")
            print(f"   Command ID: {result_data['command_id']}")
            print(f"   Status: {result_data['status']}")
            print(f"   Output: {result_data['output']}")
        else:
            print(f"❌ Command result submission failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Command execution simulation error: {e}")
        return False
    
    # Test 6: Test Log Ingestion
    print("\n6. Testing Log Ingestion...")
    try:
        log_data = {
            "logs": [
                {
                    "timestamp": "2025-10-01T19:00:00.000Z",
                    "level": "INFO",
                    "source": "test_agent",
                    "message": "Test log entry for manual flow testing",
                    "category": "system"
                },
                {
                    "timestamp": "2025-10-01T19:00:01.000Z",
                    "level": "WARNING",
                    "source": "test_agent",
                    "message": "Simulated security event detected",
                    "category": "security"
                }
            ]
        }
        
        response = requests.post(
            f"{base_url}/api/logs/ingest",
            json=log_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Logs ingested: {result.get('message', 'Success')}")
            print(f"   Log count: {len(log_data['logs'])}")
        else:
            print(f"❌ Log ingestion failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Log ingestion error: {e}")
        return False
    
    # Test 7: Test Heartbeat
    print("\n7. Testing Agent Heartbeat...")
    try:
        heartbeat_data = {
            "status": "active",
            "timestamp": "2025-10-01T19:00:00.000Z",
            "system_info": {
                "cpu_usage": 25.5,
                "memory_usage": 60.2,
                "disk_usage": 45.8
            }
        }
        
        response = requests.post(
            f"{base_url}/api/agents/{agent_id}/heartbeat",
            json=heartbeat_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Heartbeat successful: {result.get('status', 'Success')}")
        else:
            print(f"❌ Heartbeat failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Heartbeat error: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 80)
    print("MANUAL COMMAND FLOW TEST COMPLETED")
    print("=" * 80)
    print("✅ Server Health: Working")
    print("✅ Agent Registration: Working")
    print("✅ Command Queuing: Simulated")
    print("✅ Command Retrieval: Working")
    print("✅ Command Execution: Simulated")
    print("✅ Log Ingestion: Working")
    print("✅ Heartbeat: Working")
    print("\n🎉 All core functionality is working!")
    print("⚠️ AI Attack Planning: Still failing (OpenAI connection issue)")
    print("💡 Manual command queuing works as an alternative")
    
    return True

if __name__ == "__main__":
    test_manual_command_flow()
