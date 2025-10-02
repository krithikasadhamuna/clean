"""
Simple Production Server Test
Tests the actual main.py server with full logging
"""

import subprocess
import sys
import time
import requests
import io
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("PRODUCTION SERVER TEST")
print("=" * 80)
print()

print("Step 1: Starting production server...")
print("Command: python main.py server --host 127.0.0.1 --port 8081")
print()

# Start server with output visible
server_process = subprocess.Popen(
    [sys.executable, "main.py", "server", "--host", "127.0.0.1", "--port", "8081"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print(f"✅ Server process started (PID: {server_process.pid})")
print("\nServer output:")
print("-" * 80)

# Read initial output
output_lines = []
start_time = time.time()
server_ready = False

try:
    while time.time() - start_time < 30:  # 30 second timeout
        line = server_process.stdout.readline()
        if line:
            print(line.strip())
            output_lines.append(line)
            
            # Check for success indicators
            if any(keyword in line.lower() for keyword in ['application startup complete', 'uvicorn running', 'started server']):
                server_ready = True
                break
            
            # Check for errors
            if 'error' in line.lower() or 'traceback' in line.lower():
                print("\n⚠️  Error detected in server output!")
        
        # Check if process died
        if server_process.poll() is not None:
            print(f"\n❌ Server process ended with code: {server_process.poll()}")
            print("\nRemaining output:")
            for line in server_process.stdout:
                print(line.strip())
            break
        
        time.sleep(0.1)
    
    if not server_ready:
        print(f"\n⏱️  Timeout after 30 seconds")
    
    print("\n" + "-" * 80)
    print()
    
    if server_process.poll() is None:  # Still running
        print("Step 2: Testing server endpoints...")
        print()
        
        time.sleep(2)  # Give it a bit more time
        
        # Test health endpoint
        try:
            response = requests.get("http://127.0.0.1:8081/health", timeout=5)
            print(f"✅ Health endpoint: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"❌ Health endpoint failed: {e}")
        
        print()
        
        # Test API endpoints
        try:
            response = requests.get("http://127.0.0.1:8081/api/agents/test/commands", timeout=5)
            print(f"✅ Commands endpoint: {response.status_code}")
            data = response.json()
            print(f"   Commands: {len(data.get('commands', []))}")
        except Exception as e:
            print(f"❌ Commands endpoint failed: {e}")
        
        print()
        print("=" * 80)
        print("SERVER IS RUNNING!")
        print("=" * 80)
        print()
        print("Press Ctrl+C to stop the server and continue...")
        print()
        print("Server logs (live):")
        print("-" * 80)
        
        # Keep showing logs
        try:
            for line in server_process.stdout:
                print(line.strip())
        except KeyboardInterrupt:
            print("\n\nStopping server...")
    
except KeyboardInterrupt:
    print("\n\nInterrupted by user")
finally:
    # Clean up
    if server_process.poll() is None:
        print("Terminating server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()
    
    print("✅ Server stopped")
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    if server_process.poll() is None or server_process.poll() == 0:
        print("✅ Server started successfully")
    else:
        print(f"❌ Server exited with code: {server_process.returncode}")
    
    print()
    print("Check the output above for any errors or issues.")
    print()

