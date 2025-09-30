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
        
        try:
            from agents.langchain_orchestrator import soc_orchestrator
            from agents.detection_agent.langchain_detection_agent import langchain_detection_agent  
            from agents.attack_agent.langchain_attack_agent import phantomstrike_ai
            
            self.soc_orchestrator = soc_orchestrator
            self.langchain_detection_agent = langchain_detection_agent
            self.phantomstrike_ai = phantomstrike_ai
            self.agents_available = True
            
        except ImportError as e:
            logger.warning(f"LangChain agents not available for LangServe: {e}")
        
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
    
    def _add_langserve_routes(self):
        """Add LangServe routes for agents"""
        if not self.agents_available:
            logger.warning("LangChain agents not available, skipping LangServe routes")
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
                if not self.agents_available:
                    return {
                        "status": "healthy",
                        "version": "2.0.0",
                        "agents": "unavailable",
                        "langchain_integration": "disabled"
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
                    "langchain_integration": "active" if self.agents_available else "disabled"
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
                    return {"success": False, "error": "SOC orchestrator not available"}
                
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
                approvals = await self.phantomstrike_ai.get_pending_approvals()
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
        try:
            # Simple hardcoded routes that work
            
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
                    
                    # Get IP address from network interfaces
                    ip_address = '127.0.0.1'
                    network_interfaces = system_info.get('network_interfaces', [])
                    if network_interfaces:
                        # Get first non-loopback IP
                        for interface in network_interfaces:
                            if interface.get('ip') and not interface.get('ip').startswith('127.'):
                                ip_address = interface.get('ip')
                                break
                    
                    platform_info = agent_data.get('platform', system_info.get('os', platform.system()))
                    
                    # Store agent info in database
                    db_manager = DatabaseManager(db_path="soc_database.db", enable_elasticsearch=False, enable_influxdb=False)
                    
                    # Register agent in database
                    agent_data = {
                        'agent_id': agent_id,
                        'hostname': hostname,
                        'ip_address': ip_address,
                        'platform': platform_info,
                        'status': 'active',
                        'last_heartbeat': datetime.now(),
                        'agent_type': 'client_endpoint'
                    }
                    
                    # Store in agents table
                    await db_manager.store_agent_info(agent_data)
                    
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
                    db_manager = DatabaseManager(db_path="soc_database.db", enable_elasticsearch=False, enable_influxdb=False)
                    
                    # Update agent status
                    agent_data = {
                        'agent_id': agent_id,
                        'status': 'active',
                        'last_heartbeat': datetime.now()
                    }
                    await db_manager.store_agent_info(agent_data)
                    
                    # Process network topology data if present
                    network_topology = heartbeat_data.get('network_topology', {})
                    if network_topology and network_topology.get('networkTopology'):
                        logger.info(f"Received network topology from {agent_id}: {len(network_topology['networkTopology'])} hosts")
                        
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
                                    'last_heartbeat': datetime.now(),
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
                    # For now, return empty commands list
                    # In production, this would check database for pending commands
                    return {
                        "status": "success",
                        "commands": [],
                        "agent_id": agent_id
                    }
                except Exception as e:
                    logger.error(f"Commands error for {agent_id}: {e}")
                    return {"status": "error", "message": str(e)}
            
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
                                'raw_data': json.dumps(log_entry)
                            }
                            
                            # Store log entry and get the log ID
                            log_id = await db_manager.store_log_entry_with_id(log_data)
                            
                            # ANALYZE ALL LOGS - not just based on level
                            threat_analysis = await self._analyze_threat_dynamically(log_entry, agent_id)
                            
                            if threat_analysis and threat_analysis.get('threat_score', 0) > 0.3:
                                threats_detected += 1
                                logger.info(f"THREAT DETECTED: {threat_analysis.get('threat_type')} from {agent_id} - Score: {threat_analysis.get('threat_score'):.2f}")
                                
                                # Store detection result
                                detection_result = {
                                    'log_entry_id': str(log_id),
                                    'threat_detected': True,
                                    'confidence_score': threat_analysis.get('threat_score'),
                                    'threat_type': threat_analysis.get('threat_type'),
                                    'severity': self._calculate_severity(threat_analysis.get('threat_score')),
                                    'indicators': threat_analysis.get('indicators', []),
                                    'agent_id': agent_id,
                                    'log_message': log_entry.get('message', ''),
                                    'log_source': log_entry.get('source', ''),
                                    'detected_at': datetime.now().isoformat()
                                }
                                
                                # Store in detection_results table
                                await self._store_detection_result(detection_result)
                            
                            # Extract network information for topology
                            if 'ip_address' in log_entry or 'hostname' in log_entry:
                                network_info = {
                                    'agent_id': agent_id,
                                    'hostname': log_entry.get('hostname', 'unknown'),
                                    'ip_address': log_entry.get('ip_address', '127.0.0.1'),
                                    'platform': log_entry.get('platform', 'unknown'),
                                    'services': log_entry.get('services', []),
                                    'last_activity': datetime.now()
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
                        "logs": logs,
                        "total": len(logs),
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
                        'agents': [
                            {
                                'id': 'phantomstrike_ai',
                                'name': 'PhantomStrike AI',
                                'type': 'attack',
                                'status': 'inactive',
                                'location': 'Client Network',
                                'lastActivity': 'Ready for deployment',
                                'capabilities': ['Attack Planning', 'Scenario Generation', 'Red Team Operations'],
                                'platform': 'Container Agent (Standby)'
                            },
                            {
                                'id': 'phantomstrike_web_ai',
                                'name': 'PhantomStrike Web AI',
                                'type': 'attack',
                                'status': 'inactive',
                                'location': 'Client Network',
                                'lastActivity': 'Ready for deployment',
                                'capabilities': ['Web Vulnerability Scanning', 'SQL Injection', 'XSS Testing'],
                                'platform': 'Container Agent (Standby)'
                            },
                            {
                                'id': 'phantomstrike_network_ai',
                                'name': 'PhantomStrike Network AI',
                                'type': 'attack',
                                'status': 'inactive',
                                'location': 'Client Network',
                                'lastActivity': 'Ready for deployment',
                                'capabilities': ['Network Scanning', 'Port Discovery', 'Service Enumeration'],
                                'platform': 'Container Agent (Standby)'
                            },
                            {
                                'id': 'phantomstrike_phishing_ai',
                                'name': 'PhantomStrike Phishing AI',
                                'type': 'attack',
                                'status': 'inactive',
                                'location': 'Client Network',
                                'lastActivity': 'Ready for deployment',
                                'capabilities': ['Email Campaigns', 'Credential Harvesting', 'Social Engineering'],
                                'platform': 'Container Agent (Standby)'
                            }
                        ]
                    }
                except Exception as e:
                    logger.error(f"Attack agents error: {e}")
                    return {'status': 'error', 'message': str(e), 'agents': []}
            
            logger.info("Simple frontend API routes added successfully")
            logger.info("Client agent API routes added successfully")
            logger.info("Detection results API added successfully")
            
        except Exception as e:
            logger.error(f"Failed to add frontend API routes: {e}")
    
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
                from log_forwarding.server.storage.database_manager import DatabaseManager
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
    
    async def _get_attack_agents_from_clients(self) -> Dict[str, Any]:
        """Query client agents for their running attack agents"""
        try:
            from log_forwarding.server.storage.database_manager import DatabaseManager
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
                        'location': 'Client Network',
                        'lastActivity': 'Ready for deployment',
                        'capabilities': ['Attack Planning', 'Scenario Generation', 'Red Team Operations'],
                        'platform': 'Container Agent (Standby)'
                    },
                    {
                        'id': 'phantomstrike_web_ai',
                        'name': 'PhantomStrike Web AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'location': 'Client Network',
                        'lastActivity': 'Ready for deployment',
                        'capabilities': ['Web Vulnerability Scanning', 'SQL Injection', 'XSS Testing'],
                        'platform': 'Container Agent (Standby)'
                    },
                    {
                        'id': 'phantomstrike_network_ai',
                        'name': 'PhantomStrike Network AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'location': 'Client Network',
                        'lastActivity': 'Ready for deployment',
                        'capabilities': ['Network Scanning', 'Port Discovery', 'Service Enumeration'],
                        'platform': 'Container Agent (Standby)'
                    },
                    {
                        'id': 'phantomstrike_phishing_ai',
                        'name': 'PhantomStrike Phishing AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'location': 'Client Network',
                        'lastActivity': 'Ready for deployment',
                        'capabilities': ['Email Campaigns', 'Credential Harvesting', 'Social Engineering'],
                        'platform': 'Container Agent (Standby)'
                    }
                ]
            
            return {
                'status': 'success',
                'agents': all_agents
            }
            
        except Exception as e:
            logger.error(f"Error getting attack agents from clients: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'agents': []
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
                        'source_machine': agent_id,
                        'reasoning': f"Real-time analysis found {len(indicators)} threat indicators",
                        'indicators': indicators
                    }),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
            
            return {
                'threat_detected': threat_detected,
                'threat_score': threat_score,
                'threat_type': threat_type,
                'severity': severity,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"Real-time detection error: {e}")
            return None
    
    def _get_adaptive_thresholds(self, source: str, level: str) -> Dict[str, float]:
        """Get adaptive detection thresholds based on environment and context"""
        
        # Base thresholds
        base_thresholds = {
            'critical': 1.0,
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3,
            'detection_threshold': 0.3
        }
        
        # Adjust thresholds based on source criticality
        if 'security' in source:
            # Security logs are more critical - lower thresholds
            return {
                'critical': 0.8,
                'high': 0.6,
                'medium': 0.4,
                'low': 0.2,
                'detection_threshold': 0.2
            }
        elif 'system' in source:
            # System logs are important - slightly lower thresholds
            return {
                'critical': 0.9,
                'high': 0.65,
                'medium': 0.45,
                'low': 0.25,
                'detection_threshold': 0.25
            }
        elif 'process' in source:
            # Process logs can be noisy - slightly higher thresholds
            return {
                'critical': 1.1,
                'high': 0.75,
                'medium': 0.55,
                'low': 0.35,
                'detection_threshold': 0.35
            }
        elif level in ['critical', 'error']:
            # High-level logs get lower thresholds regardless of source
            return {
                'critical': 0.7,
                'high': 0.5,
                'medium': 0.3,
                'low': 0.2,
                'detection_threshold': 0.2
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
                    indicators.append(f"Attack tool detected: {tool}")
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
                    threat_type = 'reconnaissance'
            
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
                    threat_type = 'active_attack'
            
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
                    threat_type = 'network_attack'
            
            # 5. CONTAINER/ATTACK CONTEXT
            if log_entry.get('container_context') or 'attackcontainer' in source:
                threat_score += 0.5
                indicators.append("Container attack context")
                threat_type = 'container_attack'
            
            # 6. SYSTEM COMPROMISE INDICATORS
            compromise_indicators = [
                'malware', 'virus', 'trojan', 'ransomware',
                'keylogger', 'spyware', 'adware', 'botnet',
                'c2 server', 'command and control', 'exfiltration'
            ]
            
            for indicator in compromise_indicators:
                if indicator in message:
                    threat_score += 0.9
                    indicators.append(f"System compromise: {indicator}")
                    threat_type = 'system_compromise'
            
            # 7. FAILED AUTHENTICATION (even without ERROR level)
            auth_failures = [
                'failed login', 'authentication failed', 'invalid credentials',
                'access denied', 'unauthorized access', 'permission denied',
                'login attempt', 'brute force'
            ]
            
            for failure in auth_failures:
                if failure in message:
                    threat_score += 0.5
                    indicators.append(f"Authentication issue: {failure}")
                    threat_type = 'authentication_attack'
            
            # Cap threat score at 1.0
            threat_score = min(threat_score, 1.0)
            
            return {
                'threat_score': threat_score,
                'threat_type': threat_type,
                'indicators': indicators,
                'analysis_method': 'content_based_detection'
            }
            
        except Exception as e:
            logger.error(f"Content-based threat analysis failed: {e}")
            return {
                'threat_score': 0.0,
                'threat_type': 'benign',
                'indicators': [],
                'analysis_method': 'fallback'
            }
    
    async def _get_attack_agents_from_clients(self) -> Dict[str, Any]:
        """Query client agents for their running attack agents"""
        try:
            # Return default PhantomStrike agents since client querying is complex
            return {
                'status': 'success',
                'agents': [
                    {
                        'id': 'phantomstrike_ai',
                        'name': 'PhantomStrike AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'location': 'Client Network',
                        'lastActivity': 'Ready for deployment',
                        'capabilities': ['Attack Planning', 'Scenario Generation', 'Red Team Operations'],
                        'platform': 'Container Agent (Standby)'
                    },
                    {
                        'id': 'phantomstrike_web_ai',
                        'name': 'PhantomStrike Web AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'location': 'Client Network',
                        'lastActivity': 'Ready for deployment',
                        'capabilities': ['Web Vulnerability Scanning', 'SQL Injection', 'XSS Testing'],
                        'platform': 'Container Agent (Standby)'
                    },
                    {
                        'id': 'phantomstrike_network_ai',
                        'name': 'PhantomStrike Network AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'location': 'Client Network',
                        'lastActivity': 'Ready for deployment',
                        'capabilities': ['Network Scanning', 'Port Discovery', 'Service Enumeration'],
                        'platform': 'Container Agent (Standby)'
                    },
                    {
                        'id': 'phantomstrike_phishing_ai',
                        'name': 'PhantomStrike Phishing AI',
                        'type': 'attack',
                        'status': 'inactive',
                        'location': 'Client Network',
                        'lastActivity': 'Ready for deployment',
                        'capabilities': ['Email Campaigns', 'Credential Harvesting', 'Social Engineering'],
                        'platform': 'Container Agent (Standby)'
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting attack agents from clients: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'agents': []
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
                indicators.append(f"Analyzed from {source} logs")
                indicators.append(f"Environment-based detection")
            
            return indicators[:5]  # Limit to top 5 indicators
            
        except Exception as e:
            logger.debug(f"Dynamic indicator generation failed: {e}")
            return ['Dynamic analysis indicator']
    
    def get_app(self) -> FastAPI:
        """Get FastAPI application"""
        return self.app


# Create API instance
soc_api = SOCPlatformAPI()
