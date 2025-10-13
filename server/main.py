#!/usr/bin/env python3
"""
AI SOC Platform - Main Entry Point
Fully LangChain-based AI SOC Platform with PhantomStrike AI
"""

import asyncio
import logging
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.utils import setup_logging
from core.server_manager import LogForwardingServer
# from core.client.client_agent import LogForwardingClient  # Not needed for server-only mode


async def run_server(args):
    """Run SOC server"""
    setup_logging(args.log_level, args.log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting AI SOC Platform Server (LangChain-based)")
    
    server = LogForwardingServer(args.config)
    
    if args.host:
        server.host = args.host
    if args.port:
        server.port = args.port
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        await server.stop()


async def run_client(args):
    """Run SOC client"""
    setup_logging(args.log_level, args.log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting AI SOC Platform Client (LangChain-based)")
    
    client = LogForwardingClient(args.config)
    
    try:
        await client.start()
    except KeyboardInterrupt:
        logger.info("Client stopped by user")
    finally:
        await client.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI SOC Platform - LangChain Edition")
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Server subcommand
    server_parser = subparsers.add_parser('server', help='Run SOC server')
    server_parser.add_argument('--config', '-c', help='Configuration file path')
    server_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    server_parser.add_argument('--port', '-p', type=int, default=8080, help='Port to bind to')
    server_parser.add_argument('--log-level', '-l', default='INFO', 
                              choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                              help='Log level')
    server_parser.add_argument('--log-file', help='Log file path')
    
    # Client subcommand
    client_parser = subparsers.add_parser('client', help='Run SOC client')
    client_parser.add_argument('--config', '-c', help='Configuration file path')
    client_parser.add_argument('--log-level', '-l', default='INFO',
                              choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                              help='Log level')
    client_parser.add_argument('--log-file', help='Log file path')
    
    args = parser.parse_args()
    
    if args.mode == 'server':
        asyncio.run(run_server(args))
    elif args.mode == 'client':
        asyncio.run(run_client(args))
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python main.py server --host 0.0.0.0 --port 8080")
        print("  python main.py client --config config/client_config.yaml")


if __name__ == "__main__":
    main()
