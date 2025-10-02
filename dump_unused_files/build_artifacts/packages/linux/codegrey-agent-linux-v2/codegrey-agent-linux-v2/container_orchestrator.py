"""
Client-side container orchestrator for running attack scenarios locally
"""

import os
import time
import json
import asyncio
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import psutil

# Docker for container orchestration
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class ClientContainerOrchestrator:
    """Client-side container orchestrator for running attack scenarios locally"""
    
    def __init__(self, agent):
        self.agent = agent
        self.logger = agent.logger
        self.docker_client = None
        self.running_containers = {}
        self.telemetry_streams = {}
        
        # Initialize Docker client
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker is not available")
            
        try:
            self.docker_client = docker.from_env()
            self.logger.info("Docker client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            raise
    
    def execute_attack_scenario(self, scenario_config: Dict[str, Any]) -> str:
        """Execute attack scenario in a container and stream telemetry"""
        container_id = f"attack-{int(time.time())}"
        
        try:
            # Create container based on target system configuration
            container_config = self._create_container_config(scenario_config)
            
            # Get attack container image
            image_name = self._prepare_attack_image(scenario_config)
            
            # Pull image if not available locally
            try:
                self.docker_client.images.get(image_name)
            except docker.errors.ImageNotFound:
                self.logger.info(f"Pulling image: {image_name}")
                self.docker_client.images.pull(image_name)
            
            # Run container
            container = self.docker_client.containers.run(
                image_name,
                command=scenario_config.get('command', '/bin/bash'),
                detach=True,
                name=container_id,
                network_mode='host',  # Use host network for realistic testing
                volumes=scenario_config.get('volumes', {}),
                environment=scenario_config.get('environment', {}),
                **container_config
            )
            
            self.running_containers[container_id] = container
            
            # Start telemetry streaming
            self._start_telemetry_streaming(container_id, container)
            
            self.logger.info(f"Attack scenario started in container: {container_id}")
            return container_id
            
        except Exception as e:
            self.logger.error(f"Failed to execute attack scenario: {e}")
            raise
    
    def _create_container_config(self, scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create container configuration based on target system profile"""
        target_system = scenario_config.get('target_system', {})
        
        # Calculate memory limit (use 50% of target system memory or 2GB max)
        target_memory = target_system.get('memory_total', 2 * 1024**3)  # Default 2GB
        mem_limit = min(target_memory // 2, 2 * 1024**3)  # Max 2GB
        
        config = {
            'mem_limit': f"{mem_limit // (1024**2)}m",  # Convert to MB
            'cpu_count': min(psutil.cpu_count(), 2),  # Limit CPU usage
            'security_opt': ['seccomp:unconfined'],  # Allow system calls for testing
            'cap_add': ['NET_ADMIN', 'SYS_ADMIN'],  # Network and system administration
            'remove': True,  # Auto-remove when stopped
        }
        
        return config
    
    def _prepare_attack_image(self, scenario_config: Dict[str, Any]) -> str:
        """Prepare attack container image based on target system"""
        target_system = scenario_config.get('target_system', {})
        attack_type = scenario_config.get('attack_type', 'generic')
        
        return self._get_base_image(target_system, attack_type)
    
    def _get_base_image(self, target_system: Dict[str, Any], attack_type: str) -> str:
        """Get appropriate base image for target system and attack type"""
        
        # Choose image based on attack type
        if attack_type == 'web_attack':
            return 'kalilinux/kali-rolling'  # Web penetration testing tools
        elif attack_type == 'network_attack':
            return 'kalilinux/kali-rolling'  # Network penetration testing tools
        elif attack_type == 'phishing_attack':
            return 'ubuntu:20.04'  # Lightweight for phishing infrastructure
        elif attack_type == 'lateral_movement':
            return 'kalilinux/kali-rolling'  # Advanced penetration testing
        else:
            return 'kalilinux/kali-rolling'  # Default to Kali Linux
    
    def _start_telemetry_streaming(self, container_id: str, container):
        """Start streaming telemetry data from container to server"""
        
        def stream_container_logs():
            """Stream container logs to server"""
            try:
                self.logger.info(f"Starting log streaming for container: {container_id}")
                
                # Stream container logs
                for log_line in container.logs(stream=True, follow=True):
                    if not log_line:
                        continue
                        
                    telemetry_data = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'container_id': container_id,
                        'agent_id': self.agent.agent_id,
                        'type': 'container_log',
                        'data': log_line.decode('utf-8', errors='ignore').strip(),
                        'attack_scenario': {
                            'target_system': self.agent._get_system_info(),
                            'network_info': self._get_network_context()
                        }
                    }
                    
                    # Send container logs as regular logs to the log ingestion system
                    self._send_container_log_as_regular_log(log_line.decode('utf-8', errors='ignore').strip())
                    
            except Exception as e:
                self.logger.error(f"Error streaming logs for {container_id}: {e}")
        
        def stream_container_stats():
            """Stream container resource statistics"""
            try:
                self.logger.info(f"Starting stats streaming for container: {container_id}")
                
                for stats in container.stats(stream=True):
                    if not stats:
                        continue
                        
                    telemetry_data = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'container_id': container_id,
                        'agent_id': self.agent.agent_id,
                        'type': 'container_stats',
                        'data': {
                            'cpu_usage': self._calculate_cpu_usage(stats.get('cpu_stats', {})),
                            'memory_usage': stats.get('memory_stats', {}),
                            'network_io': stats.get('networks', {}),
                            'block_io': stats.get('blkio_stats', {})
                        }
                    }
                    
                    # Log container stats every 30 seconds
                    stats_message = f"Container {container_id} - CPU: {self._calculate_cpu_usage(stats.get('cpu_stats', {}))}%, Memory: {stats.get('memory_stats', {}).get('usage', 0)} bytes"
                    self._send_container_log_as_regular_log(stats_message)
                    time.sleep(30)
                    
            except Exception as e:
                self.logger.error(f"Error streaming stats for {container_id}: {e}")
        
        # Start telemetry streaming in background threads
        log_thread = threading.Thread(target=stream_container_logs, daemon=True)
        stats_thread = threading.Thread(target=stream_container_stats, daemon=True)
        
        log_thread.start()
        stats_thread.start()
        
        self.telemetry_streams[container_id] = {
            'log_thread': log_thread,
            'stats_thread': stats_thread
        }
    
    def _calculate_cpu_usage(self, cpu_stats: Dict) -> float:
        """Calculate CPU usage percentage from Docker stats"""
        try:
            cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                       cpu_stats.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                          cpu_stats.get('precpu_stats', {}).get('system_cpu_usage', 0)
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_usage = (cpu_delta / system_delta) * 100.0
                return round(cpu_usage, 2)
        except:
            pass
        return 0.0
    
    def _get_network_context(self) -> Dict[str, Any]:
        """Get current network context for attack correlation"""
        try:
            network_info = {
                'local_ip': self._get_local_ip(),
                'open_ports': self._get_open_ports(),
                'active_connections': len(psutil.net_connections()),
                'network_interfaces': len(psutil.net_if_addrs())
            }
            return network_info
        except Exception as e:
            self.logger.error(f"Failed to get network context: {e}")
            return {}
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Unknown"
    
    def _get_open_ports(self) -> List[int]:
        """Get list of open ports on the system"""
        try:
            open_ports = []
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    open_ports.append(conn.laddr.port)
            return sorted(list(set(open_ports)))[:10]  # Limit to first 10
        except:
            return []
    
    def _send_container_log_as_regular_log(self, log_message: str):
        """Send container log as regular log entry through the log ingestion system"""
        try:
            from datetime import datetime
            import json
            
            # Create log entry in the same format as regular agent logs
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'INFO',
                'source': 'AttackContainer',
                'message': log_message,
                'hostname': self.agent.agent_id,
                'platform': 'Container',
                'agent_type': 'attack_agent',
                'container_context': True,
                'network_info': self._get_network_context()
            }
            
            # Send to regular log ingestion endpoint
            url = f"{self.agent.server_url}/api/logs/ingest"
            logs_data = {
                'agent_id': self.agent.agent_id,
                'logs': [log_entry]
            }
            
            response = requests.post(
                url,
                json=logs_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.debug(f"Container log sent successfully")
            else:
                self.logger.warning(f"Failed to send container log: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error sending container log: {e}")
    
    def execute_command_in_container(self, container_id: str, command: str) -> Dict[str, Any]:
        """Execute command in running container"""
        try:
            if container_id not in self.running_containers:
                return {'success': False, 'error': 'Container not found'}
            
            container = self.running_containers[container_id]
            result = container.exec_run(command)
            
            return {
                'success': True,
                'exit_code': result.exit_code,
                'output': result.output.decode('utf-8', errors='ignore')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_container(self, container_id: str):
        """Stop and remove attack container"""
        try:
            if container_id in self.running_containers:
                container = self.running_containers[container_id]
                
                # Stop telemetry streaming
                if container_id in self.telemetry_streams:
                    # Note: Thread cleanup is handled by daemon=True
                    del self.telemetry_streams[container_id]
                
                # Stop and remove container
                container.stop(timeout=10)
                container.remove(force=True)
                
                del self.running_containers[container_id]
                self.logger.info(f"Container {container_id} stopped and removed")
                
                # Send final log
                self._send_container_log_as_regular_log(f"Container {container_id} stopped and removed")
                
        except Exception as e:
            self.logger.error(f"Error stopping container {container_id}: {e}")
    
    def get_running_containers(self) -> List[Dict[str, Any]]:
        """Get list of currently running attack containers with details"""
        containers = []
        
        for container_id, container in self.running_containers.items():
            try:
                container.reload()  # Refresh container info
                containers.append({
                    'id': container_id,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'status': container.status,
                    'created': container.attrs.get('Created', ''),
                    'uptime': self._calculate_uptime(container.attrs.get('Created', ''))
                })
            except Exception as e:
                self.logger.error(f"Error getting info for container {container_id}: {e}")
        
        return containers
    
    def get_attack_agents_api_format(self) -> Dict[str, Any]:
        """Get running attack agents in the API format like PhantomStrike AI"""
        agents = []
        
        # Map attack types to agent names
        agent_mapping = {
            'web_attack': {
                'id': 'phantomstrike_web_ai',
                'name': 'PhantomStrike Web AI',
                'capabilities': ['Web Vulnerability Scanning', 'SQL Injection', 'XSS Testing']
            },
            'network_attack': {
                'id': 'phantomstrike_network_ai', 
                'name': 'PhantomStrike Network AI',
                'capabilities': ['Network Scanning', 'Port Discovery', 'Service Enumeration']
            },
            'phishing_attack': {
                'id': 'phantomstrike_phishing_ai',
                'name': 'PhantomStrike Phishing AI', 
                'capabilities': ['Email Campaigns', 'Credential Harvesting', 'Social Engineering']
            },
            'lateral_movement': {
                'id': 'phantomstrike_lateral_ai',
                'name': 'PhantomStrike Lateral AI',
                'capabilities': ['Privilege Escalation', 'Lateral Movement', 'Persistence']
            }
        }
        
        # Get running containers and map to attack agents
        for container_id, container in self.running_containers.items():
            try:
                container.reload()
                
                # Determine attack type from container environment or image
                attack_type = 'generic'
                if hasattr(container, 'attrs'):
                    env_vars = container.attrs.get('Config', {}).get('Env', [])
                    for env_var in env_vars:
                        if env_var.startswith('ATTACK_TYPE='):
                            attack_type = env_var.split('=')[1]
                            break
                
                # Get agent info or use default
                agent_info = agent_mapping.get(attack_type, {
                    'id': f'phantomstrike_{attack_type}_ai',
                    'name': f'PhantomStrike {attack_type.title()} AI',
                    'capabilities': ['Attack Planning', 'Scenario Generation', 'Red Team Operations']
                })
                
                # Calculate uptime
                created_time = container.attrs.get('Created', '')
                uptime = self._calculate_uptime(created_time)
                
                agent = {
                    'id': f"{agent_info['id']}_{container_id}",
                    'name': agent_info['name'],
                    'type': 'attack',
                    'status': 'active' if container.status == 'running' else 'inactive',
                    'location': 'Client Network',
                    'lastActivity': f'Active - Uptime: {uptime}',
                    'capabilities': agent_info['capabilities'],
                    'platform': 'Container Agent',
                    'container_id': container_id,
                    'attack_type': attack_type
                }
                
                agents.append(agent)
                
            except Exception as e:
                self.logger.error(f"Error getting agent info for container {container_id}: {e}")
        
        # Add default agents if no containers running
        if not agents:
            agents = [
                {
                    'id': 'phantomstrike_ai',
                    'name': 'PhantomStrike AI',
                    'type': 'attack',
                    'status': 'inactive',
                    'location': 'Client Network',
                    'lastActivity': 'Ready for deployment',
                    'capabilities': ['Attack Planning', 'Scenario Generation', 'Red Team Operations'],
                    'platform': 'Container Agent (Standby)'
                }
            ]
        
        return {
            'status': 'success',
            'agents': agents
        }
    
    def _calculate_uptime(self, created_time: str) -> str:
        """Calculate container uptime"""
        try:
            from dateutil import parser
            created = parser.parse(created_time)
            uptime = datetime.utcnow() - created.replace(tzinfo=None)
            return str(uptime).split('.')[0]  # Remove microseconds
        except:
            return "Unknown"
    
    def cleanup_all_containers(self):
        """Stop and remove all running attack containers"""
        container_ids = list(self.running_containers.keys())
        
        for container_id in container_ids:
            self.stop_container(container_id)
        
        self.logger.info(f"Cleaned up {len(container_ids)} containers")
    
    def get_container_logs(self, container_id: str, tail: int = 100) -> List[str]:
        """Get recent logs from a container"""
        try:
            if container_id not in self.running_containers:
                return []
            
            container = self.running_containers[container_id]
            logs = container.logs(tail=tail).decode('utf-8', errors='ignore')
            return logs.split('\n')
            
        except Exception as e:
            self.logger.error(f"Error getting logs for container {container_id}: {e}")
            return []
