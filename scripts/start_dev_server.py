#!/usr/bin/env python3
"""
Local Development Server for CodeGrey AI SOC Platform
Runs on localhost for development and testing
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

def setup_dev_environment():
    """Setup development environment"""
    print("🛠️  Setting up CodeGrey AI SOC Platform - Development Environment")
    print("=" * 70)
    
    # Set development environment variable
    os.environ['SOC_ENV'] = 'development'
    os.environ['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Use development configuration
    dev_config = Path(__file__).parent / "config" / "dev_config.yaml"
    
    print(f"📋 Using development config: {dev_config}")
    print(f"🌐 Server will run on: http://15.207.6.45:8080")
    print(f"🔧 Environment: Development")
    print(f"🔐 Authentication: Disabled")
    print(f"📊 Database: dev_soc_database.db")
    print("")
    
    return str(dev_config)

async def run_dev_server():
    """Run development server"""
    try:
        # Setup development environment
        config_file = setup_dev_environment()
        
        # Import server components
        from core.server_manager import LogForwardingServer
        
        # Create server with development config
        server = LogForwardingServer(config_file)
        
        print("🚀 Starting development server...")
        print("   - Hot reload: Enabled")
        print("   - Debug logging: Enabled") 
        print("   - CORS: Fully open")
        print("   - API docs: http://15.207.6.45:8080/docs")
        print("")
        
        # Start server
        await server.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped by user")
    except Exception as e:
        print(f"❌ Development server error: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        asyncio.run(run_dev_server())
    except KeyboardInterrupt:
        print("\n👋 Development server shutdown complete")

if __name__ == "__main__":
    main()

