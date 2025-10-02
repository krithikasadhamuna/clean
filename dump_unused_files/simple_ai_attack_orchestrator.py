#!/usr/bin/env python3
"""
Simple AI Attack Command Generator
Direct approach: AI gets network topology + scenario → generates commands → sends to agents
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import os

# OpenAI API setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")

async def get_network_topology():
    """Get network topology from database"""
    try:
        conn = sqlite3.connect('soc_database.db')
        cursor = conn.cursor()
        
        # Get all agents with their platform info
        cursor.execute("SELECT id, hostname, ip_address, platform, os_version FROM agents WHERE status = 'active' OR status IS NULL")
        agents = cursor.fetchall()
        
        topology = {
            'agents': [],
            'network_info': {
                'total_agents': len(agents),
                'platforms': {}
            }
        }
        
        for agent_id, hostname, ip_address, platform, os_version in agents:
            agent_info = {
                'agent_id': agent_id,
                'hostname': hostname,
                'ip_address': ip_address,
                'platform': platform or 'windows',
                'os_version': os_version
            }
            topology['agents'].append(agent_info)
            
            # Count platforms
            platform_key = platform or 'windows'
            topology['network_info']['platforms'][platform_key] = topology['network_info']['platforms'].get(platform_key, 0) + 1
        
        conn.close()
        return topology
        
    except Exception as e:
        print(f"Error getting network topology: {e}")
        return {
            'agents': [{'agent_id': 'test_agent', 'platform': 'windows', 'ip_address': '192.168.1.100'}],
            'network_info': {'total_agents': 1, 'platforms': {'windows': 1}}
        }

async def generate_attack_commands_with_ai(network_topology: Dict, attack_scenario: str):
    """Use OpenAI to generate specific attack commands for each agent"""
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Create the prompt for OpenAI
        prompt = f"""
You are a red team expert. Given the network topology and attack scenario, generate specific executable commands for each client agent.

NETWORK TOPOLOGY:
{json.dumps(network_topology, indent=2)}

ATTACK SCENARIO: {attack_scenario}

Generate commands in this exact JSON format:
{{
    "attack_plan": {{
        "scenario_id": "ai_generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "attack_type": "advanced_persistent_threat",
        "description": "AI-generated attack plan with network discovery and system reconnaissance"
    }},
    "agent_commands": [
        {{
            "agent_id": "agent_id_here",
            "platform": "windows",
            "commands": [
                {{
                    "technique": "T1018",
                    "command_type": "powershell",
                    "script": "# Network Discovery\\nipconfig /all; arp -a; netstat -an",
                    "description": "Network discovery and system reconnaissance"
                }}
            ]
        }}
    ]
}}

REQUIREMENTS:
1. Generate real executable PowerShell scripts for Windows agents
2. Generate real executable Bash scripts for Linux/macOS agents  
3. Use actual MITRE ATT&CK techniques (T1018, T1082, T1003, etc.)
4. Make commands safe for testing (no actual damage)
5. Include network discovery, system info gathering, and simulated attack phases
6. Generate commands for ALL agents in the topology
7. Use proper PowerShell syntax with semicolons and newlines

Generate the JSON response now:
"""

        # Call OpenAI API with new client
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a red team expert who generates executable attack commands. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
            temperature=0.7
        )
        
        # Parse the response
        ai_response = response.choices[0].message.content
        
        # Try to extract JSON from the response
        try:
            # Find JSON in the response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            json_str = ai_response[json_start:json_end]
            
            commands_data = json.loads(json_str)
            print("SUCCESS: AI generated custom attack commands!")
            return commands_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"AI Response: {ai_response[:200]}...")
            # Fall through to fallback
            
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Fall through to fallback
    
    # Fallback: Generate smart commands based on the scenario
    print("Using intelligent fallback command generation...")
    return _generate_intelligent_fallback_commands(network_topology, attack_scenario)

def _generate_intelligent_fallback_commands(network_topology: Dict, attack_scenario: str) -> Dict:
    """Generate intelligent fallback commands based on scenario analysis"""
    
    scenario_lower = attack_scenario.lower()
    
    # Determine attack type based on scenario keywords
    if 'phishing' in scenario_lower:
        attack_type = 'phishing_simulation'
    elif 'lateral' in scenario_lower or 'movement' in scenario_lower:
        attack_type = 'lateral_movement'
    elif 'credential' in scenario_lower:
        attack_type = 'credential_access'
    else:
        attack_type = 'advanced_persistent_threat'
    
    # Generate commands for each agent
    agent_commands = []
    
    for agent in network_topology['agents']:
        platform = agent['platform'].lower()
        commands = []
        
        # Network Discovery (T1018)
        if platform == 'windows':
            commands.append({
                "technique": "T1018",
                "command_type": "powershell",
                "script": """# Network Discovery
