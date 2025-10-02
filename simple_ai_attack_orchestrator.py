#!/usr/bin/env python3
"""
Simple AI Attack Agent for Testing
Focus on active hosts only and native command execution
"""

import logging
import json
from typing import Dict, List, Any
from datetime import datetime
import sqlite3

logger = logging.getLogger(__name__)

class SimpleAIAttackAgent:
    def __init__(self):
        self.agent_id = "SimpleAIAttackAgent"
        self.db_path = 'soc_database.db'
        
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get only active agents from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get agents active in last 5 minutes
            cursor.execute("""
                SELECT id, hostname, ip_address, platform, status 
                FROM agents 
                WHERE datetime(last_heartbeat) > datetime('now', '-5 minutes')
                OR status = 'active'
                ORDER BY last_heartbeat DESC
            """)
            
            agents = []
            for agent_id, hostname, ip_address, platform, status in cursor.fetchall():
                agents.append({
                    'agent_id': agent_id,
                    'hostname': hostname or 'unknown',
                    'ip_address': ip_address or '127.0.0.1',
                    'platform': platform or 'unknown',
                    'status': status or 'unknown'
                })
            
            conn.close()
            logger.info(f"Found {len(agents)} active agents")
            return agents
            
        except Exception as e:
            logger.error(f"Error getting active agents: {e}")
            return []
    
    def generate_attack_plan(self, scenario: str) -> Dict[str, Any]:
        """Generate attack plan for active hosts only"""
        active_agents = self.get_active_agents()
        
        if not active_agents:
            return {
                'success': False,
                'error': 'No active agents found',
                'agents_found': 0,
                'plan': None
            }
        
        # Create simple attack plan based on active agents
        plan = {
            'scenario_id': f'attack_plan_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}',
            'scenario': scenario,
            'target_agents': [agent['agent_id'] for agent in active_agents],
            'active_hosts': len(active_agents),
            'attack_phases': [],
            'commands': []
        }
        
        # Generate commands for each active agent
        for agent in active_agents:
            agent_id = agent['agent_id']
            platform = agent['platform']
            
            # Phase 1: Network Discovery
            if platform.lower() == 'windows':
                discovery_cmd = {
                    'agent_id': agent_id,
                    'technique': 'T1018',
                    'command_data': {
                        'script': 'ipconfig /all; arp -a; netstat -an',
                        'description': 'Network discovery on Windows'
                    }
                }
            else:
                discovery_cmd = {
                    'agent_id': agent_id,
                    'technique': 'T1018', 
                    'command_data': {
                        'script': 'ifconfig; arp -a; netstat -an',
                        'description': 'Network discovery on Unix/Linux'
                    }
                }
            
            plan['commands'].append(discovery_cmd)
            
            # Phase 2: System Information
            if platform.lower() == 'windows':
                sysinfo_cmd = {
                    'agent_id': agent_id,
                    'technique': 'T1082',
                    'command_data': {
                        'script': 'systeminfo; whoami; net user',
                        'description': 'System information gathering on Windows'
                    }
                }
            else:
                sysinfo_cmd = {
                    'agent_id': agent_id,
                    'technique': 'T1082',
                    'command_data': {
                        'script': 'uname -a; whoami; id; ps aux',
                        'description': 'System information gathering on Unix/Linux'
                    }
                }
            
            plan['commands'].append(sysinfo_cmd)
        
        plan['attack_phases'] = [
            {
                'phase': 1,
                'name': 'Network Discovery',
                'description': 'Discover network topology and active hosts',
                'commands': len(active_agents)
            },
            {
                'phase': 2, 
                'name': 'System Information Gathering',
                'description': 'Collect system information from active hosts',
                'commands': len(active_agents)
            }
        ]
        
        return {
            'success': True,
            'agents_found': len(active_agents),
            'plan': plan,
            'active_agents': active_agents
        }
    
    def queue_commands(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Queue commands to active agents"""
        try:
            from core.server.command_queue.command_manager import CommandManager
            from core.server.storage.database_manager import DatabaseManager
            
            db_manager = DatabaseManager(db_path=self.db_path)
            cmd_manager = CommandManager(db_manager)
            
            queued_commands = []
            
            for command in plan['commands']:
                try:
                    command_id = cmd_manager.queue_command(
                        agent_id=command['agent_id'],
                        technique=command['technique'],
                        command_data=command['command_data'],
                        scenario_id=plan['scenario_id']
                    )
                    
                    queued_commands.append({
                        'command_id': command_id,
                        'agent_id': command['agent_id'],
                        'technique': command['technique'],
                        'status': 'queued'
                    })
                    
                    logger.info(f"Queued command {command_id} for agent {command['agent_id']}")
                    
                except Exception as e:
                    logger.error(f"Failed to queue command for {command['agent_id']}: {e}")
            
            return {
                'success': True,
                'commands_queued': len(queued_commands),
                'commands': queued_commands
            }
            
        except Exception as e:
            logger.error(f"Error queuing commands: {e}")
            return {
                'success': False,
                'error': str(e),
                'commands_queued': 0
            }

# Global instance
simple_ai_attack_agent = SimpleAIAttackAgent()

async def simple_ai_attack_orchestrator(scenario: str) -> Dict[str, Any]:
    """Simple AI attack orchestrator for testing"""
    logger.info(f"Starting AI attack orchestration: {scenario}")
    
    # Generate attack plan for active hosts only
    result = simple_ai_attack_agent.generate_attack_plan(scenario)
    
    if not result['success']:
        return {
            'successful': 0,
            'failed': 1,
            'commands_sent': 0,
            'error': result['error']
        }
    
    # Queue commands to active agents
    queue_result = simple_ai_attack_agent.queue_commands(result['plan'])
    
    if queue_result['success']:
        return {
            'successful': 1,
            'failed': 0,
            'commands_sent': queue_result['commands_queued'],
            'active_agents': result['agents_found'],
            'plan': result['plan']
        }
    else:
        return {
            'successful': 0,
            'failed': 1,
            'commands_sent': 0,
            'error': queue_result['error']
        }

if __name__ == "__main__":
    import asyncio
    
    async def test():
        result = await simple_ai_attack_orchestrator("Test network discovery on active hosts")
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())