#!/usr/bin/env python3
"""
Dynamic Container Builder
Builds any type of container based on command (SMTP, FTP, Web, Database, etc.)
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DynamicContainerBuilder:
    """Builds any infrastructure container on demand"""
    
    def __init__(self, agent_id: str, docker_client=None):
        self.agent_id = agent_id
        self.docker_client = docker_client
        self.active_containers = {}
    
    async def build_container(self, command_type: str, config: Dict) -> Optional[Dict]:
        """Build container based on command type"""
        try:
            if not self.docker_client:
                logger.error("Docker not available")
                return None
            
            if command_type == 'deploy_smtp_container':
                return await self.build_smtp_container(config)
            elif command_type == 'deploy_ftp_container':
                return await self.build_ftp_container(config)
            elif command_type == 'deploy_web_server_container':
                return await self.build_web_server_container(config)
            elif command_type == 'deploy_database_container':
                return await self.build_database_container(config)
            else:
                logger.warning(f"Unknown container type: {command_type}")
                return None
                
        except Exception as e:
            logger.error(f"Container build failed: {e}")
            return None
    
    async def build_smtp_container(self, config: Dict) -> Optional[Dict]:
        """Build SMTP server container"""
        try:
            container = self.docker_client.containers.run(
                image='namshi/smtp:latest',
                name=config.get('container_name', 'smtp_server'),
                network=config.get('network', 'bridge'),
                ports=config.get('ports', {'25': '25'}),
                detach=True,
                environment={
                    'RELAY_NETWORKS': ':192.168.0.0/16:10.0.0.0/8',
                    'SMARTHOST_ADDRESS': '127.0.0.1',
                    'SMARTHOST_PORT': '25'
                },
                labels={'soc_infrastructure': 'smtp', 'agent_id': self.agent_id}
            )
            
            info = {'id': container.id, 'name': container.name, 'type': 'smtp', 'status': container.status}
            self.active_containers[container.id] = info
            logger.info(f"SMTP container created: {container.name}")
            return info
            
        except Exception as e:
            logger.error(f"SMTP container creation failed: {e}")
            return None
    
    async def build_ftp_container(self, config: Dict) -> Optional[Dict]:
        """Build FTP server container"""
        try:
            container = self.docker_client.containers.run(
                image='fauria/vsftpd:latest',
                name=config.get('container_name', 'ftp_server'),
                network=config.get('network', 'bridge'),
                ports=config.get('ports', {'21': '21'}),
                detach=True,
                environment={
                    'FTP_USER': 'ftpuser',
                    'FTP_PASS': 'ftppass',
                    'PASV_ADDRESS': '127.0.0.1'
                },
                labels={'soc_infrastructure': 'ftp', 'agent_id': self.agent_id}
            )
            
            info = {'id': container.id, 'name': container.name, 'type': 'ftp', 'status': container.status}
            self.active_containers[container.id] = info
            logger.info(f"FTP container created: {container.name}")
            return info
            
        except Exception as e:
            logger.error(f"FTP container creation failed: {e}")
            return None
    
    async def build_web_server_container(self, config: Dict) -> Optional[Dict]:
        """Build web server container"""
        try:
            container = self.docker_client.containers.run(
                image=config.get('image', 'nginx:latest'),
                name=config.get('container_name', 'web_server'),
                network=config.get('network', 'bridge'),
                ports=config.get('ports', {'80': '80'}),
                detach=True,
                labels={'soc_infrastructure': 'web', 'agent_id': self.agent_id}
            )
            
            info = {'id': container.id, 'name': container.name, 'type': 'web', 'status': container.status}
            self.active_containers[container.id] = info
            logger.info(f"Web server container created: {container.name}")
            return info
            
        except Exception as e:
            logger.error(f"Web server container creation failed: {e}")
            return None
    
    async def build_database_container(self, config: Dict) -> Optional[Dict]:
        """Build database server container"""
        try:
            db_type = config.get('db_type', 'mysql')
            image_map = {'mysql': 'mysql:latest', 'postgres': 'postgres:latest'}
            
            container = self.docker_client.containers.run(
                image=image_map.get(db_type, 'mysql:latest'),
                name=config.get('container_name', f'{db_type}_server'),
                network=config.get('network', 'bridge'),
                ports=config.get('ports', {'3306': '3306'}),
                detach=True,
                environment={
                    'MYSQL_ROOT_PASSWORD': 'soc_password',
                    'MYSQL_DATABASE': 'soc_database'
                },
                labels={'soc_infrastructure': 'database', 'agent_id': self.agent_id}
            )
            
            info = {'id': container.id, 'name': container.name, 'type': 'database', 'status': container.status}
            self.active_containers[container.id] = info
            logger.info(f"Database container created: {container.name}")
            return info
            
        except Exception as e:
            logger.error(f"Database container creation failed: {e}")
            return None
    
    async def cleanup_container(self, container_id: str) -> bool:
        """Clean up a container"""
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove(force=True)
            
            if container_id in self.active_containers:
                del self.active_containers[container_id]
            
            logger.info(f"Cleaned up container: {container_id}")
            return True
            
        except Exception as e:
            logger.error(f"Container cleanup failed: {e}")
            return False

