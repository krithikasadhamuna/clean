#!/usr/bin/env python3
"""
Check Docker availability and provide setup instructions
"""

import docker
import sys

def check_docker():
    """Check if Docker is available"""
    try:
        client = docker.from_env()
        client.ping()
        print("✅ Docker is available and running")
        
        # Check Docker version
        version = client.version()
        print(f"   Docker version: {version.get('Version', 'Unknown')}")
        
        # List containers
        containers = client.containers.list()
        print(f"   Running containers: {len(containers)}")
        
        return True
        
    except docker.errors.DockerException as e:
        print("❌ Docker is not available")
        print(f"   Error: {e}")
        print("\n📋 To enable Docker (optional for container-based attacks):")
        print("   1. Install Docker Desktop: https://www.docker.com/products/docker-desktop")
        print("   2. Start Docker Desktop")
        print("   3. Restart the client")
        print("\n   Note: Platform works without Docker (attacks will be simulated)")
        
        return False
        
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        return False

def check_windows_permissions():
    """Check Windows Event Log permissions"""
    try:
        import win32evtlog
        
        # Try to open Security log
        try:
            handle = win32evtlog.OpenEventLog(None, "Security")
            win32evtlog.CloseEventLog(handle)
            print("✅ Windows Event Log access available")
            return True
        except Exception as e:
            print("⚠️  Windows Event Log access limited")
            print(f"   Error: {e}")
            print("\n📋 To enable full Windows Event Log access:")
            print("   1. Run PowerShell as Administrator")
            print("   2. Restart the client with: python main.py client --config config/client_config.yaml")
            print("\n   Note: Platform works with limited access (some logs may be missed)")
            return False
            
    except ImportError:
        print("⚠️  Windows Event Log modules not available")
        print("   Install with: pip install pywin32")
        return False

if __name__ == "__main__":
    print("AI SOC Platform - System Check")
    print("=" * 40)
    
    print("\n1. Checking Docker availability...")
    docker_ok = check_docker()
    
    print("\n2. Checking Windows permissions...")
    windows_ok = check_windows_permissions()
    
    print("\n" + "=" * 40)
    print("SYSTEM CHECK SUMMARY")
    print("=" * 40)
    
    if docker_ok and windows_ok:
        print("✅ All systems ready - full functionality available")
    elif docker_ok or windows_ok:
        print("⚠️  Partial functionality - platform will work with limitations")
    else:
        print("⚠️  Limited functionality - basic operations available")
    
    print("\n🚀 AI SOC Platform can run regardless of these issues!")
    print("   Core functionality (log forwarding, AI detection, attack planning) works without Docker or admin privileges.")
