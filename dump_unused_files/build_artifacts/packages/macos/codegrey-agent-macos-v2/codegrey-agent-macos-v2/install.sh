#!/bin/bash

echo "========================================"
echo "CodeGrey AI SOC Platform - macOS Agent v2.0"
echo "Privacy-First Dynamic Installation"
echo "========================================"
echo

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "ERROR: This installer is for macOS only"
    exit 1
fi

# Check macOS version
MACOS_VERSION=$(sw_vers -productVersion)
echo "macOS version: $MACOS_VERSION"

# Check if version is 11.0 or later
if [[ $(echo "$MACOS_VERSION" | cut -d. -f1) -lt 11 ]]; then
    echo "ERROR: macOS 11.0 (Big Sur) or later required"
    exit 1
fi

echo "[1/7] Checking system requirements..."

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run with sudo for system installation"
    exit 1
fi

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3 via Homebrew..."
    
    # Install Homebrew if not present
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install python3
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

echo "[2/7] Installing system dependencies..."

# Install system tools via Homebrew
if command -v brew &> /dev/null; then
    brew install nmap
    brew install tcpdump
else
    echo "WARNING: Homebrew not available. Some features may be limited."
fi

echo "[3/7] Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python dependencies"
    exit 1
fi

echo "[4/7] Setting up directories..."

# Create application directories
mkdir -p /opt/codegrey
mkdir -p /usr/local/var/log/codegrey
mkdir -p /usr/local/etc/codegrey

# Create user directories
mkdir -p "$HOME/Library/Application Support/CodeGrey"
mkdir -p "$HOME/Library/Logs/CodeGrey"

# Copy files
cp *.py /opt/codegrey/
cp requirements.txt /opt/codegrey/
cp README.md /opt/codegrey/

# Set permissions
chmod +x /opt/codegrey/main.py
chown -R root:wheel /opt/codegrey
chown -R root:wheel /usr/local/var/log/codegrey
chown -R root:wheel /usr/local/etc/codegrey

echo "[5/7] Creating configuration..."

# Create default config
cat > /usr/local/etc/codegrey/config.yaml << 'EOF'
server_endpoint: "http://localhost:8080"
agent_id: "auto"
heartbeat_interval: 60

# Network Discovery (privacy-aware)
network_discovery:
  enabled: true
  scan_interval: 1800
  respect_privacy: true
  user_consent_required: true
  max_threads: 20

# Log Sources (privacy-compliant)
log_forwarding:
  enabled: true
  batch_size: 100
  sources:
    - system_log
    - security_log
    - application_log
  privacy_mode: true
  anonymize_sensitive_data: true

# macOS Integration
macos_integration:
  xprotect_integration: true
  gatekeeper_monitoring: true
  system_integrity_protection: true
  privacy_compliance: true

# Container Management (requires Docker Desktop)
container_management:
  enabled: false
  docker_desktop_required: true
  max_containers: 5

# Privacy Settings
privacy_settings:
  minimal_data_collection: true
  local_processing_preferred: true
  user_consent_required: true
  data_retention_days: 30
EOF

echo "Default configuration created at /usr/local/etc/codegrey/config.yaml"

echo "[6/7] Setting up LaunchAgent..."

# Create LaunchAgent plist
cat > /Library/LaunchAgents/com.codegrey.agent.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.codegrey.agent</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/opt/codegrey/main.py</string>
        <string>--config</string>
        <string>/usr/local/etc/codegrey/config.yaml</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/opt/codegrey</string>
    
    <key>StandardOutPath</key>
    <string>/usr/local/var/log/codegrey/agent.log</string>
    
    <key>StandardErrorPath</key>
    <string>/usr/local/var/log/codegrey/agent.error.log</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>ThrottleInterval</key>
    <integer>10</integer>
    
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

# Set permissions for LaunchAgent
chown root:wheel /Library/LaunchAgents/com.codegrey.agent.plist
chmod 644 /Library/LaunchAgents/com.codegrey.agent.plist

echo "[7/7] Requesting permissions..."

echo
echo "========================================"
echo "INSTALLATION COMPLETE!"
echo "========================================"
echo
echo " IMPORTANT: PRIVACY PERMISSIONS REQUIRED"
echo "Please grant the following permissions:"
echo
echo "1. Open System Preferences > Security & Privacy"
echo "2. Go to Privacy tab"
echo "3. Grant 'Full Disk Access' to:"
echo "   - /usr/bin/python3"
echo "   - /opt/codegrey/main.py"
echo "4. Grant 'Network' access if prompted"
echo
echo " NEXT STEPS:"
echo "1. Configure the agent:"
echo "   python3 /opt/codegrey/main.py --configure"
echo
echo "2. Start the agent:"
echo "   launchctl load /Library/LaunchAgents/com.codegrey.agent.plist"
echo
echo "3. Check status:"
echo "   launchctl list | grep codegrey"
echo
echo "4. View logs:"
echo "   tail -f /usr/local/var/log/codegrey/agent.log"
echo
echo " FEATURES INCLUDED:"
echo " Privacy-aware network discovery"
echo " XProtect integration"
echo " ML-powered threat detection"
echo " Dynamic location learning"
echo " Container security testing"
echo " Zero hardcoded patterns"
echo " macOS native integration"
echo
echo " Your Mac is now protected by AI with privacy first!"
echo "========================================"
