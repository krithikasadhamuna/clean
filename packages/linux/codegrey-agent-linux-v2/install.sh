#!/bin/bash

echo "========================================"
echo "CodeGrey AI SOC Platform - Linux Agent v2.0"
echo "Dynamic Installation Script"
echo "========================================"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (use sudo)"
    exit 1
fi

echo "[1/6] Checking system requirements..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Installing..."
    
    # Detect Linux distribution
    if [ -f /etc/debian_version ]; then
        apt-get update
        apt-get install -y python3 python3-pip python3-dev
    elif [ -f /etc/redhat-release ]; then
        yum install -y python3 python3-pip python3-devel
    else
        echo "ERROR: Unsupported Linux distribution"
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

echo "[2/6] Installing system dependencies..."

# Install system packages
if [ -f /etc/debian_version ]; then
    apt-get update
    apt-get install -y \
        nmap \
        tcpdump \
        net-tools \
        iproute2 \
        curl \
        wget \
        build-essential \
        libpcap-dev \
        python3-dev \
        python3-venv
elif [ -f /etc/redhat-release ]; then
    yum install -y \
        nmap \
        tcpdump \
        net-tools \
        iproute \
        curl \
        wget \
        gcc \
        libpcap-devel \
        python3-devel
fi

echo "[3/6] Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python dependencies"
    exit 1
fi

echo "[4/6] Setting up directories..."
mkdir -p /opt/codegrey
mkdir -p /var/log/codegrey
mkdir -p /etc/codegrey

# Copy files
cp *.py /opt/codegrey/
cp requirements.txt /opt/codegrey/
cp README.md /opt/codegrey/

# Set permissions
chmod +x /opt/codegrey/main.py
chown -R root:root /opt/codegrey
chown -R root:root /var/log/codegrey
chown -R root:root /etc/codegrey

echo "[5/6] Creating configuration..."

# Create default config if it doesn't exist
if [ ! -f /etc/codegrey/config.yaml ]; then
    cat > /etc/codegrey/config.yaml << 'EOF'
server_endpoint: "http://localhost:8080"
agent_id: "auto"
heartbeat_interval: 60

network_discovery:
  enabled: true
  scan_interval: 1800
  max_threads: 50
  timeout: 3
  interfaces: "auto"

log_forwarding:
  enabled: true
  batch_size: 100
  sources:
    - syslog
    - auth_log
    - kernel_log
    - application_log

container_management:
  enabled: false
  docker_socket: "/var/run/docker.sock"
  max_containers: 10

security:
  run_as_service: true
  log_encryption: true
  certificate_validation: true
EOF
    echo "Default configuration created at /etc/codegrey/config.yaml"
fi

echo "[6/6] Setting up systemd service..."

# Create systemd service file
cat > /etc/systemd/system/codegrey-agent.service << 'EOF'
[Unit]
Description=CodeGrey AI SOC Platform - Linux Client Agent v2.0
Documentation=file:///opt/codegrey/README.md
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/codegrey
ExecStart=/usr/bin/python3 /opt/codegrey/main.py --config /etc/codegrey/config.yaml
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=codegrey-agent

# Security settings
NoNewPrivileges=false
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/log/codegrey /etc/codegrey /opt/codegrey

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo
echo "========================================"
echo "INSTALLATION COMPLETE!"
echo "========================================"
echo
echo "🎯 NEXT STEPS:"
echo "1. Configure the agent:"
echo "   python3 /opt/codegrey/main.py --configure"
echo
echo "2. Start the agent:"
echo "   systemctl start codegrey-agent"
echo
echo "3. Enable auto-start:"
echo "   systemctl enable codegrey-agent"
echo
echo "4. Check status:"
echo "   systemctl status codegrey-agent"
echo
echo "📊 FEATURES INCLUDED:"
echo "✅ Dynamic network discovery"
echo "✅ ML-powered threat detection"
echo "✅ Real-time location learning"
echo "✅ Behavioral anomaly detection"
echo "✅ Container orchestration (optional)"
echo "✅ Zero hardcoded patterns"
echo "✅ Systemd service integration"
echo
echo "📁 CONFIGURATION:"
echo "   Config file: /etc/codegrey/config.yaml"
echo "   Log files: /var/log/codegrey/"
echo "   Agent files: /opt/codegrey/"
echo
echo "🛡️ Your Linux system is now protected by AI!"
echo "========================================"
