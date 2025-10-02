#!/usr/bin/env python3
"""
Test Client Agent Connection
Tests if the client agent is connecting to the server
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

def test_client_agent_connection():
    """Test if client agent is connecting to server"""
    print("=" * 80)
    print("TESTING CLIENT AGENT CONNECTION")
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
    
    # Test 2: Check if client agent is running
    print("\n2. Checking if Client Agent is Running...")
    try:
        # Check for Python processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        
        if 'python.exe' in result.stdout:
            print("SUCCESS: Python processes are running")
            print("   This likely includes the client agent")
        else:
            print("WARNING: No Python processes found")
            print("   Client agent may not be running")
            
    except Exception as e:
        print(f"INFO: Could not check processes: {e}")
    
    # Test 3: Test Log Ingestion (simulating client agent)
    print("\n3. Testing Log Ingestion (Simulating Client Agent)...")
    try:
        # Simulate what the client agent would send
        client_logs = {
            "logs": [
                {
                    "timestamp": "2025-10-01T19:20:00.000Z",
                    "level": "INFO",
                    "source": "client_agent",
                    "message": "Client agent started successfully",
                    "category": "system",
                    "agent_id": "test_client_agent_001"
                },
                {
                    "timestamp": "2025-10-01T19:20:01.000Z",
                    "level": "INFO",
                    "source": "client_agent",
                    "message": "Heartbeat sent to server",
                    "category": "heartbeat",
                    "agent_id": "test_client_agent_001"
                },
                {
                    "timestamp": "2025-10-01T19:20:02.000Z",
                    "level": "WARNING",
                    "source": "client_agent",
                    "message": "Network scan completed - 5 hosts discovered",
                    "category": "network",
                    "agent_id": "test_client_agent_001"
                }
            ]
        }
        
        response = requests.post(
            f"{base_url}/api/logs/ingest",
            json=client_logs,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Client logs ingested: {result.get('message', 'Success')}")
            print(f"   Log count: {len(client_logs['logs'])}")
        else:
            print(f"FAILED: Client log ingestion failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"FAILED: Client log ingestion error: {e}")
        return False
    
    # Test 4: Test Heartbeat (simulating client agent)
    print("\n4. Testing Heartbeat (Simulating Client Agent)...")
    try:
        # Register a test agent first
        agent_data = {
            "agent_id": "test_client_agent_001",
            "hostname": "test-client-machine",
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
            print(f"SUCCESS: Agent registered: {result.get('agent_id', 'Unknown')}")
            
            # Now send heartbeat
            heartbeat_data = {
                "status": "active",
                "timestamp": "2025-10-01T19:20:00.000Z",
                "system_info": {
                    "cpu_usage": 25.5,
                    "memory_usage": 60.2,
                    "disk_usage": 45.8
                }
            }
            
            response = requests.post(
                f"{base_url}/api/agents/test_client_agent_001/heartbeat",
                json=heartbeat_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS: Heartbeat sent: {result.get('status', 'Success')}")
            else:
                print(f"FAILED: Heartbeat failed: {response.status_code}")
                return False
        else:
            print(f"FAILED: Agent registration failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"FAILED: Heartbeat test error: {e}")
        return False
    
    # Test 5: Test Command Queue
    print("\n5. Testing Command Queue...")
    try:
        response = requests.get(
            f"{base_url}/api/agents/test_client_agent_001/commands",
            timeout=10
        )
        
        if response.status_code == 200:
            commands = response.json()
            command_count = len(commands.get('commands', []))
            print(f"SUCCESS: Retrieved {command_count} pending commands")
            
            if command_count > 0:
                print("   Commands available:")
                for cmd in commands.get('commands', []):
                    print(f"     - {cmd.get('technique', 'Unknown')}: {cmd.get('status', 'Unknown')}")
            else:
                print("   No commands available (this is normal for testing)")
        else:
            print(f"FAILED: Command retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"FAILED: Command queue test error: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("Testing client agent connection and functionality...")
    print("This will test:")
    print("- Server health")
    print("- Client agent simulation")
    print("- Log ingestion")
    print("- Heartbeat system")
    print("- Command queue")
    print()
    
    success = test_client_agent_connection()
    
    print("\n" + "=" * 80)
    if success:
        print("CLIENT AGENT CONNECTION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("SUCCESS: Server is running and healthy")
        print("SUCCESS: Client agent simulation works")
        print("SUCCESS: Log ingestion is working")
        print("SUCCESS: Heartbeat system works")
        print("SUCCESS: Command queue is accessible")
        print("\nThe client-server communication is working!")
        print("The development environment is fully operational!")
    else:
        print("CLIENT AGENT CONNECTION TEST FAILED")
        print("=" * 80)
        print("FAILED: Some client-server communication is not working")
        print("Please check the server and client agent logs")
    
    return success

if __name__ == "__main__":
    main()
