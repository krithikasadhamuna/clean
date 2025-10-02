CodeGrey AI SOC Platform - macOS Client Agent
=============================================

SYSTEM REQUIREMENTS:
- macOS 11.0 (Big Sur) or later
- Python 3.8 or higher
- Administrator privileges
- 3 GB RAM minimum
- 400 MB disk space
- Internet connection to SOC server

OPTIONAL:
- Docker Desktop (for container-based attack simulations)
- Homebrew (for additional tools)

INSTALLATION INSTRUCTIONS:

1. Extract this archive to a folder (e.g., /Applications/CodeGrey-Agent):
   mkdir -p /Applications/CodeGrey-Agent
   tar -xzf codegrey-agent-macos.tar.gz -C /Applications/CodeGrey-Agent

2. Navigate to the folder:
   cd /Applications/CodeGrey-Agent

3. Run the installer:
   chmod +x install.sh
   ./install.sh

4. Configure the agent:
   python3 main.py --configure

5. Start the agent:
   python3 main.py

MACOS PRIVACY & SECURITY:

macOS will ask for permissions when the agent starts:
- Click "Allow" when prompted for file access
- Click "Allow" when prompted for network access
- Click "Allow" when prompted for monitoring other applications

These permissions are required for the agent to function properly.

MANUAL INSTALLATION:

If the installer fails:

1. Install Python dependencies:
   pip3 install --user -r requirements.txt

2. Install Homebrew (if not already installed):
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

3. Install additional tools (optional):
   brew install watch htop

4. Edit config.yaml and update server_endpoint

5. Start the agent:
   python3 main.py

FEATURES:

- Real-time log forwarding (system logs, process monitoring, network monitoring)
- XProtect integration (macOS built-in security)
- Remote command execution (bash, zsh commands)
- Container management (Docker Desktop support)
- System monitoring and reporting
- Automatic heartbeat and health reporting
- Golden image creation for attack scenarios
- Privacy-focused monitoring

CONFIGURATION:

Edit config.yaml to customize:
- server_endpoint: Your SOC server URL
- heartbeat_interval: How often to send heartbeat (seconds)
- log_forwarding: Configure log collection sources
- command_execution: Configure allowed commands
- container_management: Configure Docker settings
- macos_specific: macOS-specific features

RUNNING IN BACKGROUND:

To run the agent in background:
   nohup python3 main.py &

To stop background agent:
   pkill -f "python3 main.py"

LOGS:

Agent logs are written to: codegrey-agent.log
View logs: tail -f codegrey-agent.log

TROUBLESHOOTING:

1. If Python is not found:
   - Install from https://python.org/downloads/
   - Or use Homebrew: brew install python3

2. If dependencies fail to install:
   - Update pip: python3 -m pip install --upgrade pip
   - Install Xcode tools: xcode-select --install

3. If Docker commands fail:
   - Install Docker Desktop from https://docker.com/products/docker-desktop
   - Ensure Docker Desktop is running

4. If agent cannot connect to server:
   - Check server URL in config.yaml
   - Verify network connectivity: curl http://15.207.6.45:8080/health
   - Check macOS firewall settings

5. If permission errors occur:
   - Grant necessary permissions in System Preferences > Security & Privacy
   - Run with sudo if required: sudo python3 main.py

MACOS-SPECIFIC FEATURES:

- XProtect Integration: Works with macOS built-in antivirus
- Privacy-Focused: Respects macOS privacy controls
- Keychain Access: Optional integration with macOS Keychain
- System Integrity Protection: Compatible with SIP
- Notarization Ready: Code signing compatible

SUPPORT:

For support, contact your SOC administrator or check the server logs.

CodeGrey AI SOC Platform
Version: 2024.1.3
