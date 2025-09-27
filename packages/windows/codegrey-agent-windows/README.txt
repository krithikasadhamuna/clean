CodeGrey AI SOC Platform - Windows Client Agent
==============================================

SYSTEM REQUIREMENTS:
- Windows 10/11 (64-bit)
- Python 3.8 or higher
- Administrator privileges
- 4 GB RAM minimum
- 500 MB disk space
- Internet connection to SOC server

OPTIONAL:
- Docker Desktop (for container-based attack simulations)

INSTALLATION INSTRUCTIONS:

1. Extract this ZIP file to a folder (e.g., C:\CodeGrey-Agent)

2. Open Command Prompt as Administrator

3. Navigate to the extracted folder:
   cd C:\CodeGrey-Agent

4. Run the installer:
   install.bat

5. Configure the agent (replace SERVER_URL with your SOC server):
   python main.py --configure --server=http://15.207.6.45:8080

6. Start the agent:
   python main.py

MANUAL INSTALLATION:

If the installer fails, install manually:

1. Install Python dependencies:
   pip install -r requirements.txt

2. Edit config.yaml and update server_endpoint

3. Start the agent:
   python main.py

FEATURES:

- Real-time log forwarding (Windows Event Logs, Process monitoring, Network monitoring)
- Remote command execution (PowerShell, CMD)
- Container management (Docker-based attack simulations)
- System monitoring and reporting
- Automatic heartbeat and health reporting

CONFIGURATION:

Edit config.yaml to customize:
- server_endpoint: Your SOC server URL
- heartbeat_interval: How often to send heartbeat (seconds)
- log_forwarding: Configure log collection sources
- command_execution: Configure allowed commands
- container_management: Configure Docker settings

LOGS:

Agent logs are written to: codegrey-agent.log

TROUBLESHOOTING:

1. If Python is not found:
   - Install Python from https://python.org
   - Make sure "Add to PATH" is checked during installation

2. If dependencies fail to install:
   - Run Command Prompt as Administrator
   - Update pip: python -m pip install --upgrade pip

3. If Docker commands fail:
   - Install Docker Desktop from https://docker.com
   - Ensure Docker is running

4. If agent cannot connect to server:
   - Check server URL in config.yaml
   - Verify network connectivity
   - Check firewall settings

SUPPORT:

For support, contact your SOC administrator or check the server logs.

CodeGrey AI SOC Platform
Version: 2024.1.3
