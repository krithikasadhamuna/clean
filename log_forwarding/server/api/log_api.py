"""
Log ingestion API endpoints
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from ...shared.utils import decompress_data


logger = logging.getLogger(__name__)


class LogAPI:
    """Log ingestion API endpoints"""
    
    def __init__(self, log_ingester, database_manager):
        self.log_ingester = log_ingester
        self.database_manager = database_manager
        self.router = APIRouter(prefix="/api/logs", tags=["logs"])
        
        # Add routes
        self.router.add_api_route("/ingest", self.ingest_logs, methods=["POST"])
        self.router.add_api_route("/query", self.query_logs, methods=["GET"])
        self.router.add_api_route("/statistics", self.get_statistics, methods=["GET"])
    
    async def ingest_logs(self, request: Request, 
                         content_encoding: str = Header(None),
                         x_batch_size: int = Header(None)) -> JSONResponse:
        """Ingest log batch from client"""
        try:
            # Get request body
            body = await request.body()
            
            if not body:
                raise HTTPException(status_code=400, detail="Empty request body")
            
            # Process the batch
            result = await self.log_ingester.ingest_batch(
                batch_data=body,
                content_encoding=content_encoding,
                batch_size=x_batch_size
            )
            
            if result['status'] == 'error':
                raise HTTPException(status_code=400, detail=result['message'])
            
            return JSONResponse(content=result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Log ingestion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def query_logs(self, agent_id: str = None, hours: int = 24, 
                        limit: int = 1000) -> JSONResponse:
        """Query recent logs"""
        try:
            logs = await self.database_manager.get_recent_logs(
                agent_id=agent_id, 
                hours=hours, 
                limit=limit
            )
            
            return JSONResponse(content={
                'status': 'success',
                'logs': logs,
                'count': len(logs)
            })
            
        except Exception as e:
            logger.error(f"Log query error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_statistics(self) -> JSONResponse:
        """Get log ingestion statistics"""
        try:
            stats = self.log_ingester.get_statistics()
            return JSONResponse(content=stats)
            
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
