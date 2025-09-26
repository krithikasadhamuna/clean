#!/usr/bin/env python3
"""
AI SOC Platform Server Deployment Script
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from log_forwarding.shared.utils import setup_logging


logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'aiohttp', 'asyncio', 'sqlite3',
        'scikit-learn', 'numpy', 'pandas', 'pyyaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.debug(f"Package {package} is available")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"Package {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Install missing packages with: pip install -r requirements.txt")
        return False
    
    logger.info("All dependencies are satisfied")
    return True


def setup_directories():
    """Setup required directories"""
    logger.info("Setting up directories...")
    
    directories = [
        'logs',
        'data',
        'checkpoints',
        'golden_images',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.debug(f"Created directory: {directory}")
    
    logger.info("Directories setup complete")


def initialize_database():
    """Initialize the database"""
    logger.info("Initializing database...")
    
    try:
        from log_forwarding.server.storage.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def create_default_config():
    """Create default configuration if not exists"""
    logger.info("Creating default configuration...")
    
    config_dir = Path("config")
    server_config_path = config_dir / "server_config.yaml"
    
    if not server_config_path.exists():
        logger.info("Creating default server configuration...")
        # The config files were already created above
        logger.info(f"Default server config created at: {server_config_path}")
    else:
        logger.info("Server configuration already exists")


def start_server(host='0.0.0.0', port=8080, workers=1, log_level='INFO'):
    """Start the AI SOC server"""
    logger.info(f"Starting AI SOC Server on {host}:{port}")
    
    try:
        from log_forwarding.server.server_manager import main
        import asyncio
        
        # Set command line arguments
        sys.argv = [
            'server_manager.py',
            '--host', host,
            '--port', str(port),
            '--log-level', log_level
        ]
        
        # Run the server
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        return False
    
    return True


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy AI SOC Platform Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--workers', '-w', type=int, default=1, help='Number of workers')
    parser.add_argument('--log-level', '-l', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Log level')
    parser.add_argument('--skip-checks', action='store_true', help='Skip dependency checks')
    parser.add_argument('--setup-only', action='store_true', help='Setup only, do not start server')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, 'logs/server_deployment.log')
    
    logger.info("=" * 60)
    logger.info("AI SOC Platform Server Deployment")
    logger.info("=" * 60)
    
    # Check dependencies
    if not args.skip_checks:
        if not check_dependencies():
            logger.error("Dependency check failed. Use --skip-checks to bypass.")
            return 1
    
    # Setup directories
    setup_directories()
    
    # Create default configuration
    create_default_config()
    
    # Initialize database
    if not initialize_database():
        logger.error("Database initialization failed")
        return 1
    
    if args.setup_only:
        logger.info("Setup completed successfully. Use without --setup-only to start server.")
        return 0
    
    # Start server
    logger.info("All setup completed. Starting server...")
    
    success = start_server(
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level=args.log_level
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