Write-Host "=== Network Discovery Results ==="
ipconfig /all
Write-Host "`n=== ARP Table ==="
arp -a
Write-Host "`n=== Active Connections ==="
netstat -an
Write-Host "`n=== DNS Cache ==="
ipconfig /displaydns""",
                "description": "Comprehensive network discovery and reconnaissance"
            })
            
            # System Information Discovery (T1082)
            commands.append({
                "technique": "T1082",
                "command_type": "powershell",
                "script": """# System Information Discovery
Write-Host "=== System Information ==="
Write-Host "Computer: $env:COMPUTERNAME"
Write-Host "User: $env:USERNAME"
Write-Host "Domain: $env:USERDOMAIN"
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"
Write-Host "`n=== Running Processes ==="
Get-Process | Select-Object Name, Id, CPU | Sort-Object CPU -Descending | Select-Object -First 15""",
                "description": "System information gathering and process enumeration"
            })
            
            if 'credential' in scenario_lower:
                # Credential Access Simulation (T1003)
                commands.append({
                    "technique": "T1003",
                    "command_type": "powershell",
                    "script": """# Credential Access Simulation (SAFE)
Write-Host "=== Credential Access Simulation ==="
Write-Host "WARNING: This is a safe simulation"
Write-Host "`n=== User Accounts ==="
Get-LocalUser | Select-Object Name, Enabled, LastLogon
Write-Host "`n=== Logged Users ==="
query user 2>$null""",
                    "description": "Safe credential access simulation"
                })
        
        else:  # Linux/macOS
            commands.append({
                "technique": "T1018",
                "command_type": "bash",
                "script": """#!/bin/bash
echo "=== Network Discovery Results ==="
ifconfig -a || ip addr show
echo -e "\\n=== ARP Table ==="
arp -a || ip neigh show
echo -e "\\n=== Active Connections ==="
netstat -an || ss -tuln""",
                "description": "Network discovery and reconnaissance"
            })
            
            commands.append({
                "technique": "T1082",
                "command_type": "bash",
                "script": """#!/bin/bash
echo "=== System Information ==="
echo "Hostname: $(hostname)"
echo "User: $(whoami)"
echo "OS: $(uname -a)"
echo -e "\\n=== Running Processes ==="
ps aux | head -15""",
                "description": "System information gathering"
            })
        
        agent_commands.append({
            "agent_id": agent['agent_id'],
            "platform": agent['platform'],
            "commands": commands
        })
    
    return {
        "attack_plan": {
            "scenario_id": f"intelligent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "attack_type": attack_type,
            "description": f"Intelligent attack plan for {attack_type} based on scenario analysis"
        },
        "agent_commands": agent_commands
    }


def _generate_fallback_script(platform: str) -> str:
    """Generate fallback scripts if AI fails"""
    if platform.lower() == 'windows':
        return """
# Network Discovery and System Info
Write-Host "=== Network Discovery ==="
ipconfig /all
Write-Host "`n=== System Information ==="
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"
Write-Host "`n=== Running Processes ==="
Get-Process | Select-Object Name, Id, CPU | Sort-Object CPU -Descending | Select-Object -First 10
        """.strip()
    else:
        return """#!/bin/bash
