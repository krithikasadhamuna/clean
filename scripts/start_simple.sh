#!/bin/bash
# Simple startup for CodeGrey AI SOC Platform on port 8080

echo "🚀 Starting CodeGrey AI SOC Platform"
echo "===================================="
echo "Domain: dev.codegrey.ai:8080"
echo "Auth: DISABLED (for development)"
echo "Nginx: Untouched (running separately)"
echo ""

# Install missing packages if needed
echo "📦 Installing required packages..."
pip3 install --user psutil aiohttp fastapi uvicorn pydantic langchain langchain-openai openai langserve

# Set Python path
export PYTHONPATH="/home/krithika/.local/lib/python3.9/site-packages:/usr/lib/python3.9/site-packages:$PYTHONPATH"

echo ""
echo "🌐 Your API URLs:"
echo "   http://dev.codegrey.ai:8080/health"
echo "   http://dev.codegrey.ai:8080/api/backend/agents"
echo "   http://dev.codegrey.ai:8080/api/backend/network-topology"
echo "   http://dev.codegrey.ai:8080/api/backend/software-download"
echo ""
echo "✅ Starting server..."

# Start the server on port 8080
python3 main.py server --host 0.0.0.0 --port 8080
