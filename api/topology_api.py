"""
Network Topology API for Attack Planning
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from core.topology.network_mapper import NetworkTopologyMapper
from core.integrations.attack_integration import AttackIntegration


logger = logging.getLogger(__name__)


class TopologyAPI:
    """Network topology API endpoints"""
    
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.topology_mapper = NetworkTopologyMapper(database_manager)
        self.attack_integration = AttackIntegration(database_manager, self.topology_mapper)
        
        self.router = APIRouter(prefix="/api/topology", tags=["topology"])
        
        # Add routes
        self.router.add_api_route("/network", self.get_network_topology, methods=["GET"])
        self.router.add_api_route("/attack-context", self.get_attack_context, methods=["GET"])
        self.router.add_api_route("/targets", self.get_attack_targets, methods=["GET"])
        self.router.add_api_route("/attack-plan", self.generate_attack_plan, methods=["POST"])
        self.router.add_api_route("/refresh", self.refresh_topology, methods=["POST"])
        self.router.add_api_route("/status", self.get_topology_status, methods=["GET"])
    
    async def get_network_topology(self, hours: int = Query(24, description="Hours of logs to analyze")) -> JSONResponse:
        """Get complete network topology"""
        try:
            topology = await self.topology_mapper.build_topology_from_logs(hours=hours)
            
            return JSONResponse(content={
                'status': 'success',
                'topology': topology.to_dict(),
                'metadata': {
                    'analysis_period_hours': hours,
                    'generated_at': topology.last_updated.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Get topology error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_attack_context(self, agent_id: Optional[str] = Query(None, description="Specific agent ID")) -> JSONResponse:
        """Get attack context for network topology"""
        try:
            if agent_id:
                # Get context for specific agent
                context = await self.topology_mapper.get_attack_context_for_agent(agent_id)
            else:
                # Get full attack context
                topology = await self.topology_mapper.build_topology_from_logs()
                context = await self.topology_mapper.export_topology_for_attack_planning()
            
            return JSONResponse(content={
                'status': 'success',
                'attack_context': context
            })
            
        except Exception as e:
            logger.error(f"Get attack context error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_attack_targets(self) -> JSONResponse:
        """Get prioritized attack targets"""
        try:
            targets = await self.attack_integration.get_attack_targets_by_priority()
            
            return JSONResponse(content={
                'status': 'success',
                'targets': targets,
                'summary': {
                    'critical_targets': len(targets.get('critical_targets', [])),
                    'high_value_targets': len(targets.get('high_value_targets', [])),
                    'lateral_movement_targets': len(targets.get('lateral_movement_targets', [])),
                    'persistence_targets': len(targets.get('persistence_targets', [])),
                    'data_targets': len(targets.get('data_targets', []))
                }
            })
            
        except Exception as e:
            logger.error(f"Get attack targets error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def generate_attack_plan(self, request_data: Dict[str, Any]) -> JSONResponse:
        """Generate network-aware attack plan"""
        try:
            attack_objective = request_data.get('objective', 'Network assessment')
            constraints = request_data.get('constraints', {})
            
            plan = await self.attack_integration.generate_network_aware_attack_plan(attack_objective)
            
            if plan.get('success'):
                return JSONResponse(content={
                    'status': 'success',
                    'attack_plan': plan['attack_plan'],
                    'topology_context': plan.get('topology_context', {}),
                    'target_analysis': plan.get('target_analysis', {})
                })
            else:
                raise HTTPException(status_code=500, detail=plan.get('error', 'Unknown error'))
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Generate attack plan error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def refresh_topology(self) -> JSONResponse:
        """Force refresh of network topology"""
        try:
            # Update attack agent context with latest topology
            result = await self.attack_integration.update_attack_agent_context()
            
            return JSONResponse(content={
                'status': 'success',
                'message': 'Network topology refreshed',
                'update_result': result
            })
            
        except Exception as e:
            logger.error(f"Refresh topology error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_topology_status(self) -> JSONResponse:
        """Get topology monitoring status"""
        try:
            # Get topology monitor status if available
            from ..server_manager import LogForwardingServer
            
            # This is a simplified status - in production you'd access the actual monitor
            status = {
                'monitoring_enabled': True,
                'last_update': datetime.utcnow().isoformat(),
                'topology_version': 1,
                'continuous_updates': True,
                'update_frequency': '30 seconds',
                'full_refresh_frequency': '5 minutes'
            }
            
            return JSONResponse(content={
                'status': 'success',
                'topology_monitoring': status
            })
            
        except Exception as e:
            logger.error(f"Get topology status error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
