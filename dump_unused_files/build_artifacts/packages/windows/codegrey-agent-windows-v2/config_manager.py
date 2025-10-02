"""
Configuration manager for Windows client agent
"""

import os
import json
import yaml
import logging
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    """Manage configuration for Windows client agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(__file__).parent / "config.yaml"
        self.default_config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'client': {
                'agent_id': 'auto',
                'server_endpoint': 'http://backend.codegrey.ai:8080',
                'api_key': '',
                'reconnect_interval': 30,
                'heartbeat_interval': 60
            },
            'log_forwarding': {
                'enabled': True,
                'batch_size': 100,
                'flush_interval': 30,
                'compression': True,
                'sources': [
                    'windows_events',
                    'process_monitor',
                    'network_monitor',
                    'file_monitor',
                    'container_logs'
                ]
            },
            'log_sources': {
                'system_logs': {
                    'enabled': True,
                    'priority': 'high'
                },
                'security_logs': {
                    'enabled': True,
                    'priority': 'critical'
                },
                'application_logs': {
                    'enabled': True,
                    'priority': 'medium'
                },
                'attack_logs': {
                    'enabled': True,
                    'priority': 'critical'
                },
                'container_logs': {
                    'enabled': True,
                    'priority': 'high'
                }
            },
            'windows': {
                'event_logs': [
                    'Security',
                    'System',
                    'Application',
                    'Microsoft-Windows-Sysmon/Operational',
                    'Microsoft-Windows-PowerShell/Operational',
                    'Microsoft-Windows-Windows Defender/Operational'
                ],
                'wmi_enabled': True
            },
            'command_execution': {
                'enabled': True,
                'allowed_commands': [
                    'powershell',
                    'cmd',
                    'docker',
                    'bash'
                ],
                'timeout': 300
            },
            'containers': {
                'enabled': True,
                'docker_required': True,
                'max_containers': 10,
                'auto_cleanup': True,
                'cleanup_after_hours': 24,
                'preserve_golden_images': True,
                'log_forwarding': True,
                'templates': {
                    'windows_endpoint': {
                        'image': 'mcr.microsoft.com/windows/servercore:ltsc2019',
                        'platform': 'windows',
                        'memory_limit': '2g',
                        'cpu_limit': '1.0'
                    },
                    'linux_server': {
                        'image': 'ubuntu:22.04',
                        'platform': 'linux',
                        'memory_limit': '1g',
                        'cpu_limit': '0.5'
                    },
                    'web_application': {
                        'image': 'nginx:alpine',
                        'platform': 'linux',
                        'memory_limit': '512m',
                        'cpu_limit': '0.3'
                    },
                    'database_server': {
                        'image': 'mysql:8.0',
                        'platform': 'linux',
                        'memory_limit': '1g',
                        'cpu_limit': '0.5'
                    }
                }
            },
            'container_attack_execution': {
                'enabled': True,
                'max_concurrent_attacks': 5,
                'attack_timeout_minutes': 30,
                'preserve_attack_containers': False,
                'create_golden_images': True,
                'log_all_attacks': True
            },
            'golden_images': {
                'enabled': True,
                'storage_path': './golden_images',
                'max_images': 50,
                'auto_cleanup': True,
                'cleanup_after_days': 30
            },
            'container_networking': {
                'enabled': True,
                'network_mode': 'bridge',
                'create_isolated_networks': True,
                'allow_host_network': False,
                'port_mapping': True
            },
            'container_security': {
                'enabled': True,
                'read_only_root_filesystem': False,
                'no_new_privileges': True,
                'drop_capabilities': True,
                'security_opt': ['no-new-privileges:true']
            },
            'performance': {
                'max_memory_mb': 2048,
                'max_cpu_percent': 50,
                'queue_size': 10000,
                'container_memory_limit': '2g',
                'container_cpu_limit': '1.0'
            },
            'security': {
                'api_key_required': False,
                'encryption_enabled': False,
                'command_validation': True,
                'container_isolation': True,
                'attack_simulation_mode': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'codegrey-agent.log',
                'max_size_mb': 100,
                'backup_count': 5,
                'container_logs': True,
                'attack_execution_logs': True,
                'golden_image_logs': True
            },
            'development': {
                'mock_data_enabled': False,
                'test_mode': False,
                'debug_networking': False,
                'simulate_threats': True,
                'container_debug': False
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
    
    def update_server_endpoint(self, endpoint: str):
        """Update server endpoint in configuration"""
        try:
            config = self.load_config()
            if 'client' not in config:
                config['client'] = {}
            config['client']['server_endpoint'] = endpoint
            self.save_config(config)
            self.logger.info(f"Updated server endpoint to {endpoint}")
            
        except Exception as e:
            self.logger.error(f"Failed to update server endpoint: {e}")
    
    def configure_agent(self, server_url: str, api_token: str = None):
        """Configure agent with server details"""
        try:
            config = self.load_config()
            
            # Automatically add http:// if missing
            if not server_url.startswith(('http://', 'https://')):
                server_url = f'http://{server_url}'
            
            # Ensure client section exists
            if 'client' not in config:
                config['client'] = {}
            
            config['client']['server_endpoint'] = server_url
            
            if api_token:
                config['client']['api_key'] = api_token
                config['security']['api_key_required'] = True
            
            self.save_config(config)
            self.logger.info("Agent configured successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure agent: {e}")
            return False
