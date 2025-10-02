"""
Quick Client Agent Test
Simulates a client agent connecting to the production server
"""

import asyncio
import aiohttp
import platform
import socket
import sys
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER_URL = "http://127.0.0.1:8081"

async def test_client():
    """Simulate a client agent"""
    
    agent_id = f"TestClient_{socket.gethostname()[:8]}"
    
    print("=" * 80)
    print("QUICK CLIENT AGENT TEST")
    print("=" * 80)
    print()
    print(f"Agent ID: {agent_id}")
    print(f"Server: {SERVER_URL}")
    print()
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Register
        print("Step 1: Registering with server...")
        try:
            async with session.post(f"{SERVER_URL}/api/agents/register", json={
                'agent_id': agent_id,
                'hostname': socket.gethostname(),
                'platform': platform.system().lower(),
                'ip_address': '127.0.0.1'
            }) as response:
                if response.status == 200:
                    print("✅ Agent registered successfully")
                else:
                    print(f"❌ Registration failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return
        
        print()
        
        # Step 2: Poll for commands (3 times)
        print("Step 2: Polling for commands...")
        for i in range(3):
            try:
                async with session.get(f"{SERVER_URL}/api/agents/{agent_id}/commands") as response:
                    if response.status == 200:
                        data = await response.json()
                        commands = data.get('commands', [])
                        print(f"  Poll {i+1}: {len(commands)} commands received")
                        
                        if commands:
                            print(f"    Commands: {[cmd.get('technique') for cmd in commands]}")
                    else:
                        print(f"  Poll {i+1}: Failed ({response.status})")
            except Exception as e:
                print(f"  Poll {i+1}: Error - {e}")
            
            await asyncio.sleep(2)
        
        print()
        print("✅ Client test complete!")
        print()

if __name__ == "__main__":
    asyncio.run(test_client())

