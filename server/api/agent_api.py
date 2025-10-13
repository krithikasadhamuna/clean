"""
Agent management API endpoints
"""

import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from shared.models import AgentInfo
from core.server.command_queue.command_manager import get_command_manager


logger = logging.getLogger(__name__)


class AgentAPI:
    """Agent management API endpoints"""
    
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.command_manager = get_command_manager(database_manager)
        self.router = APIRouter(prefix="/api/agents", tags=["agents"])
        
        # Add routes
        self.router.add_api_route("/register", self.register_agent, methods=["POST"])
        self.router.add_api_route("/{agent_id}/heartbeat", self.agent_heartbeat, methods=["POST"])
        self.router.add_api_route("/{agent_id}", self.get_agent, methods=["GET"])
        self.router.add_api_route("/{agent_id}/commands", self.get_pending_commands, methods=["GET"])
        self.router.add_api_route("/{agent_id}/command-results", self.receive_command_results, methods=["POST"])
    
    async def register_agent(self, agent_data: Dict[str, Any]) -> JSONResponse:
        """Register new agent"""
        try:
            # Create AgentInfo object
            agent_info = AgentInfo.from_dict(agent_data) if hasattr(AgentInfo, 'from_dict') else AgentInfo()
            
            # Register in database
            await self.database_manager.register_agent(agent_info)
            
            return JSONResponse(content={
                'status': 'success',
                'message': f'Agent {agent_info.id} registered successfully',
                'agent_id': agent_info.id
            })
            
        except Exception as e:
            logger.error(f"Agent registration error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def agent_heartbeat(self, agent_id: str, heartbeat_data: Dict[str, Any]) -> JSONResponse:
        """Process agent heartbeat"""
        try:
            statistics = heartbeat_data.get('statistics', {})
            
            await self.database_manager.update_agent_heartbeat(agent_id, statistics)
            
            return JSONResponse(content={
                'status': 'success',
                'message': 'Heartbeat received'
            })
            
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_agent(self, agent_id: str) -> JSONResponse:
        """Get agent information"""
        try:
            agent_info = await self.database_manager.get_agent_info(agent_id)
            
            if not agent_info:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            return JSONResponse(content={
                'status': 'success',
                'agent': agent_info.to_dict()
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get agent error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_pending_commands(self, agent_id: str) -> JSONResponse:
        """Get pending commands for agent"""
        try:
            # Get commands from command manager
            commands = await self.command_manager.get_pending_commands(agent_id)
            
            return JSONResponse(content={
                'status': 'success',
                'commands': commands,
                'agent_id': agent_id,
                'retrieved_at': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Get pending commands error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def receive_command_results(self, agent_id: str, result_data: Dict[str, Any]) -> JSONResponse:
        """Receive command execution results from agent"""
        try:
            command_id = result_data.get('command_id')
            if not command_id:
                raise HTTPException(status_code=400, detail="Missing command_id")
            
            # Process result through command manager
            success = await self.command_manager.receive_command_result(
                command_id, agent_id, result_data
            )
            
            if success:
                return JSONResponse(content={
                    'status': 'success',
                    'message': 'Command result processed',
                    'command_id': command_id,
                    'received_at': datetime.utcnow().isoformat()
                })
            else:
                raise HTTPException(status_code=500, detail="Failed to process command result")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Receive command results error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
