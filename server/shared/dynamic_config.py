"""
Dynamic Configuration Manager
Loads configurations from database, environment, or auto-detection
"""

import os
import json
import logging
import sqlite3
import requests
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DynamicConfigManager:
    """Manages dynamic configuration loading from multiple sources"""
    
    def __init__(self, db_path: str = "soc_database.db"):
        self.db_path = db_path
        self.config_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_loaded = {}
    
    async def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration dynamically"""
        try:
            # Try database first
            config = await self._load_llm_config_from_db()
            
            if not config:
                # Try environment variables
                config = self._load_llm_config_from_env()
            
            if not config:
                # Auto-detect available providers
                config = await self._auto_detect_llm_config()
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load LLM config dynamically: {e}")
            return self._get_minimal_llm_config()
    
    async def _load_llm_config_from_db(self) -> Optional[Dict]:
        """Load LLM configuration from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if config table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='llm_config'
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    SELECT provider, model, api_key, endpoint, temperature, max_tokens 
                    FROM llm_config 
                    WHERE active = 1 
                    ORDER BY priority DESC 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    provider, model, api_key, endpoint, temperature, max_tokens = row
                    
                    config = {
                        'provider': provider,
                        'model': model,
                        'api_key': api_key,
                        'endpoint': endpoint,
                        'temperature': temperature,
                        'max_tokens': max_tokens
                    }
                    
                    conn.close()
                    logger.info(f"Loaded LLM config from database: {provider}/{model}")
                    return config
            
            conn.close()
            
        except Exception as e:
            logger.debug(f"Could not load LLM config from database: {e}")
        
        return None
    
    def _load_llm_config_from_env(self) -> Optional[Dict]:
        """Load LLM configuration from environment variables"""
        try:
            # Check for OpenAI
            if os.getenv('OPENAI_API_KEY'):
                return {
                    'provider': 'openai',
                    'model': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                    'api_key': os.getenv('OPENAI_API_KEY'),
                    'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.7')),
                    'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '2048'))
                }
            
            # Check for Anthropic
            if os.getenv('ANTHROPIC_API_KEY'):
                return {
                    'provider': 'anthropic',
                    'model': os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet'),
                    'api_key': os.getenv('ANTHROPIC_API_KEY'),
                    'temperature': float(os.getenv('ANTHROPIC_TEMPERATURE', '0.7')),
                    'max_tokens': int(os.getenv('ANTHROPIC_MAX_TOKENS', '2048'))
                }
            
            # Check for Ollama endpoint
            ollama_endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434')
            if self._test_endpoint(ollama_endpoint):
                return {
                    'provider': 'ollama',
                    'model': os.getenv('OLLAMA_MODEL', 'llama2'),
                    'endpoint': ollama_endpoint,
                    'temperature': float(os.getenv('OLLAMA_TEMPERATURE', '0.7')),
                    'max_tokens': int(os.getenv('OLLAMA_MAX_TOKENS', '2048'))
                }
                
        except Exception as e:
            logger.debug(f"Could not load LLM config from environment: {e}")
        
        return None
    
    async def _auto_detect_llm_config(self) -> Dict[str, Any]:
        """Auto-detect available LLM providers"""
        providers = []
        
        # Test Ollama
        if self._test_endpoint('http://localhost:11434'):
            providers.append({
                'provider': 'ollama',
                'model': 'llama2',
                'endpoint': 'http://localhost:11434',
                'temperature': 0.7,
                'max_tokens': 2048,
                'priority': 3
            })
        
        # Test OpenAI (if API key available)
        if os.getenv('OPENAI_API_KEY'):
            providers.append({
                'provider': 'openai',
                'model': 'gpt-3.5-turbo',
                'api_key': os.getenv('OPENAI_API_KEY'),
                'temperature': 0.7,
                'max_tokens': 2048,
                'priority': 1
            })
        
        # Return highest priority provider
        if providers:
            best_provider = max(providers, key=lambda x: x['priority'])
            logger.info(f"Auto-detected LLM provider: {best_provider['provider']}")
            return best_provider
        
        # No providers available
        return self._get_minimal_llm_config()
    
    def _test_endpoint(self, endpoint: str) -> bool:
        """Test if an endpoint is available"""
        try:
            response = requests.get(f"{endpoint}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def _get_minimal_llm_config(self) -> Dict[str, Any]:
        """Get minimal fallback configuration"""
        return {
            'provider': 'mock',
            'model': 'mock-llm',
            'temperature': 0.7,
            'max_tokens': 1024,
            'available': False
        }
    
    async def get_detection_config(self) -> Dict[str, Any]:
        """Get detection configuration dynamically"""
        try:
            # Try database first
            config = await self._load_detection_config_from_db()
            
            if not config:
                # Generate based on available resources
                config = self._generate_detection_config()
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load detection config: {e}")
            return self._get_minimal_detection_config()
    
    async def _load_detection_config_from_db(self) -> Optional[Dict]:
        """Load detection configuration from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='detection_config'
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    SELECT ml_enabled, ai_enabled, real_time_enabled, 
                           confidence_threshold, batch_size
                    FROM detection_config 
                    WHERE active = 1 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    ml_enabled, ai_enabled, real_time_enabled, confidence_threshold, batch_size = row
                    
                    config = {
                        'ml_enabled': bool(ml_enabled),
                        'ai_enabled': bool(ai_enabled),
                        'real_time_enabled': bool(real_time_enabled),
                        'confidence_threshold': confidence_threshold,
                        'batch_size': batch_size
                    }
                    
                    conn.close()
                    return config
            
            conn.close()
            
        except Exception as e:
            logger.debug(f"Could not load detection config from database: {e}")
        
        return None
    
    def _generate_detection_config(self) -> Dict[str, Any]:
        """Generate detection configuration based on system capabilities"""
        return {
            'ml_enabled': True,
            'ai_enabled': bool(os.getenv('OPENAI_API_KEY') or self._test_endpoint('http://localhost:11434')),
            'real_time_enabled': True,
            'confidence_threshold': 0.7,
            'batch_size': 100,
            'analyze_all_logs': True,
            'ml_ai_comparison': True
        }
    
    def _get_minimal_detection_config(self) -> Dict[str, Any]:
        """Get minimal detection configuration"""
        return {
            'ml_enabled': True,
            'ai_enabled': False,
            'real_time_enabled': True,
            'confidence_threshold': 0.8,
            'batch_size': 50
        }
    
    async def save_config_to_db(self, config_type: str, config_data: Dict[str, Any]):
        """Save configuration to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if config_type == 'llm':
                # Create table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS llm_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        provider TEXT NOT NULL,
                        model TEXT NOT NULL,
                        api_key TEXT,
                        endpoint TEXT,
                        temperature REAL DEFAULT 0.7,
                        max_tokens INTEGER DEFAULT 2048,
                        active BOOLEAN DEFAULT 1,
                        priority INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert new config
                cursor.execute("""
                    INSERT INTO llm_config 
                    (provider, model, api_key, endpoint, temperature, max_tokens, active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, 1, 1)
                """, (
                    config_data.get('provider'),
                    config_data.get('model'),
                    config_data.get('api_key'),
                    config_data.get('endpoint'),
                    config_data.get('temperature', 0.7),
                    config_data.get('max_tokens', 2048)
                ))
            
            elif config_type == 'detection':
                # Create table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detection_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ml_enabled BOOLEAN DEFAULT 1,
                        ai_enabled BOOLEAN DEFAULT 1,
                        real_time_enabled BOOLEAN DEFAULT 1,
                        confidence_threshold REAL DEFAULT 0.7,
                        batch_size INTEGER DEFAULT 100,
                        active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert new config
                cursor.execute("""
                    INSERT INTO detection_config 
                    (ml_enabled, ai_enabled, real_time_enabled, confidence_threshold, batch_size, active)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (
                    config_data.get('ml_enabled', True),
                    config_data.get('ai_enabled', True),
                    config_data.get('real_time_enabled', True),
                    config_data.get('confidence_threshold', 0.7),
                    config_data.get('batch_size', 100)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {config_type} configuration to database")
            
        except Exception as e:
            logger.error(f"Failed to save {config_type} config to database: {e}")

# Global instance
dynamic_config_manager = DynamicConfigManager()
