"""
Test AI Attack Planning with OpenAI API Key
"""

import asyncio
import aiohttp
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
    print("TESTING AI ATTACK PLANNING WITH API KEY")
    print("=" * 80)
    print(f"Server: {SERVER_URL}")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Check server health
        print("Step 1: Checking server health...")
        try:
            async with session.get(f"{SERVER_URL}/health") as resp:
                health = await resp.json()
                print(f"✅ Server Status: {health.get('status')}")
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
            return
        
        print()
        
        # Step 2: Check for registered agents
        print("Step 2: Checking for registered agents...")
        try:
            async with session.get(f"{SERVER_URL}/api/agents") as resp:
                if resp.status == 200:
                    agents = await resp.json()
                    print(f"✅ Found {len(agents)} registered agents")
                    for agent in agents:
                        print(f"   - {agent.get('id')} ({agent.get('platform')})")
                else:
                    print("⚠️  No agents endpoint available")
        except Exception as e:
            print(f"⚠️  Could not check agents: {e}")
        
        print()
        
        # Step 3: Test AI attack planning
        print("Step 3: Testing PhantomStrike AI attack planning...")
        print("Sending attack request to AI...")
        
        attack_request = {
            "input": {
                "attack_intent": "Create a realistic APT simulation with container replica creation, email infrastructure deployment, and spear-phishing attack",
                "target_environment": "corporate network",
                "available_agents": ["MinKri_ec11c1e5"],
                "approval_required": False
            }
        }
        
        try:
            print("📤 Sending request to PhantomStrike AI...")
            print(f"   Intent: {attack_request['input']['attack_intent']}")
            print()
            
            async with session.post(
                f"{SERVER_URL}/api/soc/plan-attack",
                json=attack_request,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                print(f"Response Status: {resp.status}")
                
                if resp.status == 200:
                    ai_response = await resp.json()
                    print("✅ PhantomStrike AI Response Received!")
                    print()
                    print("=" * 80)
                    print("AI ATTACK PLAN:")
                    print("=" * 80)
                    print(json.dumps(ai_response, indent=2))
                    print("=" * 80)
                    
                    # Check if commands were generated
                    if ai_response.get('success'):
                        print("\n🎯 AI SUCCESSFULLY GENERATED ATTACK PLAN!")
                        print("✅ Commands should be queued for execution")
                    else:
                        print(f"\n⚠️  AI Response: {ai_response.get('error', 'Unknown error')}")
                else:
                    text = await resp.text()
                    print(f"❌ Request failed: {resp.status}")
                    print(f"   Response: {text[:500]}")
        
        except asyncio.TimeoutError:
            print("❌ Request to PhantomStrike AI timed out")
        except Exception as e:
            print(f"❌ Error invoking PhantomStrike AI: {e}")
        
        print()
        
        # Step 4: Check command queue
        print("Step 4: Checking command queue...")
        try:
            async with session.get(f"{SERVER_URL}/api/agents/MinKri_ec11c1e5/commands") as resp:
                if resp.status == 200:
                    commands = await resp.json()
                    print(f"✅ Found {len(commands.get('commands', []))} commands in queue")
                    for cmd in commands.get('commands', []):
                        print(f"   - {cmd.get('technique')}: {cmd.get('status')}")
                else:
                    print("⚠️  Could not check commands")
        except Exception as e:
            print(f"⚠️  Could not check commands: {e}")
        
        print()
        print("=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
