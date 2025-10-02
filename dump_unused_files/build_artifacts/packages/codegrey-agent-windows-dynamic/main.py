#!/usr/bin/env python3
"""
CodeGrey AI SOC Platform - Windows Client Agent (Dynamic Edition)
NO HARDCODING - ALL FEATURES LEARNED FROM ENVIRONMENT
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Main entry point with dynamic configuration"""
    print("CodeGrey AI SOC Platform - Windows Agent (Dynamic Edition)")
    print("=" * 60)
    print("NO HARDCODING - ALL DYNAMIC FEATURES")
    print("ML-Based Location Detection")
    print("Environment-Learned Threat Detection") 
    print("Dynamic Network Discovery")
    print("Red Team Container Orchestration")
    print()
    
    # Check for configuration arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--configure':
        configure_agent_dynamically()
        return
    
    # Initialize dynamic agent
    from client_agent import WindowsClientAgent
    from config_manager import ConfigManager
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # Add dynamic capabilities to config
    config['dynamic_features'] = {
        'network_discovery': True,
        'ml_location_detection': True,
        'adaptive_threat_detection': True,
        'container_orchestration': True,
        'no_hardcoding': True
    }
    
    # Start dynamic agent
    agent = WindowsClientAgent(config)
    
    try:
        print("Starting dynamic Windows client agent...")
        agent.start()
    except KeyboardInterrupt:
        print("\nShutting down agent...")
        agent.stop()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def configure_agent_dynamically():
    """Configure agent with dynamic server detection"""
    print("DYNAMIC AGENT CONFIGURATION")
    print("=" * 40)
    print("No hardcoded server URLs or configurations")
    print()
    
    from config_manager import ConfigManager
    
    # Get server URL (no hardcoded defaults)
    server_url = input("Enter SOC server URL: ").strip()
    if not server_url:
        print("Server URL required for dynamic configuration")
        return
    
    api_token = input("Enter API token (optional, press Enter to skip): ").strip()
    
    config_manager = ConfigManager()
    success = config_manager.configure_agent(server_url, api_token if api_token else None)
    
    if success:
        print("Dynamic configuration saved!")
        print(f"Server: {server_url}")
        print("Run 'start_agent.bat' to start the agent")
    else:
        print("Configuration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
