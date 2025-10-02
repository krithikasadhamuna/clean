"""
Production Server Starter - With Unicode Fix
Fixes the LangServe Unicode issue for Windows
"""

import os
import sys
import subprocess

# Fix Unicode encoding issue for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("=" * 80)
print("STARTING PRODUCTION SERVER (Fixed for Windows)")
print("=" * 80)
print()

print("Server: http://127.0.0.1:8081")
print("Mode: Production code with all features")
print()

print("Starting server...")
print()

# Start the server with UTF-8 encoding
result = subprocess.run(
    [sys.executable, "main.py", "server", "--host", "127.0.0.1", "--port", "8081"],
    env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
)

sys.exit(result.returncode)

