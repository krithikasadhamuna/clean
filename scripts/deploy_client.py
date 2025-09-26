#!/usr/bin/env python3
"""
AI SOC Platform Client Deployment Script
"""

import os
import sys
import platform
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from log_forwarding.shared.utils import setup_logging, get_system_info


logger = logging.getLogger(__name__)


def check_client_dependencies():
    """Check client-specific dependencies"""
    logger.info("Checking client dependencies...")
    
    base_packages = ['aiohttp', 'asyncio', 'pyyaml', 'psutil']
    
    # Platform-specific packages
    if platform.system() == "Windows":
        windows_packages = ['pywin32', 'wmi']
        base_packages.extend(windows_packages)
    elif platform.system() == "Linux":
        linux_packages = []  # Most Linux packages are built-in
        base_packages.extend(linux_packages)
    
    missing_packages = []
    
    for package in base_packages:
        try:
            if package == 'pywin32' and platform.system() == "Windows":
                import win32evtlog
            elif package == 'wmi' and platform.system() == "Windows":
                import wmi
            else:
                __import__(package)
            logger.debug(f"Package {package} is available")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"Package {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Install missing packages with: pip install -r requirements.txt")
        if platform.system() == "Windows":
            logger.info("For Windows: pip install pywin32 python-wmi")
        return False
    
    logger.info("All client dependencies are satisfied")
    return True


def check_permissions():
    """Check required permissions"""
    logger.info("Checking permissions...")
    
    if platform.system() == "Windows":
        # Check if running as administrator for Windows Event Log access
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                logger.warning("Not running as administrator. Windows Event Log access may be limited.")
                logger.info("For full functionality, run as administrator.")
        except Exception:
            logger.warning("Could not check administrator status")
    
    elif platform.system() == "Linux":
        # Check access to log files
        log_files = ['/var/log/syslog', '/var/log/auth.log', '/var/log/audit/audit.log']
        
        accessible_logs = []
        for log_file in log_files:
            if os.path.exists(log_file) and os.access(log_file, os.R_OK):
                accessible_logs.append(log_file)
                logger.debug(f"Can read {log_file}")
            else:
                logger.warning(f"Cannot read {log_file}")
        
        if not accessible_logs:
            logger.warning("No system log files are accessible. May need to run with elevated privileges.")
            logger.info("Consider adding user to 'adm' group: sudo usermod -a -G adm $USER")
    
    return True


def create_client_config(server_endpoint, agent_id=None):
    """Create client configuration"""
    logger.info("Creating client configuration...")
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    client_config_path = config_dir / "client_config.yaml"
    
    if client_config_path.exists():
        logger.info("Client configuration already exists")
        return True
    
    # Get system info for configuration
    system_info = get_system_info()
    
    # Generate agent ID if not provided
    if not agent_id:
        hostname = system_info.get('hostname', 'unknown')
        mac = system_info.get('mac_address', 'unknown')
        agent_id = f"{hostname}_{mac.replace(':', '')[:8]}"
    
    config_content = f"""# AI SOC Platform - Client Configuration

client:
  agent_id: "{agent_id}"
  server_endpoint: "{server_endpoint}"
  api_key: "${{AI_SOC_API_KEY}}"
  reconnect_interval: 30
  heartbeat_interval: 60

log_forwarding:
  enabled: true
  batch_size: 100
  flush_interval: 5
  compression: true
  encryption: true

log_sources:
  system_logs:
    enabled: true
    priority: "high"
  security_logs:
    enabled: true
    priority: "critical"
  application_logs:
    enabled: true
    priority: "medium"
  attack_logs:
    enabled: true
    priority: "critical"

{_get_platform_specific_config()}

filtering:
  enabled: true
  exclude_patterns:
    - ".*DEBUG.*"
    - ".*routine maintenance.*"
  include_patterns:
    - ".*SECURITY.*"
    - ".*ERROR.*"
    - ".*CRITICAL.*"

performance:
  max_memory_mb: 512
  max_cpu_percent: 20
  queue_size: 10000

attack_agent:
  execution_logging: true
  command_logging: true
  result_logging: true
  process_monitoring: true
"""
    
    try:
        with open(client_config_path, 'w') as f:
            f.write(config_content)
        
        logger.info(f"Client configuration created: {client_config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create client configuration: {e}")
        return False


def _get_platform_specific_config():
    """Get platform-specific configuration"""
    if platform.system() == "Windows":
        return """windows:
  event_logs:
    - "Security"
    - "System" 
    - "Application"
    - "Microsoft-Windows-Sysmon/Operational"
    - "Microsoft-Windows-PowerShell/Operational"
    - "Microsoft-Windows-Windows Defender/Operational"
  wmi_enabled: true"""
    
    elif platform.system() == "Linux":
        return """linux:
  log_files:
    - "/var/log/auth.log"
    - "/var/log/syslog"
    - "/var/log/kern.log"
    - "/var/log/audit/audit.log"
  auditd_enabled: true"""
    
    else:
        return """# Platform-specific configuration not available for this OS"""


