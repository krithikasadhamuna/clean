"""
Configuration manager for macOS client agent
"""

import os
import json
import yaml
import logging
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    """Manage configuration for macOS client agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(__file__).parent / "config.yaml"
        self.default_config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for macOS"""
        return {
            'server_endpoint': 'http://15.207.6.45:8080',
            'agent_id': 'auto',
            'heartbeat_interval': 60,
            'log_forwarding': {
                'enabled': True,
                'batch_size': 100,
                'flush_interval': 30,
                'sources': [
                    'system_logs',
                    'process_monitor',
                    'network_monitor',
                    'file_monitor',
                    'xprotect_logs'
                ]
            },
            'command_execution': {
                'enabled': True,
                'allowed_commands': [
                    'bash',
                    'zsh',
                    'docker'
                ],
                'timeout': 300,
                'require_sudo': False
            },
            'container_management': {
                'enabled': True,
                'runtime': 'docker',  # Docker Desktop on macOS
                'max_containers': 10,
                'snapshot_enabled': True
            },
            'security': {
                'api_key_required': False,
                'encryption_enabled': False,
                'privacy_mode': True,  # macOS privacy considerations
                'restrict_commands': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'codegrey-agent.log',
                'max_size_mb': 100,
                'backup_count': 5,
                'console_enabled': True
            },
            'macos_specific': {
                'xprotect_integration': True,
                'privacy_permissions_check': True,
                'keychain_access': False
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Merge with defaults
                merged_config = self._merge_configs(self.default_config, config)
                self.logger.info(f"Loaded configuration from {self.config_file}")
                return merged_config
            else:
                # Create default config file
                self.save_config(self.default_config)
                self.logger.info("Created default configuration file")
                return self.default_config
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return self.default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with defaults"""
        merged = default.copy()
        
        for key, value in user.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def configure_agent(self, server_url: str, api_token: str = None):
        """Configure agent with server details"""
        try:
            config = self.load_config()
            config['server_endpoint'] = server_url
            
            if api_token:
                config['api_token'] = api_token
                config['security']['api_key_required'] = True
            
            self.save_config(config)
            self.logger.info("Agent configured successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure agent: {e}")
            return False
