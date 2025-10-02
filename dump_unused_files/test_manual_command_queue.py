"""
Manual Command Queue Test
Bypass AI and manually queue commands to test the complete flow
"""

import asyncio
import aiohttp
import sqlite3
import json
import sys
import io
from datetime import datetime

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER_URL = "http://127.0.0.1:8081"

async def main():
    print("=" * 80)
    print("MANUAL COMMAND QUEUE TEST")
    print("=" * 80)
    print("Bypassing AI and manually testing the complete flow")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Check server health
        print("Step 1: Server Health Check")
        print("-" * 40)
        try:
            async with session.get(f"{SERVER_URL}/health") as resp:
                health = await resp.json()
                print(f"✅ Server Status: {health.get('status')}")
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
            return
        
        print()
        
        # Step 2: Check database for agents
        print("Step 2: Checking Database for Agents")
        print("-" * 40)
        
        conn = sqlite3.connect('soc_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, hostname, platform, ip_address, status, last_heartbeat 
            FROM agents 
            ORDER BY last_heartbeat DESC 
            LIMIT 5
        ''')
        
        agents = cursor.fetchall()
        
        if not agents:
            print("❌ No agents found in database!")
            conn.close()
            return
        
        print(f"✅ Found {len(agents)} agents in database:")
        for agent_id, hostname, platform, ip, status, heartbeat in agents:
            print(f"   - {agent_id} ({platform})")
            print(f"     Hostname: {hostname}, IP: {ip}")
            print(f"     Status: {status}, Last HB: {heartbeat}")
        
        target_agent_id = agents[0][0]
        print(f"\n🎯 Target agent: {target_agent_id}")
        
        print()
        
        # Step 3: Manually queue commands
        print("Step 3: Manually Queuing Commands")
        print("-" * 40)
        
        from core.server.command_queue.command_manager import CommandManager
        from core.server.storage.database_manager import DatabaseManager
        
        db_manager = DatabaseManager(db_path='soc_database.db')
        cmd_manager = CommandManager(db_manager)
        
        commands_to_queue = [
            {
                'technique': 'create_self_replica',
                'data': {
                    'container_name': f'{target_agent_id}_replica_test',
                    'network': 'bridge',
                    'description': 'Create a replica container of the host system'
                },
                'desc': 'Create self-replica container'
            },
            {
                'technique': 'deploy_smtp_container',
                'data': {
                    'container_name': 'test_smtp_server',
                    'network': 'bridge',
                    'port': 587,
                    'description': 'Deploy SMTP server for email attacks'
                },
                'desc': 'Deploy SMTP server container'
            },
            {
                'technique': 'execute_phishing',
                'data': {
                    'from_container': 'test_smtp_server',
                    'to_targets': [f'{target_agent_id}_replica_test'],
                    'mitre_technique': 'T1566.001',
                    'description': 'Execute spear-phishing attack'
                },
                'desc': 'Execute phishing attack'
            }
        ]
        
        queued_commands = []
        for cmd in commands_to_queue:
            try:
                cmd_id = await cmd_manager.queue_command(
                    agent_id=target_agent_id,
                    technique=cmd['technique'],
                    command_data=cmd['data'],
                    scenario_id='manual_test_001'
                )
                queued_commands.append(cmd_id)
                print(f"✅ Queued: {cmd['desc']}")
                print(f"   ID: {cmd_id[:16]}...")
            except Exception as e:
                print(f"❌ Failed to queue {cmd['desc']}: {e}")
        
        print(f"\n✅ {len(queued_commands)} commands queued successfully")
        
        print()
        
        # Step 4: Test command retrieval via API
        print("Step 4: Testing Command Retrieval")
        print("-" * 40)
        
        try:
            async with session.get(f"{SERVER_URL}/api/agents/{target_agent_id}/commands") as resp:
                if resp.status == 200:
                    commands_response = await resp.json()
                    commands = commands_response.get('commands', [])
                    print(f"✅ Retrieved {len(commands)} commands via API")
                    
                    for cmd in commands:
                        print(f"   - {cmd.get('technique')}: {cmd.get('status')}")
                        print(f"     ID: {cmd.get('id', 'N/A')[:16]}...")
                else:
                    print(f"❌ Command retrieval failed: {resp.status}")
        except Exception as e:
            print(f"❌ Error retrieving commands: {e}")
        
        print()
        
        # Step 5: Monitor command execution
        print("Step 5: Monitoring Command Execution")
        print("-" * 40)
        print("Waiting for client agent to poll and execute commands...")
        print("(Monitoring for 60 seconds)")
        print()
        
        if queued_commands:
            completed = set()
            start_time = datetime.utcnow()
            timeout = 60
            
            while (datetime.utcnow() - start_time).total_seconds() < timeout:
                # Check command status
                cursor.execute('''
                    SELECT id, technique, status 
                    FROM commands 
                    WHERE id IN ({})
                '''.format(','.join('?' * len(queued_commands))), queued_commands)
                
                for cmd_id, technique, status in cursor.fetchall():
                    if cmd_id not in completed and status != 'queued':
                        print(f"  📊 {technique}: {status}")
                        completed.add(cmd_id)
                        
                        # Check for result
                        cursor.execute('''
                            SELECT success, execution_time_ms, output, error
                            FROM command_results 
                            WHERE command_id = ?
                        ''', (cmd_id,))
                        
                        result = cursor.fetchone()
                        if result:
                            success, exec_time, output, error = result
                            print(f"     Result: {'✅ Success' if success else '❌ Failed'}")
                            if exec_time:
                                print(f"     Time: {exec_time}ms")
                            if output:
                                output_preview = output[:100] + ('...' if len(output) > 100 else '')
                                print(f"     Output: {output_preview}")
                            if error:
                                print(f"     Error: {error[:100]}")
                        print()
                
                if len(completed) == len(queued_commands):
                    print("✅ All commands completed!")
                    break
                
                await asyncio.sleep(3)
            
            print(f"\n📊 Execution Summary:")
            print(f"   Total Commands: {len(queued_commands)}")
            print(f"   Completed: {len(completed)}")
            print(f"   Success Rate: {len(completed)}/{len(queued_commands)}")
        
        conn.close()
        
        print()
        print("=" * 80)
        print("MANUAL TEST COMPLETE")
        print("=" * 80)
        print()
        print("This test bypassed the AI and manually queued commands")
        print("to verify the complete command execution flow works.")
        print()

if __name__ == "__main__":
    asyncio.run(main())
