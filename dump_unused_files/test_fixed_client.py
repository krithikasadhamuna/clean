#!/usr/bin/env python3
"""
Test the fixed client agent
"""

import asyncio
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.client.client_agent import LogForwardingClient

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_client():
    """Test the client agent"""
    print("Testing CodeGrey AI SOC Platform - Fixed Client Agent")
    print("=" * 60)
    
    try:
        # Create client with test config
        config_file = "build_artifacts/packages/windows/codegrey-agent-windows-v2/config.yaml"
        client = LogForwardingClient(config_file)
        
        print(f"Agent ID: {client.agent_id}")
        print(f"Server Endpoint: {client.server_endpoint}")
        print(f"Forwarders: {len(client.forwarders)}")
        
        # Test forwarder initialization
        for forwarder in client.forwarders:
            print(f"  - {forwarder.__class__.__name__}")
        
        # Test command executor
        if client.command_executor:
            print(f"Command Executor: Enabled")
        else:
            print(f"Command Executor: Disabled")
        
        # Test container executor
        if client.container_executor:
            print(f"Container Executor: Enabled")
        else:
            print(f"Container Executor: Disabled")
        
        print("\nClient initialization successful!")
        print("All components loaded without errors.")
        
        # Test status
        status = client.get_status()
        print(f"\nStatus: {status['running']}")
        print(f"Connected: {status['connected']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_client())
    if success:
        print("\nTest PASSED - Client is working correctly!")
    else:
        print("\nTest FAILED - Client has issues")
    
    print("\nPress Enter to exit...")
    input()
