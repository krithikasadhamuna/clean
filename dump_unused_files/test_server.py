#!/usr/bin/env python3
"""
Simple test server for local testing
"""

import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import sqlite3
import json
import uuid
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="CodeGrey Test Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://dev.codegrey.ai", "https://dev.codegrey.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db_path = "test_soc_database.db"

def init_database():
    """Initialize test database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                hostname TEXT,
                ip_address TEXT,
                platform TEXT,
                status TEXT DEFAULT 'offline',
                last_heartbeat TIMESTAMP,
                agent_type TEXT DEFAULT 'client_endpoint',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create log_entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_entries (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                source TEXT,
                timestamp TIMESTAMP,
                collected_at TIMESTAMP,
                processed_at TIMESTAMP,
                message TEXT,
                raw_data TEXT,
                level TEXT,
                parsed_data TEXT,
                enriched_data TEXT,
                event_id TEXT,
                event_type TEXT,
                process_info TEXT,
                network_info TEXT,
                attack_technique TEXT,
                attack_command TEXT,
                attack_result TEXT,
                threat_score REAL DEFAULT 0.0,
                threat_level TEXT DEFAULT 'benign',
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Test database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "CodeGrey Test Server"
    }

@app.post("/api/agents/register")
async def register_agent(agent_data: dict):
    """Register a new client agent"""
    try:
        agent_id = agent_data.get('agent_id', f"agent_{int(datetime.now().timestamp())}")
        hostname = agent_data.get('hostname', 'unknown')
        platform = agent_data.get('platform', 'unknown')
        
        # Store in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO agents (
                id, hostname, ip_address, platform, status, last_heartbeat, agent_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            agent_id,
            hostname,
            agent_data.get('ip_address', '127.0.0.1'),
            platform,
            'active',
            datetime.now().isoformat(),
            'client_endpoint'
        ))
        
        conn.commit()
        conn.close()
        
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

@app.post("/api/agents/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str, heartbeat_data: dict):
    """Handle agent heartbeat with network topology data"""
    try:
        # Update agent heartbeat
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE agents 
            SET status = 'active', last_heartbeat = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), agent_id))
        
        # Process network topology data if present
        network_topology = heartbeat_data.get('network_topology', {})
        if network_topology and network_topology.get('networkTopology'):
            logger.info(f"Received network topology from {agent_id}: {len(network_topology['networkTopology'])} hosts")
            
            # Store network topology data
            for host in network_topology['networkTopology']:
                try:
                    # Store each discovered host as a network node
                    host_data = (
                        f"{agent_id}_network_{host.get('ipAddress', 'unknown')}",
                        host.get('hostname', f"host-{host.get('ipAddress', 'unknown')}"),
                        host.get('ipAddress', 'unknown'),
                        host.get('platform', 'Unknown'),
                        'discovered',
                        datetime.now().isoformat(),
                        'network_node'
                    )
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO agents (
                            id, hostname, ip_address, platform, status, last_heartbeat, agent_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', host_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to store network host {host.get('ipAddress')}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Heartbeat received from agent: {agent_id}")
        return {"status": "success", "message": "Heartbeat received"}
        
    except Exception as e:
        logger.error(f"Heartbeat error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/logs/ingest")
async def ingest_logs(logs_data: dict):
    """Handle log ingestion from client agents"""
    try:
        # Process incoming logs
        agent_id = logs_data.get('agent_id', 'unknown')
        logs = logs_data.get('logs', [])
        
        logger.info(f"Received {len(logs)} logs from agent: {agent_id}")
        
        # Store logs in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Process each log entry
        for log_entry in logs:
            try:
                # Store log entry
                cursor.execute('''
                    INSERT INTO log_entries (
                        id, agent_id, source, timestamp, collected_at, processed_at,
                        message, raw_data, level, parsed_data, enriched_data,
                        event_id, event_type, process_info, network_info,
                        attack_technique, attack_command, attack_result,
                        threat_score, threat_level, tags, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    agent_id,
                    log_entry.get('source', 'unknown'),
                    log_entry.get('timestamp', datetime.now().isoformat()),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    log_entry.get('message', ''),
                    json.dumps(log_entry),
                    log_entry.get('level', 'info'),
                    None,  # parsed_data
                    None,  # enriched_data
                    log_entry.get('event_id'),
                    log_entry.get('event_type'),
                    None,  # process_info
                    None,  # network_info
                    None,  # attack_technique
                    None,  # attack_command
                    None,  # attack_result
                    0.0,   # threat_score
                    'benign',  # threat_level
                    None,  # tags
                    datetime.now().isoformat()
                ))
                
            except Exception as log_error:
                logger.warning(f"Failed to process log entry: {log_error}")
                continue
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Processed {len(logs)} logs",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id
        }
        
    except Exception as e:
        logger.error(f"Log ingestion error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/logs")
async def get_logs(limit: int = 100, offset: int = 0, agent_id: str = None):
    """Get logs from database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM log_entries"
        params = []
        
        if agent_id:
            query += " WHERE agent_id = ?"
            params.append(agent_id)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'agent_id': row[1],
                'source': row[2],
                'timestamp': row[3],
                'collected_at': row[4],
                'processed_at': row[5],
                'message': row[6],
                'raw_data': row[7],
                'level': row[8],
                'parsed_data': row[9],
                'enriched_data': row[10],
                'event_id': row[11],
                'event_type': row[12],
                'process_info': row[13],
                'network_info': row[14],
                'attack_technique': row[15],
                'attack_command': row[16],
                'attack_result': row[17],
                'threat_score': row[18],
                'threat_level': row[19],
                'tags': row[20],
                'created_at': row[21]
            })
        
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

