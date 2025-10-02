"""
Complete Local Development Environment Setup
Starts the actual production server and client for local testing
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
import io
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("CODEGREY AI SOC PLATFORM - LOCAL DEVELOPMENT ENVIRONMENT")
print("=" * 80)
print()

# Store process references for cleanup
processes = []

def cleanup_processes():
    """Clean up all started processes"""
    print("\n\nCleaning up processes...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            try:
                proc.kill()
            except:
                pass
    print("Cleanup complete")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nReceived shutdown signal...")
    cleanup_processes()
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

async def main():
    """Main setup function"""
    
    print("STEP 1: Setting up environment")
    print("-" * 80)
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("ERROR: main.py not found. Please run this script from the project root directory.")
        return 1
    
    if not os.path.exists('core/langserve_api.py'):
        print("ERROR: core/langserve_api.py not found. Are you in the correct directory?")
        return 1
    
    print("✅ Project structure verified")
    print()
    
    # Check Python version
    python_version = sys.version_info
    print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print()
    
    print("STEP 2: Starting Production Server (Local Mode)")
    print("-" * 80)
    print("Starting server on http://127.0.0.1:8081")
    print("This uses the ACTUAL production code from main.py")
    print()
    
    # Start the server
    server_cmd = [sys.executable, "main.py", "server", "--host", "127.0.0.1", "--port", "8081"]
    
    print(f"Command: {' '.join(server_cmd)}")
    print()
    
    server_process = subprocess.Popen(
        server_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    processes.append(server_process)
    
    print("✅ Server process started (PID: {})".format(server_process.pid))
    print("   Waiting for server to initialize...")
    print()
    
    # Wait for server to start
    await asyncio.sleep(10)
    
    # Check if server is still running
    if server_process.poll() is not None:
        print("❌ Server failed to start!")
        print("\nServer output:")
        print("-" * 80)
        for line in server_process.stdout:
            print(line, end='')
        return 1
    
    print("✅ Server appears to be running")
    print()
    
    print("STEP 3: Testing Server")
    print("-" * 80)
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            try:
                async with session.get("http://127.0.0.1:8081/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        print("✅ Server health check passed")
                    else:
                        print(f"⚠️  Server returned status {response.status}")
            except Exception as e:
                print(f"⚠️  Health check failed: {e}")
                print("   (Server may still be initializing...)")
    except ImportError:
        print("⚠️  aiohttp not available for testing, skipping health check")
    
    print()
    
    print("STEP 4: Setup Instructions")
    print("-" * 80)
    print()
    print("🎯 **Server is running!**")
    print()
    print("Server Details:")
    print(f"  - URL: http://127.0.0.1:8081")
    print(f"  - API Base: http://127.0.0.1:8081/api")
    print(f"  - Process ID: {server_process.pid}")
    print()
    print("=" * 80)
    print("AVAILABLE ENDPOINTS:")
    print("=" * 80)
    print()
    print("📋 Agent Management:")
    print("  POST   /api/agents/register")
    print("  POST   /api/agents/{agent_id}/heartbeat")
    print("  GET    /api/agents/{agent_id}/commands          ← COMMAND QUEUE")
    print("  POST   /api/agents/{agent_id}/commands/result   ← RESULT REPORTING")
    print()
    print("📝 Log Ingestion:")
    print("  POST   /api/logs/ingest")
    print("  GET    /api/logs")
    print()
    print("🎯 Attack Agent (PhantomStrike AI):")
    print("  POST   /api/soc/plan-attack")
    print("  POST   /api/soc/approve-attack")
    print("  GET    /api/soc/pending-approvals")
    print()
    print("=" * 80)
    print("HOW TO TEST:")
    print("=" * 80)
    print()
    print("OPTION 1: Test with Actual Client Agent")
    print("-" * 80)
    print("Open a NEW terminal and run:")
    print()
    print("  cd CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-windows-unified")
    print("  python main.py")
    print()
    print("Or for the executable:")
    print("  cd CodeGrey-AI-SOC-Platform-Unified/packages/codegrey-agent-windows-unified")
    print("  .\\CodeGrey-Agent-Windows\\CodeGrey-Agent-Windows-Unified.exe")
    print()
    print()
    print("OPTION 2: Test with Attack Simulation Script")
    print("-" * 80)
    print("Open a NEW terminal and run:")
    print()
    print("  python test_attack_simulation_local.py")
    print()
    print("(This script will be created for you)")
    print()
    print()
    print("OPTION 3: Manual API Testing with curl")
    print("-" * 80)
    print()
    print("# Register an agent")
    print('curl -X POST http://127.0.0.1:8081/api/agents/register \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"agent_id": "test_agent", "hostname": "test", "platform": "windows"}\'')
    print()
    print("# Get pending commands")
    print('curl http://127.0.0.1:8081/api/agents/test_agent/commands')
    print()
    print()
    print("=" * 80)
    print("DATABASE LOCATION:")
    print("=" * 80)
    print(f"  {os.path.abspath('soc_database.db')}")
    print()
    print("To view database:")
    print("  sqlite3 soc_database.db")
    print("  > SELECT * FROM agents;")
    print("  > SELECT * FROM commands;")
    print("  > SELECT * FROM command_results;")
    print()
    print()
    print("=" * 80)
    print("SERVER IS RUNNING - Press Ctrl+C to stop")
    print("=" * 80)
    print()
    print("Server logs will appear below:")
    print("-" * 80)
    print()
    
    # Stream server output
    try:
        for line in iter(server_process.stdout.readline, ''):
            if line:
                print(f"[SERVER] {line}", end='')
            if server_process.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
    finally:
        cleanup_processes()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        cleanup_processes()
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        cleanup_processes()
        sys.exit(1)

