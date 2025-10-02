"""
REAL AI ATTACK PLANNING TEST
Tests the complete flow with ACTUAL PhantomStrike AI planning attacks
"""

import asyncio
import aiohttp
import sqlite3
import json
import sys
import io
from datetime import datetime
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER_URL = "http://127.0.0.1:8081"
RESULTS_FILE = "ai_attack_results.json"

async def main():
    print("=" * 80)
    print("REAL AI ATTACK PLANNING TEST")
    print("=" * 80)
    print(f"Server: {SERVER_URL}")
    print(f"Results will be saved to: {RESULTS_FILE}")
    print()
    
    results = {
        "test_date": datetime.utcnow().isoformat(),
        "server_url": SERVER_URL,
        "phases": {}
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Phase 1: Check server health
        print("=" * 80)
        print("PHASE 1: Server Health Check")
        print("=" * 80)
        
        try:
            async with session.get(f"{SERVER_URL}/health") as resp:
                health = await resp.json()
                print(f"✅ Server Status: {health.get('status')}")
                results["phases"]["health_check"] = {
                    "status": "success",
                    "data": health
                }
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
            results["phases"]["health_check"] = {
                "status": "failed",
                "error": str(e)
            }
            return
        
        print()
        
        # Phase 2: Wait for real client agent registration
        print("=" * 80)
        print("PHASE 2: Waiting for Real Client Agent")
        print("=" * 80)
        print("Waiting 15 seconds for client agent to register...")
        
        await asyncio.sleep(15)
        
        # Check database for registered agents
        conn = sqlite3.connect('soc_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, hostname, platform, ip_address, status, last_heartbeat 
            FROM agents 
            WHERE id NOT LIKE 'Test%'
            ORDER BY last_heartbeat DESC 
            LIMIT 5
        ''')
        
        real_agents = cursor.fetchall()
        
        if not real_agents:
            print("❌ No real client agents found!")
            print("   Make sure the client agent is running")
            results["phases"]["agent_check"] = {
                "status": "failed",
                "error": "No agents registered"
            }
            conn.close()
            return
        
        print(f"✅ Found {len(real_agents)} real agent(s):")
        agents_info = []
        for agent_id, hostname, platform, ip, status, heartbeat in real_agents:
            print(f"   - {agent_id}")
            print(f"     Platform: {platform}, Hostname: {hostname}")
            print(f"     IP: {ip}, Status: {status}")
            print(f"     Last heartbeat: {heartbeat}")
            agents_info.append({
                "id": agent_id,
                "hostname": hostname,
                "platform": platform,
                "ip": ip,
                "status": status
            })
        
        target_agent_id = real_agents[0][0]
        print(f"\n🎯 Target agent for attack: {target_agent_id}")
        
        results["phases"]["agent_check"] = {
            "status": "success",
            "agents_found": len(real_agents),
            "target_agent": target_agent_id,
            "agents": agents_info
        }
        
        print()
        
        # Phase 3: Invoke REAL PhantomStrike AI to plan attack
        print("=" * 80)
        print("PHASE 3: Invoking PhantomStrike AI for Attack Planning")
        print("=" * 80)
        print("Sending request to PhantomStrike AI...")
        print()
        
        attack_request = {
            "input": {
                "attack_intent": "Execute a realistic APT simulation including container replica creation, email infrastructure deployment, and spear-phishing attack",
                "target_environment": "corporate network",
                "available_agents": [target_agent_id],
                "approval_required": False
            }
        }
        
        try:
            print("📤 Sending attack planning request to AI agent...")
            print(f"   Intent: {attack_request['input']['attack_intent']}")
            print()
            
            async with session.post(
                f"{SERVER_URL}/api/soc/plan-attack",
                json=attack_request,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"❌ PhantomStrike AI request failed: {resp.status}")
                    print(f"   Response: {text[:200]}")
                    results["phases"]["ai_planning"] = {
                        "status": "failed",
                        "error": f"HTTP {resp.status}: {text[:200]}"
                    }
                else:
                    ai_response = await resp.json()
                    print("✅ PhantomStrike AI Response Received!")
                    print()
                    print("=" * 80)
                    print("AI ATTACK PLAN:")
                    print("=" * 80)
                    print(json.dumps(ai_response, indent=2))
                    print("=" * 80)
                    print()
                    
                    results["phases"]["ai_planning"] = {
                        "status": "success",
                        "ai_response": ai_response
                    }
        
        except asyncio.TimeoutError:
            print("❌ Request to PhantomStrike AI timed out")
            results["phases"]["ai_planning"] = {
                "status": "failed",
                "error": "timeout"
            }
        except Exception as e:
            print(f"❌ Error invoking PhantomStrike AI: {e}")
            results["phases"]["ai_planning"] = {
                "status": "failed",
                "error": str(e)
            }
        
        print()
        
        # Phase 4: Check if commands were queued
        print("=" * 80)
        print("PHASE 4: Checking Command Queue")
        print("=" * 80)
        
        cursor.execute('''
            SELECT id, technique, command_data, status, created_at
            FROM commands
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (target_agent_id,))
        
        commands = cursor.fetchall()
        
        if commands:
            print(f"✅ Found {len(commands)} commands queued for {target_agent_id}:")
            commands_info = []
            for cmd_id, technique, data, status, created in commands:
                print(f"   - {technique}")
                print(f"     ID: {cmd_id}")
                print(f"     Status: {status}")
                print(f"     Created: {created}")
                commands_info.append({
                    "id": cmd_id,
                    "technique": technique,
                    "status": status,
                    "created_at": created
                })
            
            results["phases"]["command_queue"] = {
                "status": "success",
                "commands_queued": len(commands),
                "commands": commands_info
            }
        else:
            print(f"⚠️  No commands found for {target_agent_id}")
            results["phases"]["command_queue"] = {
                "status": "no_commands",
                "message": "AI may not have queued commands yet"
            }
        
        print()
        
        # Phase 5: Monitor command execution
        print("=" * 80)
        print("PHASE 5: Monitoring Command Execution")
        print("=" * 80)
        print("Waiting for client agent to poll and execute commands...")
        print("(Monitoring for 60 seconds)")
        print()
        
        if commands:
            command_ids = [cmd[0] for cmd in commands]
            completed = set()
            start_time = datetime.utcnow()
            timeout = 60
            
            while (datetime.utcnow() - start_time).total_seconds() < timeout:
                cursor.execute('''
                    SELECT id, technique, status 
                    FROM commands 
                    WHERE id IN ({})
                '''.format(','.join('?' * len(command_ids))), command_ids)
                
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
                
                if len(completed) == len(command_ids):
                    print("✅ All commands completed!")
                    break
                
                await asyncio.sleep(3)
            
            results["phases"]["execution_monitoring"] = {
                "status": "success",
                "total_commands": len(command_ids),
                "completed": len(completed),
                "completion_rate": f"{len(completed)}/{len(command_ids)}"
            }
        
        conn.close()
        
        # Save results
        print()
        print("=" * 80)
        print("SAVING RESULTS")
        print("=" * 80)
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Results saved to: {RESULTS_FILE}")
        print()
        
        # Final Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print()
        print(f"  Server Health: {results['phases']['health_check']['status']}")
        print(f"  Agents Found: {results['phases']['agent_check'].get('agents_found', 0)}")
        print(f"  AI Planning: {results['phases']['ai_planning']['status']}")
        print(f"  Commands Queued: {results['phases']['command_queue'].get('commands_queued', 0)}")
        if 'execution_monitoring' in results['phases']:
            print(f"  Commands Completed: {results['phases']['execution_monitoring']['completion_rate']}")
        print()
        print(f"📄 Full results saved to: {Path(RESULTS_FILE).absolute()}")
        print()

if __name__ == "__main__":
    asyncio.run(main())