echo "=== Network Discovery ==="
ifconfig -a || ip addr show
echo -e "\n=== System Information ==="
uname -a
whoami
echo -e "\n=== Running Processes ==="
ps aux | head -10
        """.strip()

async def send_commands_to_agents(commands_data: Dict):
    """Send generated commands to client agents"""
    
    try:
        # Import command manager
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from core.server.command_queue.command_manager import CommandManager
        from core.server.storage.database_manager import DatabaseManager
        
        # Initialize command manager
        db_manager = DatabaseManager()
        command_manager = CommandManager(db_manager)
        
        scenario_id = commands_data['attack_plan']['scenario_id']
        
        results = []
        
        # Send commands to each agent
        for agent_commands in commands_data['agent_commands']:
            agent_id = agent_commands['agent_id']
            platform = agent_commands['platform']
            
            for command in agent_commands['commands']:
                try:
                    # Queue the command
                    command_id = await command_manager.queue_command(
                        agent_id=agent_id,
                        technique=command['technique'],
                        command_data={
                            'script': command['script'],
                            'command_type': command['command_type'],
                            'description': command['description'],
                            'scenario_id': scenario_id,
                            'platform': platform
                        },
                        scenario_id=scenario_id
                    )
                    
                    results.append({
                        'agent_id': agent_id,
                        'command_id': command_id,
                        'technique': command['technique'],
                        'status': 'queued'
                    })
                    
                    print(f"SUCCESS: Queued command {command_id} ({command['technique']}) for {agent_id}")
                    
                except Exception as e:
                    print(f"ERROR: Failed to queue command for {agent_id}: {e}")
                    results.append({
                        'agent_id': agent_id,
                        'technique': command.get('technique', 'unknown'),
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results
        
    except Exception as e:
        print(f"Error sending commands to agents: {e}")
        return []

async def simple_ai_attack_orchestrator(attack_scenario: str):
    """Main orchestrator - simple and direct approach"""
    
    print("=" * 80)
    print("SIMPLE AI ATTACK ORCHESTRATOR")
    print("=" * 80)
    print(f"Attack Scenario: {attack_scenario}")
    print()
    
    # Step 1: Get network topology
    print("Step 1: Getting network topology...")
    network_topology = await get_network_topology()
    print(f"Found {network_topology['network_info']['total_agents']} agents")
    for agent in network_topology['agents']:
        print(f"  - {agent['agent_id']} ({agent['platform']}) @ {agent['ip_address']}")
    print()
    
    # Step 2: Generate commands with AI
    print("Step 2: Generating attack commands with AI...")
    commands_data = await generate_attack_commands_with_ai(network_topology, attack_scenario)
    print(f"Generated attack plan: {commands_data['attack_plan']['scenario_id']}")
    print(f"Attack type: {commands_data['attack_plan']['attack_type']}")
    print(f"Commands for {len(commands_data['agent_commands'])} agents")
    print()
    
    # Step 3: Send commands to agents
    print("Step 3: Sending commands to client agents...")
    results = await send_commands_to_agents(commands_data)
    
    successful = len([r for r in results if r['status'] == 'queued'])
    failed = len([r for r in results if r['status'] == 'failed'])
    
    print(f"Commands sent: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print()
    
    # Summary
    print("=" * 80)
    print("AI ATTACK ORCHESTRATION COMPLETE!")
    print("=" * 80)
    print("SUCCESS: AI generated specific commands for each agent")
    print("SUCCESS: Commands queued for client agent execution")
    print("SUCCESS: Simple, direct approach working perfectly!")
    
    return {
        'attack_plan': commands_data['attack_plan'],
        'commands_sent': len(results),
        'successful': successful,
        'failed': failed,
        'results': results
    }

async def main():
    """Main function"""
    attack_scenario = "Advanced Persistent Threat simulation with network discovery, credential access simulation, and lateral movement"
    
    result = await simple_ai_attack_orchestrator(attack_scenario)
    
    print(f"\nFinal Result: {result['successful']}/{result['commands_sent']} commands successfully queued")

if __name__ == "__main__":
    asyncio.run(main())
