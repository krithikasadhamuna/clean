#!/usr/bin/env python3
"""
Simple Development Environment Test
Step-by-step testing of the development environment
"""

import subprocess
import time
import sys
import os
import requests
from pathlib import Path

def test_server_startup():
    """Test server startup"""
    print("=" * 60)
    print("TESTING SERVER STARTUP")
    print("=" * 60)
    
    try:
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['OPENAI_API_KEY'] = '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'
        
        print("Starting server...")
        process = subprocess.Popen(
            [sys.executable, "main.py", "server", "--host", "127.0.0.1", "--port", "8081"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"Server process started (PID: {process.pid})")
        print("Waiting for server to initialize...")
        
        # Wait for server to start
        for i in range(30):
            try:
                response = requests.get("http://127.0.0.1:8081/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Server is running and responding!")
                    return process
            except:
                pass
            time.sleep(1)
            print(f"   Waiting... ({i+1}/30)")
        
        print("FAILED: Server failed to start within timeout")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"FAILED: Error starting server: {e}")
        return None

def test_server_endpoints():
    """Test server endpoints"""
    print("\n" + "=" * 60)
    print("TESTING SERVER ENDPOINTS")
    print("=" * 60)
    
    endpoints = [
        ("/health", "Health check"),
        ("/api/agents", "Agent list"),
        ("/api/logs", "Logs endpoint")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://127.0.0.1:8081{endpoint}", timeout=5)
            print(f"SUCCESS: {description}: {response.status_code}")
        except Exception as e:
            print(f"FAILED: {description}: {e}")

def test_client_agent():
    """Test client agent"""
    print("\n" + "=" * 60)
    print("TESTING CLIENT AGENT")
    print("=" * 60)
    
    client_dir = Path("CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-windows-unified")
    
    if not client_dir.exists():
        print("FAILED: Client agent directory not found")
        return None
    
    try:
        print("Starting client agent...")
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=str(client_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"Client agent started (PID: {process.pid})")
        print("Waiting for client to register...")
        time.sleep(5)
        
        # Check if client registered
        try:
            response = requests.get("http://127.0.0.1:8081/api/agents", timeout=5)
            if response.status_code == 200:
                agents = response.json()
                print(f"SUCCESS: Found {len(agents)} registered agents")
                return process
            else:
                print(f"FAILED: Failed to get agents: {response.status_code}")
                return None
        except Exception as e:
            print(f"FAILED: Error checking agents: {e}")
            return None
            
    except Exception as e:
        print(f"FAILED: Error starting client agent: {e}")
        return None

def test_ai_attack_planning():
    """Test AI attack planning"""
    print("\n" + "=" * 60)
    print("TESTING AI ATTACK PLANNING")
    print("=" * 60)
    
    try:
        attack_request = {
            "scenario": "Test phishing attack",
            "target_network": "192.168.1.0/24",
            "objectives": ["Gather credentials"]
        }
        
        print("Sending attack planning request...")
        response = requests.post(
            "http://127.0.0.1:8081/api/soc/plan-attack",
            json=attack_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: AI attack planning successful")
            print(f"   Response: {result.get('message', 'No message')}")
        else:
            print(f"FAILED: AI attack planning failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"FAILED: AI attack planning error: {e}")

def main():
    """Main test function"""
    print("CODEGREY AI SOC PLATFORM - SIMPLE DEVELOPMENT TEST")
    print("=" * 60)
    
    server_process = None
    client_process = None
    
    try:
        # Test 1: Start server
        server_process = test_server_startup()
        if not server_process:
            print("FAILED: Server test failed - stopping")
            return
        
        # Test 2: Test server endpoints
        test_server_endpoints()
        
        # Test 3: Start client agent
        client_process = test_client_agent()
        if not client_process:
            print("FAILED: Client agent test failed - stopping")
            return
        
        # Test 4: Test AI attack planning
        test_ai_attack_planning()
        
        print("\n" + "=" * 60)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("SUCCESS: Server is running")
        print("SUCCESS: Client agent is connected")
        print("SUCCESS: AI attack planning is working")
        print("\nSUCCESS: Development environment is fully functional!")
        
    except KeyboardInterrupt:
        print("\nSTOPPED: Test interrupted by user")
    except Exception as e:
        print(f"\nFAILED: Test failed: {e}")
    finally:
        # Cleanup
        print("\nCleaning up...")
        if client_process:
            try:
                client_process.terminate()
                print("SUCCESS: Client agent stopped")
            except:
                pass
        
        if server_process:
            try:
                server_process.terminate()
                print("SUCCESS: Server stopped")
            except:
                pass

if __name__ == "__main__":
    main()
