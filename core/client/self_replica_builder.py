#!/usr/bin/env python3
"""
Self-Replica Builder
Creates exact replica of host system in a Docker container
Captures current system state and builds matching container image
"""

import logging
import platform
import socket
import subprocess
import json
import os
import tempfile
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SelfReplicaBuilder:
    """
    Creates exact replica of host system in a container
    Captures system snapshot and builds matching container image
    """
    
    def __init__(self, agent_id: str, docker_client=None):
        self.agent_id = agent_id
        self.docker_client = docker_client
        self.snapshot_cache = None
        self.replica_containers = {}
    
    async def create_self_replica(self, container_name: str = None, 
                                 network: str = 'bridge') -> Optional[Dict]:
        """
        Complete workflow: snapshot + build + run
        
        Args:
            container_name: Name for the replica container
            network: Docker network for the container
        
        Returns:
            Container information dict
        """
        try:
            if not self.docker_client:
                logger.error("Docker not available for replica creation")
                return None
            
            logger.info(f"Creating self-replica container for agent {self.agent_id}")
            
            # Step 1: Capture host snapshot
            snapshot = await self.capture_host_snapshot()
            
            # Step 2: Build replica container image
            image_name = await self.build_replica_container(snapshot)
            
            if not image_name:
                logger.error("Failed to build replica container image")
                return None
            
            # Step 3: Run the replica container
            container = await self.run_replica_container(
                image_name, 
                container_name or f'{self.agent_id}_replica',
                network
            )
            
            if container:
                self.replica_containers[container['id']] = container
                logger.info(f"Successfully created replica container: {container['name']}")
            
            return container
            
        except Exception as e:
            logger.error(f"Self-replica creation failed: {e}")
            return None
    
    async def capture_host_snapshot(self) -> Dict[str, Any]:
        """
        Capture current system state
        
        Returns:
            Complete system snapshot including:
            - OS and version
            - Hostname and network config
            - User accounts
            - Installed software
            - Running services
            - File system structure
        """
        try:
            logger.info("Capturing host system snapshot")
            
            snapshot = {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': self.agent_id,
                
                # Basic system info
                'os': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor()
                },
                
                # Network info
                'network': {
                    'hostname': socket.gethostname(),
                    'fqdn': socket.getfqdn(),
                    'interfaces': await self._get_network_interfaces()
                },
                
                # User accounts
                'users': await self._get_user_accounts(),
                
                # Installed software
                'software': await self._get_installed_software(),
                
                # Running services
                'services': await self._get_running_services(),
                
                # File system
                'filesystem': await self._get_filesystem_snapshot(),
                
                # Environment variables
                'environment': await self._get_environment_variables()
            }
            
            # Cache the snapshot
            self.snapshot_cache = snapshot
            
            logger.info(f"Snapshot captured: {snapshot['os']['system']} {snapshot['os']['release']}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Snapshot capture failed: {e}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    async def _get_network_interfaces(self) -> List[Dict]:
        """Get network interface information"""
        interfaces = []
        try:
            import psutil
            for iface_name, iface_addrs in psutil.net_if_addrs().items():
                iface_info = {'name': iface_name, 'addresses': []}
                for addr in iface_addrs:
                    iface_info['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask
                    })
                interfaces.append(iface_info)
        except Exception as e:
            logger.debug(f"Could not get network interfaces: {e}")
        
        return interfaces
    
    async def _get_user_accounts(self) -> List[str]:
        """Get user accounts on the system"""
        users = []
        try:
            system = platform.system()
            
            if system == 'Windows':
                # Windows users
                result = subprocess.run(
                    ['net', 'user'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('-') and 'command completed' not in line.lower():
                            users.extend([u.strip() for u in line.split() if u.strip()])
            
            elif system == 'Linux' or system == 'Darwin':
                # Linux/Mac users
                with open('/etc/passwd', 'r') as f:
                    for line in f:
                        if line.strip():
                            username = line.split(':')[0]
                            users.append(username)
        
        except Exception as e:
            logger.debug(f"Could not get user accounts: {e}")
        
        return list(set(users))[:20]  # Limit to 20 users
    
    async def _get_installed_software(self) -> List[str]:
        """Get installed software/packages"""
        software = []
        try:
            system = platform.system()
            
            if system == 'Windows':
                # Windows installed programs
                result = subprocess.run(
                    ['wmic', 'product', 'get', 'name'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines[1:]:  # Skip header
                        name = line.strip()
                        if name:
                            software.append(name)
            
            elif system == 'Linux':
                # Try dpkg (Debian/Ubuntu)
                result = subprocess.run(
                    ['dpkg', '--get-selections'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if line.strip():
                            pkg_name = line.split()[0]
                            software.append(pkg_name)
                else:
                    # Try rpm (Red Hat/CentOS)
                    result = subprocess.run(
                        ['rpm', '-qa'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        software = result.stdout.split('\n')
            
            elif system == 'Darwin':
                # macOS installed applications
                apps_dir = Path('/Applications')
                if apps_dir.exists():
                    software = [app.name for app in apps_dir.iterdir() if app.is_dir()]
        
        except Exception as e:
            logger.debug(f"Could not get installed software: {e}")
        
        return list(set(software))[:50]  # Limit to 50 packages
    
    async def _get_running_services(self) -> List[str]:
        """Get running services"""
        services = []
        try:
            system = platform.system()
            
            if system == 'Windows':
                # Windows services
                result = subprocess.run(
                    ['sc', 'query', 'state=', 'all'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'SERVICE_NAME' in line:
                            service_name = line.split(':')[1].strip()
                            services.append(service_name)
            
            elif system == 'Linux':
                # systemd services
                result = subprocess.run(
                    ['systemctl', 'list-units', '--type=service', '--state=running', '--no-pager'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if '.service' in line:
                            parts = line.split()
                            if parts:
                                services.append(parts[0])
        
        except Exception as e:
            logger.debug(f"Could not get running services: {e}")
        
        return services[:30]  # Limit to 30 services
    
    async def _get_filesystem_snapshot(self) -> Dict[str, Any]:
        """Get file system structure snapshot"""
        fs_snapshot = {
            'home_dirs': [],
            'system_dirs': [],
            'important_files': []
        }
        
        try:
            system = platform.system()
            
            if system == 'Windows':
                # Windows key directories
                fs_snapshot['home_dirs'] = ['C:\\Users']
                fs_snapshot['system_dirs'] = ['C:\\Windows', 'C:\\Program Files']
            
            elif system == 'Linux' or system == 'Darwin':
                # Linux/Mac key directories
                fs_snapshot['home_dirs'] = ['/home', '/root']
                fs_snapshot['system_dirs'] = ['/etc', '/usr', '/var']
            
        except Exception as e:
            logger.debug(f"Could not get filesystem snapshot: {e}")
        
        return fs_snapshot
    
    async def _get_environment_variables(self) -> Dict[str, str]:
        """Get important environment variables"""
        env_vars = {}
        try:
            # Get common environment variables
            common_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'TZ']
            for var in common_vars:
                value = os.environ.get(var)
                if value:
                    env_vars[var] = value
        except Exception as e:
            logger.debug(f"Could not get environment variables: {e}")
        
        return env_vars
    
    async def build_replica_container(self, snapshot: Dict) -> Optional[str]:
        """
        Build container image from system snapshot
        
        Args:
            snapshot: System snapshot dict
        
        Returns:
            Image name if successful, None otherwise
        """
        try:
            if not self.docker_client:
                logger.error("Docker not available")
                return None
            
            logger.info("Building replica container image")
            
            # Determine base image based on OS
            system = snapshot.get('os', {}).get('system', '').lower()
            base_image = self._select_base_image(system)
            
            # Generate Dockerfile
            dockerfile_content = self._generate_dockerfile(snapshot, base_image)
            
            # Create temporary build context
            with tempfile.TemporaryDirectory() as temp_dir:
                dockerfile_path = Path(temp_dir) / 'Dockerfile'
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                
                # Build the image
                image_name = f'soc-replica-{self.agent_id}:latest'
                
                try:
                    image, build_logs = self.docker_client.images.build(
                        path=temp_dir,
                        tag=image_name,
                        rm=True,
                        forcerm=True
                    )
                    
                    logger.info(f"Successfully built image: {image_name}")
                    return image_name
                    
                except Exception as e:
                    logger.error(f"Docker image build failed: {e}")
                    return None
        
        except Exception as e:
            logger.error(f"Replica container build failed: {e}")
            return None
    
    def _select_base_image(self, system: str) -> str:
        """Select appropriate base Docker image"""
        if 'windows' in system:
            return 'mcr.microsoft.com/windows/servercore:ltsc2022'
        elif 'linux' in system:
            return 'ubuntu:22.04'
        elif 'darwin' in system:
            # No native macOS containers, use Ubuntu
            return 'ubuntu:22.04'
        else:
            return 'ubuntu:22.04'
    
    def _generate_dockerfile(self, snapshot: Dict, base_image: str) -> str:
        """Generate Dockerfile from snapshot"""
        
        system = snapshot.get('os', {}).get('system', '').lower()
        hostname = snapshot.get('network', {}).get('hostname', 'replica')
        users = snapshot.get('users', [])
        software = snapshot.get('software', [])[:10]  # Limit installations
        
        dockerfile = f"""# Replica container for {self.agent_id}
FROM {base_image}

# Set hostname
ENV HOSTNAME={hostname}

# Set timezone
ENV TZ=UTC

"""
        
        if 'windows' not in system:
            # Linux-based replica
            dockerfile += """# Update system
RUN apt-get update && apt-get install -y \\
    curl \\
    net-tools \\
    iputils-ping \\
    openssh-server \\
    && rm -rf /var/lib/apt/lists/*

"""
            
            # Create user accounts (first 5 users only)
            for user in users[:5]:
                if user and user not in ['root', 'daemon', 'bin', 'sys']:
                    dockerfile += f"RUN useradd -m {user} || true\n"
            
            dockerfile += "\n"
            
            # Add sample data directories
            dockerfile += """# Create sample directories
RUN mkdir -p /home/replica_data /tmp/replica_logs

# Add marker file
RUN echo "SOC Replica Container" > /etc/replica_marker

"""
        
        dockerfile += """# Expose common ports
EXPOSE 22 80 443 3389

# Keep container running
CMD ["tail", "-f", "/dev/null"]
"""
        
        return dockerfile
    
    async def run_replica_container(self, image_name: str, container_name: str,
                                   network: str = 'bridge') -> Optional[Dict]:
        """
        Run the replica container
        
        Args:
            image_name: Docker image to run
            container_name: Name for the container
            network: Docker network
        
        Returns:
            Container information dict
        """
        try:
            if not self.docker_client:
                return None
            
            logger.info(f"Running replica container: {container_name}")
            
            # Run the container
            container = self.docker_client.containers.run(
                image=image_name,
                name=container_name,
                network=network,
                detach=True,
                labels={
                    'soc_replica': 'true',
                    'agent_id': self.agent_id,
                    'created_at': datetime.utcnow().isoformat()
                },
                environment={
                    'SOC_REPLICA': 'true',
                    'AGENT_ID': self.agent_id
                }
            )
            
            return {
                'id': container.id,
                'short_id': container.short_id,
                'name': container.name,
                'image': image_name,
                'status': container.status,
                'network': network,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to run replica container: {e}")
            return None
    
    async def cleanup_replica(self, container_id: str) -> bool:
        """Clean up a replica container"""
        try:
            if not self.docker_client:
                return False
            
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove(force=True)
            
            if container_id in self.replica_containers:
                del self.replica_containers[container_id]
            
            logger.info(f"Cleaned up replica container: {container_id}")
            return True
            
        except Exception as e:
            logger.error(f"Replica cleanup failed: {e}")
            return False
    
    def get_replica_info(self, container_id: str) -> Optional[Dict]:
        """Get information about a replica container"""
        return self.replica_containers.get(container_id)
    
    def list_replicas(self) -> List[Dict]:
        """List all replica containers"""
        return list(self.replica_containers.values())

