#!/bin/bash
# CodeGrey AI SOC Platform - Linux Client Agent Installer

echo "CodeGrey AI SOC Platform - Linux Client Agent"
echo "=============================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ using your package manager:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "  Amazon Linux: sudo yum install python3 python3-pip"
    exit 1
fi

echo "Python detected. Installing dependencies..."

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip..."
    sudo apt update && sudo apt install python3-pip -y 2>/dev/null || \
    sudo yum install python3-pip -y 2>/dev/null || \
    echo "Please install pip3 manually"
fi

# Install dependencies
echo "Installing Python dependencies..."
pip3 install --user -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Trying with sudo..."
    sudo pip3 install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies even with sudo"
        exit 1
    fi
fi

echo
echo "Dependencies installed successfully!"
echo

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "Docker detected"
    
    # Check if user is in docker group
    if groups $USER | grep -q docker; then
        echo "User is in docker group"
    else
        echo "WARNING: User is not in docker group"
        echo "Run: sudo usermod -aG docker $USER"
        echo "Then logout and login again"
    fi
else
    echo "WARNING: Docker is not installed"
    echo "Container management features will be disabled"
    echo "Install Docker if needed:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    echo
fi

# Check for eBPF support
if command -v bcc-tools &> /dev/null || python3 -c "import bcc" 2>/dev/null; then
    echo "eBPF support detected"
else
    echo "WARNING: eBPF tools not available"
    echo "Advanced monitoring will be limited"
    echo "Install BCC tools for enhanced monitoring:"
    echo "  Ubuntu: sudo apt install bpfcc-tools"
    echo "  CentOS: sudo yum install bcc-tools"
    echo
fi

# Create default config if it doesn't exist
if [ ! -f config.yaml ]; then
    echo "Creating default configuration..."
    python3 -c "from config_manager import ConfigManager; ConfigManager().load_config()"
fi

# Make main.py executable
chmod +x main.py

echo
echo "Installation complete!"
echo
echo "To configure the agent:"
echo "  python3 main.py --configure"
echo
echo "To start the agent:"
echo "  python3 main.py"
echo
echo "To run as a service (optional):"
echo "  sudo cp codegrey-agent.service /etc/systemd/system/"
echo "  sudo systemctl enable codegrey-agent"
echo "  sudo systemctl start codegrey-agent"
echo
