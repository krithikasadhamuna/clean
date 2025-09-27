#!/usr/bin/env python3
"""
CodeGrey AI SOC Platform - macOS Client Agent
Standalone client agent for macOS endpoints
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import client components
from client_agent import MacOSClientAgent
from config_manager import ConfigManager

def main():
    """Main entry point for macOS client agent"""
    print("CodeGrey AI SOC Platform - macOS Client Agent")
    print("=" * 50)
    
    # Check for configuration arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--configure':
        configure_agent()
        return
    
    # Initialize configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # Initialize and start client agent
    agent = MacOSClientAgent(config)
    
    try:
        print("Starting macOS client agent...")
        agent.start()
    except KeyboardInterrupt:
        print("\nShutting down client agent...")
        agent.stop()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def configure_agent():
    """Configure agent with server details"""
    print("CodeGrey Agent Configuration")
    print("=" * 30)
    
    server_url = input("Enter SOC server URL (e.g., http://15.207.6.45:8080): ").strip()
    if not server_url:
        server_url = "http://15.207.6.45:8080"
    
    api_token = input("Enter API token (optional, press Enter to skip): ").strip()
    
    config_manager = ConfigManager()
    success = config_manager.configure_agent(server_url, api_token if api_token else None)
    
    if success:
        print("Configuration saved successfully!")
        print(f"Server: {server_url}")
        print("Run 'python3 main.py' to start the agent")
    else:
        print("Configuration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
