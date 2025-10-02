"""
Complete End-to-End Test: AI Attack Agent → Server → Client Agent → Execution
Tests the full flow of AI-driven attack scenarios
"""

import asyncio
import aiohttp
import logging
import sys
import io
import os
import json
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockServerWithCommandQueue:
    """Mock server with command queue for testing"""
    
    def __init__(self, host="127.0.0.1", port=8081):
        self.host = host
        self.port = port
        self.app = None
        self.command_queue = {}  # agent_id -> [commands]
        self.execution_results = []
        self.agents = {}  # agent_id -> agent_info
        
    async def start(self):
        """Start the mock server"""
        from aiohttp import web
        
        # Store web module as instance variable for use in handlers
        self.web = web
        
        self.app = web.Application()
        
        # Register routes
        self.app.router.add_post('/api/agents/register', self.handle_register)
        self.app.router.add_post('/api/agents/{agent_id}/heartbeat', self.handle_heartbeat)
        self.app.router.add_get('/api/agents/{agent_id}/commands', self.handle_get_commands)
        self.app.router.add_post('/api/agents/{agent_id}/commands/result', self.handle_command_result)
        self.app.router.add_post('/api/logs/ingest', self.handle_logs)
        self.app.router.add_get('/api/agents', self.handle_list_agents)
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"✅ Mock server started on {self.host}:{self.port}")
        return runner
    
    async def handle_register(self, request):
        """Handle agent registration"""
        try:
            data = await request.json()
            agent_id = data.get('agent_id')
            
            self.agents[agent_id] = {
                'agent_id': agent_id,
                'hostname': data.get('hostname'),
                'ip_address': data.get('ip_address'),
                'platform': data.get('platform'),
                'registered_at': datetime.utcnow().isoformat()
            }
            
            # Initialize command queue for this agent
            if agent_id not in self.command_queue:
                self.command_queue[agent_id] = []
            
            logger.info(f"✅ Agent registered: {agent_id}")
            
            return self.web.json_response({
                'status': 'success',
                'agent_id': agent_id,
                'message': 'Registration successful'
            })
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return self.web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def handle_heartbeat(self, request):
        """Handle agent heartbeat"""
        agent_id = request.match_info['agent_id']
        return self.web.json_response({'status': 'success', 'timestamp': datetime.utcnow().isoformat()})
    
    async def handle_get_commands(self, request):
        """Handle command retrieval"""
        agent_id = request.match_info['agent_id']
        
        # Get pending commands for this agent
        commands = self.command_queue.get(agent_id, [])
        
        logger.info(f"📤 Agent {agent_id} polling: {len(commands)} pending commands")
        
        # Return commands and clear queue
        if commands:
            self.command_queue[agent_id] = []
        
        return self.web.json_response({
            'status': 'success',
            'commands': commands,
            'agent_id': agent_id
        })
    
    async def handle_command_result(self, request):
        """Handle command execution result"""
        try:
            agent_id = request.match_info['agent_id']
            result = await request.json()
            
            self.execution_results.append({
                'agent_id': agent_id,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"✅ Command result from {agent_id}: {result.get('status')}")
            
            return self.web.json_response({'status': 'success'})
        except Exception as e:
            logger.error(f"Result handling error: {e}")
            return self.web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def handle_logs(self, request):
        """Handle log ingestion"""
        try:
            data = await request.json()
            agent_id = data.get('agent_id')
            logs = data.get('logs', [])
            logger.info(f"📝 Received {len(logs)} logs from {agent_id}")
            return self.web.json_response({'status': 'success', 'logs_received': len(logs)})
        except Exception as e:
            return self.web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def handle_list_agents(self, request):
        """List all registered agents"""
        return self.web.json_response({
            'status': 'success',
            'agents': list(self.agents.values())
        })
    
    def queue_command_for_agent(self, agent_id: str, command: dict):
        """Queue a command for an agent"""
        if agent_id not in self.command_queue:
            self.command_queue[agent_id] = []
        
        self.command_queue[agent_id].append(command)
        logger.info(f"📥 Command queued for {agent_id}: {command.get('technique')}")


class AIAttackAgentSimulator:
    """Simulates the AI Attack Agent planning attacks"""
    
    def __init__(self, server_url="http://127.0.0.1:8081"):
        self.server_url = server_url
    
    async def get_registered_agents(self):
        """Get list of registered agents"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/api/agents") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('agents', [])
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
        return []
    
    async def plan_and_queue_attack(self, server: MockServerWithCommandQueue, attack_request: str):
        """Plan and queue attack based on request"""
        logger.info(f"\n🤖 AI Attack Agent Planning: '{attack_request}'\n")
        
        # Get available agents
        agents = await self.get_registered_agents()
        
        if not agents:
            logger.warning("⚠️  No agents registered!")
            return None
        
        logger.info(f"📊 Available endpoints: {len(agents)}")
        for agent in agents:
            logger.info(f"  - {agent['agent_id']} ({agent['platform']}) @ {agent['ip_address']}")
        
        # Simulate AI planning based on attack request
        if "phishing" in attack_request.lower():
            return await self._plan_phishing_attack(server, agents)
        elif "lateral" in attack_request.lower():
            return await self._plan_lateral_movement(server, agents)
        elif "replica" in attack_request.lower() or "container" in attack_request.lower():
            return await self._plan_container_test(server, agents)
        else:
            logger.warning(f"⚠️  Unknown attack type in request: {attack_request}")
            return None
    
    async def _plan_phishing_attack(self, server: MockServerWithCommandQueue, agents: list):
        """Plan a phishing attack scenario"""
        logger.info("\n📋 AI Planning: Spear Phishing Attack\n")
        
        # Step 1: Find an endpoint to create SMTP container
        smtp_agent = agents[0]
        target_agent = agents[0]  # Same agent for demo
        
        logger.info(f"🎯 Strategy:")
        logger.info(f"  1. Deploy SMTP container on {smtp_agent['agent_id']}")
        logger.info(f"  2. Create self-replica of {target_agent['agent_id']}")
        logger.info(f"  3. Execute phishing attack from SMTP → replica")
        
        # Queue commands
        commands = [
            {
                'id': 'cmd_001',
                'technique': 'deploy_smtp_container',
                'payload': {
                    'container_name': 'phishing_smtp_server',
                    'network': 'bridge',
                    'port': 587
                },
                'priority': 'high'
            },
            {
                'id': 'cmd_002',
                'technique': 'create_self_replica',
                'payload': {
                    'container_name': f"{target_agent['agent_id']}_replica",
                    'network': 'bridge'
                },
                'priority': 'high'
            },
            {
                'id': 'cmd_003',
                'technique': 'execute_phishing',
                'payload': {
                    'from_container': 'phishing_smtp_server',
                    'to_targets': [f"{target_agent['agent_id']}_replica"],
                    'mitre_technique': 'T1566.001',
                    'email_subject': 'Urgent: Update Required',
                    'phishing_type': 'spear_phishing'
                },
                'priority': 'high'
            }
        ]
        
        for cmd in commands:
            server.queue_command_for_agent(smtp_agent['agent_id'], cmd)
        
        logger.info(f"\n✅ Attack plan created: {len(commands)} commands queued\n")
        
        return {
            'scenario_id': 'scenario_001',
            'attack_type': 'spear_phishing',
            'commands_queued': len(commands),
            'target_agents': [smtp_agent['agent_id']]
        }
    
    async def _plan_lateral_movement(self, server: MockServerWithCommandQueue, agents: list):
        """Plan a lateral movement scenario"""
        logger.info("\n📋 AI Planning: Lateral Movement Attack\n")
        
        agent = agents[0]
        
        commands = [
            {
                'id': 'cmd_101',
                'technique': 'create_self_replica',
                'payload': {
                    'container_name': f"{agent['agent_id']}_initial",
                    'network': 'bridge'
                }
            },
            {
                'id': 'cmd_102',
                'technique': 'execute_lateral_movement',
                'payload': {
                    'from_container': f"{agent['agent_id']}_initial",
                    'target_container': f"{agent['agent_id']}_replica",
                    'mitre_technique': 'T1021.001',
                    'method': 'rdp'
                }
            }
        ]
        
        for cmd in commands:
            server.queue_command_for_agent(agent['agent_id'], cmd)
        
        logger.info(f"✅ Attack plan created: {len(commands)} commands queued\n")
        
        return {
            'scenario_id': 'scenario_002',
            'attack_type': 'lateral_movement',
            'commands_queued': len(commands)
        }
    
    async def _plan_container_test(self, server: MockServerWithCommandQueue, agents: list):
        """Plan a simple container test"""
        logger.info("\n📋 AI Planning: Container Replica Test\n")
        
        agent = agents[0]
        
        command = {
            'id': 'cmd_test_001',
            'technique': 'create_self_replica',
            'payload': {
                'container_name': f"{agent['agent_id']}_test_replica",
                'network': 'bridge'
            },
            'priority': 'high'
        }
        
        server.queue_command_for_agent(agent['agent_id'], command)
        
        logger.info(f"✅ Container test command queued\n")
        
        return {
            'scenario_id': 'scenario_test',
            'attack_type': 'container_test',
            'commands_queued': 1
        }


async def run_client_agent_simulator(server_url="http://127.0.0.1:8081", duration_seconds=30):
    """Simulate a client agent connecting and executing commands"""
    import platform
    import uuid
    
    agent_id = f"TestAgent_{platform.node()[:8]}"
    
    logger.info(f"\n🤖 Starting Client Agent: {agent_id}\n")
    
    async with aiohttp.ClientSession() as session:
        # Register
        try:
            async with session.post(f"{server_url}/api/agents/register", json={
                'agent_id': agent_id,
                'hostname': platform.node(),
                'ip_address': '127.0.0.1',
                'platform': platform.system().lower(),
                'agent_type': 'endpoint'
            }) as response:
                if response.status == 200:
                    logger.info(f"✅ Agent registered: {agent_id}")
                else:
                    logger.error(f"❌ Registration failed: {response.status}")
                    return
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return
        
        # Poll for commands
        start_time = datetime.utcnow()
        poll_count = 0
        
        while (datetime.utcnow() - start_time).total_seconds() < duration_seconds:
            try:
                # Poll for commands
                async with session.get(f"{server_url}/api/agents/{agent_id}/commands") as response:
                    if response.status == 200:
                        data = await response.json()
                        commands = data.get('commands', [])
                        
                        poll_count += 1
                        
                        if commands:
                            logger.info(f"\n📨 Received {len(commands)} commands!\n")
                            
                            for cmd in commands:
                                logger.info(f"⚡ Executing: {cmd.get('technique')}")
                                
                                # Simulate execution
                                result = await simulate_command_execution(cmd)
                                
                                # Report result
                                await session.post(
                                    f"{server_url}/api/agents/{agent_id}/commands/result",
                                    json=result
                                )
                                
                                logger.info(f"✅ Command executed: {result.get('status')}")
                        else:
                            if poll_count % 3 == 0:  # Log every 3rd poll
                                logger.info(f"⏳ Polling... (attempt {poll_count})")
                
                await asyncio.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                logger.error(f"❌ Polling error: {e}")
                await asyncio.sleep(5)
        
        logger.info(f"\n✅ Client agent test complete ({poll_count} polls)\n")


async def simulate_command_execution(command: dict) -> dict:
    """Simulate command execution"""
    technique = command.get('technique')
    cmd_id = command.get('id')
    
    # Simulate execution delay
    await asyncio.sleep(2)
    
    return {
        'command_id': cmd_id,
        'status': 'completed',
        'technique': technique,
        'message': f'Successfully executed {technique}',
        'execution_time_ms': 2000,
        'timestamp': datetime.utcnow().isoformat()
    }


async def main():
    """Main test flow"""
    print("=" * 80)
    print("COMPLETE AI ATTACK FLOW TEST")
    print("=" * 80)
    
    # Start mock server
    logger.info("\n🚀 STEP 1: Starting Mock Server\n")
    server = MockServerWithCommandQueue(host="127.0.0.1", port=8081)
    runner = await server.start()
    
    await asyncio.sleep(2)
    
    try:
        # Start client agent in background
        logger.info("\n🚀 STEP 2: Starting Client Agent\n")
        client_task = asyncio.create_task(run_client_agent_simulator(duration_seconds=40))
        
        await asyncio.sleep(3)  # Wait for registration
        
        # AI Attack Agent plans attack
        logger.info("\n🚀 STEP 3: AI Attack Agent Planning\n")
        ai_agent = AIAttackAgentSimulator()
        
        # Test 1: Container replica test
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Container Replica Creation")
        logger.info("=" * 80)
        result1 = await ai_agent.plan_and_queue_attack(server, "Create a container replica for testing")
        
        await asyncio.sleep(10)  # Wait for execution
        
        # Test 2: Phishing attack
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Spear Phishing Attack Scenario")
        logger.info("=" * 80)
        result2 = await ai_agent.plan_and_queue_attack(server, "Execute spear phishing attack against executives")
        
        await asyncio.sleep(15)  # Wait for execution
        
        # Wait for client to finish
        await client_task
        
        # Show results
        logger.info("\n" + "=" * 80)
        logger.info("TEST RESULTS")
        logger.info("=" * 80)
        
        logger.info(f"\n✅ Agents registered: {len(server.agents)}")
        for agent_id, agent_info in server.agents.items():
            logger.info(f"  - {agent_id} ({agent_info['platform']})")
        
        logger.info(f"\n✅ Commands executed: {len(server.execution_results)}")
        for i, result in enumerate(server.execution_results, 1):
            logger.info(f"  {i}. {result['result'].get('technique')} - {result['result'].get('status')}")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 COMPLETE FLOW TEST SUCCESSFUL!")
        logger.info("=" * 80)
        
    finally:
        # Cleanup
        await runner.cleanup()
        logger.info("\n✅ Server stopped\n")


if __name__ == "__main__":
    asyncio.run(main())

