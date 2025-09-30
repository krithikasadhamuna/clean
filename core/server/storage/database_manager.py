"""
Database management for log storage and retrieval
"""

import asyncio
import logging
import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from shared.models import LogEntry, LogBatch, AgentInfo, DetectionResult


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for log storage"""
    
    def __init__(self, db_path: str = "soc_database.db", 
                 enable_elasticsearch: bool = False,
                 enable_influxdb: bool = False):
        self.db_path = db_path
        self.enable_elasticsearch = enable_elasticsearch
        self.enable_influxdb = enable_influxdb
        
        # Database connections
        self._db_connection = None
        self._elasticsearch_client = None
        self._influxdb_client = None
        
        # Initialize databases
        self._initialize_sqlite()
        
        if enable_elasticsearch:
            self._initialize_elasticsearch()
        
        if enable_influxdb:
            self._initialize_influxdb()
    
    def _initialize_sqlite(self) -> None:
        """Initialize SQLite database with required tables"""
        try:
            # Ensure database directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create agents table (extend existing if needed)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    hostname TEXT,
                    ip_address TEXT,
                    platform TEXT,
                    os_version TEXT,
                    agent_version TEXT,
                    status TEXT DEFAULT 'offline',
                    last_heartbeat TIMESTAMP,
                    last_log_sent TIMESTAMP,
                    capabilities TEXT,  -- JSON array
                    log_sources TEXT,   -- JSON array
                    configuration TEXT, -- JSON object
                    security_zone TEXT DEFAULT 'internal',
                    importance TEXT DEFAULT 'medium',
                    logs_sent_count INTEGER DEFAULT 0,
                    bytes_sent INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    parsed_data TEXT,    -- JSON object
                    enriched_data TEXT,  -- JSON object
                    event_id TEXT,
                    event_type TEXT,
                    process_info TEXT,   -- JSON object
                    network_info TEXT,   -- JSON object
                    attack_technique TEXT,
                    attack_command TEXT,
                    attack_result TEXT,
                    threat_score REAL DEFAULT 0.0,
                    threat_level TEXT DEFAULT 'benign',
                    tags TEXT,           -- JSON array
                    metadata TEXT,       -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # Create detection_results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detection_results (
                    id TEXT PRIMARY KEY,
                    log_entry_id TEXT,
                    threat_detected BOOLEAN DEFAULT FALSE,
                    confidence_score REAL DEFAULT 0.0,
                    threat_type TEXT,
                    severity TEXT DEFAULT 'low',
                    ml_results TEXT,     -- JSON object
                    ai_analysis TEXT,    -- JSON object
                    rule_matches TEXT,   -- JSON array
                    mitre_techniques TEXT, -- JSON array
                    tactics TEXT,        -- JSON array
                    analyst_notes TEXT,
                    false_positive BOOLEAN DEFAULT FALSE,
                    verified BOOLEAN DEFAULT FALSE,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (log_entry_id) REFERENCES log_entries (id)
                )
            ''')
            
            # Create log_batches table for tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS log_batches (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    batch_size INTEGER,
                    compressed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_entries_agent_id ON log_entries (agent_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_entries_timestamp ON log_entries (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_entries_level ON log_entries (level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_entries_source ON log_entries (source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_entries_threat_score ON log_entries (threat_score)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detection_results_threat_detected ON detection_results (threat_detected)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detection_results_severity ON detection_results (severity)')
            
            conn.commit()
            conn.close()
            
            logger.info("SQLite database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            raise
    
    def _initialize_elasticsearch(self) -> None:
        """Initialize Elasticsearch connection"""
        try:
            from elasticsearch import AsyncElasticsearch
            
            self._elasticsearch_client = AsyncElasticsearch([
                {'host': 'localhost', 'port': 9200}
            ])
            
            logger.info("Elasticsearch client initialized")
            
        except ImportError:
            logger.warning("Elasticsearch not available. Install with: pip install elasticsearch")
            self.enable_elasticsearch = False
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch: {e}")
            self.enable_elasticsearch = False
    
    def _initialize_influxdb(self) -> None:
        """Initialize InfluxDB connection"""
        try:
            from influxdb_client import InfluxDBClient
            from influxdb_client.client.write_api import SYNCHRONOUS
            
            self._influxdb_client = InfluxDBClient(
                url="http://localhost:8086",
                token="your-token",  # In production, use proper token
                org="ai-soc"
            )
            
            logger.info("InfluxDB client initialized")
            
        except ImportError:
            logger.warning("InfluxDB not available. Install with: pip install influxdb-client")
            self.enable_influxdb = False
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB: {e}")
            self.enable_influxdb = False
    
    async def store_log_batch(self, log_batch: LogBatch) -> None:
        """Store a batch of logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store batch metadata
            cursor.execute('''
                INSERT OR REPLACE INTO log_batches 
                (id, agent_id, batch_size, compressed, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                log_batch.id,
                log_batch.agent_id,
                log_batch.batch_size,
                log_batch.compressed,
                log_batch.created_at.isoformat()
            ))
            
            # Store individual log entries
            for log_entry in log_batch.logs:
                await self._store_log_entry(cursor, log_entry)
            
            conn.commit()
            conn.close()
            
            # Store in Elasticsearch if enabled
            if self.enable_elasticsearch and self._elasticsearch_client:
                await self._store_logs_elasticsearch(log_batch.logs)
            
            # Store metrics in InfluxDB if enabled
            if self.enable_influxdb and self._influxdb_client:
                await self._store_logs_influxdb(log_batch.logs)
            
            logger.debug(f"Stored log batch {log_batch.id} with {log_batch.batch_size} entries")
            
        except Exception as e:
            logger.error(f"Failed to store log batch: {e}")
            raise
    
    async def _store_log_entry(self, cursor, log_entry: LogEntry) -> None:
        """Store individual log entry"""
        cursor.execute('''
            INSERT OR REPLACE INTO log_entries (
                id, agent_id, source, timestamp, collected_at, processed_at,
                message, raw_data, level, parsed_data, enriched_data,
                event_id, event_type, process_info, network_info,
                attack_technique, attack_command, attack_result,
                threat_score, threat_level, tags, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_entry.id,
            log_entry.agent_id,
            log_entry.source.value,
            log_entry.timestamp.isoformat(),
            log_entry.collected_at.isoformat(),
            log_entry.processed_at.isoformat() if log_entry.processed_at else None,
            log_entry.message,
            log_entry.raw_data,
            log_entry.level.value,
            json.dumps(log_entry.parsed_data),
            json.dumps(log_entry.enriched_data),
            log_entry.event_id,
            log_entry.event_type,
            json.dumps(log_entry.process_info),
            json.dumps(log_entry.network_info),
            log_entry.attack_technique,
            log_entry.attack_command,
            log_entry.attack_result,
            log_entry.threat_score,
            log_entry.threat_level.value,
            json.dumps(log_entry.tags),
            json.dumps(log_entry.metadata)
        ))
    
    async def _store_logs_elasticsearch(self, log_entries: List[LogEntry]) -> None:
        """Store logs in Elasticsearch for full-text search"""
        try:
            if not self._elasticsearch_client:
                return
            
            # Prepare bulk insert
            actions = []
            for log_entry in log_entries:
                doc = {
                    'timestamp': log_entry.timestamp.isoformat(),
                    'agent_id': log_entry.agent_id,
                    'source': log_entry.source.value,
                    'level': log_entry.level.value,
                    'message': log_entry.message,
                    'event_type': log_entry.event_type,
                    'tags': log_entry.tags,
                    'threat_score': log_entry.threat_score,
                    'threat_level': log_entry.threat_level.value,
                    **log_entry.parsed_data,
                    **log_entry.enriched_data
                }
                
                action = {
                    '_index': f'ai-soc-logs-{datetime.utcnow().strftime("%Y-%m")}',
                    '_id': log_entry.id,
                    '_source': doc
                }
                actions.append(action)
            
            # Bulk insert
            from elasticsearch.helpers import async_bulk
            await async_bulk(self._elasticsearch_client, actions)
            
        except Exception as e:
            logger.error(f"Failed to store logs in Elasticsearch: {e}")
    
    async def _store_logs_influxdb(self, log_entries: List[LogEntry]) -> None:
        """Store log metrics in InfluxDB"""
        try:
            if not self._influxdb_client:
                return
            
            from influxdb_client import Point
            
            points = []
            for log_entry in log_entries:
                point = Point("security_events") \
                    .tag("agent_id", log_entry.agent_id) \
                    .tag("source", log_entry.source.value) \
                    .tag("level", log_entry.level.value) \
                    .tag("threat_level", log_entry.threat_level.value) \
                    .field("count", 1) \
                    .field("threat_score", log_entry.threat_score) \
                    .time(log_entry.timestamp)
                
                if log_entry.event_type:
                    point = point.tag("event_type", log_entry.event_type)
                
                points.append(point)
            
            # Write points
            write_api = self._influxdb_client.write_api()
            write_api.write(bucket="ai-soc", record=points)
            
        except Exception as e:
            logger.error(f"Failed to store metrics in InfluxDB: {e}")
    
    async def store_detection_result(self, detection_result: DetectionResult) -> None:
        """Store detection result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO detection_results (
                    id, log_entry_id, threat_detected, confidence_score,
                    threat_type, severity, ml_results, ai_analysis,
                    rule_matches, mitre_techniques, tactics,
                    analyst_notes, false_positive, verified, detected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                detection_result.id,
                detection_result.log_entry_id,
                detection_result.threat_detected,
                detection_result.confidence_score,
                detection_result.threat_type,
                detection_result.severity,
                json.dumps(detection_result.ml_results),
                json.dumps(detection_result.ai_analysis),
                json.dumps(detection_result.rule_matches),
                json.dumps(detection_result.mitre_techniques),
                json.dumps(detection_result.tactics),
                detection_result.analyst_notes,
                detection_result.false_positive,
                detection_result.verified,
                detection_result.detected_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store detection result: {e}")
            raise
    
    async def register_agent(self, agent_info: AgentInfo) -> None:
        """Register or update agent information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO agents (
                    id, hostname, ip_address, platform, os_version, agent_version,
                    status, last_heartbeat, capabilities, log_sources, configuration,
                    security_zone, importance, logs_sent_count, bytes_sent, errors_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent_info.id,
                agent_info.hostname,
                agent_info.ip_address,
                agent_info.platform,
                agent_info.os_version,
                agent_info.agent_version,
                agent_info.status,
                agent_info.last_heartbeat.isoformat(),
                json.dumps(agent_info.capabilities),
                json.dumps(agent_info.log_sources),
                json.dumps(agent_info.configuration),
                agent_info.security_zone,
                agent_info.importance,
                agent_info.logs_sent_count,
                agent_info.bytes_sent,
                agent_info.errors_count
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            raise
    
    async def update_agent_heartbeat(self, agent_id: str, statistics: Dict[str, Any] = None) -> None:
        """Update agent heartbeat and statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            update_fields = ['last_heartbeat = ?', 'status = ?']
            update_values = [datetime.utcnow().isoformat(), 'online']
            
            if statistics:
                update_fields.extend([
                    'logs_sent_count = ?',
                    'bytes_sent = ?', 
                    'errors_count = ?'
                ])
                update_values.extend([
                    statistics.get('logs_sent', 0),
                    statistics.get('bytes_sent', 0),
                    statistics.get('connection_errors', 0)
                ])
            
            update_values.append(agent_id)  # For WHERE clause
            
            cursor.execute(f'''
                UPDATE agents SET {', '.join(update_fields)}
                WHERE id = ?
            ''', update_values)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update agent heartbeat: {e}")
    
    async def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                agent_info = AgentInfo()
                agent_info.id = row['id']
                agent_info.hostname = row['hostname']
                agent_info.ip_address = row['ip_address']
                agent_info.platform = row['platform']
                agent_info.os_version = row['os_version']
                agent_info.agent_version = row['agent_version']
                agent_info.status = row['status']
                agent_info.last_heartbeat = datetime.fromisoformat(row['last_heartbeat'])
                agent_info.capabilities = json.loads(row['capabilities'] or '[]')
                agent_info.log_sources = json.loads(row['log_sources'] or '[]')
                agent_info.configuration = json.loads(row['configuration'] or '{}')
                agent_info.security_zone = row['security_zone']
                agent_info.importance = row['importance']
                agent_info.logs_sent_count = row['logs_sent_count']
                agent_info.bytes_sent = row['bytes_sent']
                agent_info.errors_count = row['errors_count']
                
                return agent_info
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get agent info: {e}")
            return None
    
    async def get_recent_logs(self, agent_id: Optional[str] = None, 
                            hours: int = 24, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            if agent_id:
                cursor.execute('''
                    SELECT * FROM log_entries 
                    WHERE agent_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (agent_id, since_time.isoformat(), limit))
            else:
                cursor.execute('''
                    SELECT * FROM log_entries 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (since_time.isoformat(), limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            logs = []
            for row in rows:
                log_data = dict(row)
                # Parse JSON fields
                log_data['parsed_data'] = json.loads(row['parsed_data'] or '{}')
                log_data['enriched_data'] = json.loads(row['enriched_data'] or '{}')
                log_data['process_info'] = json.loads(row['process_info'] or '{}')
                log_data['network_info'] = json.loads(row['network_info'] or '{}')
                log_data['tags'] = json.loads(row['tags'] or '[]')
                log_data['metadata'] = json.loads(row['metadata'] or '{}')
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    async def get_detection_results(self, hours: int = 24, 
                                  threat_detected_only: bool = True) -> List[Dict[str, Any]]:
        """Get recent detection results"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            if threat_detected_only:
                cursor.execute('''
                    SELECT * FROM detection_results 
                    WHERE detected_at >= ? AND threat_detected = 1
                    ORDER BY detected_at DESC
                ''', (since_time.isoformat(),))
            else:
                cursor.execute('''
                    SELECT * FROM detection_results 
                    WHERE detected_at >= ?
                    ORDER BY detected_at DESC
                ''', (since_time.isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                result_data = dict(row)
                # Parse JSON fields
                result_data['ml_results'] = json.loads(row['ml_results'] or '{}')
                result_data['ai_analysis'] = json.loads(row['ai_analysis'] or '{}')
                result_data['rule_matches'] = json.loads(row['rule_matches'] or '[]')
                result_data['mitre_techniques'] = json.loads(row['mitre_techniques'] or '[]')
                result_data['tactics'] = json.loads(row['tactics'] or '[]')
                results.append(result_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get detection results: {e}")
            return []
    
    async def store_agent_info(self, agent_data: dict) -> None:
        """Store agent information in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            agent_id = agent_data.get('agent_id')
            
            # Check if agent already exists
            cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
            existing_agent = cursor.fetchone()
            
            if existing_agent:
                # Update existing agent with new data (preserve existing data)
                update_fields = []
                update_values = []
                
                if 'status' in agent_data:
                    update_fields.append('status = ?')
                    update_values.append(agent_data['status'])
                
                if 'last_heartbeat' in agent_data:
                    update_fields.append('last_heartbeat = ?')
                    update_values.append(agent_data['last_heartbeat'].isoformat() if agent_data['last_heartbeat'] else datetime.now().isoformat())
                
                if 'hostname' in agent_data and agent_data['hostname']:
                    update_fields.append('hostname = ?')
                    update_values.append(agent_data['hostname'])
                
                if 'ip_address' in agent_data and agent_data['ip_address']:
                    update_fields.append('ip_address = ?')
                    update_values.append(agent_data['ip_address'])
                
                if 'platform' in agent_data and agent_data['platform']:
                    update_fields.append('platform = ?')
                    update_values.append(agent_data['platform'])
                
                if 'agent_type' in agent_data and agent_data['agent_type']:
                    update_fields.append('agent_version = ?')
                    update_values.append(agent_data['agent_type'])
                
                update_fields.append('updated_at = ?')
                update_values.append(datetime.now().isoformat())
                update_values.append(agent_id)
                
                if update_fields:
                    cursor.execute(f'''
                        UPDATE agents SET {', '.join(update_fields)} WHERE id = ?
                    ''', update_values)
            else:
                # Insert new agent
                cursor.execute('''
                    INSERT INTO agents (
                        id, hostname, ip_address, platform, status, last_heartbeat, agent_version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent_id,
                    agent_data.get('hostname'),
                    agent_data.get('ip_address'),
                    agent_data.get('platform'),
                    agent_data.get('status', 'active'),
                    agent_data.get('last_heartbeat').isoformat() if agent_data.get('last_heartbeat') else datetime.now().isoformat(),
                    agent_data.get('agent_type', 'client_endpoint'),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store agent info: {e}")
    
    async def store_log_entry(self, log_data: dict) -> None:
        """Store log entry in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate a unique ID for the log entry
            import uuid
            log_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO log_entries (
                    id, agent_id, source, timestamp, collected_at, message, level, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id,
                log_data.get('agent_id'),
                log_data.get('source'),
                log_data.get('timestamp').isoformat() if log_data.get('timestamp') else datetime.now().isoformat(),
                datetime.now().isoformat(),
                log_data.get('message'),
                log_data.get('level'),
                log_data.get('raw_data')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store log entry: {e}")
    
    async def store_log_entry_with_id(self, log_data: dict) -> str:
        """Store log entry in database and return the log ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate a unique ID for the log entry
            import uuid
            log_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO log_entries (
                    id, agent_id, source, timestamp, collected_at, message, level, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id,
                log_data.get('agent_id'),
                log_data.get('source'),
                log_data.get('timestamp').isoformat() if log_data.get('timestamp') else datetime.now().isoformat(),
                datetime.now().isoformat(),
                log_data.get('message'),
                log_data.get('level'),
                log_data.get('raw_data')
            ))
            
            conn.commit()
            conn.close()
            
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to store log entry: {e}")
            return None
    
    async def store_network_node(self, network_info: dict) -> None:
        """Store network node information"""
        try:
            # For now, just update agent info with network details
            await self.store_agent_info(network_info)
            
        except Exception as e:
            logger.error(f"Failed to store network node: {e}")
    
    async def get_log_entries(self, limit: int = 100, offset: int = 0, agent_id: str = None) -> list:
        """Get log entries from database"""
        try:
            conn = sqlite3.connect(self.db_path)
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
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get log entries: {e}")
            return []
    
    async def get_all_agents(self) -> list:
        """Get all agents from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, hostname, ip_address, platform, status, last_heartbeat, agent_version
                FROM agents 
                ORDER BY last_heartbeat DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            agents = []
            for row in rows:
                agents.append({
                    'agent_id': row[0],
                    'hostname': row[1],
                    'ip_address': row[2],
                    'platform': row[3],
                    'status': row[4],
                    'last_heartbeat': row[5],
                    'agent_type': row[6] if row[6] else 'client_endpoint'
                })
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to get all agents: {e}")
            return []