@app.get("/api/agents")
async def get_agents():
    """Get all registered agents"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, hostname, ip_address, platform, status, last_heartbeat, agent_type
            FROM agents 
            ORDER BY last_heartbeat DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        agents = []
        for row in rows:
            agents.append({
                'id': row[0],
                'hostname': row[1],
                'ip_address': row[2],
                'platform': row[3],
                'status': row[4],
                'last_heartbeat': row[5],
                'agent_type': row[6]
            })
        
        return {
            "status": "success",
            "agents": agents,
            "total": len(agents)
        }
        
    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/soc/plan-attack")
async def plan_attack(attack_request: dict):
    """Plan attack scenario"""
    try:
        scenario_id = f"scenario_{int(time.time())}"
        
        # Simulate attack planning
        scenario = {
            "scenario_id": scenario_id,
            "name": attack_request.get("scenario", "Test Attack"),
            "target": attack_request.get("target", "localhost"),
            "objectives": attack_request.get("objectives", []),
            "constraints": attack_request.get("constraints", []),
            "techniques": attack_request.get("techniques", []),
            "status": "planned",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Attack scenario planned: {scenario_id}")
        
        return {
            "success": True,
            "scenario_id": scenario_id,
            "scenario": scenario,
            "message": "Attack scenario planned successfully"
        }
        
    except Exception as e:
        logger.error(f"Attack planning error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/soc/approve-attack")
async def approve_attack(approval_request: dict):
    """Approve or reject attack scenario"""
    try:
        scenario_id = approval_request.get("scenario_id")
        approved = approval_request.get("approved", False)
        
        if approved:
            logger.info(f"Attack scenario {scenario_id} approved")
            return {
                "success": True,
                "message": f"Attack scenario {scenario_id} approved and executed",
                "execution_id": f"exec_{int(time.time())}"
            }
        else:
            logger.info(f"Attack scenario {scenario_id} rejected")
            return {
                "success": True,
                "message": f"Attack scenario {scenario_id} rejected"
            }
        
    except Exception as e:
        logger.error(f"Attack approval error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/soc/pending-approvals")
async def get_pending_approvals():
    """Get pending attack approvals"""
    try:
        # Simulate pending approvals
        pending_approvals = [
            {
                "scenario_id": "scenario_123",
                "name": "Test Penetration Scenario",
                "target": "192.168.1.100",
                "status": "pending_approval",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        return {
            "success": True,
            "pending_approvals": pending_approvals,
            "total": len(pending_approvals)
        }
        
    except Exception as e:
        logger.error(f"Pending approvals error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/network-topology")
async def get_network_topology():
    """Get network topology data"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get network nodes from agents table
        cursor.execute("SELECT hostname, ip_address, platform, status, last_heartbeat FROM agents WHERE agent_type = 'network_node'")
        rows = cursor.fetchall()
        conn.close()
        
        nodes = []
        for row in rows:
            nodes.append({
                "hostname": row[0],
                "ipAddress": row[1],
                "platform": row[2],
                "status": row[3],
                "lastSeen": row[4]
            })
        
        return {
            "status": "success",
            "networkTopology": nodes,
            "totalNodes": len(nodes)
        }
        
    except Exception as e:
        logger.error(f"Network topology error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/logs/ingest")
async def ingest_logs(log_data: dict):
    """Ingest logs from client agents"""
    try:
        agent_id = log_data.get('agent_id', 'unknown')
        logs = log_data.get('logs', [])
        
        logger.info(f"Received {len(logs)} logs from agent: {agent_id}")
        
        return {
            "status": "success",
            "message": f"Processed {len(logs)} logs",
            "agent_id": agent_id
        }
        
    except Exception as e:
        logger.error(f"Log ingestion error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/agents/{agent_id}/commands")
async def get_agent_commands(agent_id: str):
    """Get pending commands for client agent"""
    return {
        "status": "success",
        "commands": [],
        "agent_id": agent_id
    }

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Start server
    logger.info("Starting CodeGrey Test Server on http://127.0.0.1:8081")
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="info")
