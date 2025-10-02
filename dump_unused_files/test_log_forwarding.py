#!/usr/bin/env python3
"""
Test script to verify log forwarding is working
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import sys

async def test_log_ingestion_endpoint(server_url="http://backend.codegrey.ai:8080"):
    """Test the log ingestion endpoint directly"""
    
    print("=" * 60)
    print("CodeGrey Log Forwarding Test")
    print("=" * 60)
    print(f"Server: {server_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test data
    test_logs = [
        {
            "agent_id": "test_agent_log_forwarding",
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "info",
                    "message": "Test log entry 1 - System startup",
                    "source": "windows_system",
                    "event_id": 1001,
                    "log_name": "System",
                    "provider": "Microsoft-Windows-Kernel-General"
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "warning",
                    "message": "Test log entry 2 - Security event",
                    "source": "windows_security",
                    "event_id": 4624,
                    "log_name": "Security",
                    "provider": "Microsoft-Windows-Security-Auditing"
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "error",
                    "message": "Test log entry 3 - Application error",
                    "source": "windows_application",
                    "event_id": 1000,
                    "log_name": "Application",
                    "provider": "Application Error"
                }
            ]
        }
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Check if server is reachable
            print("Test 1: Server Connectivity")
            print("-" * 40)
            
            try:
                async with session.get(f"{server_url}/health", timeout=10) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"Server is reachable: {health_data.get('status', 'unknown')}")
                    else:
                        print(f"Server returned status {response.status}")
                        return False
            except Exception as e:
                print(f"Cannot reach server: {e}")
                return False
            
            # Test 2: Test log ingestion endpoint
            print("\nTest 2: Log Ingestion Endpoint")
            print("-" * 40)
            
            for i, test_data in enumerate(test_logs, 1):
                print(f"Sending test batch {i} with {len(test_data['logs'])} logs...")
                
                try:
                    async with session.post(
                        f"{server_url}/api/logs/ingest",
                        json=test_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=30
                    ) as response:
                        
                        response_text = await response.text()
                        
                        if response.status == 200:
                            print(f"Log batch {i} sent successfully")
                            try:
                                response_data = json.loads(response_text)
                                print(f"   Response: {response_data}")
                            except:
                                print(f"   Response: {response_text}")
                        else:
                            print(f"Log batch {i} failed: {response.status}")
                            print(f"   Error: {response_text}")
                            return False
                
                except Exception as e:
                    print(f"Log batch {i} error: {e}")
                    return False
            
            # Test 3: Check if logs were stored
            print("\n🗄️ Test 3: Database Verification")
            print("-" * 40)
            
            try:
                async with session.get(f"{server_url}/api/logs", timeout=10) as response:
                    if response.status == 200:
                        logs_data = await response.json()
                        total_logs = logs_data.get('total', 0)
                        print(f" Database contains {total_logs} total logs")
                        
                        # Check for our test logs
                        logs = logs_data.get('logs', [])
                        test_logs_found = 0
                        for log in logs:
                            if log.get('agent_id') == 'test_agent_log_forwarding':
                                test_logs_found += 1
                        
                        print(f" Found {test_logs_found} test logs in database")
                        
                        if test_logs_found > 0:
                            print(" Log forwarding is working correctly!")
                        else:
                            print("WARNING: Test logs not found in database")
                        
                    else:
                        print(f" Failed to retrieve logs: {response.status}")
                        return False
            
            except Exception as e:
                print(f" Database verification error: {e}")
                return False
            
            # Test 4: Check agent status
            print("\n👤 Test 4: Agent Status Check")
            print("-" * 40)
            
            try:
                async with session.get(f"{server_url}/api/agents", timeout=10) as response:
                    if response.status == 200:
                        agents_data = await response.json()
                        agents = agents_data.get('agents', [])
                        
                        test_agent_found = False
                        for agent in agents:
                            if agent.get('id') == 'test_agent_log_forwarding':
                                test_agent_found = True
                                print(f" Test agent found: {agent.get('status', 'unknown')} status")
                                break
                        
                        if not test_agent_found:
                            print("WARNING: Test agent not found in agents list")
                    
                    else:
                        print(f" Failed to retrieve agents: {response.status}")
            
            except Exception as e:
                print(f" Agent status check error: {e}")
            
            return True
    
    except Exception as e:
        print(f" Test failed: {e}")
        return False

async def test_client_agent_log_collection():
    """Test if the client agent can actually collect logs"""
    
    print("\n🔍 Test 5: Client Agent Log Collection")
    print("-" * 40)
    
    try:
        # Import client agent components
        from core.client.forwarders.windows_forwarder import WindowsLogForwarder
        from shared.models import LogSource
        
        # Test configuration
        test_config = {
            'windows': {
                'event_logs': ['System', 'Application'],
                'wmi_enabled': False
            }
        }
        
        print("Creating Windows log forwarder...")
        forwarder = WindowsLogForwarder("test_agent", test_config)
        
        print("Testing log collection (5 seconds)...")
        
        # Start forwarder
        await forwarder.start()
        
        # Wait for logs to be collected
        await asyncio.sleep(5)
        
        # Check if logs were collected
        logs_collected = 0
        while not forwarder.log_queue.empty():
            log = await forwarder.log_queue.get()
            logs_collected += 1
            print(f"   Collected log: {log.get('message', 'No message')[:50]}...")
        
        await forwarder.stop()
        
        if logs_collected > 0:
            print(f" Client agent collected {logs_collected} logs")
            return True
        else:
            print(" Client agent collected no logs")
            return False
    
    except Exception as e:
        print(f" Client agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all log forwarding tests"""
    
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://backend.codegrey.ai:8080"
    
    print("Starting CodeGrey Log Forwarding Tests...")
    print("=" * 60)
    
    results = []
    
    # Test server-side log ingestion
    results.append(await test_log_ingestion_endpoint(server_url))
    
    # Test client-side log collection
    results.append(await test_client_agent_log_collection())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print(" All tests passed! Log forwarding is working correctly.")
    else:
        print(" Some tests failed. Log forwarding has issues.")
    
    print("\n RECOMMENDATIONS:")
    print("-" * 40)
    
    if not results[0]:
        print("- Fix server-side log ingestion endpoint")
        print("- Check server logs for errors")
        print("- Verify database connectivity")
    
    if not results[1]:
        print("- Fix client-side log collection")
        print("- Check Windows Event Log permissions")
        print("- Verify PowerShell execution policy")
    
    if results[0] and results[1]:
        print("- Log forwarding is working correctly!")
        print("- Monitor production logs for any issues")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
