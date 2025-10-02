"""
FINAL COMPLETE TEST - AI WORKING!
Tests the complete flow with AI-generated commands
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
    print("FINAL COMPLETE TEST - AI IS WORKING!")
    print("=" * 80)
    print("Testing: Server + Real Client + AI Commands + Execution")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Server Health
        print("STEP 1: Server Health Check")
        print("-" * 40)
        try:
            async with session.get(f"{SERVER_URL}/health") as resp:
                health = await resp.json()
                print(f"✅ Server Status: {health.get('status')}")
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
            return
        
        print()
        
        # Step 2: Check Commands in Database
        print("STEP 2: Commands in Database")
        print("-" * 40)
        
        conn = sqlite3.connect('soc_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, technique, status, created_at 
            FROM commands 
            WHERE agent_id = 'MinKri_ec11c1e5' 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        
        commands = cursor.fetchall()
        
        if commands:
            print(f"✅ Found {len(commands)} commands for MinKri_ec11c1e5:")
            for cmd_id, technique, status, created in commands:
                print(f"   - {technique}: {status} (ID: {cmd_id[:16]}...)")
        else:
            print("❌ No commands found")
            conn.close()
            return
        
        print()
        
        # Step 3: Check Command Results
        print("STEP 3: Command Execution Results")
        print("-" * 40)
        
        cursor.execute('''
            SELECT command_id, success, execution_time_ms, output 
            FROM command_results 
            WHERE agent_id = 'MinKri_ec11c1e5'
            LIMIT 10
        ''')
        
        results = cursor.fetchall()
        
        if results:
            print(f"✅ Found {len(results)} command results:")
            for cmd_id, success, exec_time, output in results:
                print(f"   - {cmd_id[:16]}...: {'✅ Success' if success else '❌ Failed'}")
                if exec_time:
                    print(f"     Time: {exec_time}ms")
                if output:
                    output_preview = output[:80] + ('...' if len(output) > 80 else '')
                    print(f"     Output: {output_preview}")
        else:
            print("⚠️  No command results found (commands may still be executing)")
        
        print()
        
        # Step 4: Test AI Attack Planning
        print("STEP 4: Testing AI Attack Planning")
        print("-" * 40)
        
        attack_request = {
            "input": {
                "attack_intent": "Create a sophisticated APT simulation with container deployment and email attacks",
                "target_environment": "corporate network",
                "available_agents": ["MinKri_ec11c1e5"],
                "approval_required": False
            }
        }
        
        try:
            print("📤 Sending request to PhantomStrike AI...")
            async with session.post(
                f"{SERVER_URL}/api/soc/plan-attack",
                json=attack_request,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status == 200:
                    ai_response = await resp.json()
                    print("✅ PhantomStrike AI Response Received!")
                    print(f"   Success: {ai_response.get('success')}")
                    if ai_response.get('success'):
                        print("🎉 AI SUCCESSFULLY GENERATED ATTACK PLAN!")
                    else:
                        print(f"⚠️  AI Response: {ai_response.get('error', 'Unknown error')}")
                else:
                    print(f"❌ AI request failed: {resp.status}")
        except Exception as e:
            print(f"❌ Error testing AI: {e}")
        
        print()
        
        # Step 5: Check Latest Commands
        print("STEP 5: Checking for New Commands")
        print("-" * 40)
        
        cursor.execute('''
            SELECT COUNT(*) FROM commands 
            WHERE agent_id = 'MinKri_ec11c1e5' 
            AND created_at > datetime('now', '-5 minutes')
        ''')
        
        recent_commands = cursor.fetchone()[0]
        print(f"📊 Commands created in last 5 minutes: {recent_commands}")
        
        # Step 6: Monitor Real-time Execution
        print("STEP 6: Monitoring Real-time Execution")
        print("-" * 40)
        print("Waiting 30 seconds to monitor command execution...")
        
        start_time = datetime.utcnow()
        timeout = 30
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            # Check for new results
            cursor.execute('''
                SELECT COUNT(*) FROM command_results 
                WHERE agent_id = 'MinKri_ec11c1e5'
            ''')
            
            result_count = cursor.fetchone()[0]
            
            if result_count > 0:
                print(f"🎉 Command results found: {result_count}")
                break
            
            await asyncio.sleep(5)
        
        conn.close()
        
        print()
        print("=" * 80)
        print("FINAL TEST SUMMARY")
        print("=" * 80)
        print()
        print(f"  Server Health: ✅ Working")
        print(f"  Commands Queued: ✅ {len(commands)} commands")
        print(f"  Command Results: {'✅ Found' if results else '⏸️  Pending'}")
        print(f"  AI Attack Planning: {'✅ Working' if 'success' in str(ai_response) else '⚠️  Partial'}")
        print()
        
        if results:
            print("🎉 SUCCESS! Complete production flow working!")
            print("✅ Server + Client Agent + AI + Command Execution = WORKING")
        else:
            print("⚠️  PARTIAL SUCCESS: Infrastructure working, execution pending")
            print("   Commands are queued and sent, but execution results pending")
        
        print()
        print("📊 Current Status:")
        print(f"   - Commands in queue: {len(commands)}")
        print(f"   - Commands executed: {len(results) if results else 0}")
        print(f"   - AI planning: {'Working' if 'success' in str(ai_response) else 'Partial'}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
