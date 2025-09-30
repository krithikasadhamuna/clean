#!/usr/bin/env python3
"""
Local Development Client for CodeGrey AI SOC Platform
Runs on localhost and connects to local dev server
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

def setup_dev_client():
    """Setup development client environment"""
    print("Starting CodeGrey AI SOC Platform - Development Client")
    print("=" * 60)
    
    # Set development environment
    os.environ['SOC_ENV'] = 'development'
    os.environ['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Use development client configuration
    dev_config = Path(__file__).parent / "config" / "client_dev_config.yaml"
    
    print(f"Using development config: {dev_config}")
    print(f"Will connect to: http://15.207.6.45:8080")
    print(f"Environment: Development")
    print(f"Mock data: Enabled")
    print("")
    
    return str(dev_config)

async def run_dev_client():
    """Run development client"""
    try:
        # Setup development environment
        config_file = setup_dev_client()
        
        # Import client components
        from core.client_agent import LogForwardingClient
        
        # Create client with development config
        client = LogForwardingClient(config_file)
        
        print("Starting development client...")
        print("   - Debug logging: Enabled")
        print("   - Mock threats: Disabled") 
        print("   - Container isolation: Enabled")
        print("   - Log forwarding: http://15.207.6.45:8080")
        print("")
        
        # Start client
        await client.start()
        
    except KeyboardInterrupt:
        print("\nDevelopment client stopped by user")
    except Exception as e:
        print(f"Development client error: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        asyncio.run(run_dev_client())
    except KeyboardInterrupt:
        print("\nDevelopment client shutdown complete")

if __name__ == "__main__":
    main()

