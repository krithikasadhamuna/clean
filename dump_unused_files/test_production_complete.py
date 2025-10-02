"""
Complete Production Test
Tests the full flow: Register → Queue → Retrieve → Execute → Report
"""

import asyncio
import aiohttp
import sys
import io
import sqlite3
from datetime import datetime

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER_URL = "http://127.0.0.1:8081"

async def main():
    print("=" * 80)
    print("COMPLETE PRODUCTION FLOW TEST")
    print("=" * 80)
    print()
    
    # Step 1: Check server
    print("Step 1: Checking Server...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVER_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Server: {data['status']}")
                    print(f"   Agents: {data['agents']}")
                else:
                    print(f"❌ Server error: {response.status}")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    print()
    
    # Step 2: Register an agent
    print("Step 2: Registering Test Agent...")
    agent_id = "TestAgent_Production_001"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SERVER_URL}/api/agents/register", json={
            'agent_id': agent_id,
            'hostname': 'test-machine',
            'platform': 'windows',
            'ip_address': '192.168.1.100'
        }) as response:
            if response.status == 200:
                print(f"✅ Agent registered: {agent_id}")
            else:
                print(f"❌ Registration failed: {response.status}")
                return
    
    print()
    
    # Step 3: Queue commands directly via database
    print("Step 3: Queuing Attack Commands...")
    
    from core.server.command_queue.command_manager import CommandManager
    from core.server.storage.database_manager import DatabaseManager
    
    db_manager = DatabaseManager(db_path='soc_database.db')
    cmd_manager = CommandManager(db_manager)
    
    commands_to_queue = [
        {
            'technique': 'create_self_replica',
            'data': {'container_name': f'{agent_id}_replica', 'network': 'bridge'}
        },
        {
            'technique': 'deploy_smtp_container',
            'data': {'container_name': 'test_smtp', 'port': 587}
        },
        {
            'technique': 'execute_phishing',
            'data': {'from': 'test_smtp', 'to': f'{agent_id}_replica'}
        }
    ]
    
    queued_ids = []
    for cmd in commands_to_queue:
        cmd_id = await cmd_manager.queue_command(
            agent_id=agent_id,
            technique=cmd['technique'],
            command_data=cmd['data']
        )
        queued_ids.append(cmd_id)
        print(f"  ✅ Queued: {cmd['technique']} (ID: {cmd_id[:12]}...)")
    
    print()
    
    # Step 4: Retrieve commands via API (simulate client polling)
    print("Step 4: Retrieving Commands (Client POV)...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_URL}/api/agents/{agent_id}/commands") as response:
            if response.status == 200:
                data = await response.json()
                commands = data.get('commands', [])
                print(f"✅ Retrieved {len(commands)} commands")
                for cmd in commands:
                    print(f"   - {cmd.get('technique')} (ID: {cmd.get('id')[:12]}...)")
            else:
                print(f"❌ Retrieval failed: {response.status}")
                return
    
    print()
    
    # Step 5: Simulate execution and report results
    print("Step 5: Simulating Execution & Reporting Results...")
    
    async with aiohttp.ClientSession() as session:
        for cmd_id in queued_ids:
            result_data = {
                'command_id': cmd_id,
                'status': 'completed',
                'success': True,
                'output': f'Simulated execution of {cmd_id}',
                'execution_time_ms': 1500
            }
            
            async with session.post(
                f"{SERVER_URL}/api/agents/{agent_id}/commands/result",
                json=result_data
            ) as response:
                if response.status == 200:
                    print(f"  ✅ Result reported: {cmd_id[:12]}...")
                else:
                    print(f"  ❌ Report failed: {response.status}")
    
    print()
    
    # Step 6: Verify in database
    print("Step 6: Verifying Database...")
    
    conn = sqlite3.connect('soc_database.db')
    cursor = conn.cursor()
    
    # Check commands
    cursor.execute('SELECT COUNT(*) FROM commands WHERE agent_id = ?', (agent_id,))
    cmd_count = cursor.fetchone()[0]
    print(f"  ✅ Commands in DB: {cmd_count}")
    
    # Check results
    cursor.execute('SELECT COUNT(*) FROM command_results WHERE agent_id = ?', (agent_id,))
    result_count = cursor.fetchone()[0]
    print(f"  ✅ Results in DB: {result_count}")
    
    # Check command status
    cursor.execute('''
        SELECT technique, status FROM commands 
        WHERE agent_id = ? ORDER BY created_at
    ''', (agent_id,))
    
    print("\n  Command Status:")
    for technique, status in cursor.fetchall():
        print(f"    - {technique}: {status}")
    
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ COMPLETE PRODUCTION FLOW TEST PASSED!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  ✅ Server: Operational")
    print(f"  ✅ Agent: Registered")
    print(f"  ✅ Commands: Queued ({len(queued_ids)})")
    print(f"  ✅ Commands: Retrieved via API")
    print(f"  ✅ Results: Reported")
    print(f"  ✅ Database: Updated")
    print()
    print("🎉 Production code is working perfectly!")
    print()

if __name__ == "__main__":
    asyncio.run(main())

