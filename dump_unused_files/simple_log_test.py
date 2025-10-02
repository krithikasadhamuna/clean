#!/usr/bin/env python3
"""
Simple log forwarding test without Unicode characters
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import sys

async def test_log_ingestion(server_url="http://127.0.0.1:8081"):
    """Test log ingestion endpoint"""
    
    print("=" * 60)
    print("CodeGrey Log Forwarding Test")
    print("=" * 60)
    print(f"Server: {server_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test data
    test_data = {
        "agent_id": "test_agent_log_forwarding",
        "logs": [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": "Test log entry - System startup",
                "source": "windows_system",
                "event_id": 1001,
                "log_name": "System"
            }
        ]
    }
    
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
            
            # Test 2: Test log ingestion
            print("\nTest 2: Log Ingestion")
            print("-" * 40)
            
            try:
                async with session.post(
                    f"{server_url}/api/logs/ingest",
                    json=test_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                ) as response:
                    
                    response_text = await response.text()
                    
                    if response.status == 200:
                        print("SUCCESS: Log sent successfully")
                        try:
                            response_data = json.loads(response_text)
                            print(f"Response: {response_data}")
                        except:
                            print(f"Response: {response_text}")
                    else:
                        print(f"FAILED: Log send failed - {response.status}")
                        print(f"Error: {response_text}")
                        return False
            
            except Exception as e:
                print(f"FAILED: Log send error - {e}")
                return False
            
            # Test 3: Check database
            print("\nTest 3: Database Check")
            print("-" * 40)
            
            try:
                async with session.get(f"{server_url}/api/logs", timeout=10) as response:
                    if response.status == 200:
                        logs_data = await response.json()
                        total_logs = logs_data.get('total', 0)
                        print(f"SUCCESS: Database contains {total_logs} total logs")
                        
                        # Check for our test logs
                        logs = logs_data.get('logs', [])
                        test_logs_found = 0
                        for log in logs:
                            if log.get('agent_id') == 'test_agent_log_forwarding':
                                test_logs_found += 1
                        
                        print(f"Found {test_logs_found} test logs in database")
                        
                        if test_logs_found > 0:
                            print("SUCCESS: Log forwarding is working!")
                            return True
                        else:
                            print("WARNING: Test logs not found in database")
                            return False
                    
                    else:
                        print(f"FAILED: Cannot retrieve logs - {response.status}")
                        return False
            
            except Exception as e:
                print(f"FAILED: Database check error - {e}")
                return False
    
    except Exception as e:
        print(f"FAILED: Test error - {e}")
        return False

async def main():
    """Run log forwarding test"""
    
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081"
    
    print("Starting CodeGrey Log Forwarding Test...")
    print("=" * 60)
    
    result = await test_log_ingestion(server_url)
    
    print("\n" + "=" * 60)
    print("TEST RESULT")
    print("=" * 60)
    
    if result:
        print("SUCCESS: Log forwarding is working correctly!")
    else:
        print("FAILED: Log forwarding has issues.")
        print("\nTROUBLESHOOTING:")
        print("1. Check if server is running")
        print("2. Check server logs for errors")
        print("3. Verify database connectivity")
        print("4. Check client agent configuration")
    
    return result

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
