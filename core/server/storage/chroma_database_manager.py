"""
ChromaDB Database Manager for AI SOC Platform
Vector-based database for intelligent threat detection and semantic search
"""

import os
import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from shared.models import LogEntry, LogBatch, AgentInfo, DetectionResult


logger = logging.getLogger(__name__)


class ChromaDatabaseManager:
    """ChromaDB-based database manager with vector embeddings"""
    
    def __init__(self, db_path: str = "chroma_soc_db", openai_api_key: str = None):
        """
        Initialize ChromaDB database manager
        
        Args:
            db_path: Path to store ChromaDB data
            openai_api_key: OpenAI API key for embeddings (optional)
        """
        self.db_path = db_path
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding function
        self.embedding_function = self._get_embedding_function()
        
        # Initialize collections
        self._initialize_collections()
        
        logger.info(f"ChromaDB initialized at {db_path}")
    
    def _get_embedding_function(self):
        """Get appropriate embedding function"""
        if self.openai_api_key:
            try:
                return embedding_functions.OpenAIEmbeddingFunction(
                    api_key=self.openai_api_key,
                    model_name="text-embedding-3-small"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
        
        # Fallback to sentence transformers
        try:
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as e:
            logger.error(f"Failed to initialize sentence transformers: {e}")
            raise
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections"""
        try:
            # Agents collection
            self.agents_collection = self.client.get_or_create_collection(
                name="agents",
                embedding_function=self.embedding_function,
                metadata={"description": "Agent information and capabilities"}
            )
            
            # Logs collection
            self.logs_collection = self.client.get_or_create_collection(
                name="logs",
                embedding_function=self.embedding_function,
                metadata={"description": "Security logs and events"}
            )
            
            # Detections collection
            self.detections_collection = self.client.get_or_create_collection(
                name="detections",
                embedding_function=self.embedding_function,
                metadata={"description": "Threat detections and alerts"}
            )
            
            # Network topology collection
            self.topology_collection = self.client.get_or_create_collection(
                name="topology",
                embedding_function=self.embedding_function,
                metadata={"description": "Network topology and device information"}
            )
            
            logger.info("ChromaDB collections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    # Agent Management Methods
    async def register_agent(self, agent_info: AgentInfo) -> bool:
        """Register a new agent"""
        try:
            agent_id = str(agent_info.id)
            
            # Create document for agent
            agent_doc = {
                "id": agent_id,
                "name": agent_info.name,
                "type": agent_info.type,
                "status": agent_info.status,
                "location": agent_info.location,
                "capabilities": json.dumps(agent_info.capabilities),
                "platform": agent_info.platform,
                "last_activity": agent_info.last_activity.isoformat() if agent_info.last_activity else datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            # Create text for embedding (combine all relevant info)
            agent_text = f"Agent {agent_info.name} of type {agent_info.type} with capabilities {', '.join(agent_info.capabilities)} located at {agent_info.location}"
            
            self.agents_collection.add(
                documents=[agent_text],
                metadatas=[agent_doc],
                ids=[agent_id]
            )
            
            logger.info(f"Agent {agent_id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        try:
            result = self.agents_collection.get(ids=[agent_id])
            if result['ids']:
                return result['metadatas'][0]
            return None
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None
    
    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        try:
            result = self.agents_collection.get()
            return result['metadatas'] if result['metadatas'] else []
        except Exception as e:
            logger.error(f"Failed to get all agents: {e}")
            return []
    
    async def search_similar_agents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for agents similar to query"""
        try:
            result = self.agents_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            agents = []
            if result['metadatas'] and result['metadatas'][0]:
                for metadata in result['metadatas'][0]:
                    agents.append(metadata)
            
            return agents
        except Exception as e:
            logger.error(f"Failed to search similar agents: {e}")
            return []
    
    # Log Management Methods
    async def store_logs(self, logs: List[LogEntry]) -> bool:
        """Store log entries with embeddings"""
        try:
            if not logs:
                return True
            
            documents = []
            metadatas = []
            ids = []
            
            for log in logs:
                log_id = str(uuid.uuid4())
                
                # Create document for embedding
                log_text = f"Log from {log.source} at {log.timestamp}: {log.message} Level: {log.level}"
                if log.metadata:
                    log_text += f" Metadata: {json.dumps(log.metadata)}"
                
                # Create metadata
                log_metadata = {
                    "id": log_id,
                    "source": log.source.value,
                    "level": log.level.value,
                    "message": log.message,
                    "timestamp": log.timestamp.isoformat(),
                    "agent_id": log.agent_id,
                    "metadata": json.dumps(log.metadata) if log.metadata else None,
                    "created_at": datetime.now().isoformat()
                }
                
                documents.append(log_text)
                metadatas.append(log_metadata)
                ids.append(log_id)
            
            # Batch insert
            self.logs_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Stored {len(logs)} log entries")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store logs: {e}")
            return False
    
    async def search_logs(self, query: str, limit: int = 100, hours: int = 24) -> List[Dict[str, Any]]:
        """Search logs using semantic similarity"""
        try:
            # Calculate time filter
            time_filter = datetime.now() - timedelta(hours=hours)
            
            result = self.logs_collection.query(
                query_texts=[query],
                n_results=limit,
                where={"timestamp": {"$gte": time_filter.isoformat()}}
            )
            
            logs = []
            if result['metadatas'] and result['metadatas'][0]:
                for metadata in result['metadatas'][0]:
                    logs.append(metadata)
            
            return logs
        except Exception as e:
            logger.error(f"Failed to search logs: {e}")
            return []
    
    async def get_recent_logs(self, agent_id: str = None, hours: int = 24, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent logs with optional agent filter"""
        try:
            time_filter = datetime.now() - timedelta(hours=hours)
            where_clause = {"timestamp": {"$gte": time_filter.isoformat()}}
            
            if agent_id:
                where_clause["agent_id"] = agent_id
            
            result = self.logs_collection.get(
                where=where_clause,
                limit=limit
            )
            
            return result['metadatas'] if result['metadatas'] else []
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    # Detection Management Methods
    async def store_detection(self, detection: DetectionResult) -> bool:
        """Store threat detection result"""
        try:
            detection_id = str(uuid.uuid4())
            
            # Create document for embedding
            detection_text = f"Threat detection: {detection.threat_type} with confidence {detection.confidence} for agent {detection.agent_id}. Details: {detection.description}"
            
            # Create metadata
            detection_metadata = {
                "id": detection_id,
                "agent_id": detection.agent_id,
                "threat_type": detection.threat_type,
                "confidence": detection.confidence,
                "description": detection.description,
                "timestamp": detection.timestamp.isoformat(),
                "metadata": json.dumps(detection.metadata) if detection.metadata else None,
                "created_at": datetime.now().isoformat()
            }
            
            self.detections_collection.add(
                documents=[detection_text],
                metadatas=[detection_metadata],
                ids=[detection_id]
            )
            
            logger.info(f"Stored detection {detection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store detection: {e}")
            return False
    
    async def search_detections(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search detections using semantic similarity"""
        try:
            result = self.detections_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            detections = []
            if result['metadatas'] and result['metadatas'][0]:
                for metadata in result['metadatas'][0]:
                    detections.append(metadata)
            
            return detections
        except Exception as e:
            logger.error(f"Failed to search detections: {e}")
            return []
    
    # Network Topology Methods
    async def store_network_device(self, device_info: Dict[str, Any]) -> bool:
        """Store network device information"""
        try:
            device_id = device_info.get('id', str(uuid.uuid4()))
            
            # Create document for embedding
            device_text = f"Network device {device_info.get('name', 'Unknown')} at IP {device_info.get('ip', 'Unknown')} with OS {device_info.get('os', 'Unknown')}"
            
            # Add metadata
            device_metadata = {
                "id": device_id,
                "name": device_info.get('name'),
                "ip": device_info.get('ip'),
                "os": device_info.get('os'),
                "type": device_info.get('type'),
                "status": device_info.get('status'),
                "last_seen": device_info.get('last_seen', datetime.now().isoformat()),
                "metadata": json.dumps(device_info.get('metadata', {})),
                "created_at": datetime.now().isoformat()
            }
            
            self.topology_collection.add(
                documents=[device_text],
                metadatas=[device_metadata],
                ids=[device_id]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store network device: {e}")
            return False
    
    async def get_network_topology(self) -> List[Dict[str, Any]]:
        """Get all network devices"""
        try:
            result = self.topology_collection.get()
            return result['metadatas'] if result['metadatas'] else []
        except Exception as e:
            logger.error(f"Failed to get network topology: {e}")
            return []
    
    # Statistics and Health Methods
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {
                "agents_count": self.agents_collection.count(),
                "logs_count": self.logs_collection.count(),
                "detections_count": self.detections_collection.count(),
                "topology_count": self.topology_collection.count(),
                "embedding_model": self.embedding_function.__class__.__name__,
                "database_path": self.db_path
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    async def clear_database(self) -> bool:
        """Clear all data from database"""
        try:
            self.client.reset()
            self._initialize_collections()
            logger.info("Database cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        try:
            # ChromaDB persistent client doesn't need explicit closing
            logger.info("ChromaDB connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")


# Test function
async def test_chroma_db():
    """Test ChromaDB functionality"""
    print("Testing ChromaDB Database Manager...")
    
    # Initialize database
    db = ChromaDatabaseManager("test_chroma_db")
    
    # Test agent registration
    test_agent = AgentInfo(
        id="test-agent-1",
        name="Test Agent",
        type="detection",
        status="active",
        location="Test Location",
        capabilities=["threat_detection", "log_analysis"],
        platform="Test Platform"
    )
    
    await db.register_agent(test_agent)
    print("Agent registered")
    
    # Test agent retrieval
    agents = await db.get_all_agents()
    print(f"Retrieved {len(agents)} agents")
    
    # Test semantic search
    similar_agents = await db.search_similar_agents("threat detection agent", limit=3)
    print(f"Found {len(similar_agents)} similar agents")
    
    # Test log storage
    test_log = LogEntry(
        source="application",
        level="info",
        message="Test log message for threat detection",
        timestamp=datetime.now(),
        agent_id="test-agent-1",
        metadata={"test": "data"}
    )
    
    await db.store_logs([test_log])
    print("Log stored")
    
    # Test log search
    logs = await db.search_logs("threat detection", limit=5)
    print(f"Found {len(logs)} relevant logs")
    
    # Test statistics
    stats = await db.get_database_stats()
    print(f"Database stats: {stats}")
    
    print("ChromaDB test completed successfully!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chroma_db())
