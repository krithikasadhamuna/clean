#!/bin/bash
# CodeGrey AI SOC Platform - macOS Client Agent Installer

echo "CodeGrey AI SOC Platform - macOS Client Agent"
echo "=============================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from:"
    echo "  - https://python.org/downloads/"
    echo "  - Or use Homebrew: brew install python3"
    exit 1
fi

echo "Python detected. Installing dependencies..."

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip..."
    python3 -m ensurepip --upgrade
fi

# Install dependencies
echo "Installing Python dependencies..."
pip3 install --user -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Trying alternative installation..."
    python3 -m pip install --user -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        echo "Please install manually: pip3 install -r requirements.txt"
        exit 1
    fi
fi

echo
echo "Dependencies installed successfully!"
echo

# Check if Docker Desktop is available
if command -v docker &> /dev/null; then
    echo "Docker Desktop detected"
    
    # Test if Docker is running
    if docker info &> /dev/null; then
        echo "Docker is running"
    else
        echo "WARNING: Docker is installed but not running"
        echo "Please start Docker Desktop"
    fi
else
    echo "WARNING: Docker Desktop is not installed"
    echo "Container management features will be disabled"
    echo "Install Docker Desktop from: https://docker.com/products/docker-desktop"
    echo
fi

# Check for Homebrew (common on macOS)
if command -v brew &> /dev/null; then
    echo "Homebrew detected - you can install additional tools with:"
    echo "  brew install watch htop"
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
echo "IMPORTANT: macOS Privacy & Security"
echo "=================================="
echo "macOS may ask for permissions when the agent starts:"
echo "- Allow 'Terminal' or 'Python' to access files"
echo "- Allow network connections"
echo "- Allow monitoring other applications"
echo
echo "To configure the agent:"
echo "  python3 main.py --configure"
echo
echo "To start the agent:"
echo "  python3 main.py"
echo
echo "To run in background:"
echo "  nohup python3 main.py &"
echo
