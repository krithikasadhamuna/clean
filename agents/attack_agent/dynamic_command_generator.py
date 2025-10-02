#!/usr/bin/env python3
"""
Dynamic Command Generator
Generates specific commands for client agents to execute
Translates attack plans into executable commands
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class DynamicCommandGenerator:
    """
    Generates specific commands for client agents
    Translates high-level attack plans into executable commands
    """
    
    def __init__(self):
        self.command_templates = self._load_command_templates()
    
    def _load_command_templates(self) -> Dict[str, Dict]:
        """Load command templates for different operations"""
        return {
            'create_self_replica': {
                'description': 'Create exact replica of host system in container',
                'required_params': ['container_name'],
                'optional_params': ['network', 'resource_limits']
            },
            'deploy_smtp_container': {
                'description': 'Deploy SMTP server container',
                'required_params': ['container_name'],
                'optional_params': ['ports', 'configuration']
            },
            'deploy_ftp_container': {
                'description': 'Deploy FTP server container',
                'required_params': ['container_name'],
                'optional_params': ['ports', 'configuration']
            },
            'deploy_web_server_container': {
                'description': 'Deploy web server container',
                'required_params': ['container_name'],
                'optional_params': ['ports', 'server_type']
            },
            'deploy_database_container': {
                'description': 'Deploy database server container',
                'required_params': ['container_name', 'db_type'],
                'optional_params': ['ports', 'initial_data']
            },
            'execute_phishing': {
                'description': 'Execute phishing attack',
                'required_params': ['from_container', 'to_targets'],
                'optional_params': ['email_template', 'technique']
            },
            'execute_lateral_movement': {
                'description': 'Execute lateral movement',
                'required_params': ['source_container', 'target_containers'],
                'optional_params': ['technique', 'credentials']
            },
            'execute_data_exfiltration': {
                'description': 'Execute data exfiltration',
                'required_params': ['source_container', 'data_types'],
                'optional_params': ['exfil_method', 'destination']
            },
            'execute_ransomware': {
                'description': 'Execute ransomware simulation',
                'required_params': ['target_container'],
                'optional_params': ['file_types', 'spread_method']
            },
            'cleanup_containers': {
                'description': 'Clean up attack containers',
                'required_params': ['container_ids'],
                'optional_params': []
            }
        }
    
    def generate_commands_from_plan(self, attack_plan) -> List[Dict[str, Any]]:
        """
        Generate all commands from an attack plan
        
        Args:
            attack_plan: AttackPlan object with phases
        
        Returns:
            List of commands ready to be queued to client agents
        """
        all_commands = []
        
        try:
            # Process each phase
            for phase in attack_plan.phases:
                phase_commands = self.generate_phase_commands(phase, attack_plan)
                all_commands.extend(phase_commands)
            
            logger.info(f"Generated {len(all_commands)} commands from attack plan")
            return all_commands
            
        except Exception as e:
            logger.error(f"Command generation from plan failed: {e}")
            return []
    
    def generate_phase_commands(self, phase, attack_plan) -> List[Dict[str, Any]]:
        """Generate commands for a single phase"""
        commands = []
        
        try:
            for cmd_spec in phase.commands:
                command = self.generate_command(
                    command_type=cmd_spec.get('command_type'),
                    endpoint_id=cmd_spec.get('endpoint_id'),
                    command_data=cmd_spec.get('data', {}),
                    scenario_id=attack_plan.plan_id,
                    phase_name=phase.name,
                    purpose=cmd_spec.get('purpose', ''),
                    techniques=phase.techniques
                )
                
                if command:
                    commands.append(command)
            
            return commands
            
        except Exception as e:
            logger.error(f"Phase command generation failed: {e}")
            return []
    
    def generate_command(self, command_type: str, endpoint_id: str, 
                        command_data: Dict = None, **kwargs) -> Dict[str, Any]:
        """
        Generate a single command
        
        Args:
            command_type: Type of command to generate
            endpoint_id: Target endpoint ID
            command_data: Additional command data
            **kwargs: Additional metadata
        
        Returns:
            Complete command dict ready to queue
        """
        try:
            command_data = command_data or {}
            
            # Get command template
            template = self.command_templates.get(command_type)
            if not template:
                logger.warning(f"Unknown command type: {command_type}")
                return None
            
            # Generate command based on type
            if command_type == 'create_self_replica':
                return self.generate_self_replica_command(endpoint_id, command_data, **kwargs)
            
            elif command_type == 'deploy_smtp_container':
                return self.generate_smtp_deployment_command(endpoint_id, command_data, **kwargs)
            
            elif command_type == 'deploy_ftp_container':
                return self.generate_ftp_deployment_command(endpoint_id, command_data, **kwargs)
            
            elif command_type == 'deploy_web_server_container':
                return self.generate_web_server_deployment_command(endpoint_id, command_data, **kwargs)
            
            elif command_type == 'deploy_database_container':
                return self.generate_database_deployment_command(endpoint_id, command_data, **kwargs)
            
            elif command_type == 'execute_phishing':
                return self.generate_phishing_execution_command(endpoint_id, command_data, **kwargs)
            
            elif command_type == 'execute_lateral_movement':
                return self.generate_lateral_movement_command(endpoint_id, command_data, **kwargs)
            
            elif command_type == 'execute_data_exfiltration':
                return self.generate_data_exfiltration_command(endpoint_id, command_data, **kwargs)
            
            elif command_type == 'execute_ransomware':
                return self.generate_ransomware_command(endpoint_id, command_data, **kwargs)
            
            elif command_type == 'cleanup_containers':
                return self.generate_cleanup_command(endpoint_id, command_data, **kwargs)
            
            else:
                # Generic command
                return self.generate_generic_command(command_type, endpoint_id, command_data, **kwargs)
                
        except Exception as e:
            logger.error(f"Command generation failed for {command_type}: {e}")
            return None
    
    def generate_self_replica_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to create self-replica container"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'create_self_replica',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': {
                'snapshot_host': True,
                'container_name': data.get('container_name', f'{endpoint_id}_replica'),
                'network': data.get('network', 'soc-attack-network'),
                'resource_limits': data.get('resource_limits', {
                    'memory': '2GB',
                    'cpu': '2 cores'
                }),
                'purpose': kwargs.get('purpose', 'Host system replica for attack simulation')
            },
            'priority': 'high',
            'timeout': 300,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', [])
        }
    
    def generate_smtp_deployment_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to deploy SMTP server"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'deploy_smtp_container',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': {
                'container_name': data.get('container_name', 'smtp_server'),
                'image': 'postfix:latest',
                'ports': data.get('ports', {'25': '25', '587': '587'}),
                'network': data.get('network', 'soc-attack-network'),
                'configuration': data.get('configuration', 'phishing_optimized'),
                'environment': {
                    'SMTP_MODE': 'phishing',
                    'RELAY_DOMAINS': '*'
                },
                'purpose': kwargs.get('purpose', 'SMTP server for phishing attack')
            },
            'priority': 'high',
            'timeout': 180,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', ['T1566.001'])
        }
    
    def generate_ftp_deployment_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to deploy FTP server"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'deploy_ftp_container',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': {
                'container_name': data.get('container_name', 'ftp_server'),
                'image': 'vsftpd:latest',
                'ports': data.get('ports', {'21': '21'}),
                'network': data.get('network', 'soc-attack-network'),
                'configuration': data.get('configuration', 'anonymous_enabled'),
                'purpose': kwargs.get('purpose', 'FTP server for data exfiltration')
            },
            'priority': 'medium',
            'timeout': 180,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', ['T1048'])
        }
    
    def generate_web_server_deployment_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to deploy web server"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'deploy_web_server_container',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': {
                'container_name': data.get('container_name', 'web_server'),
                'image': data.get('server_type', 'nginx:latest'),
                'ports': data.get('ports', {'80': '80', '443': '443'}),
                'network': data.get('network', 'soc-attack-network'),
                'purpose': kwargs.get('purpose', 'Web server for attack infrastructure')
            },
            'priority': 'medium',
            'timeout': 180,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', ['T1190'])
        }
    
    def generate_database_deployment_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to deploy database server"""
        db_type = data.get('db_type', 'mysql')
        image_map = {
            'mysql': 'mysql:latest',
            'postgres': 'postgres:latest',
            'mssql': 'mcr.microsoft.com/mssql/server:latest'
        }
        
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'deploy_database_container',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': {
                'container_name': data.get('container_name', f'{db_type}_server'),
                'image': image_map.get(db_type, 'mysql:latest'),
                'db_type': db_type,
                'ports': data.get('ports', {'3306': '3306'}),
                'network': data.get('network', 'soc-attack-network'),
                'initial_data': data.get('initial_data', 'sample_customer_data'),
                'purpose': kwargs.get('purpose', 'Database server with sample data')
            },
            'priority': 'medium',
            'timeout': 240,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', ['T1003'])
        }
    
    def generate_phishing_execution_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to execute phishing attack"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'execute_phishing',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': {
                'from_container': data.get('from', 'smtp_container'),
                'to_targets': data.get('to', []),
                'email_template': data.get('email_template', 'executive_phishing'),
                'technique': data.get('technique', 'T1566.001'),
                'subject': 'Urgent: Password Reset Required',
                'sender': 'IT Support <support@company.local>',
                'attachment': data.get('attachment', 'password_reset.html'),
                'purpose': kwargs.get('purpose', 'Spear phishing attack')
            },
            'priority': 'high',
            'timeout': 120,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', ['T1566.001'])
        }
    
    def generate_lateral_movement_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to execute lateral movement"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'execute_lateral_movement',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': {
                'source_container': data.get('source', f'{endpoint_id}_replica'),
                'target_containers': data.get('targets', []),
                'technique': data.get('technique', 'T1021.001'),
                'method': data.get('method', 'rdp'),
                'credentials': data.get('credentials', 'harvested'),
                'purpose': kwargs.get('purpose', 'Lateral movement between systems')
            },
            'priority': 'high',
            'timeout': 180,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', ['T1021.001'])
        }
    
    def generate_data_exfiltration_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to execute data exfiltration"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'execute_data_exfiltration',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': {
                'source_container': data.get('source', f'{endpoint_id}_replica'),
                'data_types': data.get('data_types', ['credentials', 'sensitive_files']),
                'exfil_method': data.get('exfil_method', 'ftp'),
                'destination': data.get('destination', 'ftp_server'),
                'technique': data.get('technique', 'T1041'),
                'purpose': kwargs.get('purpose', 'Data exfiltration simulation')
            },
            'priority': 'high',
            'timeout': 240,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', ['T1041'])
        }
    
    def generate_ransomware_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to execute ransomware simulation"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'execute_ransomware',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': {
                'target_container': data.get('target_container', f'{endpoint_id}_replica'),
                'file_types': data.get('file_types', ['*.doc', '*.pdf', '*.xls']),
                'spread_method': data.get('spread_method', 'network_shares'),
                'technique': 'T1486',
                'ransom_note': 'Your files have been encrypted (simulation)',
                'purpose': kwargs.get('purpose', 'Ransomware simulation')
            },
            'priority': 'critical',
            'timeout': 300,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', ['T1486', 'T1490'])
        }
    
    def generate_cleanup_command(self, endpoint_id: str, data: Dict, **kwargs) -> Dict:
        """Generate command to clean up containers"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': 'cleanup_containers',
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name', 'cleanup'),
            'command_data': {
                'container_ids': data.get('container_ids', ['all']),
                'remove_volumes': data.get('remove_volumes', True),
                'remove_networks': data.get('remove_networks', True),
                'purpose': 'Clean up attack simulation containers'
            },
            'priority': 'low',
            'timeout': 180,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': []
        }
    
    def generate_generic_command(self, command_type: str, endpoint_id: str, 
                                data: Dict, **kwargs) -> Dict:
        """Generate a generic command"""
        return {
            'command_id': f"cmd_{uuid.uuid4().hex[:12]}",
            'agent_id': endpoint_id,
            'command_type': command_type,
            'scenario_id': kwargs.get('scenario_id'),
            'phase': kwargs.get('phase_name'),
            'command_data': data,
            'priority': 'medium',
            'timeout': 180,
            'created_at': datetime.utcnow().isoformat(),
            'techniques': kwargs.get('techniques', [])
        }
    
    def validate_command(self, command: Dict) -> bool:
        """Validate a command has all required fields"""
        required_fields = ['command_id', 'agent_id', 'command_type', 'command_data']
        return all(field in command for field in required_fields)


# Global instance
command_generator = DynamicCommandGenerator()

