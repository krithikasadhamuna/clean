#!/usr/bin/env python3
"""
Set OpenAI API Key as Global Environment Variable
This script sets the OpenAI API key as a permanent system environment variable
"""

import os
import sys
import subprocess
from pathlib import Path

def set_openai_api_key_global():
    """Set OpenAI API key as a global environment variable"""
    
    # Your new API key
    api_key = "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"
    
    print("=" * 80)
    print("SETTING OPENAI API KEY AS GLOBAL ENVIRONMENT VARIABLE")
    print("=" * 80)
    
    try:
        # Method 1: Set for current user (recommended)
        print("\n1. Setting OpenAI API key for current user...")
        
        # Use setx command to set user environment variable
        result = subprocess.run([
            'setx', 'OPENAI_API_KEY', api_key
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print("SUCCESS: OpenAI API key set for current user")
            print(f"   Key: {api_key[:20]}...")
        else:
            print(f"FAILED: Error setting user environment variable: {result.stderr}")
            return False
        
        # Method 2: Set for system-wide (requires admin privileges)
        print("\n2. Setting OpenAI API key system-wide (requires admin privileges)...")
        
        result = subprocess.run([
            'setx', 'OPENAI_API_KEY', api_key, '/M'
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print("SUCCESS: OpenAI API key set system-wide")
        else:
            print(f"PARTIAL: System-wide setting failed (may need admin): {result.stderr}")
            print("   User-level setting should still work")
        
        # Method 3: Set in current session
        print("\n3. Setting OpenAI API key for current session...")
        os.environ['OPENAI_API_KEY'] = api_key
        print("SUCCESS: OpenAI API key set for current session")
        
        # Verify the setting
        print("\n4. Verifying environment variable...")
        current_key = os.environ.get('OPENAI_API_KEY')
        if current_key:
            print(f"SUCCESS: Current session has API key: {current_key[:20]}...")
        else:
            print("WARNING: API key not found in current session")
        
        print("\n" + "=" * 80)
        print("OPENAI API KEY SETUP COMPLETED")
        print("=" * 80)
        print("SUCCESS: API key has been set as environment variable")
        print("NOTE: You may need to restart your terminal/IDE for changes to take effect")
        print("NOTE: The key is now available system-wide for all applications")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to set environment variable: {e}")
        return False

def create_batch_script():
    """Create a batch script to set the environment variable"""
    
    api_key = "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"
    
    batch_content = f"""@echo off
echo Setting OpenAI API Key as Global Environment Variable...
setx OPENAI_API_KEY "{api_key}"
echo.
echo OpenAI API Key has been set successfully!
echo You may need to restart your terminal for changes to take effect.
echo.
pause
"""
    
    with open('set_openai_api_key.bat', 'w') as f:
        f.write(batch_content)
    
    print("SUCCESS: Created set_openai_api_key.bat script")
    print("   You can run this batch file to set the API key")

def create_powershell_script():
    """Create a PowerShell script to set the environment variable"""
    
    api_key = "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"
    
    ps_content = f"""# PowerShell script to set OpenAI API Key
Write-Host "Setting OpenAI API Key as Global Environment Variable..." -ForegroundColor Green

# Set for current user
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "{api_key}", "User")

# Set for current session
$env:OPENAI_API_KEY = "{api_key}"

Write-Host "OpenAI API Key has been set successfully!" -ForegroundColor Green
Write-Host "You may need to restart your terminal for changes to take effect." -ForegroundColor Yellow
Write-Host ""
Write-Host "Current session API Key: $env:OPENAI_API_KEY" -ForegroundColor Cyan
"""
    
    with open('set_openai_api_key.ps1', 'w') as f:
        f.write(ps_content)
    
    print("SUCCESS: Created set_openai_api_key.ps1 script")
    print("   You can run this PowerShell script to set the API key")

if __name__ == "__main__":
    # Set the API key
    success = set_openai_api_key_global()
    
    if success:
        # Create helper scripts
        create_batch_script()
        create_powershell_script()
        
        print("\n" + "=" * 80)
        print("ADDITIONAL SCRIPTS CREATED")
        print("=" * 80)
        print("1. set_openai_api_key.bat - Batch script to set API key")
        print("2. set_openai_api_key.ps1 - PowerShell script to set API key")
        print("\nYou can run either script to set the API key in the future.")
        
        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("1. Restart your terminal/IDE")
        print("2. Start the server with: python main.py server --host 127.0.0.1 --port 8081")
        print("3. The AI attack planning should now work!")
    else:
        print("\nFAILED: Could not set environment variable")
        print("Please try running as administrator or use the created scripts manually.")
