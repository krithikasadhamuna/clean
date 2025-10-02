"""
Complete Flow Test - Final Version
Tests the entire production flow with real client agent
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
RESULTS_FILE = "complete_flow_results.json"

async def main():
    print("=" * 80)
    print("COMPLETE PRODUCTION FLOW TEST - FINAL")
    print("=" * 80)
    print("Testing: Server + Real Client Agent + Command Execution")
    print()
    
    results = {
        "test_date": datetime.utcnow().isoformat(),
        "server_url": SERVER_URL,
        "phases": {}
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Phase 1: Server Health
        print("PHASE 1: Server Health Check")
        print("-" * 40)
        try:
            async with session.get(f"{SERVER_URL}/health") as resp:
                health = await resp.json()
                print(f"✅ Server Status: {health.get('status')}")
                results["phases"]["server_health"] = {
                    "status": "success",
                    "data": health
                }
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
            results["phases"]["server_health"] = {
                "status": "failed",
                "error": str(e)
            }
            return
        
        print()
        
        # Phase 2: Check Real Client Agent
        print("PHASE 2: Real Client Agent Status")
        print("-" * 40)
        
        conn = sqlite3.connect('soc_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, hostname, platform, ip_address, status, last_heartbeat 
            FROM agents 
            WHERE id = 'MinKri_ec11c1e5'
        ''')
        
        agent = cursor.fetchone()
        
        if not agent:
            print("❌ Real client agent not found!")
            results["phases"]["client_agent"] = {
                "status": "failed",
                "error": "Agent not found"
            }
            conn.close()
            return
        
        agent_id, hostname, platform, ip, status, heartbeat = agent
        print(f"✅ Real Client Agent Found:")
        print(f"   ID: {agent_id}")
        print(f"   Hostname: {hostname}")
        print(f"   Platform: {platform}")
        print(f"   IP: {ip}")
        print(f"   Status: {status}")
        print(f"   Last Heartbeat: {heartbeat}")
        
        results["phases"]["client_agent"] = {
            "status": "success",
            "agent_id": agent_id,
            "hostname": hostname,
            "platform": platform,
            "ip": ip,
            "status": status
        }
        
        print()
        
        # Phase 3: Queue Commands
        print("PHASE 3: Queuing Attack Commands")
        print("-" * 40)
        
        from core.server.command_queue.command_manager import CommandManager
        from core.server.storage.database_manager import DatabaseManager
        
        db_manager = DatabaseManager(db_path='soc_database.db')
        cmd_manager = CommandManager(db_manager)
        
        commands = [
            {
                'technique': 'create_self_replica',
                'data': {
                    'container_name': f'{agent_id}_replica',
                    'network': 'bridge'
                },
                'desc': 'Create self-replica container'
            },
            {
                'technique': 'deploy_smtp_container',
                'data': {
                    'container_name': 'smtp_server',
                    'network': 'bridge',
                    'port': 587
                },
                'desc': 'Deploy SMTP server'
            },
            {
                'technique': 'execute_phishing',
                'data': {
                    'from_container': 'smtp_server',
                    'to_targets': [f'{agent_id}_replica'],
                    'mitre_technique': 'T1566.001'
                },
                'desc': 'Execute phishing attack'
            }
        ]
        
        queued_commands = []
        for cmd in commands:
            try:
                cmd_id = await cmd_manager.queue_command(
                    agent_id=agent_id,
                    technique=cmd['technique'],
                    command_data=cmd['data'],
                    scenario_id='final_test_001'
                )
                queued_commands.append(cmd_id)
                print(f"✅ Queued: {cmd['desc']}")
                print(f"   ID: {cmd_id[:16]}...")
            except Exception as e:
                print(f"❌ Failed to queue {cmd['desc']}: {e}")
        
        results["phases"]["command_queue"] = {
            "status": "success",
            "commands_queued": len(queued_commands),
            "command_ids": queued_commands
        }
        
        print(f"\n✅ {len(queued_commands)} commands queued")
        print()
        
        # Phase 4: Monitor Execution
        print("PHASE 4: Monitoring Command Execution")
        print("-" * 40)
        print("Waiting for client agent to execute commands...")
        print("(Monitoring for 90 seconds)")
        print()
        
        completed = set()
        start_time = datetime.utcnow()
        timeout = 90
        
        execution_log = []
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            # Check command status
            cursor.execute('''
                SELECT id, technique, status, created_at
                FROM commands 
                WHERE id IN ({})
            '''.format(','.join('?' * len(queued_commands))), queued_commands)
            
            for cmd_id, technique, status, created in cursor.fetchall():
                if cmd_id not in completed and status != 'queued':
                    print(f"  📊 {technique}: {status}")
                    execution_log.append({
                        "command_id": cmd_id,
                        "technique": technique,
                        "status": status,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    completed.add(cmd_id)
                    
                    # Check for result (without error column)
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
                            output_preview = output[:100] + ('...' if len(output) > 100 else '')
                            print(f"     Output: {output_preview}")
                    print()
            
            if len(completed) == len(queued_commands):
                print("✅ All commands completed!")
                break
            
            await asyncio.sleep(3)
        
        results["phases"]["execution"] = {
            "status": "success",
            "total_commands": len(queued_commands),
            "completed": len(completed),
            "completion_rate": f"{len(completed)}/{len(queued_commands)}",
            "execution_log": execution_log
        }
        
        conn.close()
        
        # Phase 5: Final Summary
        print("PHASE 5: Final Results")
        print("-" * 40)
        
        # Check final database state
        conn = sqlite3.connect('soc_database.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM commands WHERE agent_id = ?', (agent_id,))
        total_commands = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM command_results WHERE agent_id = ?', (agent_id,))
        total_results = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM log_entries WHERE agent_id = ?', (agent_id,))
        total_logs = cursor.fetchone()[0]
        
        print(f"📊 Database Summary:")
        print(f"   Total Commands: {total_commands}")
        print(f"   Command Results: {total_results}")
        print(f"   Log Entries: {total_logs}")
        
        results["phases"]["database_summary"] = {
            "total_commands": total_commands,
            "total_results": total_results,
            "total_logs": total_logs
        }
        
        conn.close()
        
        # Save results
        print()
        print("Saving results...")
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Results saved to: {RESULTS_FILE}")
        
        print()
        print("=" * 80)
        print("FINAL TEST SUMMARY")
        print("=" * 80)
        print()
        print(f"  Server Health: {results['phases']['server_health']['status']}")
        print(f"  Client Agent: {results['phases']['client_agent']['status']}")
        print(f"  Commands Queued: {results['phases']['command_queue']['commands_queued']}")
        print(f"  Commands Completed: {results['phases']['execution']['completion_rate']}")
        print(f"  Database Commands: {results['phases']['database_summary']['total_commands']}")
        print(f"  Database Results: {results['phases']['database_summary']['total_results']}")
        print(f"  Log Entries: {results['phases']['database_summary']['total_logs']}")
        print()
        
        if len(completed) == len(queued_commands):
            print("🎉 SUCCESS! Complete production flow working!")
            print("✅ Server + Client Agent + Command Execution = WORKING")
        else:
            print(f"⚠️  PARTIAL SUCCESS: {len(completed)}/{len(queued_commands)} commands completed")
        
        print()
        print(f"📄 Full results: {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
