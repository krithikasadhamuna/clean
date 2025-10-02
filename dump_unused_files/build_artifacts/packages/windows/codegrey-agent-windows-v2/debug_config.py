#!/usr/bin/env python3
"""
Debug config loading in executable
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config_manager import ConfigManager

def debug_config():
    """Debug config loading"""
    print("=== CONFIG DEBUG ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {current_dir}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
    print()
    
    config_manager = ConfigManager()
    print(f"Config file path: {config_manager.config_file}")
    print(f"Config file exists: {config_manager.config_file.exists()}")
    print(f"Config file absolute path: {config_manager.config_file.absolute()}")
    print()
    
    # List files in current directory
    print("Files in current directory:")
    for f in current_dir.iterdir():
        print(f"  {f.name}")
    print()
    
    config = config_manager.load_config()
    print(f"Server endpoint: {config.get('client', {}).get('server_endpoint', 'Not found')}")
    print(f"Agent ID: {config.get('client', {}).get('agent_id', 'Not found')}")
    print("=== END DEBUG ===")

if __name__ == "__main__":
    debug_config()
