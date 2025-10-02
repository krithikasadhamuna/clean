"""
Configuration management for log forwarding system
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration manager"""
    
    # File paths
    config_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "config")
    server_config_file: str = "server_config.yaml"
    client_config_file: str = "client_config.yaml"
    
    # Loaded configuration
    _server_config: Optional[Dict[str, Any]] = None
    _client_config: Optional[Dict[str, Any]] = None
    
    def load_server_config(self) -> Dict[str, Any]:
        """Load server configuration"""
        if self._server_config is None:
            config_path = self.config_dir / self.server_config_file
            self._server_config = self._load_yaml_config(config_path)
        return self._server_config
    
    def load_client_config(self) -> Dict[str, Any]:
        """Load client configuration"""
        if self._client_config is None:
            # Fix config path resolution
            if self.client_config_file.startswith('config/'):
                config_path = Path(self.client_config_file)
            else:
                config_path = self.config_dir / self.client_config_file
            self._client_config = self._load_yaml_config(config_path)
        return self._client_config
    
    def _load_yaml_config(self, config_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file with environment variable substitution"""
        try:
            if not config_path.exists():
                logger.warning(f"Config file not found: {config_path}")
                return self._get_default_config()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace environment variables
            content = self._substitute_env_vars(content)
            
            config = yaml.safe_load(content)
            logger.info(f"Loaded configuration from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return self._get_default_config()
    
    def _substitute_env_vars(self, content: str) -> str:
        """Replace ${VAR_NAME} with environment variable values"""
        import re
        
        def replace_env_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""
            return os.getenv(var_name, default_value)
        
        # Pattern for ${VAR_NAME} or ${VAR_NAME:default_value}
        pattern = r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}'
        return re.sub(pattern, replace_env_var, content)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file loading fails"""
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 8080,
                'log_level': 'INFO'
            },
            'client': {
                'server_endpoint': 'http://localhost:8080',
                'reconnect_interval': 30,
                'batch_size': 100
            },
            'database': {
                'sqlite_path': 'soc_database.db'
            },
            'llm': {
                'ollama_endpoint': 'http://localhost:11434',
                'ollama_model': 'cybersec-ai'
            }
        }
    
    def get_server_setting(self, key_path: str, default: Any = None) -> Any:
        """Get server setting using dot notation (e.g., 'server.port')"""
        config = self.load_server_config()
        return self._get_nested_value(config, key_path, default)
    
    def get_client_setting(self, key_path: str, default: Any = None) -> Any:
        """Get client setting using dot notation"""
        config = self.load_client_config()
        return self._get_nested_value(config, key_path, default)
    
    def _get_nested_value(self, config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """Get nested dictionary value using dot notation"""
        keys = key_path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def update_server_config(self, updates: Dict[str, Any]) -> None:
        """Update server configuration in memory"""
        if self._server_config is None:
            self.load_server_config()
        
        self._update_nested_dict(self._server_config, updates)
    
    def update_client_config(self, updates: Dict[str, Any]) -> None:
        """Update client configuration in memory"""
        if self._client_config is None:
            self.load_client_config()
        
        self._update_nested_dict(self._client_config, updates)
    
    def _update_nested_dict(self, target: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Update nested dictionary with new values"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._update_nested_dict(target[key], value)
            else:
                target[key] = value
    
    def save_server_config(self) -> None:
        """Save server configuration to file"""
        if self._server_config is not None:
            config_path = self.config_dir / self.server_config_file
            self._save_yaml_config(config_path, self._server_config)
    
    def save_client_config(self) -> None:
        """Save client configuration to file"""
        if self._client_config is not None:
            config_path = self.config_dir / self.client_config_file
            self._save_yaml_config(config_path, self._client_config)
    
    def _save_yaml_config(self, config_path: Path, config: Dict[str, Any]) -> None:
        """Save configuration to YAML file"""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            logger.info(f"Saved configuration to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")


# Global configuration instance
config = Config()
