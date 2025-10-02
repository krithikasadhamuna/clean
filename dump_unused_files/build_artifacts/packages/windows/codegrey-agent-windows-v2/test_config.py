#!/usr/bin/env python3
"""
Test config loading
"""

import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config_manager import ConfigManager

def test_config():
    """Test config loading"""
    print("Testing config loading...")
    print(f"Current directory: {current_dir}")
    
    config_manager = ConfigManager()
    print(f"Config file path: {config_manager.config_file}")
    print(f"Config file exists: {config_manager.config_file.exists()}")
    
    config = config_manager.load_config()
    print(f"Server endpoint: {config.get('client', {}).get('server_endpoint', 'Not found')}")
    print(f"Agent ID: {config.get('client', {}).get('agent_id', 'Not found')}")

if __name__ == "__main__":
    test_config()
