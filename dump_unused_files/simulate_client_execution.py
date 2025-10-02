#!/usr/bin/env python3
"""
Simulate Client Agent Command Execution
This script will act like a real client agent, poll for commands, and execute them
"""

import requests
import json
import time
import subprocess
import sqlite3
from datetime import datetime

SERVER_URL = "http://127.0.0.1:8081"

def get_active_agent():
    """Get an active agent from the database"""
    try:
        conn = sqlite3.connect('soc_database.db')
        cursor = conn.cursor()
        
        # Get agents with queued commands
        cursor.execute('''
            SELECT DISTINCT agent_id 
            FROM commands 
            WHERE status = "queued" 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            return "TestClient_MinKri"  # Fallback
            
    except Exception as e:
        print(f"Error getting agent: {e}")
        return "TestClient_MinKri"

def poll_for_commands(agent_id):
    """Poll server for commands"""
    try:
        response = requests.get(f"{SERVER_URL}/api/agents/{agent_id}/commands", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            commands = data.get('commands', [])
            print(f"SUCCESS: Found {len(commands)} commands for {agent_id}")
            return commands
        else:
            print(f"No commands found for {agent_id}: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error polling for commands: {e}")
        return []

def execute_powershell_command(script):
    """Execute a PowerShell command safely"""
    try:
        # For safety, we'll simulate the execution instead of running real commands
        # In a real scenario, you'd run: subprocess.run(['powershell', '-Command', script], ...)
        
        print(f"SIMULATING PowerShell execution:")
        print(f"Script: {script}")
        
        # Simulate network discovery output
        if "ipconfig" in script.lower():
            simulated_output = """
Windows IP Configuration

Ethernet adapter Ethernet:
   Connection-specific DNS Suffix  . : 
   IPv4 Address. . . . . . . . . . . : 192.168.1.100
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.1.1

ARP Table:
Interface: 192.168.1.100 --- 0x3
  Internet Address      Physical Address      Type
  192.168.1.1          00-11-22-33-44-55     dynamic
  192.168.1.10         aa-bb-cc-dd-ee-ff     dynamic

Active Connections:
  Proto  Local Address          Foreign Address        State
  TCP    192.168.1.100:445      0.0.0.0:0              LISTENING
  TCP    192.168.1.100:3389     0.0.0.0:0              LISTENING
            """
            return True, simulated_output.strip()
        
        # Simulate system info output
        elif "systeminfo" in script.lower():
            simulated_output = """
Host Name:                 DESKTOP-TEST
OS Name:                   Microsoft Windows 10 Pro
OS Version:                10.0.19044 N/A Build 19044
System Type:               x64-based PC
Total Physical Memory:     16,384 MB
            """
            return True, simulated_output.strip()
        
        else:
            return True, f"Simulated execution of: {script[:50]}..."
            
    except Exception as e:
        return False, f"Execution error: {e}"

def send_command_result(agent_id, command_id, success, output, execution_time_ms):
    """Send command execution result back to server"""
    try:
        result_data = {
            'command_id': command_id,
            'status': 'completed' if success else 'failed',
            'success': success,
            'output': output,
            'execution_time_ms': execution_time_ms
        }
        
        response = requests.post(
            f"{SERVER_URL}/api/agents/{agent_id}/commands/result",
            json=result_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"SUCCESS: Result sent for command {command_id}")
            return True
        else:
            print(f"ERROR: Failed to send result for {command_id}: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: Error sending result: {e}")
        return False

def simulate_client_execution():
    """Main function to simulate client agent execution"""
    print("=" * 80)
    print("SIMULATING CLIENT AGENT COMMAND EXECUTION")
    print("=" * 80)
    
    agent_id = get_active_agent()
    print(f"Acting as agent: {agent_id}")
    print()
    
    # Poll for commands
    print("Step 1: Polling for commands...")
    commands = poll_for_commands(agent_id)
    
    if not commands:
        print("No commands to execute")
        return
    
    print(f"Found {len(commands)} commands to execute")
    print()
    
    # Execute each command
    for i, command in enumerate(commands, 1):
        command_id = command.get('id')
        technique = command.get('technique')
        command_data = command.get('command_data', {})
        
        print(f"Step {i+1}: Executing command {command_id}")
        print(f"   Technique: {technique}")
        print(f"   Command ID: {command_id}")
        
        # Get the script to execute
        script = command_data.get('script', '')
        command_type = command_data.get('command_type', 'powershell')
        description = command_data.get('description', 'No description')
        
        print(f"   Description: {description}")
        print(f"   Command Type: {command_type}")
        
        # Execute the command
        start_time = time.time()
        
        if command_type.lower() == 'powershell':
            success, output = execute_powershell_command(script)
        else:
            success, output = True, f"Simulated execution of {command_type} command"
        
        end_time = time.time()
        execution_time_ms = int((end_time - start_time) * 1000)
        
        print(f"   Execution Time: {execution_time_ms}ms")
        print(f"   Success: {success}")
        if output:
            output_preview = output[:200].replace('\n', ' | ')
            print(f"   Output Preview: {output_preview}...")
        
        # Send result back to server
        result_sent = send_command_result(agent_id, command_id, success, output, execution_time_ms)
        
        if result_sent:
            print(f"   SUCCESS: Command {command_id} completed and reported")
        else:
            print(f"   ERROR: Failed to report command {command_id}")
        
        print()
    
    print("=" * 80)
    print("CLIENT AGENT EXECUTION SIMULATION COMPLETE")
    print("=" * 80)
    print(f"Total commands executed: {len(commands)}")
    print("All commands have been simulated and results sent to server!")

if __name__ == "__main__":
    simulate_client_execution()
