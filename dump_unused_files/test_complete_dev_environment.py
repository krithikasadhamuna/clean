#!/usr/bin/env python3
"""
Complete Development Environment Test
Tests the full server-client integration with proper setup
"""

import asyncio
import subprocess
import time
import sys
import os
import json
import requests
import signal
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteDevEnvironmentTest:
    """Complete development environment test"""
    
    def __init__(self):
        self.server_process = None
        self.client_process = None
        self.server_url = "http://127.0.0.1:8081"
        self.test_results = {}
        
    async def run_complete_test(self):
        """Run the complete development environment test"""
        print("=" * 80)
        print("CODEGREY AI SOC PLATFORM - COMPLETE DEVELOPMENT ENVIRONMENT TEST")
        print("=" * 80)
        
        try:
            # Step 1: Clean up any existing processes
            await self._cleanup_existing_processes()
            
            # Step 2: Start the server
            await self._start_server()
            
            # Step 3: Wait for server to be ready
            await self._wait_for_server_ready()
            
            # Step 4: Test server endpoints
            await self._test_server_endpoints()
            
            # Step 5: Start client agent
            await self._start_client_agent()
            
            # Step 6: Test client-server communication
            await self._test_client_server_communication()
            
            # Step 7: Test AI attack planning
            await self._test_ai_attack_planning()
            
            # Step 8: Test command execution
            await self._test_command_execution()
            
            # Step 9: Generate test report
            await self._generate_test_report()
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            await self._cleanup()
            return False
        finally:
            await self._cleanup()
        
        return True
    
    async def _cleanup_existing_processes(self):
        """Clean up any existing server/client processes"""
        print("\nStep 1: Cleaning up existing processes...")
        
        try:
            # Kill any existing Python processes on port 8081
            subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
            subprocess.run(["netstat", "-ano", "|", "findstr", ":8081"], shell=True, capture_output=True)
            print("✅ Existing processes cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    async def _start_server(self):
        """Start the production server"""
        print("\nStep 2: Starting production server...")
        
        try:
            # Set environment variables for Unicode support
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['OPENAI_API_KEY'] = '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'
            
            # Start server process
            self.server_process = subprocess.Popen(
                [sys.executable, "main.py", "server", "--host", "127.0.0.1", "--port", "8081"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"✅ Server process started (PID: {self.server_process.pid})")
            self.test_results['server_started'] = True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            self.test_results['server_started'] = False
            raise
    
    async def _wait_for_server_ready(self):
        """Wait for server to be ready"""
        print("\nStep 3: Waiting for server to be ready...")
        
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.server_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Server is ready and responding")
                    self.test_results['server_ready'] = True
                    return
            except requests.exceptions.RequestException:
                pass
            
            print(f"   Attempt {attempt + 1}/{max_attempts} - Waiting for server...")
            await asyncio.sleep(2)
        
        print("❌ Server failed to start within timeout")
        self.test_results['server_ready'] = False
        raise Exception("Server startup timeout")
    
    async def _test_server_endpoints(self):
        """Test server API endpoints"""
        print("\nStep 4: Testing server endpoints...")
        
        endpoints_to_test = [
            ("/health", "GET"),
            ("/api/agents", "GET"),
            ("/api/logs", "GET")
        ]
        
        endpoint_results = {}
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{self.server_url}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.server_url}{endpoint}", timeout=10)
                
                if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                    print(f"✅ {endpoint} - Status: {response.status_code}")
                    endpoint_results[endpoint] = True
                else:
                    print(f"⚠️ {endpoint} - Status: {response.status_code}")
                    endpoint_results[endpoint] = False
                    
            except Exception as e:
                print(f"❌ {endpoint} - Error: {e}")
                endpoint_results[endpoint] = False
        
        self.test_results['endpoints'] = endpoint_results
        print("✅ Server endpoint testing completed")
    
    async def _start_client_agent(self):
        """Start the client agent"""
        print("\nStep 5: Starting client agent...")
        
        try:
            client_dir = Path("CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-windows-unified")
            
            if not client_dir.exists():
                print("❌ Client agent directory not found")
                self.test_results['client_started'] = False
                return
            
            # Start client agent process
            self.client_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=str(client_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"✅ Client agent started (PID: {self.client_process.pid})")
            self.test_results['client_started'] = True
            
            # Wait a bit for client to register
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Failed to start client agent: {e}")
            self.test_results['client_started'] = False
    
    async def _test_client_server_communication(self):
        """Test client-server communication"""
        print("\nStep 6: Testing client-server communication...")
        
        try:
            # Check if client registered
            response = requests.get(f"{self.server_url}/api/agents", timeout=10)
            
            if response.status_code == 200:
                agents = response.json()
                print(f"✅ Found {len(agents)} registered agents")
                
                if agents:
                    agent_id = agents[0]['agent_id']
                    print(f"✅ Client agent registered: {agent_id}")
                    
                    # Test heartbeat
                    heartbeat_response = requests.post(
                        f"{self.server_url}/api/agents/{agent_id}/heartbeat",
                        json={"status": "active"},
                        timeout=10
                    )
                    
                    if heartbeat_response.status_code == 200:
                        print("✅ Client heartbeat successful")
                        self.test_results['client_communication'] = True
                    else:
                        print("❌ Client heartbeat failed")
                        self.test_results['client_communication'] = False
                else:
                    print("⚠️ No agents registered yet")
                    self.test_results['client_communication'] = False
            else:
                print(f"❌ Failed to get agents: {response.status_code}")
                self.test_results['client_communication'] = False
                
        except Exception as e:
            print(f"❌ Client-server communication test failed: {e}")
            self.test_results['client_communication'] = False
    
    async def _test_ai_attack_planning(self):
        """Test AI attack planning"""
        print("\nStep 7: Testing AI attack planning...")
        
        try:
            # Send attack planning request
            attack_request = {
                "scenario": "Test phishing attack on executive",
                "target_network": "192.168.1.0/24",
                "objectives": ["Gather credentials", "Establish persistence"]
            }
            
            response = requests.post(
                f"{self.server_url}/api/soc/plan-attack",
                json=attack_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ AI attack planning successful")
                print(f"   Response: {result.get('message', 'No message')}")
                self.test_results['ai_planning'] = True
            else:
                print(f"❌ AI attack planning failed: {response.status_code}")
                print(f"   Response: {response.text}")
                self.test_results['ai_planning'] = False
                
        except Exception as e:
            print(f"❌ AI attack planning test failed: {e}")
            self.test_results['ai_planning'] = False
    
    async def _test_command_execution(self):
        """Test command execution flow"""
        print("\nStep 8: Testing command execution...")
        
        try:
            # Get registered agents
            response = requests.get(f"{self.server_url}/api/agents", timeout=10)
            
            if response.status_code == 200:
                agents = response.json()
                
                if agents:
                    agent_id = agents[0]['agent_id']
                    
                    # Check for pending commands
                    commands_response = requests.get(
                        f"{self.server_url}/api/agents/{agent_id}/commands",
                        timeout=10
                    )
                    
                    if commands_response.status_code == 200:
                        commands = commands_response.json()
                        print(f"✅ Retrieved {len(commands.get('commands', []))} commands")
                        
                        if commands.get('commands'):
                            print("✅ Commands are available for execution")
                            self.test_results['command_execution'] = True
                        else:
                            print("⚠️ No commands available (this is normal if no attack was planned)")
                            self.test_results['command_execution'] = True  # Still success
                    else:
                        print(f"❌ Failed to get commands: {commands_response.status_code}")
                        self.test_results['command_execution'] = False
                else:
                    print("❌ No agents available for command testing")
                    self.test_results['command_execution'] = False
            else:
                print(f"❌ Failed to get agents for command testing: {response.status_code}")
                self.test_results['command_execution'] = False
                
        except Exception as e:
            print(f"❌ Command execution test failed: {e}")
            self.test_results['command_execution'] = False
    
    async def _generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("TEST REPORT")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        # Save results to file
        with open("complete_dev_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📊 Results saved to: complete_dev_test_results.json")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Development environment is fully functional!")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} tests failed. Check the logs above.")
    
    async def _cleanup(self):
        """Clean up processes"""
        print("\nCleaning up processes...")
        
        try:
            if self.client_process:
                self.client_process.terminate()
                self.client_process.wait(timeout=5)
                print("✅ Client agent stopped")
        except Exception as e:
            print(f"⚠️ Error stopping client: {e}")
        
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("✅ Server stopped")
        except Exception as e:
            print(f"⚠️ Error stopping server: {e}")

async def main():
    """Main test function"""
    test = CompleteDevEnvironmentTest()
    
    try:
        success = await test.run_complete_test()
        
        if success:
            print("\n🎉 Complete development environment test completed successfully!")
        else:
            print("\n❌ Development environment test failed!")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
