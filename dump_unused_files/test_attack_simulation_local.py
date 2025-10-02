"""
Local Attack Simulation Test
Tests the complete AI attack flow with the local development server
"""

import asyncio
import aiohttp
import json
import sys
import io
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER_URL = "http://127.0.0.1:8081"

print("=" * 80)
print("CODEGREY AI SOC PLATFORM - LOCAL ATTACK SIMULATION TEST")
print("=" * 80)
print()


async def queue_commands_directly():
    """Queue commands directly using the database"""
    print("STEP 1: Queuing Attack Commands")
    print("-" * 80)
    
    # Import the command manager
    from core.server.command_queue.command_manager import CommandManager
    from core.server.storage.database_manager import DatabaseManager
    
    # Initialize
    db_manager = DatabaseManager(db_path='soc_database.db')
    cmd_manager = CommandManager(db_manager)
    
    # Get registered agents
    import sqlite3
    conn = sqlite3.connect('soc_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, hostname, platform FROM agents')
    agents = cursor.fetchall()
    conn.close()
    
    if not agents:
        print("❌ No agents registered yet!")
        print("   Please start a client agent first.")
        return None
    
    print(f"✅ Found {len(agents)} registered agent(s):")
    for agent_id, hostname, platform in agents:
        print(f"   - {agent_id} ({platform}) @ {hostname}")
    print()
    
    # Use the first agent
    target_agent_id = agents[0][0]
    
    print(f"🎯 Target agent: {target_agent_id}")
    print()
    
    # Queue test commands
    commands_to_queue = [
        {
            'technique': 'create_self_replica',
            'command_data': {
                'container_name': f'{target_agent_id}_test_replica',
                'network': 'bridge'
            },
            'description': 'Create self-replica container'
        },
        {
            'technique': 'deploy_smtp_container',
            'command_data': {
                'container_name': 'phishing_smtp_local',
                'network': 'bridge',
                'port': 587
            },
            'description': 'Deploy SMTP server for phishing'
        },
        {
            'technique': 'execute_phishing',
            'command_data': {
                'from_container': 'phishing_smtp_local',
                'to_targets': [f'{target_agent_id}_test_replica'],
                'mitre_technique': 'T1566.001',
                'email_subject': 'LOCAL TEST: Urgent Action Required'
            },
            'description': 'Execute phishing attack'
        }
    ]
    
    queued_ids = []
    
    for cmd in commands_to_queue:
        try:
            cmd_id = await cmd_manager.queue_command(
                agent_id=target_agent_id,
                technique=cmd['technique'],
                command_data=cmd['command_data'],
                scenario_id='local_test_001'
            )
            queued_ids.append(cmd_id)
            print(f"✅ Queued: {cmd['description']}")
            print(f"   Command ID: {cmd_id}")
            print()
        except Exception as e:
            print(f"❌ Failed to queue {cmd['technique']}: {e}")
    
    print(f"✅ Total commands queued: {len(queued_ids)}")
    print()
    
    return target_agent_id, queued_ids


async def monitor_command_execution(agent_id: str, command_ids: list, timeout_seconds: int = 60):
    """Monitor command execution"""
    print("STEP 2: Monitoring Command Execution")
    print("-" * 80)
    print(f"Monitoring agent: {agent_id}")
    print(f"Watching {len(command_ids)} commands")
    print(f"Timeout: {timeout_seconds} seconds")
    print()
    
    import sqlite3
    start_time = datetime.utcnow()
    
    completed_commands = set()
    
    while (datetime.utcnow() - start_time).total_seconds() < timeout_seconds:
        try:
            # Check command status in database
            conn = sqlite3.connect('soc_database.db')
            cursor = conn.cursor()
            
            for cmd_id in command_ids:
                if cmd_id in completed_commands:
                    continue
                
                # Check command status
                cursor.execute('SELECT status, technique FROM commands WHERE id = ?', (cmd_id,))
                row = cursor.fetchone()
                
                if row:
                    status, technique = row
                    
                    if status != 'queued':
                        if cmd_id not in completed_commands:
                            print(f"📊 {technique}: {status}")
                            completed_commands.add(cmd_id)
                            
                            # Check for result
                            cursor.execute('''
                                SELECT success, output, execution_time_ms 
                                FROM command_results 
                                WHERE command_id = ?
                            ''', (cmd_id,))
                            result_row = cursor.fetchone()
                            
                            if result_row:
                                success, output, exec_time = result_row
                                print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
                                print(f"   Execution time: {exec_time}ms")
                                if output:
                                    print(f"   Output: {output[:100]}...")
                                print()
            
            conn.close()
            
            # Check if all commands completed
            if len(completed_commands) == len(command_ids):
                print("✅ All commands completed!")
                return True
            
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"⚠️  Monitoring error: {e}")
            await asyncio.sleep(2)
    
    print(f"⏱️  Timeout reached: {len(completed_commands)}/{len(command_ids)} commands completed")
    return False


async def test_api_endpoints():
    """Test the API endpoints"""
    print("STEP 0: Testing API Endpoints")
    print("-" * 80)
    
    async with aiohttp.ClientSession() as session:
        # Test health
        try:
            async with session.get(f"{SERVER_URL}/health") as response:
                if response.status == 200:
                    print("✅ Server health check passed")
                else:
                    print(f"⚠️  Server returned status {response.status}")
        except Exception as e:
            print(f"❌ Server connection failed: {e}")
            print("   Is the server running? (run start_local_dev_environment.py)")
            return False
        
        # Test command endpoint
        try:
            async with session.get(f"{SERVER_URL}/api/agents/test/commands") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Command endpoint accessible")
                else:
                    print(f"⚠️  Command endpoint returned {response.status}")
        except Exception as e:
            print(f"❌ Command endpoint error: {e}")
            return False
    
    print()
    return True


async def main():
    """Main test function"""
    
    # Test API endpoints first
    if not await test_api_endpoints():
        return 1
    
    print()
    
    # Queue commands
    result = await queue_commands_directly()
    if result is None:
        return 1
    
    agent_id, command_ids = result
    
    print()
    
    # Monitor execution
    print("Waiting for client agent to poll and execute commands...")
    print("(Make sure the client agent is running!)")
    print()
    
    success = await monitor_command_execution(agent_id, command_ids, timeout_seconds=90)
    
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    if success:
        print("✅ LOCAL ATTACK SIMULATION TEST PASSED")
        print()
        print("All commands were executed successfully!")
    else:
        print("⚠️  TEST INCOMPLETE")
        print()
        print("Some commands may still be pending.")
        print("Check the client agent logs for details.")
    
    print()
    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print()
    print("1. Check the database:")
    print("   sqlite3 soc_database.db")
    print("   > SELECT * FROM commands;")
    print("   > SELECT * FROM command_results;")
    print()
    print("2. Check server logs in the other terminal")
    print()
    print("3. Check client agent logs")
    print()
    print("4. Test with Docker:")
    print("   - Ensure Docker is running")
    print("   - Client agent will create actual containers")
    print("   - Use 'docker ps' to see running containers")
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

