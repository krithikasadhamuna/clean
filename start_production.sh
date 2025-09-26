#!/bin/bash
# Production startup script for CodeGrey AI SOC Platform

echo "Starting CodeGrey AI SOC Platform - Production Mode"
echo "=================================================="
echo "Domain: dev.codegrey.ai"
echo "Port: 80 (no port number needed in URLs)"
echo "Auth: DISABLED (for development)"
echo ""

# Install missing packages if needed
echo "Installing required packages..."
pip3 install --user psutil aiohttp fastapi uvicorn pydantic

# Start server on port 80 (requires sudo)
echo "Starting server on port 80..."
echo "Note: Requires sudo for port 80"
echo ""

# Check if port 80 is already in use
if sudo netstat -tulpn | grep :80 > /dev/null; then
    echo "⚠️  Port 80 is already in use"
    echo "Checking what's using it..."
    sudo netstat -tulpn | grep :80
    echo ""
    echo "Options:"
    echo "1. Stop the service using port 80"
    echo "2. Use port 8080 instead: python3 main.py server --host 0.0.0.0 --port 8080"
    exit 1
fi

# Start the platform
echo "🚀 Starting AI SOC Platform..."
sudo PYTHONPATH=/home/krithika/.local/lib/python3.9/site-packages:/usr/lib/python3.9/site-packages python3 main.py server --host 0.0.0.0 --port 80
