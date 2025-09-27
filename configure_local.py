#!/usr/bin/env python3
"""
Quick configuration for local development
"""

from config_manager import ConfigManager

def main():
    """Configure agent for local development"""
    print("🔧 Configuring for local development...")
    
    config_manager = ConfigManager()
    success = config_manager.configure_agent("localhost:8080", None)
    
    if success:
        print("✅ Configuration successful!")
        print("🚀 Server: http://localhost:8080")
        print("📝 Run 'python main.py' to start the agent")
    else:
        print("❌ Configuration failed!")

if __name__ == "__main__":
    main()
