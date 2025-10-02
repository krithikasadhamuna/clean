#!/bin/bash
# AI SOC Platform Startup Script for Linux

echo " Starting CodeGrey AI SOC Platform on Amazon Linux 2023"
echo "========================================================"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
    echo " Environment variables loaded"
fi

# Check Python
python3_version=$(python3 --version 2>&1)
echo "🐍 Python: $python3_version"

# Check if server is already running
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo " Server already running"
else
    echo " Starting AI SOC Platform server..."
    
    # Start server
    echo "   Host: 0.0.0.0"
    echo "   Port: 8080"
    echo "   External IP: 15.207.6.45"
    echo ""
    
    python3 main.py server --host 0.0.0.0 --port 8080
fi
