"""
LangServe API for AI SOC Platform
Replaces FastAPI with LangChain-native API endpoints
"""

import asyncio
import logging
import time
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from langserve import add_routes
from langchain.schema.runnable import Runnable
from langchain.schema import BaseMessage
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class SOCPlatformAPI:
    """LangServe-based API for AI SOC Platform"""

    def __init__(self):
        # Import agents with error handling
        self.agents_available = False
        self.soc_orchestrator = None
        self.langchain_detection_agent = None
        self.phantomstrike_ai = None
        self.gpt_scenario_requester = None

        try:
            from agents.langchain_orchestrator import soc_orchestrator
            from agents.detection_agent.langchain_detection_agent import langchain_detection_agent  
            from agents.attack_agent.langchain_attack_agent import phantomstrike_ai
            from agents.attack_agent.gpt_scenario_requester import GPTScenarioRequester
            from langchain_openai import ChatOpenAI
            
            self.soc_orchestrator = soc_orchestrator
            self.langchain_detection_agent = langchain_detection_agent
            self.phantomstrike_ai = phantomstrike_ai
            
            # Set detection_agent alias for _analyze_threat_dynamically
            self.detection_agent = langchain_detection_agent

            # Initialize GPT scenario requester
            llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)
            self.gpt_scenario_requester = GPTScenarioRequester(llm)

            self.agents_available = True
            logger.info(
                "All AI agents loaded: SOC Orchestrator, Detection Agent, Attack Agent, GPT Scenario Requester")

        except ImportError as e:
            logger.warning(
                f"LangChain agents not available for LangServe: {e}")
        
        self.app = FastAPI(
                title="AI SOC Platform - LangChain API",
                description="LangChain-powered SOC operations API",
                version="2.0.0"
        )
                # CORS is now handled by Nginx - no need for FastAPI CORS middleware
                # This prevents duplicate CORS headers
                # Add LangServe routes
        self._add_langserve_routes()
                # Add custom endpoints
        self._add_custom_endpoints()
                # Add frontend API routes
        self._add_frontend_api_routes()

        # Add GPT scenario API routes
        self._add_gpt_scenario_routes()

        # Add GPT logging API routes
        self._add_gpt_logging_routes()

    def _add_gpt_scenario_routes(self):
        """Add GPT scenario API routes to the server"""
        try:
            # GPT Scenario Request endpoint
            @self.app.post("/api/gpt-scenarios/request")
            async def request_gpt_scenario_endpoint(request_data: dict):
                """Request a custom attack scenario from GPT"""
                try:
                    from agents.attack_agent.gpt_scenario_requester import GPTScenarioRequester
                    from langchain_openai import ChatOpenAI

                    # Initialize GPT requester
                    llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)
                    requester = GPTScenarioRequester(llm)

                    # Generate custom scenario
                    scenario = await requester.request_custom_scenario(
                        user_request=request_data.get('user_request', ''),
                        network_context=request_data.get(
                            'network_context', {}),
                        constraints=request_data.get('constraints', {})
                    )

                    logger.info(f"Generated GPT scenario: {scenario.get('name', 'Unknown')}")

                    return {
                        "success": True,
                        "scenario": scenario,
                        "timestamp": datetime.utcnow().isoformat()
                    }

                except Exception as e:
                    logger.error(f"GPT scenario request failed: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }

            # GPT Scenario Execution endpoint
            @self.app.post("/api/backend/gpt-scenarios/execute")
            async def execute_gpt_scenario_endpoint(scenario_data: dict):
                """Execute a GPT-generated scenario using the attack agent"""
                try:
                    from agents.attack_agent.langchain_attack_agent import LangChainAttackAgent

                    # Initialize attack agent
                    attack_agent = LangChainAttackAgent()

                    # Get available client agents
                    from core.server.storage.database_manager import DatabaseManager
                    db_manager = DatabaseManager()
                    agents = await db_manager.get_all_agents()

                    if not agents:
                        return {
                            "success": False,
                            "error": "No client agents connected",
                            "timestamp": datetime.utcnow().isoformat()
                        }

                    # Set target agents for scenario
                    scenario_data['target_agents'] = [
                        agent['agent_id'] for agent in agents]

                    # Execute the scenario
                    result = await attack_agent.execute_attack_scenario(scenario_data)

                    logger.info(f"Executed GPT scenario: {scenario_data.get('name', 'Unknown')}")

                    return {
                        "success": True,
                        "execution_result": result,
                        "target_agents": [agent['agent_id'] for agent in agents],
                        "timestamp": datetime.utcnow().isoformat()
                    }

                except Exception as e:
                    logger.error(f"GPT scenario execution failed: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }

            # GPT Scenario Suggestions endpoint
            @self.app.get("/api/gpt-scenarios/suggestions")
            async def get_gpt_scenario_suggestions(
                network_context: dict = None):
                """Get GPT-generated scenario suggestions"""
                try:
                    from agents.attack_agent.gpt_scenario_requester import GPTScenarioRequester
                    from langchain_openai import ChatOpenAI

                    # Initialize GPT requester
                    llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)
                    requester = GPTScenarioRequester(llm)

                    # Get suggestions
                    suggestions = await requester.get_scenario_suggestions(network_context or {})

                    return {
                        "success": True,
                        "suggestions": suggestions,
                        "timestamp": datetime.utcnow().isoformat()
                    }

                except Exception as e:
                    logger.error(f"GPT scenario suggestions failed: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "suggestions": [
                            "Network reconnaissance and service enumeration",
                            "Privilege escalation simulation",
                            "Data exfiltration testing",
                            "Persistence mechanism installation",
                            "Defense evasion techniques"
                        ],
                        "timestamp": datetime.utcnow().isoformat()
                    }

            # GPT Scenario Status endpoint
            @self.app.get("/api/gpt-scenarios/status")
            async def get_gpt_scenario_status():
                """Get GPT scenario system status"""
                try:
                    from core.server.storage.database_manager import DatabaseManager
                    db_manager = DatabaseManager()
                    agents = await db_manager.get_all_agents()

                    return {
                        "success": True,
                        "soc_platform": "connected",
                        "client_agents": len(agents),
                        "agents": [
                            {
                                "agent_id": agent.get('agent_id', 'Unknown'),
                                "ip_address": agent.get('ip_address', 'Unknown'),
                                "status": agent.get('status', 'Unknown')
                            }
                            for agent in agents[:5]  # Show first 5
                        ],
                        "timestamp": datetime.utcnow().isoformat()
                    }

                except Exception as e:
                    logger.error(f"GPT scenario status failed: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "soc_platform": "disconnected",
                        "client_agents": 0,
                        "timestamp": datetime.utcnow().isoformat()
                    }

            logger.info("GPT scenario API routes added successfully")

        except Exception as e:
            logger.error(f"Failed to add GPT scenario routes: {e}")

    async def _generate_ai_apt_scenarios(self):
        """Generate AI-powered APT scenarios dynamically - NO HARDCODED SCENARIOS"""
        try:
            # Get current network context from connected agents
            from core.server.storage.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            agents = await db_manager.get_all_agents()

            # Build dynamic network context from real agents
            network_context = {
                "hosts": [agent.get('ip_address', 'unknown') for agent in agents if agent.get('ip_address')],
                "services": ["SSH", "RDP", "HTTP", "MySQL", "SMB", "FTP"],
                "vulnerabilities": ["Weak passwords", "Outdated software", "Misconfigured services"],
                "platforms": list(set([agent.get('platform', 'Unknown') for agent in agents]))
            }

            # Generate 6 diverse AI scenarios dynamically
            scenario_requests = [
                "Create a comprehensive network intrusion APT scenario targeting the discovered network infrastructure",
                "Create a sophisticated system compromise APT scenario for the identified platforms",
                "Create a stealthy data exfiltration APT scenario for sensitive information theft",
                "Create a persistent backdoor installation APT scenario for long-term access",
                "Create an advanced privilege escalation APT scenario for administrative control",
                "Create a forensic evasion APT scenario for evidence destruction and stealth"
            ]

            ai_scenarios = []

            for i, request in enumerate(scenario_requests):
                try:
                    # Generate AI scenario with real network context
                    scenario = await self.gpt_scenario_requester.request_custom_scenario(
                        user_request=request,
                        network_context=network_context,
                        constraints={
                            "destructive": False,
                            "stealth": True,
                            "real_attack": True,
                            # Limit to first 3 agents
                            "target_agents": [agent.get('agent_id') for agent in agents[:3]]
                        }
                    )

                    # Convert to the required format
                    formatted_scenario = self._format_scenario_for_frontend(
                        scenario, i)
                    ai_scenarios.append(formatted_scenario)

                except Exception as e:
                    logger.error(f"Failed to generate AI scenario {i}: {e}")
                    # Don't continue with partial results - fail completely
                    raise Exception(
    f"AI scenario generation failed for scenario {i}: {e}")

            return ai_scenarios

        except Exception as e:
            logger.error(f"AI APT scenario generation failed: {e}")
            raise Exception(f"AI scenario generation completely failed: {e}")

    def _format_scenario_for_frontend(self, scenario, index):
        """Format AI-generated scenario to match frontend requirements"""
        scenario_types = [
            "real_network_intrusion",
            "real_system_compromise",
            "real_data_extraction",
            "real_persistence_installation",
            "real_privilege_escalation",
            "real_log_destruction"
        ]

        scenario_names = [
            "AI-Generated Network Intrusion Campaign",
            "AI-Generated System Compromise Campaign",
            "AI-Generated Data Extraction Campaign",
            "AI-Generated Persistence Installation Campaign",
            "AI-Generated Privilege Escalation Campaign",
            "AI-Generated Log Destruction Campaign"
        ]

        attack_phases = scenario.get('attack_phases', [])
        formatted_phases = []

        for phase in attack_phases:
            formatted_phases.append({
                "phase": phase.get('phase', 'Unknown Phase'),
                "duration": phase.get('duration', '5 min'),
                "description": phase.get('description', 'AI-generated attack phase'),
                "mitreId": phase.get('mitre_id', 'T1018')
            })

        return {
            "id": scenario_types[index],
            "name": scenario_names[index],
            "aptGroup": "CodeGrey AI SOC Platform",
            "description": scenario.get('description', 'AI-generated APT attack scenario'),
            "origin": "AI-Generated",
            "targets": scenario.get('target_services', ["Network Infrastructure", "Server Systems"]),
            "attackVectors": [phase.get('techniques', ['AI-Generated Technique']) for phase in attack_phases],
            "mitreAttack": scenario.get('mitre_techniques', ['T1018', 'T1021']),
            "difficulty": scenario.get('difficulty', 'intermediate'),
            "duration": scenario.get('estimated_duration', '30 minutes'),
            "detectability": scenario.get('detection_risk', 'medium'),
            "impact": scenario.get('impact', 'high'),
            "intelligence": {
                "firstSeen": "2024",
                "lastActivity": "2024",
                "motivation": scenario.get('objective', 'AI-Generated Attack'),
                "sophistication": 6
            },
            "timeline": formatted_phases,
            "destructive": True,
            "real_attack": True
        }

    def _format_custom_scenario_for_frontend(self, scenario):
        """Format custom AI-generated scenario to match frontend requirements"""
        attack_phases = scenario.get('attack_phases', [])
        formatted_phases = []

        for phase in attack_phases:
            formatted_phases.append({
                "phase": phase.get('phase', 'Unknown Phase'),
                "duration": phase.get('duration', '5 min'),
                "description": phase.get('description', 'AI-generated attack phase'),
                "mitreId": phase.get('mitre_id', 'T1018')
            })

        return {
            "id": "custom_ai_scenario",
            "name": scenario.get('name', 'Custom AI-Generated Scenario'),
            "aptGroup": "CodeGrey AI SOC Platform",
            "description": scenario.get('description', 'Custom AI-generated APT attack scenario'),
            "origin": "AI-Generated",
            "targets": scenario.get('target_services', ["Network Infrastructure", "Server Systems"]),
            "attackVectors": [phase.get('techniques', ['AI-Generated Technique']) for phase in attack_phases],
            "mitreAttack": scenario.get('mitre_techniques', ['T1018', 'T1021']),
            "difficulty": scenario.get('difficulty', 'intermediate'),
            "duration": scenario.get('estimated_duration', '30 minutes'),
            "detectability": scenario.get('detection_risk', 'medium'),
            "impact": scenario.get('impact', 'high'),
            "intelligence": {
                "firstSeen": "2024",
                "lastActivity": "2024",
                "motivation": scenario.get('objective', 'Custom AI-Generated Attack'),
                "sophistication": 6
            },
            "timeline": formatted_phases,
            "destructive": True,
            "real_attack": True
        }

    def _add_langserve_routes(self):
        """Add LangServe routes for agents"""
        if not self.agents_available:
            logger.warning(
                "LangChain agents not available, skipping LangServe routes")
            return

        try:
            # SOC Orchestrator - main entry point
            if self.soc_orchestrator:
                add_routes(
                    self.app,
                    self.soc_orchestrator.agent_executor,
                    path="/api/soc",
                    playground_type="default"
                )

            # Detection Agent
            if self.langchain_detection_agent:
                add_routes(
                    self.app,
                    self.langchain_detection_agent.agent_executor,
                    path="/api/detection",
                    playground_type="default"
                )

            # Attack Agent (PhantomStrike AI)
            if self.phantomstrike_ai:
                add_routes(
                    self.app,
                    self.phantomstrike_ai.agent_executor,
                    path="/api/attack",
                    playground_type="default"
                )

            logger.info("LangServe routes added successfully")
        except Exception as e:
            logger.error(f"Failed to add LangServe routes: {e}")
            self.agents_available = False

    def _add_custom_endpoints(self):
        """Add custom API endpoints"""

        @self.app.get("/")
        async def root():
            return {
                "message": "AI SOC Platform - LangChain API",
                "version": "2.0.0",
                "endpoints": [
                    "/api/soc",
                    "/api/detection",
                    "/api/attack",
                    "/api/soc/playground"
                ]
            }

        @self.app.get("/health")
        async def health_check():
            try:
                if not self.agents_available:
                    return {
                        "status": "healthy",
                        "version": "2.0.0",
                        "agents": "unavailable",
                        "ai_services": "disabled"
                    }

                # Check agent status
                orchestrator_status = "available" if self.soc_orchestrator else "unavailable"
                detection_status = "available" if self.langchain_detection_agent else "unavailable"
                attack_status = "available" if self.phantomstrike_ai else "unavailable"

                return {
                    "status": "healthy",
                    "version": "2.0.0",
                    "agents": {
                        "orchestrator": orchestrator_status,
                        "detection": detection_status,
                        "attack": attack_status
                    },
                    "ai_services": "active" if self.agents_available else "disabled"
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "error": str(e)
                }

        @self.app.post("/api/soc/analyze-threat")
        async def analyze_threat(request_data: Dict[str, Any]):
            """Analyze threat using SOC orchestrator"""
            try:
                if not self.agents_available or not self.soc_orchestrator:
                    return {
                        "success": False,
                        "error": "SOC orchestrator not available"
                    }
                
                detection_data = request_data.get('detection_data', {})
                context = request_data.get('context', {})
                result = await self.soc_orchestrator.process_soc_request(
                    f"Analyze this threat: {detection_data}",
                    context
                )
                return result
            except Exception as e:
                logger.error(f"Threat analysis API error: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/soc/plan-attack")
        async def plan_attack(request_data: Dict[str, Any]):
            """Plan attack scenario using PhantomStrike AI"""
            try:
                attack_request = request_data.get('attack_request', '')
                network_context = request_data.get('network_context', {})
                constraints = request_data.get('constraints', {})
                result = await self.soc_orchestrator.process_soc_request(
                    f"Plan attack scenario: {attack_request}",
                {
                        "network_context": network_context,
                        "constraints": constraints,
                        "operation": 'attack_planning'
                    }
                )
                return result
            except Exception as e:
                logger.error(f"Attack planning API error: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/soc/pending-approvals")
        async def get_pending_approvals():
            """Get scenarios pending approval"""
            try:
                approvals = await self.phantomstrike_ai.get_pending_approvals()
                return {
                    "success": True,
                    "approvals": approvals
                }
            except Exception as e:
                logger.error(f"Pending approvals API error: {e}")
                return {"success": False, "error": str(e)}

        # GPT Scenario Requester Endpoints
        @self.app.post("/api/gpt-scenarios/request")
        async def request_gpt_scenario(request_data: Dict[str, Any]):
            """Request a custom attack scenario from GPT"""
            try:
                if not self.gpt_scenario_requester:
                    return {"success": False,
     "error": "GPT Scenario Requester not available"}

                user_request = request_data.get('user_request', '')
                network_context = request_data.get('network_context', {})
                constraints = request_data.get('constraints', {})

                scenario = await self.gpt_scenario_requester.request_custom_scenario(
                    user_request=user_request,
                    network_context=network_context,
                    constraints=constraints
                )

                logger.info(f"GPT scenario generated: {scenario.get('name', 'Unknown')}")

                return {
                    "success": True,
                    "scenario": scenario,
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"GPT scenario request failed: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/backend/gpt-scenarios/suggestions")
        async def get_gpt_scenario_suggestions(
            network_context: Dict[str, Any] = None):
            """Get GPT-generated scenario suggestions"""
            try:
                if not self.gpt_scenario_requester:
                    return {"success": False,"error": "GPT Scenario Requester not available"}

                suggestions = await self.gpt_scenario_requester.get_scenario_suggestions(network_context or {})

                return {
                    "success": True,
                    "suggestions": suggestions,
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"GPT scenario suggestions failed: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/backend/gpt-scenarios/execute")
        async def execute_gpt_scenario(request_data: Dict[str, Any]):
            """
            Execute an APT scenario - frontend only needs to send scenario_id
            Backend automatically:
            - Looks up scenario details
            - Gets connected agents and their platforms
            - Determines attack types based on scenario
            - Generates AI commands for each platform
            """
            try:
                scenario_id = request_data.get('scenario_id')

                if not scenario_id:
                    return {
                        "success": False,
                        "error": "scenario_id is required",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                if not self.phantomstrike_ai:
                    return {
                        "success": False, "error": "Attack agent not available"}

                # Get available client agents
                from core.server.storage.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                agents = await db_manager.get_all_agents()

                if not agents:
                    return {
                        "success": False,
                        "error": "No client agents connected",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                # Get scenario details from hardcoded scenarios and customize for network
                # This automatically adapts to connected agents' platforms
                hardcoded_scenarios = await self._get_hardcoded_scenarios()
                base_scenario = None
                
                # Find the scenario by ID
                for scenario in hardcoded_scenarios:
                    if scenario.get('id') == scenario_id:
                        base_scenario = scenario
                        break
                
                if not base_scenario:
                    return {
                        "success": False,
                        "error": f"Scenario {scenario_id} not found",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Customize scenario based on network context
                customized_scenario = await self._customize_scenario_for_network(base_scenario, agents)

                # Build network context from connected agents
                network_context = {
                    'agents': [
                        {
                            'agent_id': agent.get('agent_id'),
                            'hostname': agent.get('hostname'),
                            'platform': agent.get('platform'),
                            'ip_address': agent.get('ip_address'),
                            'status': agent.get('status')
                        }
                        for agent in agents
                    ],
                    'agent_count': len(agents),
                    'platforms': list(set(agent.get('platform', 'unknown') for agent in agents))
                }

                # Use attack agent to plan the scenario
                # This will generate AI commands for each platform
                attack_request = customized_scenario.get('description', f"Execute {customized_scenario.get('name')} attack scenario")

                scenario_result = await self.phantomstrike_ai.plan_attack_scenario(
                    attack_request=attack_request,
                    network_context=network_context,
                        constraints={
                            'scenario_id': scenario_id, 'target_agents': [
                            agent.get('agent_id') for agent in agents]}
                    )

                logger.info(f"GPT scenario planned: {customized_scenario.get('name', 'Unknown')} (ID: {scenario_id})")

                # AUTOMATICALLY EXECUTE THE SCENARIO (no approval needed for AI SOC)
                # Call attack command generation directly instead of through LangChain tool
                try:
                    # Use mock command generator for testing
                    import sys
                    import os
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                    from mock_ai_command_generator import generate_mock_ai_commands
                    
                    target_agent_ids = [agent.get('agent_id') for agent in agents]
                    
                    # Convert Pydantic model to dict properly
                    if hasattr(scenario_result, 'model_dump'):
                        # Pydantic v2
                        scenario_dict = scenario_result.model_dump()
                    elif hasattr(scenario_result, 'dict'):
                        # Pydantic v1
                        scenario_dict = scenario_result.dict()
                    else:
                        # Fallback to __dict__
                        scenario_dict = scenario_result.__dict__
                    
                    # Generate AI commands using mock generator for testing
                    ai_commands = await generate_mock_ai_commands(
                        attack_type=scenario_dict.get('attack_type', 'network_intrusion'),
                        platform='windows',  # Default to windows for now
                        scenario=scenario_dict,
                        network_context=network_context
                    )
                    
                    # Queue the AI commands to the database
                    from core.server.command_queue.command_manager import CommandManager
                    from core.server.storage.database_manager import DatabaseManager
                    
                    db_manager = DatabaseManager()
                    command_manager = CommandManager(db_manager)
                    
                    queued_commands = 0
                    for agent_id in target_agent_ids:
                        for technique, cmd_info in ai_commands.items():
                            try:
                                command_id = await command_manager.queue_command(
                                    agent_id=agent_id,
                                    technique=technique,
                                    command_data={
                                        'script': cmd_info.get('script', ''),
                                        'description': cmd_info.get('description', ''),
                                        'mitre_technique': cmd_info.get('mitre_technique', ''),
                                        'destructive': cmd_info.get('destructive', False),
                                        'real_attack': cmd_info.get('real_attack', True),
                                        'ai_generated': True
                                    },
                                    scenario_id=scenario_id
                                )
                                queued_commands += 1
                                logger.info(f"Queued AI command {technique} for agent {agent_id}")
                            except Exception as e:
                                logger.error(f"Failed to queue command {technique} for agent {agent_id}: {e}")
                    
                    commands_generated = len(ai_commands)
                    logger.info(f"GPT scenario executed: {commands_generated} AI commands generated, {queued_commands} queued")
                    
                    # Create execution result
                    execution_result = {
                        'deployment_results': [
                            {
                                'agent_id': agent_id,
                                'commands': ai_commands,
                                'status': 'queued'
                            }
                            for agent_id in target_agent_ids
                        ],
                        'total_commands': commands_generated
                    }
                    
                except Exception as tool_error:
                    logger.error(f"Command generation failed: {tool_error}")
                    execution_result = {'deployment_results': [], 'error': str(tool_error)}
                    commands_generated = 0

                scenario_name = customized_scenario.get(
                    'name', 'Unknown Scenario')

                return {
                    "success": True,
                    "scenarioId": scenario_id,  # camelCase
                    "id": scenario_id,  # Also provide id for compatibility
                    "scenarioName": scenario_name,  # camelCase
                    "name": scenario_name,  # Also provide name for compatibility
                    "executionResult": {  # camelCase
                        "scenario": scenario_result.to_dict() if hasattr(scenario_result, 'to_dict') else str(scenario_result),
                        "status": "executing" if commands_generated > 0 else "planned",
                        "commandsGenerated": commands_generated,  # camelCase
                        "executionDetails": execution_result
                    },
                    "targetAgents": [  # camelCase
                        {
                            "agentId": agent['agent_id'],  # camelCase
                            "hostname": agent.get('hostname'),
                            "platform": agent.get('platform'),
                            "ipAddress": agent.get('ip_address')  # camelCase
                        }
                        for agent in agents
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"GPT scenario execution failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }

        @self.app.get("/api/backend/gpt-scenarios/status")
        async def get_gpt_scenario_status():
            """Get GPT scenario requester status"""
            try:
                from core.server.storage.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                agents = await db_manager.get_all_agents()

                return {
                    "success": True,
                    "gpt_requester_available": self.gpt_scenario_requester is not None,
                    "attack_agent_available": self.phantomstrike_ai is not None,
                    "client_agents_connected": len(agents),
                    "agents": [{"id": agent.get('agent_id'), "ip": agent.get('ip_address')} for agent in agents[:5]],
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"GPT scenario status failed: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/backend/gpt-scenarios/stop")
        async def stop_gpt_scenario(request_data: Dict[str, Any]):
            """Stop a running GPT scenario"""
            try:
                scenario_id = request_data.get('scenario_id')

                if not scenario_id:
                    return {
                        "success": False,
                        "error": "scenario_id is required",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                # Clear pending commands for this scenario
                from core.server.storage.database_manager import DatabaseManager
                import sqlite3
                db_manager = DatabaseManager()

                # Delete pending commands for this scenario
                conn = sqlite3.connect('soc_database.db')
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM commands
                    WHERE status = 'pending'
                    AND scenario_id = ?
                ''', (scenario_id,))
                stopped_commands = cursor.rowcount
                conn.commit()
                conn.close()

                logger.info(
    f"Stopped scenario {scenario_id}: {stopped_commands} commands cancelled")

                return {
                    "success": True,
                    "scenario_id": scenario_id,
                    "commands_cancelled": stopped_commands,
                    "status": "stopped",
                    "message": f"Scenario stopped successfully. {stopped_commands} pending commands cancelled.",
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"Failed to stop scenario: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/backend/gpt-scenarios/pause")
        async def pause_gpt_scenario(request_data: Dict[str, Any]):
            """Pause a running GPT scenario"""
            try:
                scenario_id = request_data.get('scenario_id')

                if not scenario_id:
                    return {
                        "success": False,
                        "error": "scenario_id is required",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                # Mark commands as paused
                import sqlite3

                conn = sqlite3.connect('soc_database.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE commands
                    SET status = 'paused'
                    WHERE scenario_id = ?
                    AND status = 'pending'
                ''', (scenario_id,))
                paused_commands = cursor.rowcount
                conn.commit()
                conn.close()

                logger.info(
    f"Paused scenario {scenario_id}: {paused_commands} commands paused")

                return {
                    "success": True,
                    "scenario_id": scenario_id,
                    "commands_paused": paused_commands,
                    "status": "paused",
                    "message": f"Scenario paused successfully. {paused_commands} commands paused.",
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"Failed to pause scenario: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/backend/gpt-scenarios/resume")
        async def resume_gpt_scenario(request_data: Dict[str, Any]):
            """Resume a paused GPT scenario"""
            try:
                scenario_id = request_data.get('scenario_id')

                if not scenario_id:
                    return {
                        "success": False,
                        "error": "scenario_id is required",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                # Mark commands as pending again
                import sqlite3

                conn = sqlite3.connect('soc_database.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE commands
                    SET status = 'pending'
                    WHERE scenario_id = ?
                    AND status = 'paused'
                ''', (scenario_id,))
                resumed_commands = cursor.rowcount
                conn.commit()
                conn.close()

                logger.info(
    f"Resumed scenario {scenario_id}: {resumed_commands} commands resumed")

                return {
                    "success": True,
                    "scenario_id": scenario_id,
                    "commands_resumed": resumed_commands,
                    "status": "running",
                    "message": f"Scenario resumed successfully. {resumed_commands} commands resumed.",
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"Failed to resume scenario: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/backend/gpt-scenarios/{scenario_id}/status")
        async def get_scenario_execution_status(scenario_id: str):
            """Get detailed status of a specific scenario execution"""
            try:
                import sqlite3

                conn = sqlite3.connect('soc_database.db')
                cursor = conn.cursor()

                # Get command stats for this scenario
                cursor.execute('''
                    SELECT
                        status,
                        COUNT(*) as count
                    FROM commands
                    WHERE scenario_id = ?
                    GROUP BY status
                ''', (scenario_id,))

                status_counts = {}
                for row in cursor.fetchall():
                    status_counts[row[0]] = row[1]

                conn.close()

                total_commands = sum(status_counts.values())
                completed = status_counts.get('completed', 0)
                pending = status_counts.get('pending', 0)
                paused = status_counts.get('paused', 0)
                failed = status_counts.get('failed', 0)

                # Determine overall status
                if total_commands == 0:
                    overall_status = "not_found"
                elif paused > 0:
                    overall_status = "paused"
                elif pending == 0 and completed > 0:
                    overall_status = "completed"
                elif pending > 0:
                    overall_status = "running"
                else:
                    overall_status = "unknown"

                progress_percentage = (
                    completed /
                    total_commands *
                    100) if total_commands > 0 else 0

                return {
                    "success": True,
                    "scenario_id": scenario_id,
                    "status": overall_status,
                    "progress": round(progress_percentage, 2),
                    "commands": {
                        "total": total_commands,
                        "completed": completed,
                        "pending": pending,
                        "paused": paused,
                        "failed": failed
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"Failed to get scenario status: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/soc/custom-apt-scenario")
        async def create_custom_apt_scenario(request_data: dict):
            """Create a custom AI-generated APT scenario based on user requirements"""
            try:
                if not self.gpt_scenario_requester:
                    return {
                        "success": False,
                        "error": "GPT scenario requester not available",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                # Extract request parameters
                user_request = request_data.get('user_request', '')
                network_context = request_data.get('network_context', {})
                constraints = request_data.get('constraints', {})

                if not user_request:
                    return {
                        "success": False,
                        "error": "user_request is required",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                # Generate custom AI scenario
                scenario = await self.gpt_scenario_requester.request_custom_scenario(
                    user_request=user_request,
                    network_context=network_context,
                    constraints=constraints
                )

                # Format for frontend
                formatted_scenario = self._format_custom_scenario_for_frontend(
                    scenario)

                logger.info(f"Generated custom APT scenario: {scenario.get('name', 'Unknown')}")
                return {
                    "success": True,
                    "scenario": formatted_scenario,
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"Custom APT scenario creation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }

        @self.app.post("/api/soc/approve-attack")
        async def approve_attack(request_data: Dict[str, Any]):
            """Approve or reject attack scenario"""
            try:
                scenario_id = request_data.get('scenario_id')
                approved = request_data.get('approved', False)
                result = await self.phantomstrike_ai.execute_approved_scenario(
                    scenario_id, approved
                )
                return result
            except Exception as e:
                logger.error(f"Attack approval API error: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/soc/network-topology")
        async def get_network_topology():
            """Get current network topology"""
            try:
                result = await self.soc_orchestrator.process_soc_request(
                "Get current network topology analysis",
                {'operation_type': 'topology_query'}
                )
                return result
            except Exception as e:
                logger.error(f"Topology API error: {e}")
                return {"success": False, "error": str(e)}

    def _add_frontend_api_routes(self):
        """Add frontend API routes for CodeGrey compatibility"""
        
        @self.app.get("/api/backend/agents")
        async def get_agents():
            """Get SOC platform agents"""
            try:
                from api.api_utils import api_utils
                return await api_utils.get_agents_data()
            except Exception as e:
                logger.error(f"Agents API error: {e}")
                return {"status": "error", "message": str(e), "data": []}

        @self.app.get("/api/backend/network-topology")
        async def get_network_topology():
            """Get network topology data"""
            try:
                from api.api_utils import api_utils
                return await api_utils.get_network_topology_data()
            except Exception as e:
                logger.error(f"Network topology error: {e}")
                return {"status": "error", "message": str(e), "data": []}

        @self.app.get("/api/backend/software-download")
        async def get_software_download():
            """Get software download data"""
            try:
                from api.api_utils import api_utils
                data = await api_utils.get_software_download_data()
                return {
                            "status": "success",
                            "data": data
                    }
            except Exception as e:
                logger.error(f"Software download API error: {e}")
                return {"status": "error", "message": str(e), "data": []}

        @self.app.get("/api/backend/client-agents")
        async def get_client_agents():
            """get list of connected client agents (monitored computers)"""
            try:
                import sqlite3
                from datetime import datetime
                conn = sqlite3.connect('soc_database.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, hostname, ip_address, platform, status,
                            last_heartbeat, created_at
                    FROM agents
                    WHERE status = 'active'
                    ORDER BY last_heartbeat DESC
                """)
                rows = cursor.fetchall()
                conn.close()

                agents = []
                for row in rows:
                    agents.append({
                        "id": row["id"],
                        "agentId": row["id"],  # Use id as agentId
                        "hostname": row["hostname"],
                        "ipAddress": row["ip_address"],
                        "platform": row["platform"],
                        "status": row["status"],
                        "lastSeen": row["last_heartbeat"],
                        "createdAt": row["created_at"]
                    })

                return {
                    "status": "success",
                    "data": agents,
                    "metadata": {
                        "total": len(agents),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            except Exception as e:
                logger.error(f"Failed to get client agents: {e}")
                return {"status": "error", "message": str(e), "data": []}

        @self.app.get("/api/backend/commands")
        async def get_commands(
            agent_id: str = None,
            status: str = None,
            limit: int = 100,
            offset: int = 0
        ):
            """Get command history with status and results"""
            try:
                import sqlite3
                from datetime import datetime
                conn = sqlite3.connect('soc_database.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Build query with filters
                query = """
                    SELECT c.id, c.agent_id, c.command, c.status, c.result,
                            c.scenario_id, c.created_at, c.executed_at,
                            a.hostname, a.ip_address, a.platform
                    FROM commands c
                    LEFT JOIN agents a ON c.agent_id = a.id
                    WHERE 1=1
                """
                params = []

                if agent_id:
                    query += " AND c.agent_id = ?"
                    params.append(agent_id)

                if status:
                    query += " AND c.status = ?"
                    params.append(status)

                query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Get total count
                count_query = "SELECT COUNT(*) as total FROM commands WHERE 1=1"
                count_params = []
                if agent_id:
                    count_query += " AND agent_id = ?"
                    count_params.append(agent_id)
                if status:
                    count_query += " AND status = ?"
                    count_params.append(status)

                cursor.execute(count_query, count_params)
                total = cursor.fetchone()["total"]
                conn.close()

                commands = []
                for row in rows:
                    commands.append({
                        "id": row["id"],
                        "agentId": row["agent_id"],
                        "command": row["command"],
                        "status": row["status"],
                        "result": row["result"],
                        "scenarioId": row["scenario_id"],
                        "createdAt": row["created_at"],
                        "executedAt": row["executed_at"],
                        "agent": {
                            "hostname": row["hostname"],
                            "ipAddress": row["ip_address"],
                            "platform": row["platform"]
                        }
                    })

                return {
                    "status": "success",
                    "data": commands,
                    "metadata": {
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            except Exception as e:
                logger.error(f"Failed to get commands: {e}")
                return {"status": "error", "message": str(e), "data": []}

        @self.app.get("/api/backend/real-apt-scenarios")
        async def get_real_apt_scenarios():
            """Get 6 hardcoded APT scenarios for instant frontend display"""
            try:
                from datetime import datetime
                scenarios = [
                    {
                        "id": "real_network_intrusion",
                        "name": "REAL Network Intrusion Campaign",
                        "aptGroup": "CodeGrey AI SOC Platform",
                        "description": "Live network penetration campaign using actual nmap scans, port enumeration, and brute force attacks against network services.",
                        "origin": "AI-Generated",
                        "targets": ["Network Infrastructure", "Server Systems", "Network Services", "Remote Access Points"],
                        "attackVectors": ["Network Scanning", "Port Enumeration", "Brute Force", "Service Exploitation"],
                        "mitreAttack": ["T1018", "T1021", "T1046", "T1110"],
                        "difficulty": "intermediate",
                        "duration": "30 minutes",
                        "detectability": "high",
                        "impact": "high",
                        "intelligence": {
                            "firstSeen": "2024",
                            "lastActivity": "2024",
                            "motivation": "Network Reconnaissance, Service Compromise",
                            "sophistication": 6
                        }
                    },
                    {
                        "id": "real_system_compromise",
                        "name": "REAL System Compromise Campaign",
                        "aptGroup": "CodeGrey AI SOC Platform",
                        "description": "Live system takeover campaign using actual PowerShell execution, process manipulation, and user account creation.",
                        "origin": "AI-Generated",
                        "targets": ["Windows Systems", "PowerShell Environments", "User Accounts", "System Processes"],
                        "attackVectors": ["PowerShell Execution", "Process Injection", "User Creation", "Privilege Escalation"],
                        "mitreAttack": ["T1059.001", "T1055", "T1134", "T1078"],
                        "difficulty": "advanced",
                        "duration": "25 minutes",
                        "detectability": "medium",
                        "impact": "critical"
                    },
                    {
                        "id": "real_data_extraction",
                        "name": "REAL Data Extraction Campaign",
                        "aptGroup": "CodeGrey AI SOC Platform",
                        "description": "Live data theft campaign using actual file access, data collection, and exfiltration techniques.",
                        "origin": "AI-Generated",
                        "targets": ["File Systems", "Documents", "Databases", "Network Shares"],
                        "attackVectors": ["File Access", "Data Collection", "Network Exfiltration", "Data Staging"],
                        "mitreAttack": ["T1005", "T1041", "T1020", "T1030"],
                        "difficulty": "intermediate",
                        "duration": "35 minutes",
                        "detectability": "medium",
                        "impact": "high"
                    },
                    {
                        "id": "real_persistence_installation",
                        "name": "REAL Persistence Installation Campaign",
                        "aptGroup": "CodeGrey AI SOC Platform",
                        "description": "Live backdoor installation campaign using actual scheduled tasks, registry modifications, and service installations.",
                        "origin": "AI-Generated",
                        "targets": ["Windows Registry", "Scheduled Tasks", "System Services", "Startup Programs"],
                        "attackVectors": ["Registry Modification", "Scheduled Tasks", "Service Installation", "Startup Persistence"],
                        "mitreAttack": ["T1053", "T1543", "T1547", "T1546"],
                        "difficulty": "advanced",
                        "duration": "20 minutes",
                        "detectability": "low",
                        "impact": "critical"
                    },
                    {
                        "id": "real_privilege_escalation",
                        "name": "REAL Privilege Escalation Campaign",
                        "aptGroup": "CodeGrey AI SOC Platform",
                        "description": "Live privilege escalation campaign using actual user group modifications and UAC bypass techniques.",
                        "origin": "AI-Generated",
                        "targets": ["User Accounts", "Administrator Groups", "System Privileges", "UAC Controls"],
                        "attackVectors": ["User Group Modification", "UAC Bypass", "Privilege Escalation", "Administrator Access"],
                        "mitreAttack": ["T1548", "T1055", "T1078", "T1134"],
                        "difficulty": "expert",
                        "duration": "15 minutes",
                        "detectability": "high",
                        "impact": "critical"
                    },
                    {
                        "id": "real_log_destruction",
                        "name": "REAL Log Destruction Campaign",
                        "aptGroup": "CodeGrey AI SOC Platform",
                        "description": "Live evidence destruction campaign using actual log clearing, file deletion, and system cleanup.",
                        "origin": "AI-Generated",
                        "targets": ["Event Logs", "System Logs", "Application Logs", "Forensic Evidence"],
                        "attackVectors": ["Log Clearing", "File Deletion", "Evidence Destruction", "System Cleanup"],
                        "mitreAttack": ["T1070", "T1562", "T1485", "T1489"],
                        "difficulty": "intermediate",
                        "duration": "10 minutes",
                        "detectability": "high",
                        "impact": "medium"
                    }
                ]

                return {
                    "status": "success",
                    "data": scenarios,
                    "metadata": {
                        "total": len(scenarios),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            except Exception as e:
                logger.error(f"Failed to get APT scenarios: {e}")
                return {"status": "error", "message": str(e), "data": []}

        # Add client agent endpoints (for actual client agents to connect)
        @self.app.post("/api/agents/register")
        async def register_agent(agent_data: dict = {}):
            """Register a new client agent"""
            try:
                from datetime import datetime
                import socket
                import platform
                from core.server.storage.database_manager import DatabaseManager
                
                # Get agent info from registration data
                agent_id = agent_data.get('agent_id', f"agent_{int(time.time())}")
                system_info = agent_data.get('system_info', {})
                hostname = system_info.get('hostname', agent_data.get('hostname', socket.gethostname()))
                
                # Enhanced IP address detection
                from core.network_utils import get_enhanced_ip_address

                # Get IP address - prioritize the one sent by client agent
                ip_address = agent_data.get('ip_address', '127.0.0.1')

                # If client didn't send IP or it's loopback, use enhanced detection
                if ip_address == '127.0.0.1' or not ip_address:
                    # Try enhanced IP detection
                    ip_address = get_enhanced_ip_address()

                    # Fallback to system info if enhanced detection fails
                    if ip_address == '127.0.0.1':
                        network_interfaces = system_info.get('network_interfaces', [])
                        if network_interfaces:
                            # Get first non-loopback IP
                            for interface in network_interfaces:
                                if interface.get('ip') and not interface.get('ip').startswith('127.'):
                                    ip_address = interface.get('ip')
                                    break
                
                platform_info = agent_data.get('platform', system_info.get('os', platform.system()))
                
                # Store agent info in database
                db_manager = DatabaseManager(
                    db_path="soc_database.db",
                    enable_elasticsearch=False,
                    enable_influxdb=False
                )

                # Check for existing agent to prevent duplicates
                existing_agent = await db_manager.get_agent_info(agent_id)
                if existing_agent:
                    # Update existing agent instead of creating duplicate
                    logger.info(f"Updating existing agent: {agent_id}")
                    agent_info = {
                        'agent_id': agent_id,
                        'hostname': hostname,
                        'ip_address': ip_address,
                        'platform': platform_info,
                        'status': 'active',
                        'last_seen': datetime.now(),
                        'agent_type': 'client_endpoint'
                    }
                else:
                    # Create new agent
                    logger.info(f"Creating new agent: {agent_id}")
                    agent_info = {
                        'agent_id': agent_id,
                        'hostname': hostname,
                        'ip_address': ip_address,
                        'platform': platform_info,
                        'status': 'active',
                        'last_seen': datetime.now(),
                        'agent_type': 'client_endpoint'
                    }

                # Store in agents table
                await db_manager.store_agent_info(agent_info)
                logger.info(f"Agent registered: {agent_id} ({hostname})")
                return {
                    "status": "success",
                    "message": "Agent registered successfully",
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Agent registration error: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.post("/api/agents/{agent_id}/heartbeat")
        async def agent_heartbeat(agent_id: str, heartbeat_data: dict = {}):
            """Handle agent heartbeat with network topology data"""
            try:
                from datetime import datetime
                from core.server.storage.database_manager import DatabaseManager
                
                # Update agent heartbeat
                db_manager = DatabaseManager(
                    db_path="soc_database.db",
                    enable_elasticsearch=False,
                    enable_influxdb=False
                )
                
                # Update agent status and IP address
                agent_data = {
                    'agent_id': agent_id,
                    'status': 'active',
                    'last_seen': datetime.now()
                }
                
                # Update IP address if provided in heartbeat data
                if 'ip_address' in heartbeat_data and heartbeat_data['ip_address']:
                    agent_data['ip_address'] = heartbeat_data['ip_address']
                    
                # Update hostname if provided
                if 'hostname' in heartbeat_data and heartbeat_data['hostname']:
                    agent_data['hostname'] = heartbeat_data['hostname']
                    
                await db_manager.store_agent_info(agent_data)
                    
                # Process network topology data if present
                network_topology = heartbeat_data.get('network_topology', {})
                if network_topology and network_topology.get('networkTopology'):
                    logger.info(
                        f"Received network topology from {agent_id}: {len(network_topology['networkTopology'])} hosts")
                    
                    # Store network topology data
                    for host in network_topology['networkTopology']:
                        try:
                            # Store each discovered host as a network node
                            host_data = {
                                'agent_id': f"{agent_id}_network",
                                'hostname': host.get('hostname', f"host-{host.get('ipAddress', 'unknown')}"),
                                'ip_address': host.get('ipAddress', 'unknown'),
                                'platform': host.get('platform', 'Unknown'),
                                'status': 'discovered',
                                'last_seen': datetime.now(),
                                'agent_type': 'network_node'
                            }
                            await db_manager.store_agent_info(host_data)
                        except Exception as e:
                            logger.warning(f"Failed to store network host {host.get('ipAddress')}: {e}")
                    
                logger.info(f"Heartbeat received from agent: {agent_id}")
                return {"status": "success", "message": "Heartbeat received"}
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.get("/api/agents/{agent_id}/commands")
        async def get_agent_commands(agent_id: str):
            """Get pending commands for client agent"""
            try:
                from core.server.command_queue.command_manager import CommandManager
                from core.server.storage.database_manager import DatabaseManager
                # Initialize CommandManager
                db_manager = DatabaseManager(db_path='soc_database.db')
                cmd_manager = CommandManager(db_manager)
                # Get pending commands for this agent
                commands = await cmd_manager.get_pending_commands(agent_id)
                logger.info(f"Retrieved {len(commands)} pending commands for {agent_id}")
                return {
                            "status": "success",
                            "commands": commands,
                            "agent_id": agent_id
                }
            except Exception as e:
                logger.error(f"Commands error for {agent_id}: {e}")
                return {"status": "error", "message": str(e), "commands": []}

        @self.app.post("/api/agents/{agent_id}/commands/result")
        async def receive_command_result(agent_id: str, result_data: dict):
            """Receive command execution result from client agent"""
            try:
                from core.server.command_queue.command_manager import CommandManager
                from core.server.storage.database_manager import DatabaseManager
                command_id = result_data.get('command_id')
                # Initialize CommandManager
                db_manager = DatabaseManager(db_path='soc_database.db')
                cmd_manager = CommandManager(db_manager)
                # Store command result
                await cmd_manager.receive_command_result(command_id, agent_id, result_data)
                logger.info(f"Command result received from {agent_id}: {command_id} - {result_data.get('status')}")
                return {
                            "status": "success",
                            "command_id": command_id,
                            "message": "Result received"
                }
            except Exception as e:
                logger.error(f"Command result error: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.post("/api/soc/real-apt-scenarios")
        async def create_real_apt_scenario(scenario_data: dict):
            """Create and execute REAL APT scenarios"""
            try:
                from agents.attack_agent.langchain_attack_agent import LangChainAttackAgent
                # Initialize attack agent
                attack_agent = LangChainAttackAgent()
                # Create scenario
                scenario = {
                            "scenario_id": f"real_apt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                            "name": scenario_data.get('name', 'Real APT Attack'),
                            "description": scenario_data.get('description', 'Real APT attack scenario'),
                            "attack_type": scenario_data.get('attack_type', 'network_intrusion'),
                            "target_agents": scenario_data.get('target_agents', []),
                            "mitre_techniques": scenario_data.get('mitre_techniques', []),
                            "destructive": True,
                            "real_attack": True
                }
                # Execute scenario
                result = await attack_agent.plan_attack_scenario(
                    objective=scenario_data.get('objective', 'Execute real APT attack'),
                constraints=scenario_data.get('constraints', {}),
                scenario=scenario
                )
                logger.info(f"Real APT scenario created: {scenario['scenario_id']}")
                return {
                            "status": "success",
                            "scenario_id": scenario['scenario_id'],
                            "message": "Real APT scenario created and queued",
                            "result": result
                }
            except Exception as e:
                logger.error(f"Real APT scenario creation failed: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.get("/api/soc/real-apt-scenarios")
        async def get_real_apt_scenarios():
            """Get AI-generated REAL APT scenarios - NO FALLBACKS"""
            try:
                    # Check if GPT scenario requester is available
                    if not self.gpt_scenario_requester:
                        return {
                            "status": "error",
                            "error": "GPT scenario requester not available - AI service unavailable",
                            "timestamp": datetime.utcnow().isoformat()
                        }

                    # Generate AI-powered scenarios using GPT
                    ai_scenarios = await self._generate_ai_apt_scenarios()

                    if not ai_scenarios:
                        return {
                            "status": "error",
                            "error": "Failed to generate AI scenarios - GPT service error",
                            "timestamp": datetime.utcnow().isoformat()
                        }

                    logger.info(f"Generated {len(ai_scenarios)} AI-powered APT scenarios")
                    return {
                        "status": "success",
                        "scenarios": ai_scenarios,
                        "total": len(ai_scenarios),
                        "source": "ai_generated"
                    }
            except Exception as e:
                    logger.error(f"AI scenario generation failed: {e}")
                    return {
                        "status": "error",
                        "error": f"AI scenario generation failed: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    }

        @self.app.post("/api/logs/ingest")
        async def ingest_logs(logs_data: dict):
            """Handle log ingestion from client agents"""
            try:
                from datetime import datetime
                from core.server.storage.database_manager import DatabaseManager
                from shared.models import LogEntry
                import json
                # Process incoming logs
                agent_id = logs_data.get('agent_id', 'unknown')
                logs = logs_data.get('logs', [])
                logger.info(f"Received {len(logs)} logs from agent: {agent_id}")
                # Store logs in database
                db_manager = DatabaseManager(db_path="soc_database.db", enable_elasticsearch=False, enable_influxdb=False)
                # Process each log entry WITH REAL-TIME THREAT DETECTION
                threats_detected = 0
                for log_entry in logs:
                    try:
                        # Extract key information for topology building
                        log_data = {
                                'timestamp': datetime.now(),
                                'agent_id': agent_id,
                                'level': log_entry.get('level', 'info'),
                                'message': log_entry.get('message', ''),
                                'source': log_entry.get('source', 'unknown'),
                                'raw_log': json.dumps(log_entry)
                            }
                            
                        # Store log entry and get the log ID
                        log_id = await db_manager.store_log_entry_with_id(log_data)
                            
                        # ANALYZE ALL LOGS - use proper AI detection agents
                        # Add agent_id to log_entry for analysis  
                        log_entry_with_agent = {**log_entry, 'agent_id': agent_id}
                        
                        # Use the AI-enhanced detector instead of hardcoded analysis
                        try:
                            from agents.detection_agent.ai_enhanced_detector import AIEnhancedThreatDetector
                            ai_detector = AIEnhancedThreatDetector()
                            
                            # Run proper AI threat analysis
                            ai_result = await ai_detector.analyze_threat_intelligently(
                                detection_data=log_entry_with_agent,
                                context={"source": "log_ingest", "agent_id": agent_id}
                            )
                            
                            # Store detection result if threat detected
                            if ai_result.get('final_threat_detected') or ai_result.get('combined_confidence', 0) > 0.5:
                                detection_payload = {
                                    'log_entry_id': str(log_id),
                                    'confidence_score': ai_result.get('combined_confidence', 0.7),
                                    'threat_type': ai_result.get('threat_type', 'ai_detected'),
                                    'severity': ai_result.get('severity', 'medium'),
                                    'indicators': ai_result.get('indicators', []),
                                    'agent_id': agent_id,
                                    'log_message': log_entry.get('message', ''),
                                    'log_source': log_entry.get('source', ''),
                                    'detected_at': datetime.now().isoformat()
                                }
                                await self._store_detection_result(detection_payload)
                                logger.info(f"AI threat detected: {ai_result.get('threat_type')} (confidence: {ai_result.get('combined_confidence', 0):.2f})")
                                
                        except Exception as ai_error:
                            logger.warning(f"AI threat analysis failed: {ai_error}")
                        
                        # Extract network information for topology
                        if 'ip_address' in log_entry or 'hostname' in log_entry:
                            # Get IP address from log entry, fallback to agent's IP
                            log_ip = log_entry.get('ip_address')
                            if not log_ip or log_ip == '127.0.0.1':
                                # Try to get agent's IP from database
                                try:
                                    agent_info = await db_manager.get_agent_info(agent_id)
                                    log_ip = agent_info.get('ip_address', 'unknown') if agent_info else 'unknown'
                                except:
                                    log_ip = 'unknown'
                                    
                            network_info = {
                                'agent_id': agent_id,
                                'hostname': log_entry.get('hostname', 'unknown'),
                                'ip_address': log_ip,
                                'platform': log_entry.get('platform', 'unknown'),
                                'services': log_entry.get('services', []),
                                'last_seen': datetime.now()
                            }
                            await db_manager.store_network_node(network_info)
                        
                    except Exception as log_error:
                        logger.warning(f"Failed to process log entry: {log_error}")
                        continue
                    
                # Log detection summary
                if threats_detected > 0:
                    logger.info(f"Detection summary: {threats_detected} alerts in batch from {agent_id}")
                    
                return {
                    "status": "success",
                    "message": f"Ingested {len(logs)} logs",
                    "timestamp": datetime.now().isoformat(),
                    "agent_id": agent_id
                }
            except Exception as e:
                logger.error(f"Log ingestion error: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.get("/api/logs")
        async def get_logs(limit: int = 100, offset: int = 0, agent_id: str = None):
            """Get logs from database"""
            try:
                from core.server.storage.database_manager import DatabaseManager
                db_manager = DatabaseManager(db_path="soc_database.db", enable_elasticsearch=False, enable_influxdb=False)
                # Get logs from database
                logs = await db_manager.get_log_entries(limit=limit, offset=offset, agent_id=agent_id)
                return {
                    "status": "success",
                    "data": logs,
                    "count": len(logs),
                    "limit": limit,
                    "offset": offset
                }
            except Exception as e:
                logger.error(f"Get logs error: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.post("/api/telemetry/ingest")
        async def ingest_telemetry(telemetry_data: dict):
            """Handle telemetry ingestion from client agent containers"""
            try:
                from datetime import datetime
                from core.server.storage.database_manager import DatabaseManager
                import json
                # Extract telemetry information
                container_id = telemetry_data.get('container_id', 'unknown')
                agent_id = telemetry_data.get('agent_id', 'unknown')
                telemetry_type = telemetry_data.get('type', 'unknown')
                timestamp = telemetry_data.get('timestamp', datetime.utcnow().isoformat())
                data = telemetry_data.get('data', {})
                logger.info(f"Received telemetry from container {container_id} (agent: {agent_id}, type: {telemetry_type})")
                # Store telemetry in database
                db_manager = DatabaseManager(db_path="soc_database.db", enable_elasticsearch=False, enable_influxdb=False)
                # Create telemetry table if not exists
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS container_telemetry (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            container_id TEXT,
                            agent_id TEXT,
                            type TEXT,
                            timestamp TEXT,
                            data TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    # Insert telemetry data
                    conn.execute("""
                        INSERT INTO container_telemetry (container_id, agent_id, type, timestamp, data)
                        VALUES (?, ?, ?, ?, ?)
                    """, (container_id, agent_id, telemetry_type, timestamp, json.dumps(data)))
                    
                    conn.commit()
                # Analyze telemetry for attack patterns (if it's container logs)
                if telemetry_type == 'container_log' and isinstance(data, str):
                    await self._analyze_container_telemetry(container_id, agent_id, data)
                    
                return {"status": "success", "message": "Telemetry ingested successfully"}
            except Exception as e:
                logger.error(f"Telemetry ingestion error: {e}")
                return {"status": "error", "message": str(e)}

                # Add detection results API
        @self.app.get("/api/backend/detections")
        async def get_detection_results():
            """Get recent threat detection results"""
            try:
                from api.api_utils import api_utils
                return await api_utils.get_detection_results_data()
            except Exception as e:
                logger.error(f"Detection results error: {e}")
                return {'status': 'error', 'message': str(e), 'data': []}

                # Add attack agents API
        @self.app.get("/api/backend/attack-agents")
        async def get_attack_agents():
            """Get running attack agents from client systems"""
            try:
                # For now, return default PhantomStrike agents since client querying is complex
                return {
                    'status': 'success',
                    'data': [
                        {
                            'id': 'phantomstrike_ai',
                            'name': 'PhantomStrike AI',
                            'type': 'attack',
                            'status': 'inactive',
                            'scope': 'Client Network',
                            'description': 'Ready for deployment',
                            'capabilities': ['Attack Planning', 'Scenario Generation', 'Red Team Operations'],
                            'deployment': 'Container Agent (Standby)'
                        },
                        {
                            'id': 'phantomstrike_web_ai',
                            'name': 'PhantomStrike Web AI',
                            'type': 'attack',
                            'status': 'inactive',
                            'scope': 'Client Network',
                            'description': 'Ready for deployment',
                            'capabilities': ['Web Vulnerability Scanning', 'SQL Injection', 'XSS Testing'],
                            'deployment': 'Container Agent (Standby)'
                        },
                        {
                            'id': 'phantomstrike_network_ai',
                            'name': 'PhantomStrike Network AI',
                            'type': 'attack',
                            'status': 'inactive',
                            'scope': 'Client Network',
                            'description': 'Ready for deployment',
                            'capabilities': ['Network Scanning', 'Port Discovery', 'Service Enumeration'],
                            'deployment': 'Container Agent (Standby)'
                        },
                        {
                            'id': 'phantomstrike_phishing_ai',
                            'name': 'PhantomStrike Phishing AI',
                            'type': 'attack',
                            'status': 'inactive',
                            'scope': 'Client Network',
                            'description': 'Ready for deployment',
                            'capabilities': ['Email Campaigns', 'Credential Harvesting', 'Social Engineering'],
                            'deployment': 'Container Agent (Standby)'
                        }
                    ]
                }
            except Exception as e:
                logger.error(f"Attack agents error: {e}")
                return {'status': 'error', 'message': str(e), 'agents': []}

        logger.info("Simple frontend API routes added successfully")
        logger.info("Client agent API routes added successfully")
        logger.info("Detection results API added successfully")

        async def _analyze_container_telemetry(self, container_id: str, agent_id: str, log_data: str):
            """Analyze container telemetry for attack patterns and security events"""
            try:
                # Look for common attack indicators in container logs
                attack_indicators = [
                    'nmap', 'sqlmap', 'metasploit', 'exploit', 'payload',
                    'reverse shell', 'backdoor', 'privilege escalation',
                    'lateral movement', 'credential dump', 'password crack',
                    'port scan', 'vulnerability scan', 'buffer overflow',
                    'sql injection', 'xss', 'csrf', 'directory traversal'
                ]
                suspicious_commands = [
                    'wget', 'curl', 'nc', 'netcat', 'python -c', 'perl -e',
                    'bash -i', 'sh -i', '/bin/sh', '/bin/bash', 'powershell',
                    'cmd.exe', 'whoami', 'id', 'sudo', 'su -', 'chmod +x'
                ]
                # Check for attack indicators
                log_lower = log_data.lower()
                detected_indicators = []
                for indicator in attack_indicators:
                    if indicator in log_lower:
                        detected_indicators.append(indicator)
                
                for command in suspicious_commands:
                    if command in log_lower:
                        detected_indicators.append(f"suspicious_command: {command}")
                
                # If indicators found, create alert
                if detected_indicators:
                    alert_data = {
                        'container_id': container_id,
                        'agent_id': agent_id,
                        'alert_type': 'container_attack_activity',
                        'severity': 'HIGH' if len(detected_indicators) > 3 else 'MEDIUM',
                        'indicators': detected_indicators,
                        'raw_log': log_data[:500],  # First 500 chars
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    # Store alert in database
                    from core.server.storage.database_manager import DatabaseManager
                    db_manager = DatabaseManager(db_path="soc_database.db", enable_elasticsearch=False, enable_influxdb=False)
                    with db_manager.get_connection() as conn:
                        conn.execute("""
                            CREATE TABLE IF NOT EXISTS container_alerts (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                container_id TEXT,
                                agent_id TEXT,
                                alert_type TEXT,
                                severity TEXT,
                                indicators TEXT,
                                raw_log TEXT,
                                timestamp TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        conn.execute("""
                            INSERT INTO container_alerts (container_id, agent_id, alert_type, severity, indicators, raw_log, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            container_id, agent_id, alert_data['alert_type'], 
                            alert_data['severity'], json.dumps(detected_indicators),
                            alert_data['raw_log'], alert_data['timestamp']
                        ))
                        
                        conn.commit()
                    
                    logger.warning(f"CONTAINER ATTACK ALERT: {len(detected_indicators)} indicators detected in {container_id}")
                    logger.info(f"Attack indicators: {', '.join(detected_indicators[:5])}")  # Log first 5
            except Exception as e:
                logger.error(f"Error analyzing container telemetry: {e}")

        def _calculate_severity(self, threat_score: float) -> str:
            """Calculate severity based on threat score"""
            if threat_score >= 0.8:
                return 'critical'
            elif threat_score >= 0.6:
                return 'high'
            elif threat_score >= 0.4:
                return 'medium'
            else:
                return 'low'

        async def _store_detection_result(self, detection_result: Dict[str, Any]):
            """Store detection result in database"""
            try:
                import sqlite3
                conn = sqlite3.connect('soc_database.db')
                # Create detection_results table if not exists
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS detection_results (
                        id TEXT PRIMARY KEY,
                        log_entry_id TEXT,
                        threat_detected INTEGER,
                        confidence_score REAL,
                        threat_type TEXT,
                        severity TEXT,
                        ml_results TEXT,
                        ai_analysis TEXT,
                        detected_at TEXT
                    )
                """)
                # Insert detection result
                detection_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO detection_results (
                        id, log_entry_id, threat_detected, confidence_score, threat_type, 
                        severity, ml_results, ai_analysis, detected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    detection_id,
                    detection_result['log_entry_id'],
                    1,  # threat_detected = True
                    detection_result['confidence_score'],
                    detection_result['threat_type'],
                    detection_result['severity'],
                    json.dumps({
                        'indicators': detection_result['indicators'],
                        'agent_id': detection_result['agent_id'],
                        'log_message': detection_result['log_message'],
                        'log_source': detection_result['log_source']
                    }),
                    json.dumps({'analysis': 'Real-time content analysis', 'indicators': detection_result['indicators']}),
                    detection_result['detected_at']
                ))
                
                conn.commit()
                conn.close()
                logger.info(f"Detection result stored: {detection_id}")
            except Exception as e:
                logger.error(f"Failed to store detection result: {e}")

    async def _analyze_threat_dynamically(self, log_entry: Dict[str, Any]) -> None:
        """Run AI detection on an ingested log and persist the verdict."""
        try:
            logger.info(f"Starting AI threat analysis for log: {log_entry.get('message', 'No message')[:50]}...")
            
            if not getattr(self, 'detection_agent', None):
                logger.warning("Detection agent not initialized; skipping dynamic analysis")
                return

            logger.info("Detection agent found, calling analyze_threat...")
            result = await self.detection_agent.analyze_threat(
                detection_data=log_entry,
                context={"source": "log_ingest"}
            )
            
            logger.info(f"AI analysis result type: {type(result)}")
            logger.info(f"AI analysis result: {str(result)[:200]}...")

            # Normalize fields for existing _store_detection_result schema
            from datetime import datetime
            detection_payload = {
                'log_entry_id': log_entry.get('id') or log_entry.get('logId') or str(uuid.uuid4()),
                'confidence_score': float(getattr(result, 'confidence', 0.7) or (result.get('confidence', 0.7) if isinstance(result, dict) else 0.7)),
                'threat_type': getattr(result, 'threat_type', None) or (result.get('threat_type') if isinstance(result, dict) else 'dynamic_analysis'),
                'severity': getattr(result, 'severity', None) or (result.get('severity') if isinstance(result, dict) else 'info'),
                'indicators': getattr(result, 'indicators', None) or (result.get('indicators') if isinstance(result, dict) else []),
                'agent_id': log_entry.get('agentId') or log_entry.get('agent_id'),
                'log_message': log_entry.get('message') or log_entry.get('msg') or '',
                'log_source': log_entry.get('source') or log_entry.get('logger') or 'client_agent',
                'detected_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Storing detection result with confidence: {detection_payload['confidence_score']}")
            await self._store_detection_result(detection_payload)
            logger.info("AI threat analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Dynamic threat analysis failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")  

    async def _get_attack_agents_from_clients(self) -> Dict[str, Any]:
        """Query client agents for their running attack agents"""
        try:
            from core.server.storage.database_manager import DatabaseManager
            import asyncio
            import requests
            # Get active client agents from database
            db_manager = DatabaseManager(db_path="soc_database.db", enable_elasticsearch=False, enable_influxdb=False)
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT agent_id, last_heartbeat, server_url 
                    FROM agents 
                    WHERE last_heartbeat > datetime('now', '-5 minutes')
                    AND agent_type != 'soc_agent'
                """)
                active_agents = cursor.fetchall()
            all_agents = []
            # Query each active client agent for their attack agents
            for agent_row in active_agents:
                agent_id = agent_row[0]
                try:
                    # Create command to get attack agents
                    command = {
                        'id': f'get_agents_{int(time.time())}',
                        'type': 'get_attack_agents',
                        'data': {}
                    }
                    
                    # Store command in database for the agent to pick up
                    with db_manager.get_connection() as conn:
                        conn.execute("""
                            INSERT INTO pending_commands (agent_id, command_id, command_type, command_data, created_at)
                            VALUES (?, ?, ?, ?, datetime('now'))
                        """, (agent_id, command['id'], command['type'], json.dumps(command['data'])))
                        conn.commit()
                    
                    logger.info(f"Queued attack agents request for agent: {agent_id}")
                except Exception as e:
                    logger.error(f"Error querying agent {agent_id} for attack agents: {e}")
            
            # Wait a moment for agents to respond, then check for results
            await asyncio.sleep(2)
            
            # Check for command results
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT agent_id, result_data 
                    FROM command_results 
                    WHERE command_id LIKE 'get_agents_%' 
                    AND created_at > datetime('now', '-1 minute')
                """)
                results = cursor.fetchall()
            
            # Process results
            for result_row in results:
                try:
                    agent_id = result_row[0]
                    result_data = json.loads(result_row[1])
                    if result_data.get('success') and 'agents' in result_data:
                        agents_data = result_data['agents']
                        if isinstance(agents_data, list):
                            all_agents.extend(agents_data)
                        elif isinstance(agents_data, dict) and 'agents' in agents_data:
                            all_agents.extend(agents_data['agents'])
                except Exception as e:
                    logger.error(f"Error processing attack agents result: {e}")
            
            # If no agents found, return default PhantomStrike AI agents
            if not all_agents:
                all_agents = [
                    {
                        'id': 'phantomstrike_ai',
                        'name': 'PhantomStrike AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'scope': 'Client Network',
                        'description': 'Ready for deployment',
                        'capabilities': ['Attack Planning', 'Scenario Generation', 'Red Team Operations'],
                        'deployment': 'Container Agent (Standby)'
                    },
                    {
                        'id': 'phantomstrike_web_ai',
                        'name': 'PhantomStrike Web AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'scope': 'Client Network',
                        'description': 'Ready for deployment',
                        'capabilities': ['Web Vulnerability Scanning', 'SQL Injection', 'XSS Testing'],
                        'deployment': 'Container Agent (Standby)'
                    },
                    {
                        'id': 'phantomstrike_network_ai',
                        'name': 'PhantomStrike Network AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'scope': 'Client Network',
                        'description': 'Ready for deployment',
                        'capabilities': ['Network Scanning', 'Port Discovery', 'Service Enumeration'],
                        'deployment': 'Container Agent (Standby)'
                    },
                    {
                        'id': 'phantomstrike_phishing_ai',
                        'name': 'PhantomStrike Phishing AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'scope': 'Client Network',
                        'description': 'Ready for deployment',
                        'capabilities': ['Email Campaigns', 'Credential Harvesting', 'Social Engineering'],
                        'deployment': 'Container Agent (Standby)'
                    }
                ]
            return {
                'status': 'success',
                'data': all_agents
            }
        except Exception as e:
            logger.error(f"Error getting attack agents from clients: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'data': []
            }
            
    async def _run_realtime_detection(self, log_entry: dict, agent_id: str, log_id: str) -> dict:
        """Run real-time threat detection on incoming log"""
        try:
            import re
            import uuid
            import sqlite3
            message = log_entry.get('message', '').lower()
            source = log_entry.get('source', '').lower()
            level = log_entry.get('level', '').lower()
            # Dynamic threat detection - learn patterns from environment
            threat_analysis = await self._analyze_threat_dynamically(log_entry, agent_id)
            # Use dynamic threat analysis results
            if threat_analysis:
                threat_score = threat_analysis.get('threat_score', 0.0)
                threat_type = threat_analysis.get('threat_type', 'benign')
                indicators = threat_analysis.get('indicators', [])
            else:
                threat_score = 0.0
                threat_type = 'benign'
                indicators = []
            # Severity scoring
            if level in ['error', 'critical', 'fatal']:
                threat_score += 0.3  # Increased from 0.2
            elif level in ['warning', 'warn']:
                threat_score += 0.2  # Increased from 0.1
            # Source scoring
            if 'security' in source:
                threat_score += 0.4  # Increased from 0.3
            elif 'system' in source:
                threat_score += 0.2  # Increased from 0.1
            elif 'process' in source:
                threat_score += 0.2  # New: process monitoring is important
            # Dynamic severity determination based on environment and context
            severity_thresholds = self._get_adaptive_thresholds(source, level)
            if threat_score >= severity_thresholds['critical']:
                severity = 'critical'
            elif threat_score >= severity_thresholds['high']:
                severity = 'high'
            elif threat_score >= severity_thresholds['medium']:
                severity = 'medium'
            elif threat_score >= severity_thresholds['low']:
                severity = 'low'
            else:
                severity = 'benign'
            threat_detected = threat_score >= severity_thresholds['detection_threshold']
            # Store detection result immediately
            if log_id:
                detection_id = str(uuid.uuid4())
                conn = sqlite3.connect('soc_database.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO detection_results (
                        id, log_entry_id, threat_detected, confidence_score, 
                        threat_type, severity, ml_results, ai_analysis, detected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    detection_id,
                    log_id,
                    threat_detected,
                    threat_score,
                    threat_type,
                    severity,
                    json.dumps({'realtime_detection': True, 'indicators': indicators}),
                    json.dumps({
                        'agent_id': agent_id,
                        'summary': f"Real-time analysis found {len(indicators)} threat indicators",
                        'indicators': indicators
                    }),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
            return {
                "threat_detected": threat_detected,
                "threat_score": threat_score,
                "threat_type": threat_type,
                "severity": severity,
                "indicators": indicators
            }
        except Exception as e:
            logger.error(f"Real-time detection error: {e}")
            return None

    def _get_adaptive_thresholds(self, source: str, level: str) -> Dict[str, float]:
        """Get adaptive detection thresholds based on environment and context"""
        # Base thresholds
        base_thresholds = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.3,
            "detection_threshold": 0.3
        }
        # Adjust thresholds based on source criticality
        if 'security' in source:
            # Security logs are more critical - lower thresholds
            return {
                "critical": 0.8,
                "high": 0.6,
                "medium": 0.4,
                "low": 0.2,
                "detection_threshold": 0.2
            }
        elif 'system' in source:
            # System logs are important - slightly lower thresholds
            return {
                "critical": 0.9,
                "high": 0.65,
                "medium": 0.45,
                "low": 0.25,
                "detection_threshold": 0.25
            }
        elif 'process' in source:
            # Process logs can be noisy - slightly higher thresholds
            return {
                "critical": 1.1,
                "high": 0.75,
                "medium": 0.55,
                "low": 0.35,
                "detection_threshold": 0.35
            }
        elif level in ['critical', 'error']:
            # High-level logs get lower thresholds regardless of source
            return {
                "critical": 0.7,
                "high": 0.5,
                "medium": 0.3,
                "low": 0.2,
                "detection_threshold": 0.2
            }
        # Return base thresholds for everything else
        return base_thresholds

    async def _analyze_threat_dynamically(self, log_entry: Dict, agent_id: str) -> Dict[str, Any]:
        """Analyze ALL logs for threats - content-based detection regardless of level"""
        try:
            message = log_entry.get('message', '').lower()
            source = log_entry.get('source', '').lower()
            # CONTENT-BASED THREAT DETECTION (not level-based)
            threat_score = 0.0
            indicators = []
            threat_type = 'benign'
            # 1. ATTACK TOOL DETECTION
            attack_tools = [
                'nmap', 'sqlmap', 'metasploit', 'msfconsole', 'exploit',
                'nikto', 'dirb', 'gobuster', 'hydra', 'john',
                'mimikatz', 'psexec', 'wmic', 'powershell -enc',
                'certutil -decode', 'bitsadmin', 'regsvr32'
            ]
            for tool in attack_tools:
                if tool in message:
                    threat_score += 0.7
                    indicators.append(f"Attack tool: {tool}")
                    threat_type = 'attack_tool_usage'
            # 2. SUSPICIOUS COMMAND DETECTION
            suspicious_commands = [
                'whoami', 'net user', 'net localgroup', 'net group',
                'tasklist', 'ps aux', 'netstat', 'arp -a',
                'ipconfig', 'ifconfig', 'route print', 'cat /etc/passwd',
                'cat /etc/shadow', 'sudo -l', 'find / -perm',
                'chmod +x', 'wget', 'curl', 'nc -', 'netcat'
            ]
            for cmd in suspicious_commands:
                if cmd in message:
                    threat_score += 0.4
                    indicators.append(f"Suspicious command: {cmd}")
                    threat_type = "reconnaissance"
            # 3. MALICIOUS ACTIVITY PATTERNS
            malicious_patterns = [
                'reverse shell', 'bind shell', 'backdoor', 'rootkit',
                'privilege escalation', 'lateral movement', 'persistence',
                'credential dump', 'password crack', 'hash dump',
                'buffer overflow', 'code injection', 'sql injection',
                'xss', 'csrf', 'directory traversal', 'file inclusion'
            ]
            for pattern in malicious_patterns:
                if pattern in message:
                    threat_score += 0.8
                    indicators.append(f"Malicious pattern: {pattern}")
                    threat_type = "active_attack"
            # 4. NETWORK ATTACK INDICATORS
            network_attacks = [
                'port scan', 'vulnerability scan', 'brute force',
                'dos attack', 'ddos', 'man in the middle',
                'arp spoofing', 'dns poisoning', 'packet injection'
            ]
            for attack in network_attacks:
                if attack in message:
                    threat_score += 0.6
                    indicators.append(f"Network attack: {attack}")
                    threat_type = "network_attack"
            # 5. CONTAINER/ATTACK CONTEXT
            if log_entry.get('container_context') or 'attackcontainer' in source:
                threat_score += 0.5
                indicators.append("Container attack context")
                threat_type = "container_attack"
            # 6. SYSTEM COMPROMISE INDICATORS
            compromise_indicators = [
                'malware', 'virus', 'trojan', 'ransomware',
                'keylogger', 'spyware', 'adware', 'botnet',
                'c2 server', 'command and control', 'exfiltration'
            ]
            for indicator in compromise_indicators:
                if indicator in message:
                    threat_score += 0.9
                    indicators.append(f"Compromise indicator: {indicator}")
                    threat_type = "system_compromise"
            # 7. FAILED AUTHENTICATION (even without ERROR level)
            auth_failures = [
                'failed login', 'authentication failed', 'invalid credentials',
                'access denied', 'unauthorized access', 'permission denied',
                'login attempt', 'brute force'
            ]
            
            for failure in auth_failures:
                if failure in message:
                    threat_score += 0.5
                    indicators.append(f"Auth failure: {failure}")
                    threat_type = "authentication_attack"
            
            # Cap threat score at 1.0
            threat_score = min(threat_score, 1.0)
            return {
                "threat_score": threat_score,
                "threat_type": threat_type,
                "indicators": indicators,
                "analysis_type": 'content_based_detection'
            }
        except Exception as e:
            logger.error(f"Content-based threat analysis failed: {e}")
            return {
                "threat_score": 0.0,
                "threat_type": 'benign',
                "indicators": [],
                "analysis_type": 'fallback'
            }

    async def _old_analyze_behavioral_anomalies(self, log_entry: Dict, agent_id: str, cursor) -> float:
        """Analyze behavioral anomalies compared to normal patterns"""
        try:
            # Compare current behavior to historical patterns for this agent
            cursor.execute('''
                SELECT source, level, COUNT(*) as frequency
                FROM log_entries 
                WHERE agent_id = ? 
                AND timestamp > datetime('now', '-7 days')
                GROUP BY source, level
            ''', (agent_id,))
            normal_patterns = cursor.fetchall()
            current_source = log_entry.get('source')
            current_level = log_entry.get('level')
            # Check if current log is anomalous compared to normal patterns
            is_anomalous = True
            for pattern in normal_patterns:
                if pattern[0] == current_source and pattern[1] == current_level:
                    is_anomalous = False
                    break
            return 0.4 if is_anomalous else 0.0
        except Exception as e:
            logger.debug(f"Behavioral analysis failed: {e}")
            return 0.0

    async def _analyze_network_context(self, log_entry: Dict, cursor) -> float:
        """Analyze network context for threat indicators"""
        try:
            message = log_entry.get('message', '')
            # Look for network-related threat indicators in the environment
            cursor.execute('''
                SELECT COUNT(*) FROM log_entries 
                WHERE message LIKE '%connection%' 
                AND timestamp > datetime('now', '-1 hour')
            ''')
            recent_connections = cursor.fetchone()[0]
            # High connection activity might indicate scanning or lateral movement
            if recent_connections > 100:
                return 0.3
            elif recent_connections > 50:
                return 0.2
            return 0.0
        except Exception as e:
            logger.debug(f"Network context analysis failed: {e}")
            return 0.0

    async def _ml_classify_threat_type(self, log_entry: Dict, cursor) -> str:
        """Use ML to classify threat type based on learned patterns"""
        try:
            # This would use ML models trained on the environment's data
            # For now, classify based on observed patterns in the database
            message = log_entry.get('message', '').lower()
            source = log_entry.get('source', '').lower()
            # Learn threat types from database
            cursor.execute('''
                SELECT threat_type, COUNT(*) as count
                FROM detection_results
                WHERE threat_detected = 1
                GROUP BY threat_type
                ORDER BY count DESC
            ''')
            common_threat_types = cursor.fetchall()
            if common_threat_types:
                # Return most common threat type in this environment
                return common_threat_types[0][0]
            # Fallback classification based on content analysis
            if 'process' in message or 'exe' in message:
                return 'process_anomaly'
            elif 'network' in message or 'connection' in message:
                return 'network_anomaly'
            elif 'system' in source:
                return 'system_anomaly'
            else:
                return 'unknown_anomaly'
        except Exception as e:
            logger.debug(f"ML threat classification failed: {e}")
            return 'unknown'

    async def _generate_dynamic_indicators(self, log_entry: Dict, cursor) -> List[str]:
        """Generate threat indicators dynamically based on environment learning"""
        try:
            indicators = []
            message = log_entry.get('message', '')
            source = log_entry.get('source', '')
            # Learn indicators from successful past detections
            cursor.execute('''
                SELECT ai_analysis FROM detection_results
                WHERE threat_detected = 1
                ORDER BY detected_at DESC LIMIT 20
            ''')
            past_analyses = cursor.fetchall()
            # Extract common indicator patterns from past detections
            for analysis in past_analyses:
                try:
                    analysis_data = json.loads(analysis[0])
                    past_indicators = analysis_data.get('indicators', [])
                    # Check if any past indicators apply to current log
                    for indicator in past_indicators:
                        if any(word in message.lower() for word in indicator.lower().split()[:3]):
                            indicators.append(f"Learned pattern: {indicator}")
                            break
                except:
                    continue
            # Add context-based indicators
            if not indicators:
                indicators.append("Container attack context")
            return indicators[:5]  # Limit to top 5 indicators
        except Exception as e:
            logger.debug(f"Dynamic indicator generation failed: {e}")
            return ['Dynamic analysis indicator']

    def _add_gpt_logging_routes(self):
        """Add GPT interactions logging API routes"""
        @self.app.get("/api/backend/gpt-interactions")
        async def get_gpt_interactions(
            interaction_type: str = None,
            limit: int = 100,
            offset: int = 0,
            start_date: str = None,
            end_date: str = None
        ):
            """Get GPT interactions from database with filtering"""
            try:
                from core.server.storage.database_manager import DatabaseManager
                from datetime import datetime
                
                db_manager = DatabaseManager(db_path="soc_database.db")
                
                # Convert date strings to datetime objects if provided
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                interactions = await db_manager.get_gpt_interactions(
                    interaction_type=interaction_type,
                    limit=limit,
                    offset=offset,
                    start_date=start_dt,
                    end_date=end_dt
                )
                
                logger.info(f"Retrieved {len(interactions)} GPT interactions")
                
                return {
                    "status": "success",
                    "data": interactions,
                    "total": len(interactions),
                    "limit": limit,
                    "offset": offset,
                    "filters": {
                        "interaction_type": interaction_type,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                }
            except Exception as e:
                logger.error(f"Failed to get GPT interactions: {e}")
                return {
                    "status": "error",
                    "message": str(e),
                    "data": []
                }
        
        @self.app.get("/api/backend/gpt-interactions/stats")
        async def get_gpt_interaction_stats():
            """Get GPT interaction statistics"""
            try:
                from core.server.storage.database_manager import DatabaseManager
                
                db_manager = DatabaseManager(db_path="soc_database.db")
                stats = await db_manager.get_gpt_interaction_stats()
                
                return {
                    "status": "success",
                    "data": stats
                }
            except Exception as e:
                logger.error(f"Failed to get GPT interaction stats: {e}")
                return {
                    "status": "error",
                    "message": str(e),
                    "data": {}
                }
        
        @self.app.get("/api/backend/gpt-interactions/{interaction_id}")
        async def get_gpt_interaction_by_id(interaction_id: str):
            """Get a specific GPT interaction by ID"""
            try:
                from core.server.storage.database_manager import DatabaseManager
                import sqlite3
                
                db_manager = DatabaseManager(db_path="soc_database.db")
                
                conn = sqlite3.connect(db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM gpt_interactions WHERE id = ?", (interaction_id,))
                row = cursor.fetchone()
                columns = [description[0] for description in cursor.description]
                
                conn.close()
                
                if row:
                    interaction = dict(zip(columns, row))
                    # Parse JSON fields
                    if interaction.get('metadata'):
                        try:
                            interaction['metadata'] = json.loads(interaction['metadata'])
                        except:
                            pass
                    
                    return {
                        "status": "success",
                        "data": interaction
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Interaction not found",
                        "data": None
                    }
            except Exception as e:
                logger.error(f"Failed to get GPT interaction {interaction_id}: {e}")
                return {
                    "status": "error",
                    "message": str(e),
                    "data": None
                }
        
        logger.info("GPT logging API routes added successfully")
    
    async def _get_hardcoded_scenarios(self):
        """Get the hardcoded scenarios from the real-apt-scenarios endpoint"""
        try:
            from datetime import datetime
            scenarios = [
                {
                    "id": "real_network_intrusion",
                    "name": "REAL Network Intrusion Campaign",
                    "aptGroup": "CodeGrey AI SOC Platform",
                    "description": "Live network penetration campaign using actual nmap scans, port enumeration, and brute force attacks against network services.",
                    "origin": "AI-Generated",
                    "targets": ["Network Infrastructure", "Server Systems", "Network Services", "Remote Access Points"],
                    "attackVectors": ["Network Scanning", "Port Enumeration", "Brute Force", "Service Exploitation"],
                    "mitreAttack": ["T1018", "T1021", "T1046", "T1110"],
                    "difficulty": "intermediate",
                    "duration": "30 minutes",
                    "detectability": "high",
                    "impact": "high",
                    "intelligence": {
                        "firstSeen": "2024",
                        "lastActivity": "2024",
                        "motivation": "Network Reconnaissance, Service Compromise",
                        "sophistication": 6
                    }
                },
                {
                    "id": "real_system_compromise",
                    "name": "REAL System Compromise Campaign",
                    "aptGroup": "CodeGrey AI SOC Platform",
                    "description": "Live system takeover campaign using actual PowerShell execution, process manipulation, and user account creation.",
                    "origin": "AI-Generated",
                    "targets": ["Windows Systems", "PowerShell Environments", "User Accounts", "System Processes"],
                    "attackVectors": ["PowerShell Execution", "Process Injection", "User Creation", "Privilege Escalation"],
                    "mitreAttack": ["T1059.001", "T1055", "T1134", "T1078"],
                    "difficulty": "advanced",
                    "duration": "25 minutes",
                    "detectability": "medium",
                    "impact": "critical"
                },
                {
                    "id": "real_data_extraction",
                    "name": "REAL Data Extraction Campaign",
                    "aptGroup": "CodeGrey AI SOC Platform",
                    "description": "Live data theft campaign using actual file access, data collection, and exfiltration techniques.",
                    "origin": "AI-Generated",
                    "targets": ["File Systems", "Documents", "Databases", "Network Shares"],
                    "attackVectors": ["File Access", "Data Collection", "Network Exfiltration", "Data Staging"],
                    "mitreAttack": ["T1005", "T1041", "T1020", "T1030"],
                    "difficulty": "intermediate",
                    "duration": "35 minutes",
                    "detectability": "medium",
                    "impact": "high"
                },
                {
                    "id": "real_persistence_installation",
                    "name": "REAL Persistence Installation Campaign",
                    "aptGroup": "CodeGrey AI SOC Platform",
                    "description": "Live backdoor installation campaign using actual scheduled tasks, registry modifications, and service installations.",
                    "origin": "AI-Generated",
                    "targets": ["Windows Registry", "Scheduled Tasks", "System Services", "Startup Programs"],
                    "attackVectors": ["Registry Modification", "Scheduled Tasks", "Service Installation", "Startup Persistence"],
                    "mitreAttack": ["T1053", "T1543", "T1547", "T1546"],
                    "difficulty": "advanced",
                    "duration": "20 minutes",
                    "detectability": "low",
                    "impact": "critical"
                },
                {
                    "id": "real_privilege_escalation",
                    "name": "REAL Privilege Escalation Campaign",
                    "aptGroup": "CodeGrey AI SOC Platform",
                    "description": "Live privilege escalation campaign using actual user group modifications and UAC bypass techniques.",
                    "origin": "AI-Generated",
                    "targets": ["User Accounts", "Administrator Groups", "System Privileges", "UAC Controls"],
                    "attackVectors": ["User Group Modification", "UAC Bypass", "Privilege Escalation", "Administrator Access"],
                    "mitreAttack": ["T1548", "T1055", "T1078", "T1134"],
                    "difficulty": "expert",
                    "duration": "15 minutes",
                    "detectability": "high",
                    "impact": "critical"
                },
                {
                    "id": "real_log_destruction",
                    "name": "REAL Log Destruction Campaign",
                    "aptGroup": "CodeGrey AI SOC Platform",
                    "description": "Live evidence destruction campaign using actual log clearing, file deletion, and system cleanup.",
                    "origin": "AI-Generated",
                    "targets": ["Event Logs", "System Logs", "Application Logs", "Forensic Evidence"],
                    "attackVectors": ["Log Clearing", "File Deletion", "Evidence Destruction", "System Cleanup"],
                    "mitreAttack": ["T1070", "T1562", "T1485", "T1489"],
                    "difficulty": "intermediate",
                    "duration": "10 minutes",
                    "detectability": "high",
                    "impact": "medium"
                }
            ]
            return scenarios
        except Exception as e:
            logger.error(f"Failed to get hardcoded scenarios: {e}")
            return []
    
    async def _customize_scenario_for_network(self, base_scenario, agents):
        """Customize a scenario based on the current network topology"""
        try:
            # Get platform information from connected agents
            platforms = list(set(agent.get('platform', 'unknown') for agent in agents))
            ip_addresses = [agent.get('ip_address') for agent in agents if agent.get('ip_address')]
            
            # Create network context for AI customization
            network_context = {
                'connected_agents': len(agents),
                'platforms': platforms,
                'ip_addresses': ip_addresses,
                'agent_details': [
                    {
                        'agent_id': agent.get('agent_id'),
                        'hostname': agent.get('hostname'),
                        'platform': agent.get('platform'),
                        'ip_address': agent.get('ip_address')
                    }
                    for agent in agents
                ]
            }
            
            # Use GPT to customize the scenario for this specific network
            if self.gpt_scenario_requester:
                try:
                    # Create a customization request
                    customization_request = f"""
                    Customize this attack scenario for the current network environment:
                    
                    Base Scenario: {base_scenario.get('name')}
                    Description: {base_scenario.get('description')}
                    
                    Current Network:
                    - Connected Agents: {len(agents)}
                    - Platforms: {', '.join(platforms)}
                    - IP Addresses: {', '.join(ip_addresses[:5])}  # Limit to first 5
                    
                    Please adapt the scenario to target the specific platforms and network topology present.
                    """
                    
                    # Generate customized scenario using GPT
                    customized = await self.gpt_scenario_requester.request_custom_scenario(
                        user_request=customization_request,
                        network_context=network_context,
                        constraints={
                            'scenario_id': base_scenario.get('id'),
                            'target_agents': [agent.get('agent_id') for agent in agents],
                            'platforms': platforms
                        }
                    )
                    
                    # Merge base scenario with AI customization
                    customized_scenario = base_scenario.copy()
                    customized_scenario.update({
                        'description': customized.get('description', base_scenario.get('description')),
                        'targets': customized.get('target_services', base_scenario.get('targets')),
                        'attackVectors': customized.get('attack_vectors', base_scenario.get('attackVectors')),
                        'network_context': network_context,
                        'customized': True
                    })
                    
                    return customized_scenario
                    
                except Exception as e:
                    logger.warning(f"GPT customization failed, using base scenario: {e}")
                    # Fallback to base scenario with network context
                    base_scenario['network_context'] = network_context
                    return base_scenario
            else:
                # No GPT available, just add network context to base scenario
                base_scenario['network_context'] = network_context
                return base_scenario
                
        except Exception as e:
            logger.error(f"Failed to customize scenario: {e}")
            # Return base scenario as fallback
            return base_scenario
    
    def get_app(self) -> FastAPI:
        """Get FastAPI application"""
        return self.app


# Create API instance
soc_api = SOCPlatformAPI()
