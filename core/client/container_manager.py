"""
Container Management Engine for Attack Execution
Manages Docker containers for safe attack simulation at endpoints
"""

import asyncio
import logging
import json
import docker
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from shared.models import LogEntry
from shared.utils import safe_json_loads


logger = logging.getLogger(__name__)


class ContainerManager:
    """Manages Docker containers for attack execution"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        
        # Docker client
        self.docker_client = None
        self.docker_available = False
        
        # Container management
        self.active_containers = {}
        self.container_logs = {}
        self.golden_images = {}
        
        # Configuration
        self.container_config = config.get('containers', {})
        self.max_containers = self.container_config.get('max_containers', 5)
        self.log_forwarding_enabled = self.container_config.get('log_forwarding', True)
        
        # Statistics
        self.stats = {
            'containers_created': 0,
            'containers_destroyed': 0,
            'attacks_executed': 0,
            'snapshots_created': 0,
            'start_time': None
        }
        
        self._initialize_docker()
    
    def _initialize_docker(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            
            # Test Docker connection
            self.docker_client.ping()
            self.docker_available = True
            
            logger.info("Docker client initialized successfully")
            
        except docker.errors.DockerException as e:
            logger.error(f"Docker not available: {e}")
            self.docker_available = False
        except Exception as e:
            logger.error(f"Docker initialization failed: {e}")
            self.docker_available = False
    
    async def create_attack_container(self, scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create container for attack execution"""
        try:
            if not self.docker_available:
                return {'success': False, 'error': 'Docker not available'}
            
            container_name = f"phantomstrike-{self.agent_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Determine container image based on target platform
            platform = scenario_config.get('target_platform', 'linux')
            image_name = self._get_container_image(platform)
            
            # Prepare container configuration
            container_config = {
                'image': image_name,
                'name': container_name,
                'detach': True,
                'network_mode': 'bridge',
                'volumes': {
                    # Mount log directory for log forwarding
                    str(Path.cwd() / 'container_logs'): {'bind': '/var/log/attack', 'mode': 'rw'}
                },
                'environment': {
                    'ATTACK_SCENARIO_ID': scenario_config.get('scenario_id', 'unknown'),
                    'AGENT_ID': self.agent_id,
                    'LOG_FORWARDING_ENABLED': str(self.log_forwarding_enabled).lower()
                },
                'labels': {
                    'phantomstrike.agent_id': self.agent_id,
                    'phantomstrike.scenario_id': scenario_config.get('scenario_id', ''),
                    'phantomstrike.created_at': datetime.utcnow().isoformat()
                }
            }
            
            # Create container
            logger.info(f"Creating attack container: {container_name}")
            container = self.docker_client.containers.run(**container_config)
            
            # Store container info
            self.active_containers[container.id] = {
                'container': container,
                'name': container_name,
                'scenario_id': scenario_config.get('scenario_id'),
                'created_at': datetime.utcnow(),
                'platform': platform,
                'status': 'running'
            }
            
            # Start log monitoring for this container
            asyncio.create_task(self._monitor_container_logs(container))
            
            self.stats['containers_created'] += 1
            
            return {
                'success': True,
                'container_id': container.id,
                'container_name': container_name,
                'image': image_name,
                'status': 'running'
            }
            
        except Exception as e:
            logger.error(f"Failed to create attack container: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_container_image(self, platform: str) -> str:
        """Get appropriate container image for platform"""
        image_mapping = {
            'windows': 'mcr.microsoft.com/windows/servercore:ltsc2019',
            'linux': 'ubuntu:22.04',
            'web_app': 'nginx:alpine',
            'database': 'mysql:8.0',
            'domain_controller': 'phantomstrike/windows-dc:latest'
        }
        
        return image_mapping.get(platform, 'ubuntu:22.04')
    
    async def execute_attack_in_container(self, container_id: str, 
                                        technique: str, 
                                        command: str) -> Dict[str, Any]:
        """Execute attack command inside container"""
        try:
            if container_id not in self.active_containers:
                return {'success': False, 'error': 'Container not found'}
            
            container_info = self.active_containers[container_id]
            container = container_info['container']
            
            logger.info(f"Executing {technique} in container {container.name}")
            
            # Execute command in container
            exec_result = container.exec_run(
                cmd=command,
                stdout=True,
                stderr=True,
                stream=False
            )
            
            # Decode output
            stdout = exec_result.output.decode('utf-8', errors='ignore') if exec_result.output else ''
            
            result = {
                'success': exec_result.exit_code == 0,
                'technique': technique,
                'command': command,
                'output': stdout,
                'exit_code': exec_result.exit_code,
                'container_id': container_id,
                'container_name': container.name,
                'executed_at': datetime.utcnow().isoformat()
            }
            
            # Log the execution
            await self._log_container_execution(result)
            
            self.stats['attacks_executed'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Container command execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _monitor_container_logs(self, container) -> None:
        """Monitor container logs and forward them"""
        try:
            logger.info(f"Starting log monitoring for container {container.name}")
            
            # Stream container logs
            for log_line in container.logs(stream=True, follow=True):
                if not self.docker_available:
                    break
                
                try:
                    log_text = log_line.decode('utf-8', errors='ignore').strip()
                    if log_text:
                        # Create log entry
                        log_entry = LogEntry()
                        log_entry.agent_id = self.agent_id
                        log_entry.message = log_text
                        log_entry.source = 'container'
                        log_entry.metadata = {
                            'container_id': container.id,
                            'container_name': container.name,
                            'attack_execution': True
                        }
                        
                        # Add to container logs
                        if container.id not in self.container_logs:
                            self.container_logs[container.id] = []
                        self.container_logs[container.id].append(log_entry)
                        
                        # Forward to main log forwarding system
                        if self.log_forwarding_enabled:
                            await self._forward_container_log(log_entry)
                
                except Exception as e:
                    logger.error(f"Container log processing error: {e}")
        
        except Exception as e:
            logger.error(f"Container log monitoring failed: {e}")
    
    async def _forward_container_log(self, log_entry: LogEntry) -> None:
        """Forward container log to main log forwarding system"""
        try:
            # This would integrate with your log forwarding client
            # Add attack context to the log
            log_entry.tags.append('attack_execution')
            log_entry.tags.append('container_generated')
            
            # Mark as attack-generated log
            log_entry.enriched_data['attack_simulation'] = True
            log_entry.enriched_data['container_source'] = True
            
            # The log would be picked up by your existing log forwarders
            logger.debug(f"Forwarding container log: {log_entry.message[:50]}...")
            
        except Exception as e:
            logger.error(f"Container log forwarding failed: {e}")
    
    async def _log_container_execution(self, execution_result: Dict[str, Any]) -> None:
        """Log container execution for audit trail"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': self.agent_id,
                'event_type': 'container_attack_execution',
                'technique': execution_result.get('technique'),
                'command': execution_result.get('command'),
                'container_id': execution_result.get('container_id'),
                'container_name': execution_result.get('container_name'),
                'success': execution_result.get('success'),
                'output': execution_result.get('output', '')[:1000],  # Truncate for storage
                'exit_code': execution_result.get('exit_code')
            }
            
            # This would be forwarded to your detection system
            logger.info(f"Container execution logged: {execution_result.get('technique')}")
            
        except Exception as e:
            logger.error(f"Container execution logging failed: {e}")
    
    async def create_golden_image_snapshot(self, container_id: str, 
                                         snapshot_name: str = None) -> Dict[str, Any]:
        """Create golden image snapshot of container"""
        try:
            if container_id not in self.active_containers:
                return {'success': False, 'error': 'Container not found'}
            
            container_info = self.active_containers[container_id]
            container = container_info['container']
            
            if not snapshot_name:
                snapshot_name = f"golden-{self.agent_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            logger.info(f"Creating golden image snapshot: {snapshot_name}")
            
            # Commit container to new image (this creates the golden image)
            image = container.commit(
                repository=f"phantomstrike/golden-images",
                tag=snapshot_name,
                message=f"Golden image for agent {self.agent_id}",
                author="PhantomStrike AI"
            )
            
            # Store golden image info
            self.golden_images[snapshot_name] = {
                'image_id': image.id,
                'image_name': f"phantomstrike/golden-images:{snapshot_name}",
                'container_id': container_id,
                'created_at': datetime.utcnow(),
                'size_bytes': self._get_image_size(image),
                'metadata': {
                    'original_container': container.name,
                    'agent_id': self.agent_id,
                    'platform': container_info.get('platform', 'unknown')
                }
            }
            
            self.stats['snapshots_created'] += 1
            
            return {
                'success': True,
                'snapshot_name': snapshot_name,
                'image_id': image.id,
                'image_name': f"phantomstrike/golden-images:{snapshot_name}",
                'size_bytes': self.golden_images[snapshot_name]['size_bytes']
            }
            
        except Exception as e:
            logger.error(f"Golden image snapshot creation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def restore_from_golden_image(self, snapshot_name: str, 
                                      new_container_name: str = None) -> Dict[str, Any]:
        """Restore container from golden image snapshot"""
        try:
            if snapshot_name not in self.golden_images:
                return {'success': False, 'error': 'Golden image not found'}
            
            golden_image = self.golden_images[snapshot_name]
            image_name = golden_image['image_name']
            
            if not new_container_name:
                new_container_name = f"restored-{self.agent_id}-{datetime.utcnow().strftime('%H%M%S')}"
            
            logger.info(f"Restoring from golden image: {snapshot_name}")
            
            # Create new container from golden image
            container = self.docker_client.containers.run(
                image=image_name,
                name=new_container_name,
                detach=True,
                volumes={
                    str(Path.cwd() / 'container_logs'): {'bind': '/var/log/attack', 'mode': 'rw'}
                },
                environment={
                    'RESTORED_FROM': snapshot_name,
                    'AGENT_ID': self.agent_id,
                    'RESTORED_AT': datetime.utcnow().isoformat()
                }
            )
            
            # Store restored container info
            self.active_containers[container.id] = {
                'container': container,
                'name': new_container_name,
                'created_at': datetime.utcnow(),
                'restored_from': snapshot_name,
                'status': 'running'
            }
            
            # Start log monitoring
            asyncio.create_task(self._monitor_container_logs(container))
            
            return {
                'success': True,
                'container_id': container.id,
                'container_name': new_container_name,
                'restored_from': snapshot_name,
                'status': 'running'
            }
            
        except Exception as e:
            logger.error(f"Golden image restoration failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def destroy_container(self, container_id: str, 
                              create_snapshot: bool = False) -> Dict[str, Any]:
        """Destroy attack container"""
        try:
            if container_id not in self.active_containers:
                return {'success': False, 'error': 'Container not found'}
            
            container_info = self.active_containers[container_id]
            container = container_info['container']
            
            # Create snapshot before destruction if requested
            snapshot_result = None
            if create_snapshot:
                snapshot_name = f"pre-destroy-{container.name}"
                snapshot_result = await self.create_golden_image_snapshot(container_id, snapshot_name)
            
            logger.info(f"Destroying container: {container.name}")
            
            # Stop and remove container
            container.stop(timeout=10)
            container.remove()
            
            # Clean up tracking
            del self.active_containers[container_id]
            if container_id in self.container_logs:
                del self.container_logs[container_id]
            
            self.stats['containers_destroyed'] += 1
            
            return {
                'success': True,
                'container_id': container_id,
                'destroyed_at': datetime.utcnow().isoformat(),
                'snapshot_created': snapshot_result.get('success', False) if snapshot_result else False
            }
            
        except Exception as e:
            logger.error(f"Container destruction failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def execute_attack_technique(self, container_id: str, 
                                     technique: str, 
                                     parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MITRE ATT&CK technique in container"""
        try:
            if not self.docker_available:
                return {'success': False, 'error': 'Docker not available'}
            
            if container_id not in self.active_containers:
                return {'success': False, 'error': 'Container not found'}
            
            container_info = self.active_containers[container_id]
            container = container_info['container']
            
            # Generate technique-specific command
            command = self._generate_technique_command(technique, parameters)
            
            if not command:
                return {'success': False, 'error': f'No command generated for {technique}'}
            
            logger.info(f"🎯 Executing {technique} in container {container.name}")
            
            # Execute in container
            exec_result = container.exec_run(
                cmd=command,
                stdout=True,
                stderr=True,
                stream=False,
                environment={'TECHNIQUE': technique}
            )
            
            # Process result
            stdout = exec_result.output.decode('utf-8', errors='ignore') if exec_result.output else ''
            
            result = {
                'success': exec_result.exit_code == 0,
                'technique': technique,
                'command': command,
                'output': stdout,
                'exit_code': exec_result.exit_code,
                'container_id': container_id,
                'container_name': container.name,
                'executed_at': datetime.utcnow().isoformat(),
                'parameters': parameters
            }
            
            # Log execution
            await self._log_technique_execution(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Technique execution in container failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_technique_command(self, technique: str, parameters: Dict[str, Any]) -> Optional[str]:
        """Generate command for MITRE ATT&CK technique"""
        
        # Map MITRE techniques to actual commands
        technique_commands = {
            'T1082': 'uname -a && cat /proc/version && whoami',  # System Information Discovery
            'T1083': 'find /home -type f -name "*.txt" | head -10',  # File and Directory Discovery
            'T1057': 'ps aux | head -20',  # Process Discovery
            'T1033': 'whoami && id',  # System Owner/User Discovery
            'T1016': 'ip addr show && cat /etc/resolv.conf',  # System Network Configuration Discovery
            'T1018': 'ping -c 1 8.8.8.8 && nslookup google.com',  # Remote System Discovery
            'T1059.004': 'echo "PhantomStrike test execution" > /tmp/test.txt',  # Unix Shell
            'T1005': 'find /home -name "*.doc" -o -name "*.pdf" | head -5',  # Data from Local System
            'T1039': 'ls -la /tmp && ls -la /var/tmp',  # Data from Network Shared Drive
        }
        
        # Get base command
        base_command = technique_commands.get(technique)
        
        if not base_command:
            # Fallback to parameter-specified command
            return parameters.get('command')
        
        # Customize command with parameters
        if parameters.get('target_path'):
            base_command = base_command.replace('/home', parameters['target_path'])
        
        return base_command
    
    async def _log_technique_execution(self, execution_result: Dict[str, Any]) -> None:
        """Log technique execution for detection analysis"""
        try:
            # Create detailed log entry for the attack execution
            log_data = {
                'timestamp': execution_result['executed_at'],
                'agent_id': self.agent_id,
                'source': 'container_attack',
                'event_type': 'attack_technique_execution',
                'level': 'info',
                'message': f"Attack technique {execution_result['technique']} executed in container",
                'attack_technique': execution_result['technique'],
                'attack_command': execution_result['command'],
                'attack_result': 'success' if execution_result['success'] else 'failure',
                'container_id': execution_result['container_id'],
                'container_name': execution_result['container_name'],
                'output': execution_result['output'],
                'exit_code': execution_result['exit_code'],
                'tags': ['attack_execution', 'container_generated', 'phantomstrike']
            }
            
            # This log will be picked up by your detection agents!
            logger.info(f"Attack execution logged: {execution_result['technique']}")
            
        except Exception as e:
            logger.error(f"Technique execution logging failed: {e}")
    
    def _get_image_size(self, image) -> int:
        """Get Docker image size"""
        try:
            return image.attrs.get('Size', 0)
        except Exception:
            return 0
    
    async def cleanup_containers(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """Clean up old containers"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            containers_cleaned = 0
            
            for container_id, container_info in list(self.active_containers.items()):
                if container_info['created_at'] < cutoff_time:
                    result = await self.destroy_container(container_id, create_snapshot=True)
                    if result.get('success'):
                        containers_cleaned += 1
            
            return {
                'success': True,
                'containers_cleaned': containers_cleaned,
                'cleanup_completed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Container cleanup failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_container_status(self) -> Dict[str, Any]:
        """Get status of all managed containers"""
        try:
            container_status = {}
            
            for container_id, container_info in self.active_containers.items():
                container = container_info['container']
                
                try:
                    container.reload()  # Refresh container status
                    status = {
                        'name': container_info['name'],
                        'status': container.status,
                        'created_at': container_info['created_at'].isoformat(),
                        'platform': container_info.get('platform', 'unknown'),
                        'scenario_id': container_info.get('scenario_id', 'unknown'),
                        'logs_count': len(self.container_logs.get(container_id, [])),
                        'uptime_seconds': (datetime.utcnow() - container_info['created_at']).total_seconds()
                    }
                    container_status[container_id] = status
                
                except Exception as e:
                    logger.error(f"Failed to get status for container {container_id}: {e}")
            
            return {
                'docker_available': self.docker_available,
                'active_containers': len(self.active_containers),
                'golden_images': len(self.golden_images),
                'containers': container_status,
                'statistics': self.stats
            }
            
        except Exception as e:
            logger.error(f"Container status check failed: {e}")
            return {'docker_available': False, 'error': str(e)}
