#!/usr/bin/env python3
"""
Simple Test for Windows Client Agent Capabilities
"""

import asyncio
import logging
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_system_info():
    """Test system information gathering"""
    print("Testing System Information...")
    
    try:
        from shared.utils import get_system_info
        system_info = get_system_info()
        
        print(f"Platform: {system_info.get('platform', 'unknown')}")
        print(f"Hostname: {system_info.get('hostname', 'unknown')}")
        print(f"IP Address: {system_info.get('ip_address', 'unknown')}")
        print("System info test: PASSED")
        return True
        
    except Exception as e:
        print(f"System info test: FAILED - {e}")
        return False

def test_docker_availability():
    """Test Docker availability"""
    print("\nTesting Docker Availability...")
    
    try:
        import docker
        docker_client = docker.from_env()
        docker_client.ping()
        
        docker_info = docker_client.info()
        print(f"Docker Version: {docker_info.get('ServerVersion', 'unknown')}")
        print(f"Containers: {docker_info.get('Containers', 0)}")
        print("Docker test: PASSED")
        return True
        
    except ImportError:
        print("Docker Python library not installed")
        print("Docker test: SKIPPED")
        return False
        
    except Exception as e:
        print(f"Docker not available: {e}")
        print("Docker test: FAILED")
        return False

def test_network_connectivity():
    """Test network connectivity"""
    print("\nTesting Network Connectivity...")
    
    try:
        import aiohttp
        
        async def test_connection():
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get("http://backend.codegrey.ai:8080/health") as response:
                    return response.status == 200
        
        result = asyncio.run(test_connection())
        
        if result:
            print("Server connectivity: PASSED")
            return True
        else:
            print("Server connectivity: FAILED")
            return False
            
    except Exception as e:
        print(f"Network test: FAILED - {e}")
        return False

def test_log_forwarders():
    """Test log forwarders"""
    print("\nTesting Log Forwarders...")
    
    try:
        from core.client.forwarders.windows_forwarder import WindowsLogForwarder
        from core.client.forwarders.application_forwarder import ApplicationLogForwarder
        
        # Test Windows forwarder
        windows_forwarder = WindowsLogForwarder("test_agent", {})
        print("Windows forwarder: PASSED")
        
        # Test Application forwarder
        app_forwarder = ApplicationLogForwarder("test_agent", {})
        print("Application forwarder: PASSED")
        
        print("Log forwarders test: PASSED")
        return True
        
    except Exception as e:
        print(f"Log forwarders test: FAILED - {e}")
        return False

def test_command_execution():
    """Test command execution"""
    print("\nTesting Command Execution...")
    
    try:
        from core.client.command_executor import CommandExecutionEngine
        
        executor = CommandExecutionEngine("test_agent", "http://backend.codegrey.ai:8080")
        
        # Test basic command
        test_cmd = {'technique': 'T1082', 'parameters': {'type': 'basic'}}
        
        async def test_execution():
            return await executor._execute_command(test_cmd)
        
        result = asyncio.run(test_execution())
        
        if result.get('success'):
            print("Command execution: PASSED")
            return True
        else:
            print(f"Command execution: FAILED - {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"Command execution test: FAILED - {e}")
        return False

def test_client_agent():
    """Test full client agent"""
    print("\nTesting Full Client Agent...")
    
    try:
        from core.client.client_agent import LogForwardingClient
        
        # Create test config
        test_config = {
            'client': {
                'agent_id': 'test_agent',
                'server_endpoint': 'http://backend.codegrey.ai:8080',
                'api_key': '',
                'reconnect_interval': 30,
                'heartbeat_interval': 60
            },
            'log_forwarding': {
                'enabled': True,
                'batch_size': 10,
                'flush_interval': 5
            },
            'log_sources': {
                'system_logs': {'enabled': True},
                'security_logs': {'enabled': True}
            },
            'windows': {
                'event_logs': ['Security', 'System'],
                'wmi_enabled': True
            },
            'command_execution': {
                'enabled': True,
                'allowed_commands': ['powershell', 'cmd']
            },
            'containers': {
                'enabled': True,
                'max_containers': 5
            }
        }
        
        # Create temporary config file
        config_file = Path('test_config.yaml')
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        # Create client
        client = LogForwardingClient(str(config_file))
        
        # Test client status
        status = client.get_status()
        
        # Clean up
        if config_file.exists():
            config_file.unlink()
        
        print(f"Client initialization: PASSED")
        print(f"Forwarders: {status.get('forwarders', 0)}")
        print(f"Command executor: {'Enabled' if client.command_executor else 'Disabled'}")
        print(f"Container executor: {'Enabled' if client.container_executor else 'Disabled'}")
        
        print("Full client agent test: PASSED")
        return True
        
    except Exception as e:
        print(f"Full client agent test: FAILED - {e}")
        return False

def main():
    """Run all tests"""
    print("CodeGrey AI SOC Platform - Windows Client Capability Test")
    print("=" * 60)
    
    tests = [
        ("System Information", test_system_info),
        ("Docker Availability", test_docker_availability),
        ("Network Connectivity", test_network_connectivity),
        ("Log Forwarders", test_log_forwarders),
        ("Command Execution", test_command_execution),
        ("Full Client Agent", test_client_agent)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name} test: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("Status: EXCELLENT - All tests passed!")
    elif passed >= total * 0.8:
        print("Status: GOOD - Most tests passed")
    elif passed >= total * 0.6:
        print("Status: ACCEPTABLE - Some tests failed")
    else:
        print("Status: POOR - Many tests failed")
    
    # Recommendations
    print("\nRECOMMENDATIONS:")
    
    if not results.get("Docker Availability", False):
        print("- Docker not available - Container capabilities will be limited")
        print("- Client will still work for log forwarding and command execution")
        print("- Consider installing Docker for full container-based attack simulation")
    
    if not results.get("Network Connectivity", False):
        print("- Server not reachable - Check network connectivity")
        print("- Verify server endpoint: http://backend.codegrey.ai:8080")
    
    if passed >= total * 0.8:
        print("- Client agent is ready for deployment!")
    else:
        print("- Review failed tests and fix issues before deployment")
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    main()

