#!/bin/bash
# AI SOC Platform Installation Script for Amazon Linux 2023

echo "🚀 AI SOC Platform - Amazon Linux 2023 Installation"
echo "=================================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root. Consider using a regular user for security."
fi

# Update system
echo "📦 Updating system packages..."
sudo dnf update -y

# Install Python 3 and development tools
echo "🐍 Installing Python and development tools..."
sudo dnf install python3 python3-pip python3-devel -y
sudo dnf groupinstall "Development Tools" -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo dnf install gcc gcc-c++ make cmake -y
sudo dnf install openssl-devel libffi-devel -y

# Check Python version
python3_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Python version: $python3_version"

# Upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install core Python packages first
echo "📦 Installing core Python packages..."
pip3 install --user wheel setuptools

# Install ML and data science packages
echo "🧠 Installing ML packages..."
pip3 install --user numpy pandas scikit-learn joblib

# Install web framework packages
echo "🌐 Installing web framework packages..."
pip3 install --user fastapi uvicorn aiohttp aiosqlite

# Install LangChain ecosystem
echo "🔗 Installing LangChain packages..."
pip3 install --user langchain langchain-community langchain-core
pip3 install --user langchain-openai openai
pip3 install --user langserve

# Install additional packages
echo "📦 Installing additional packages..."
pip3 install --user requests psutil pyyaml pydantic

# Install Docker (optional)
echo "🐳 Installing Docker..."
sudo dnf install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker $USER

# Install eBPF tools (optional)
echo "🔍 Installing eBPF tools..."
sudo dnf install bcc-tools python3-bcc -y || echo "⚠️  eBPF tools installation failed (optional)"

# Set up directories
echo "📁 Setting up directories..."
mkdir -p logs data checkpoints golden_images

# Set permissions
chmod +x main.py
chmod +x *.sh

# Create environment file
echo "🔧 Creating environment file..."
cat > .env << EOF
OPENAI_API_KEY=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
AI_SOC_API_KEY=api_codegrey_2024
EOF

# Load environment
source .env

echo "✅ Installation completed!"
echo ""
echo "🎯 Next steps:"
echo "1. Start the platform: ./start_platform.sh"
echo "2. Test APIs: curl http://localhost:8080/health"
echo "3. Access from external: curl http://15.207.6.45:8080/health"
echo ""
echo "📊 Platform URLs:"
echo "   Health: http://15.207.6.45:8080/health"
echo "   Agents: http://15.207.6.45:8080/api/backend/agents"
echo "   Network: http://15.207.6.45:8080/api/backend/network-topology"
echo ""
echo "🔐 API Key: api_codegrey_2024"