def install_service(service_name="ai-soc-client"):
    """Install client as system service"""
    logger.info(f"Installing {service_name} as system service...")
    
    if platform.system() == "Windows":
        return _install_windows_service(service_name)
    elif platform.system() == "Linux":
        return _install_linux_service(service_name)
    else:
        logger.warning("Service installation not supported on this platform")
        return False


def _install_windows_service(service_name):
    """Install Windows service"""
    try:
        # Create Windows service script
        service_script = f"""
import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
import asyncio

# Add project path
sys.path.insert(0, r"{Path(__file__).parent.parent.absolute()}")

from log_forwarding.client.client_agent import LogForwardingClient

class AISocClientService(win32serviceutil.ServiceFramework):
    _svc_name_ = "{service_name}"
    _svc_display_name_ = "AI SOC Log Forwarding Client"
    _svc_description_ = "Forwards logs to AI SOC platform for threat detection"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.client = None
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.client:
            asyncio.create_task(self.client.stop())
    
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        self.client = LogForwardingClient()
        asyncio.run(self.client.start())

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AISocClientService)
"""
        
        service_path = Path("service_windows.py")
        with open(service_path, 'w') as f:
            f.write(service_script)
        
        logger.info(f"Windows service script created: {service_path}")
        logger.info(f"To install: python {service_path} install")
        logger.info(f"To start: python {service_path} start")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create Windows service: {e}")
        return False


def _install_linux_service(service_name):
    """Install Linux systemd service"""
    try:
        service_content = f"""[Unit]
Description=AI SOC Log Forwarding Client
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={Path(__file__).parent.parent.absolute()}
ExecStart=/usr/bin/python3 -m log_forwarding.client.client_agent
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_path = Path(f"/etc/systemd/system/{service_name}.service")
        
        logger.info(f"Systemd service file content:")
        logger.info(service_content)
        logger.info(f"To install manually:")
        logger.info(f"1. sudo cp service_linux.service {service_path}")
        logger.info(f"2. sudo systemctl daemon-reload")
        logger.info(f"3. sudo systemctl enable {service_name}")
        logger.info(f"4. sudo systemctl start {service_name}")
        
        # Save service file locally
        local_service_path = Path("service_linux.service")
        with open(local_service_path, 'w') as f:
            f.write(service_content)
        
        logger.info(f"Service file created: {local_service_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create Linux service: {e}")
        return False


def start_client(config_file=None):
    """Start the client"""
    logger.info("Starting AI SOC Log Forwarding Client...")
    
    try:
        from log_forwarding.client.client_agent import main
        import asyncio
        
        # Set command line arguments
        sys.argv = ['client_agent.py']
        if config_file:
            sys.argv.extend(['--config', config_file])
        
        # Run the client
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Client stopped by user")
    except Exception as e:
        logger.error(f"Client startup failed: {e}")
        return False
    
    return True


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy AI SOC Platform Client")
    parser.add_argument('--server', '-s', required=True, help='Server endpoint (e.g., https://soc-server.company.com)')
    parser.add_argument('--agent-id', help='Agent ID (auto-generated if not provided)')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--log-level', '-l', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Log level')
    parser.add_argument('--skip-checks', action='store_true', help='Skip dependency checks')
    parser.add_argument('--install-service', action='store_true', help='Install as system service')
    parser.add_argument('--setup-only', action='store_true', help='Setup only, do not start client')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, 'logs/client_deployment.log')
    
    logger.info("=" * 60)
    logger.info("AI SOC Platform Client Deployment")
    logger.info("=" * 60)
    
    # Show system information
    system_info = get_system_info()
    logger.info(f"Platform: {system_info.get('platform')} {system_info.get('platform_release')}")
    logger.info(f"Hostname: {system_info.get('hostname')}")
    logger.info(f"IP Address: {system_info.get('ip_address')}")
    
    # Check dependencies
    if not args.skip_checks:
        if not check_client_dependencies():
            logger.error("Dependency check failed. Use --skip-checks to bypass.")
            return 1
    
    # Check permissions
    check_permissions()
    
    # Create configuration
    if not create_client_config(args.server, args.agent_id):
        logger.error("Configuration creation failed")
        return 1
    
    # Install as service if requested
    if args.install_service:
        install_service()
    
    if args.setup_only:
        logger.info("Setup completed successfully. Use without --setup-only to start client.")
        return 0
    
    # Start client
    logger.info("All setup completed. Starting client...")
    
    success = start_client(args.config)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
