"""
Test with Real Client Agent
Queues commands and monitors execution with the actual client agent
"""

import asyncio
import sqlite3
import sys
import io
from datetime import datetime

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    print("=" * 80)
    print("TESTING WITH REAL CLIENT AGENT")
    print("=" * 80)
    print()
    
    # Step 1: Find registered agents
    print("Step 1: Checking for registered agents...")
    
    conn = sqlite3.connect('soc_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, hostname, platform, ip_address, last_heartbeat 
        FROM agents 
        ORDER BY last_heartbeat DESC 
        LIMIT 5
    ''')
    
    agents = cursor.fetchall()
    
    if not agents:
        print("❌ No agents registered yet!")
        print("   The client agent may still be initializing...")
        print("   Wait a few seconds and try again.")
        conn.close()
        return
    
    print(f"✅ Found {len(agents)} registered agent(s):")
    for agent_id, hostname, platform, ip, heartbeat in agents:
        print(f"   - {agent_id} ({platform}) @ {hostname}")
        print(f"     IP: {ip}, Last heartbeat: {heartbeat}")
    
    # Use the most recent agent
    target_agent_id = agents[0][0]
    print(f"\n🎯 Target agent: {target_agent_id}")
    print()
    
    # Step 2: Queue commands
    print("Step 2: Queuing attack commands...")
    
    from core.server.command_queue.command_manager import CommandManager
    from core.server.storage.database_manager import DatabaseManager
    
    db_manager = DatabaseManager(db_path='soc_database.db')
    cmd_manager = CommandManager(db_manager)
    
    commands = [
        {
            'technique': 'create_self_replica',
            'data': {
                'container_name': f'{target_agent_id}_test_replica',
                'network': 'bridge'
            },
            'desc': 'Create self-replica container'
        },
        {
            'technique': 'deploy_smtp_container',
            'data': {
                'container_name': 'realtest_smtp',
                'network': 'bridge',
                'port': 587
            },
            'desc': 'Deploy SMTP server'
        },
        {
            'technique': 'execute_phishing',
            'data': {
                'from_container': 'realtest_smtp',
                'to_targets': [f'{target_agent_id}_test_replica'],
                'mitre_technique': 'T1566.001'
            },
            'desc': 'Execute phishing attack'
        }
    ]
    
    queued_ids = []
    for cmd in commands:
        cmd_id = await cmd_manager.queue_command(
            agent_id=target_agent_id,
            technique=cmd['technique'],
            command_data=cmd['data'],
            scenario_id='realclient_test_001'
        )
        queued_ids.append(cmd_id)
        print(f"  ✅ Queued: {cmd['desc']}")
        print(f"     ID: {cmd_id[:16]}...")
    
    print(f"\n✅ {len(queued_ids)} commands queued for {target_agent_id}")
    print()
    
    # Step 3: Monitor execution
    print("Step 3: Monitoring command execution...")
    print("(Waiting for client to poll and execute...)")
    print()
    
    completed = set()
    start_time = datetime.utcnow()
    timeout = 60  # 60 seconds
    
    while (datetime.utcnow() - start_time).total_seconds() < timeout:
        # Check command status
        cursor.execute('''
            SELECT id, technique, status 
            FROM commands 
            WHERE id IN ({})
        '''.format(','.join('?' * len(queued_ids))), queued_ids)
        
        for cmd_id, technique, status in cursor.fetchall():
            if cmd_id not in completed and status != 'queued':
                print(f"  📊 {technique}: {status}")
                completed.add(cmd_id)
                
                # Check for result
                cursor.execute('''
                    SELECT success, execution_time_ms, output 
                    FROM command_results 
                    WHERE command_id = ?
                ''', (cmd_id,))
                
                result = cursor.fetchone()
                if result:
                    success, exec_time, output = result
                    print(f"     Result: {'✅ Success' if success else '❌ Failed'}")
                    if exec_time:
                        print(f"     Time: {exec_time}ms")
                    if output:
                        output_preview = output[:80] + ('...' if len(output) > 80 else '')
                        print(f"     Output: {output_preview}")
                print()
        
        # Check if all completed
        if len(completed) == len(queued_ids):
            print("✅ All commands completed!")
            break
        
        await asyncio.sleep(3)
    
    conn.close()
    
    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    print(f"  Agent: {target_agent_id}")
    print(f"  Commands Queued: {len(queued_ids)}")
    print(f"  Commands Completed: {len(completed)}")
    print()
    
    if len(completed) == len(queued_ids):
        print("✅ SUCCESS! Real client agent executed all commands!")
    else:
        print(f"⏱️  Timeout: {len(completed)}/{len(queued_ids)} commands completed")
        print("   Some commands may still be executing")
    
    print()
    print("Check server logs for detailed execution traces")
    print()

if __name__ == "__main__":
    asyncio.run(main())

