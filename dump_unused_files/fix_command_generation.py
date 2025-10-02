#!/usr/bin/env python3
"""
Fix Command Generation
This script fixes the command generation issue by forcing tool calls after AI scenario creation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.server.command_queue.command_manager import CommandManager
from core.server.storage.database_manager import DatabaseManager
import asyncio

async def generate_commands_for_scenario(scenario: dict):
    """Generate commands for a scenario by calling the tools directly"""
    
    # Initialize managers
    db_manager = DatabaseManager()
    command_manager = CommandManager(db_manager)
    
    scenario_id = scenario.get('scenario_id', 'manual_test')
    attack_type = scenario.get('attack_type', 'advanced_persistent_threat')
    
    # Get all registered agents
    try:
        import sqlite3
        conn = sqlite3.connect('soc_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM agents WHERE status = 'active' OR status IS NULL")
        target_agents = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error getting agents: {e}")
        target_agents = []
    
    if not target_agents:
        print("No registered agents found")
        return []
    
    print(f"Generating commands for {len(target_agents)} agents: {target_agents}")
    
    # Generate commands for each agent
    commands_generated = []
    
    for agent_id in target_agents:
        # 1. Container Deployment Command
        deployment_command = {
            'scenario_id': scenario_id,
            'attack_type': attack_type,
            'container_specs': {
                'target_container': {
                    'image': 'ubuntu:latest',
                    'network': 'bridge'
                },
                'attack_container': {
                    'image': 'kalilinux/kali-rolling:latest',
                    'network': 'bridge'
                }
            },
            'deployment_instructions': 'Deploy attack containers for APT simulation'
        }
        
        cmd_id1 = await command_manager.queue_command(
            agent_id=agent_id,
            technique='container_deployment',
            command_data=deployment_command,
            scenario_id=scenario_id
        )
        commands_generated.append(cmd_id1)
        print(f"  SUCCESS: Queued deployment command {cmd_id1} for {agent_id}")
        
        # 2. Attack Execution Command
        execution_command = {
            'scenario_id': scenario_id,
            'attack_type': attack_type,
            'mitre_techniques': scenario.get('mitre_techniques', ['T1566.001', 'T1190']),
            'execution_instructions': 'Execute phishing and lateral movement attack',
            'attack_phases': [
                {'phase': 'initial_access', 'technique': 'T1566.001'},
                {'phase': 'lateral_movement', 'technique': 'T1570'}
            ]
        }
        
        cmd_id2 = await command_manager.queue_command(
            agent_id=agent_id,
            technique='attack_execution',
            command_data=execution_command,
            scenario_id=scenario_id
        )
        commands_generated.append(cmd_id2)
        print(f"  SUCCESS: Queued execution command {cmd_id2} for {agent_id}")
        
        # 3. Self-Replica Command (for testing)
        replica_command = {
            'scenario_id': scenario_id,
            'container_name': f'{agent_id}_replica',
            'network': 'bridge'
        }
        
        cmd_id3 = await command_manager.queue_command(
            agent_id=agent_id,
            technique='create_self_replica',
            command_data=replica_command,
            scenario_id=scenario_id
        )
        commands_generated.append(cmd_id3)
        print(f"  SUCCESS: Queued replica command {cmd_id3} for {agent_id}")
    
    print(f"\nSUCCESS: Generated {len(commands_generated)} commands total")
    return commands_generated

async def main():
    """Main function"""
    print("=" * 80)
    print("FIXING COMMAND GENERATION")
    print("=" * 80)
    
    # Create a test scenario
    scenario = {
        'scenario_id': 'fix_test_scenario_001',
        'name': 'Manual Command Generation Test',
        'attack_type': 'advanced_persistent_threat',
        'mitre_techniques': ['T1566.001', 'T1190', 'T1059.001'],
        'requires_approval': False
    }
    
    print("\nGenerating commands for test scenario...")
    commands = await generate_commands_for_scenario(scenario)
    
    print("\n" + "=" * 80)
    print("COMMAND GENERATION COMPLETE!")
    print("=" * 80)
    print(f"SUCCESS: Generated {len(commands)} commands")
    print("\nNow test with: python test_command_generation_fix.py")

if __name__ == "__main__":
    asyncio.run(main())
