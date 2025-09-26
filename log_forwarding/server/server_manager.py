"""
Main log forwarding server manager
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..shared.config import config
from ..shared.utils import setup_logging

from .ingestion.log_ingester import LogIngester
from .storage.database_manager import DatabaseManager
from .api.log_api import LogAPI
from .api.agent_api import AgentAPI


logger = logging.getLogger(__name__)


class LogForwardingServer:
    """Main log forwarding server"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Load configuration
        if config_file:
            config.server_config_file = config_file
        
        self.server_config = config.load_server_config()
        
        # Server settings
        self.host = self.server_config.get('server', {}).get('host', '0.0.0.0')
        self.port = self.server_config.get('server', {}).get('port', 8080)
        self.workers = self.server_config.get('server', {}).get('workers', 1)
        
        # Initialize components
        self.database_manager = self._initialize_database()
        self.detection_engine = self._initialize_detection_engine()
        self.topology_monitor = self._initialize_topology_monitor()
        self.log_ingester = LogIngester(self.database_manager, self.detection_engine, self.topology_monitor)
        
        # Initialize LangServe API app
        self.app = self._create_langserve_app()
        
        # State
        self.running = False
    
    def _initialize_database(self) -> DatabaseManager:
        """Initialize database manager"""
        db_config = self.server_config.get('database', {})
        
        return DatabaseManager(
            db_path=db_config.get('sqlite_path', 'soc_database.db'),
            enable_elasticsearch=db_config.get('elasticsearch', {}).get('enabled', False),
            enable_influxdb=db_config.get('influxdb', {}).get('enabled', False)
        )
    
    def _initialize_detection_engine(self):
        """Initialize detection engine integration"""
        try:
            # Import your existing detection agents
            from ...agents.detection_agent.ai_enhanced_detector import AIEnhancedThreatDetector
            
            detection_config = self.server_config.get('detection', {})
            
            if detection_config.get('real_time_enabled', True):
                return AIEnhancedThreatDetector()
            
        except ImportError as e:
            logger.warning(f"Detection engine not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize detection engine: {e}")
        
        return None
    
    def _initialize_topology_monitor(self):
        """Initialize continuous topology monitor"""
        try:
            from .topology.network_mapper import NetworkTopologyMapper
            from .topology.continuous_topology_monitor import ContinuousTopologyMonitor
            
            topology_config = self.server_config.get('topology', {})
            
            if topology_config.get('continuous_monitoring', True):
                topology_mapper = NetworkTopologyMapper(self.database_manager)
                return ContinuousTopologyMonitor(self.database_manager, topology_mapper)
            
        except ImportError as e:
            logger.warning(f"Topology monitor not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize topology monitor: {e}")
        
        return None
    
    def _create_langserve_app(self) -> FastAPI:
        """Create LangServe-based application"""
        try:
            from .langserve_api import soc_api
            app = soc_api.get_app()
            
            logger.info("LangServe API initialized successfully")
            return app
            
        except ImportError as e:
            logger.warning(f"LangServe not available, falling back to FastAPI: {e}")
            return self._create_fallback_fastapi_app()
    
    def _create_fallback_fastapi_app(self) -> FastAPI:
        """Create fallback FastAPI application"""
        app = FastAPI(
            title="AI SOC Platform - Fallback API",
            description="Fallback API when LangServe unavailable",
            version="1.0.0"
        )
        
        # Add CORS middleware for frontend development
        app.add_middleware(
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
        
        # Initialize basic APIs
        try:
            from .api.log_api import LogAPI
            from .api.agent_api import AgentAPI
            from .api.dynamic_frontend_api import DynamicFrontendAPI
            
            log_api = LogAPI(self.log_ingester, self.database_manager)
            agent_api = AgentAPI(self.database_manager)
            frontend_api = DynamicFrontendAPI(self.database_manager)
            
            app.include_router(log_api.router)
            app.include_router(agent_api.router)
            app.include_router(frontend_api.router)
            
        except ImportError as e:
            logger.error(f"Failed to initialize fallback APIs: {e}")
        
        # Add health check endpoint
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "version": "1.0.0",
                "api_type": "fallback_fastapi",
                "components": {
                    "database": "operational",
                    "log_ingester": "operational" if self.log_ingester.running else "stopped",
                    "detection_engine": "operational" if self.detection_engine else "disabled"
                }
            }
        
        # Add startup/shutdown events
        @app.on_event("startup")
        async def startup_event():
            await self.start_background_tasks()
        
        @app.on_event("shutdown")
        async def shutdown_event():
            await self.stop_background_tasks()
        
        return app
    
    async def start_background_tasks(self):
        """Start background tasks"""
        try:
            # Start log ingestion system
            asyncio.create_task(self.log_ingester.start())
            
            # Start topology monitoring if available
            if self.topology_monitor:
                asyncio.create_task(self.topology_monitor.start())
                logger.info("Background tasks started (including topology monitoring)")
            else:
                logger.info("Background tasks started (topology monitoring disabled)")
                
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
    
    async def stop_background_tasks(self):
        """Stop background tasks"""
        try:
            await self.log_ingester.stop()
            
            if self.topology_monitor:
                await self.topology_monitor.stop()
                
            logger.info("Background tasks stopped")
        except Exception as e:
            logger.error(f"Failed to stop background tasks: {e}")
    
    async def start(self):
        """Start the server"""
        logger.info(f"Starting AI SOC Log Forwarding Server on {self.host}:{self.port}")
        self.running = True
        
        # Configure uvicorn
        uvicorn_config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            workers=self.workers,
            log_level=self.server_config.get('server', {}).get('log_level', 'info').lower(),
            access_log=True
        )
        
        server = uvicorn.Server(uvicorn_config)
        
        try:
            await server.serve()
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.running = False
    
    async def stop(self):
        """Stop the server"""
        logger.info("Stopping AI SOC Log Forwarding Server")
        self.running = False
        await self.stop_background_tasks()


def setup_signal_handlers(server: LogForwardingServer):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(server.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI SOC Log Forwarding Server")
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--log-level', '-l', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Log level')
    parser.add_argument('--log-file', help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Create and start server
    server = LogForwardingServer(args.config)
    
    # Override host/port if specified
    if args.host != '0.0.0.0':
        server.host = args.host
    if args.port != 8080:
        server.port = args.port
    
    setup_signal_handlers(server)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
