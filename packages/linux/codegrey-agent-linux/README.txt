CodeGrey AI SOC Platform - Linux Client Agent
=============================================

SYSTEM REQUIREMENTS:
- Linux (Ubuntu 18.04+, CentOS 7+, RHEL 8+, Amazon Linux 2)
- Python 3.8 or higher
- Root/sudo access for installation
- 2 GB RAM minimum
- 300 MB disk space
- Internet connection to SOC server

OPTIONAL:
- Docker or Podman (for container-based attack simulations)
- BCC tools (for eBPF-based advanced monitoring)

INSTALLATION INSTRUCTIONS:

1. Extract this archive to a folder (e.g., /opt/codegrey-agent):
   sudo mkdir -p /opt/codegrey-agent
   sudo tar -xzf codegrey-agent-linux.tar.gz -C /opt/codegrey-agent

2. Navigate to the folder:
   cd /opt/codegrey-agent

3. Run the installer:
   chmod +x install.sh
   ./install.sh

4. Configure the agent:
   python3 main.py --configure

5. Start the agent:
   python3 main.py

MANUAL INSTALLATION:

If the installer fails:

1. Install Python dependencies:
   pip3 install --user -r requirements.txt

2. Install system dependencies (Ubuntu/Debian):
   sudo apt update
   sudo apt install python3-dev build-essential

3. Install system dependencies (CentOS/RHEL):
   sudo yum groupinstall "Development Tools"
   sudo yum install python3-devel

4. For eBPF support (optional):
   Ubuntu: sudo apt install bpfcc-tools
   CentOS: sudo yum install bcc-tools

5. Edit config.yaml and update server_endpoint

6. Start the agent:
   python3 main.py

FEATURES:

- Real-time log forwarding (syslog, process monitoring, network monitoring)
- eBPF-based advanced monitoring (syscalls, kernel events)
- Remote command execution (bash, shell commands)
- Container management (Docker/Podman support)
- System monitoring and reporting
- Automatic heartbeat and health reporting
- Golden image creation for attack scenarios

CONFIGURATION:

Edit config.yaml to customize:
- server_endpoint: Your SOC server URL
- heartbeat_interval: How often to send heartbeat (seconds)
- log_forwarding: Configure log collection sources
- command_execution: Configure allowed commands
- container_management: Configure Docker/Podman settings
- ebpf_enabled: Enable/disable eBPF monitoring

RUNNING AS A SERVICE:

To run as a systemd service:

1. Copy service file:
   sudo cp codegrey-agent.service /etc/systemd/system/

2. Enable and start:
   sudo systemctl enable codegrey-agent
   sudo systemctl start codegrey-agent

3. Check status:
   sudo systemctl status codegrey-agent

LOGS:

Agent logs are written to: codegrey-agent.log
System logs: journalctl -u codegrey-agent

TROUBLESHOOTING:

1. If Python is not found:
   - Install Python 3.8+: sudo apt install python3 python3-pip

2. If dependencies fail to install:
   - Update pip: python3 -m pip install --upgrade pip
   - Install build tools: sudo apt install build-essential python3-dev

3. If eBPF fails:
   - Install BCC: sudo apt install bpfcc-tools
   - Check kernel version: uname -r (requires 4.1+)

4. If Docker commands fail:
   - Install Docker: curl -fsSL https://get.docker.com | sh
   - Add user to docker group: sudo usermod -aG docker $USER

5. If agent cannot connect to server:
   - Check server URL in config.yaml
   - Verify network connectivity: curl http://15.207.6.45:8080/health
   - Check firewall settings

ADVANCED FEATURES:

- eBPF Monitoring: Kernel-level process and network monitoring
- Container Isolation: Attack simulations in isolated containers
- Golden Images: Automatic container snapshots for restoration
- Real-time Detection: Live threat detection and response

SECURITY:

- Agent runs with minimal privileges by default
- Container isolation for attack simulations
- Encrypted communication (if enabled)
- Audit logging for all operations

SUPPORT:

For support, contact your SOC administrator or check the server logs.

CodeGrey AI SOC Platform
Version: 2024.1.3
