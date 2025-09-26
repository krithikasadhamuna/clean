"""
LangServe API for AI SOC Platform
Replaces FastAPI with LangChain-native API endpoints
"""

import asyncio
import logging
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

# Import agents with error handling
try:
    from agents.langchain_orchestrator import soc_orchestrator
    from agents.detection_agent.langchain_detection_agent import langchain_detection_agent  
    from agents.attack_agent.langchain_attack_agent import phantomstrike_ai
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    soc_orchestrator = None
    langchain_detection_agent = None
    phantomstrike_ai = None


logger = logging.getLogger(__name__)

if not AGENTS_AVAILABLE:
    logger.warning("LangChain agents not available for LangServe")


class SOCPlatformAPI:
    """LangServe-based API for AI SOC Platform"""
    
    def __init__(self):
        self.app = FastAPI(
            title="AI SOC Platform - LangChain API",
            description="LangChain-powered SOC operations API",
            version="2.0.0"
        )
        
        # Add CORS middleware for frontend development
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000",  # React dev server
                "http://localhost:3001",  # Alternative React port
                "http://localhost:8080",  # Same origin
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080", 
                "http://dev.codegrey.ai",  # CodeGrey domain
                "*"  # Allow all for development
            ],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=[
                "Content-Type",
                "Authorization",
                "X-API-Key",  # CodeGrey API key header
                "X-Requested-With",
                "Accept",
                "Origin",
                "Access-Control-Request-Method", 
                "Access-Control-Request-Headers"
            ],
            expose_headers=[
                "X-Total-Count",
                "X-Page-Count",
                "X-API-Version"
            ]
        )
        
        # Add LangServe routes
        self._add_langserve_routes()
        
        # Add custom endpoints
        self._add_custom_endpoints()
    
    def _add_langserve_routes(self):
        """Add LangServe routes for agents"""
        
        if not AGENTS_AVAILABLE:
            logger.warning("LangChain agents not available, skipping LangServe routes")
            return
        
        try:
            # SOC Orchestrator - main entry point
            if soc_orchestrator:
                add_routes(
                    self.app,
                    soc_orchestrator.agent_executor,
                    path="/api/soc",
                    playground_type="default"
                )
            
            # Detection Agent
            if langchain_detection_agent:
                add_routes(
                    self.app,
                    langchain_detection_agent.agent_executor,
                    path="/api/detection",
                    playground_type="default"
                )
            
            # Attack Agent (PhantomStrike AI)
            if phantomstrike_ai:
                add_routes(
                    self.app,
                    phantomstrike_ai.agent_executor,
                    path="/api/attack",
                    playground_type="default"
                )
                
            logger.info("LangServe routes added successfully")
            
        except Exception as e:
            logger.error(f"Failed to add LangServe routes: {e}")
            global AGENTS_AVAILABLE
            AGENTS_AVAILABLE = False
    
    def _add_custom_endpoints(self):
        """Add custom API endpoints"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "AI SOC Platform - LangChain API",
                "version": "2.0.0",
                "endpoints": {
                    "soc_orchestrator": "/api/soc",
                    "detection_agent": "/api/detection", 
                    "attack_agent": "/api/attack",
                    "playground": "/api/soc/playground"
                }
            }
        
        @self.app.get("/health")
        async def health_check():
            try:
                # Check agent status
                orchestrator_status = await soc_orchestrator.get_orchestrator_status()
                detection_status = await langchain_detection_agent.get_detection_statistics()
                attack_status = await phantomstrike_ai.get_execution_status()
                
                return {
                    "status": "healthy",
                    "version": "2.0.0",
                    "agents": {
                        "orchestrator": orchestrator_status,
                        "detection": detection_status,
                        "attack": attack_status
                    },
                    "langchain_integration": "active"
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
                detection_data = request_data.get('detection_data', {})
                context = request_data.get('context', {})
                
                result = await soc_orchestrator.process_soc_request(
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
                
                result = await soc_orchestrator.process_soc_request(
                    f"Plan attack scenario: {attack_request}",
                    {
                        'network_context': network_context,
                        'constraints': constraints,
                        'operation_type': 'attack_planning'
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
                approvals = await phantomstrike_ai.get_pending_approvals()
                return {
                    "success": True,
                    "pending_approvals": approvals
                }
            
            except Exception as e:
                logger.error(f"Pending approvals API error: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/soc/approve-attack")
        async def approve_attack(request_data: Dict[str, Any]):
            """Approve or reject attack scenario"""
            try:
                scenario_id = request_data.get('scenario_id')
                approved = request_data.get('approved', False)
                
                result = await phantomstrike_ai.execute_approved_scenario(
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
                result = await soc_orchestrator.process_soc_request(
                    "Get current network topology analysis",
                    {'operation_type': 'topology_query'}
                )
                
                return result
            
            except Exception as e:
                logger.error(f"Topology API error: {e}")
                return {"success": False, "error": str(e)}
    
    def get_app(self) -> FastAPI:
        """Get FastAPI application"""
        return self.app


# Create API instance
soc_api = SOCPlatformAPI()
