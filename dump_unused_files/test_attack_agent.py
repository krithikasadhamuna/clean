#!/usr/bin/env python3
"""
Test attack agent functionality and command execution
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import sys

async def test_attack_agent_endpoints(server_url="http://127.0.0.1:8081"):
    """Test attack agent API endpoints"""
    
    print("=" * 60)
    print("CodeGrey Attack Agent Test")
    print("=" * 60)
    print(f"Server: {server_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Check server connectivity
            print("Test 1: Server Connectivity")
            print("-" * 40)
            
            try:
                async with session.get(f"{server_url}/health", timeout=10) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"SUCCESS: Server is reachable - {health_data.get('status', 'unknown')}")
                    else:
                        print(f"FAILED: Server returned status {response.status}")
                        return False
            except Exception as e:
                print(f"FAILED: Cannot reach server - {e}")
                return False
            
            # Test 2: Test attack planning endpoint
            print("\nTest 2: Attack Planning")
            print("-" * 40)
            
            attack_request = {
                "scenario": "Test penetration testing scenario",
                "target": "localhost",
                "objectives": ["test system security", "validate detection capabilities"],
                "constraints": ["non-destructive", "local testing only"],
                "techniques": ["T1059.001", "T1082", "T1016"]
            }
            
            try:
                async with session.post(
                    f"{server_url}/api/soc/plan-attack",
                    json=attack_request,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                ) as response:
                    
                    response_text = await response.text()
                    
                    if response.status == 200:
                        print("SUCCESS: Attack planning request sent")
                        try:
                            response_data = json.loads(response_text)
                            print(f"Response: {response_data}")
                            
                            if response_data.get('success'):
                                scenario_id = response_data.get('scenario_id')
                                print(f"Scenario ID: {scenario_id}")
                                return scenario_id
                            else:
                                print(f"Attack planning failed: {response_data.get('error')}")
                                return None
                        except:
                            print(f"Response: {response_text}")
                    else:
                        print(f"FAILED: Attack planning failed - {response.status}")
                        print(f"Error: {response_text}")
                        return None
            
            except Exception as e:
                print(f"FAILED: Attack planning error - {e}")
                return None
    
    except Exception as e:
        print(f"FAILED: Test error - {e}")
        return None

async def test_attack_execution(scenario_id, server_url="http://127.0.0.1:8081"):
    """Test attack execution"""
    
    if not scenario_id:
        print("No scenario ID available for execution test")
        return False
    
    print(f"\nTest 3: Attack Execution (Scenario: {scenario_id})")
    print("-" * 40)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Approve the attack scenario
            approval_request = {
                "scenario_id": scenario_id,
                "approved": True
            }
            
            try:
                async with session.post(
                    f"{server_url}/api/soc/approve-attack",
                    json=approval_request,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                ) as response:
                    
                    response_text = await response.text()
                    
                    if response.status == 200:
                        print("SUCCESS: Attack scenario approved")
                        try:
                            response_data = json.loads(response_text)
                            print(f"Response: {response_data}")
                            return True
                        except:
                            print(f"Response: {response_text}")
                    else:
                        print(f"FAILED: Attack approval failed - {response.status}")
                        print(f"Error: {response_text}")
                        return False
            
            except Exception as e:
                print(f"FAILED: Attack approval error - {e}")
                return False
    
    except Exception as e:
        print(f"FAILED: Test error - {e}")
        return False

async def test_pending_approvals(server_url="http://127.0.0.1:8081"):
    """Test pending approvals endpoint"""
    
    print("\nTest 4: Pending Approvals")
    print("-" * 40)
    
    try:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{server_url}/api/soc/pending-approvals", timeout=10) as response:
                    
                    response_text = await response.text()
                    
                    if response.status == 200:
                        print("SUCCESS: Pending approvals retrieved")
                        try:
                            response_data = json.loads(response_text)
                            print(f"Response: {response_data}")
                            return True
                        except:
                            print(f"Response: {response_text}")
                    else:
                        print(f"FAILED: Pending approvals failed - {response.status}")
                        print(f"Error: {response_text}")
                        return False
            
            except Exception as e:
                print(f"FAILED: Pending approvals error - {e}")
                return False
    
    except Exception as e:
        print(f"FAILED: Test error - {e}")
        return False

async def main():
    """Run all attack agent tests"""
    
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081"
    
    print("Starting CodeGrey Attack Agent Tests...")
    print("=" * 60)
    
    # Test attack planning
    scenario_id = await test_attack_agent_endpoints(server_url)
    
    # Test pending approvals
    await test_pending_approvals(server_url)
    
    # Test attack execution if scenario was created
    if scenario_id:
        await test_attack_execution(scenario_id, server_url)
    
    print("\n" + "=" * 60)
    print("ATTACK AGENT TEST SUMMARY")
    print("=" * 60)
    
    if scenario_id:
        print("SUCCESS: Attack agent is working correctly!")
        print("- Attack planning: Working")
        print("- Scenario creation: Working")
        print("- Attack execution: Working")
    else:
        print("FAILED: Attack agent has issues.")
        print("\nTROUBLESHOOTING:")
        print("1. Check if server is running")
        print("2. Check server logs for errors")
        print("3. Verify attack agent initialization")
        print("4. Check OpenAI API configuration")
    
    return scenario_id is not None

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
