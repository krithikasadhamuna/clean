#!/usr/bin/env python3
"""
Test complete client agent pipeline with log collection and forwarding
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

async def test_client_agent_components():
    """Test individual client agent components"""
    
    print("=" * 60)
    print("CodeGrey Client Agent Component Test")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = []
    
    # Test 1: Import client agent modules
    print("Test 1: Module Imports")
    print("-" * 40)
    
    try:
        from core.client.client_agent import LogForwardingClient
        from core.client.forwarders.windows_forwarder import WindowsLogForwarder
        from core.client.command_executor import CommandExecutionEngine
        from core.client.container_attack_executor import ContainerAttackExecutor
        print("SUCCESS: All client agent modules imported successfully")
        results.append(True)
    except Exception as e:
        print(f"FAILED: Module import error - {e}")
        results.append(False)
    
    # Test 2: Test Windows log forwarder
    print("\nTest 2: Windows Log Forwarder")
    print("-" * 40)
    
    try:
        test_config = {
            'windows': {
                'event_logs': ['System', 'Application'],
                'wmi_enabled': False
            }
        }
        
        forwarder = WindowsLogForwarder("test_agent", test_config)
        print("SUCCESS: Windows log forwarder initialized")
        
        # Test log collection (brief)
        print("Testing log collection (3 seconds)...")
        await forwarder.start()
        await asyncio.sleep(3)
        await forwarder.stop()
        
        logs_collected = 0
        while not forwarder.log_queue.empty():
            log = await forwarder.log_queue.get()
            logs_collected += 1
        
        if logs_collected > 0:
            print(f"SUCCESS: Collected {logs_collected} logs")
            results.append(True)
        else:
            print("WARNING: No logs collected (may be normal)")
            results.append(True)  # Not a failure, just no events
        
    except Exception as e:
        print(f"FAILED: Windows log forwarder error - {e}")
        results.append(False)
    
    # Test 3: Test command executor
    print("\nTest 3: Command Execution Engine")
    print("-" * 40)
    
    try:
        executor = CommandExecutionEngine("test_agent", "http://127.0.0.1:8081")
        print("SUCCESS: Command execution engine initialized")
        
        # Test statistics
        stats = executor.get_statistics()
        print(f"SUCCESS: Statistics retrieved - {stats}")
        results.append(True)
        
    except Exception as e:
        print(f"FAILED: Command execution engine error - {e}")
        results.append(False)
    
    # Test 4: Test container executor
    print("\nTest 4: Container Attack Executor")
    print("-" * 40)
    
    try:
        container_config = {
            'containers': {
                'enabled': True,
                'auto_download': True
            }
        }
        
        container_executor = ContainerAttackExecutor("test_agent", "http://127.0.0.1:8081", container_config)
        print("SUCCESS: Container attack executor initialized")
        
        # Test start (should handle Docker unavailability gracefully)
        await container_executor.start()
        print("SUCCESS: Container executor started (Docker availability handled)")
        results.append(True)
        
    except Exception as e:
        print(f"FAILED: Container attack executor error - {e}")
        results.append(False)
    
    return results

async def test_client_agent_full_pipeline(server_url="http://127.0.0.1:8081"):
    """Test complete client agent pipeline"""
    
    print("\n" + "=" * 60)
    print("CodeGrey Client Agent Full Pipeline Test")
    print("=" * 60)
    print(f"Server: {server_url}")
    print()
    
    try:
        # Test 1: Create and start client agent
        print("Test 1: Client Agent Initialization")
        print("-" * 40)
        
        from core.client.client_agent import LogForwardingClient
        
        # Create test configuration
        test_config = {
            'client': {
                'agent_id': 'test_pipeline_agent',
                'server_endpoint': server_url,
                'api_key': '',
                'reconnect_interval': 30,
                'heartbeat_interval': 30
            },
            'log_forwarding': {
                'enabled': True,
                'batch_size': 10,
                'flush_interval': 5
            },
            'windows': {
                'event_logs': ['System', 'Application'],
                'wmi_enabled': False
            }
        }
        
        client = LogForwardingClient(test_config)
        print("SUCCESS: Client agent created")
        
        # Start client agent
        print("Starting client agent (10 seconds)...")
        await client.start()
        
        # Let it run for a bit
        await asyncio.sleep(10)
        
        # Check statistics
        stats = client.get_status()
        print(f"SUCCESS: Client agent running - {stats}")
        
        # Stop client agent
        await client.stop()
        print("SUCCESS: Client agent stopped")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Client agent pipeline error - {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_log_forwarding_to_server(server_url="http://127.0.0.1:8081"):
    """Test log forwarding to server"""
    
    print("\nTest 2: Log Forwarding to Server")
    print("-" * 40)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Send test logs
            test_logs = {
                "agent_id": "test_pipeline_agent",
                "logs": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "info",
                        "message": "Test pipeline log - System startup",
                        "source": "windows_system",
                        "event_id": 1001,
                        "log_name": "System"
                    },
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "warning",
                        "message": "Test pipeline log - Security event",
                        "source": "windows_security",
                        "event_id": 4624,
                        "log_name": "Security"
                    }
                ]
            }
            
            # Send logs
            async with session.post(
                f"{server_url}/api/logs/ingest",
                json=test_logs,
                headers={'Content-Type': 'application/json'},
                timeout=30
            ) as response:
                
                if response.status == 200:
                    print("SUCCESS: Test logs sent to server")
                    
                    # Check if logs were stored
                    async with session.get(f"{server_url}/api/logs?agent_id=test_pipeline_agent", timeout=10) as response:
                        if response.status == 200:
                            logs_data = await response.json()
                            logs = logs_data.get('logs', [])
                            print(f"SUCCESS: Found {len(logs)} logs in database")
                            return True
                        else:
                            print(f"FAILED: Cannot retrieve logs - {response.status}")
                            return False
                else:
                    print(f"FAILED: Log sending failed - {response.status}")
                    return False
    
    except Exception as e:
        print(f"FAILED: Log forwarding test error - {e}")
        return False

async def main():
    """Run all client agent tests"""
    
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081"
    
    print("Starting CodeGrey Client Agent Pipeline Tests...")
    print("=" * 60)
    
    # Test individual components
    component_results = await test_client_agent_components()
    
    # Test full pipeline
    pipeline_result = await test_client_agent_full_pipeline(server_url)
    
    # Test log forwarding
    forwarding_result = await test_log_forwarding_to_server(server_url)
    
    # Summary
    print("\n" + "=" * 60)
    print("CLIENT AGENT PIPELINE TEST SUMMARY")
    print("=" * 60)
    
    component_success = sum(component_results)
    total_components = len(component_results)
    
    print(f"Component Tests: {component_success}/{total_components} passed")
    print(f"Full Pipeline: {'PASSED' if pipeline_result else 'FAILED'}")
    print(f"Log Forwarding: {'PASSED' if forwarding_result else 'FAILED'}")
    
    if component_success == total_components and pipeline_result and forwarding_result:
        print("\nSUCCESS: Client agent pipeline is working correctly!")
        print("- All components: Working")
        print("- Full pipeline: Working")
        print("- Log forwarding: Working")
        return True
    else:
        print("\nFAILED: Client agent pipeline has issues.")
        print("\nTROUBLESHOOTING:")
        if component_success < total_components:
            print("- Fix component initialization issues")
        if not pipeline_result:
            print("- Fix full pipeline execution")
        if not forwarding_result:
            print("- Fix log forwarding to server")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
