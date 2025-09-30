#!/bin/bash
# Start CodeGrey AI SOC Platform with Nginx reverse proxy

echo " Starting CodeGrey AI SOC Platform with Nginx"
echo "================================================"
echo "Domain: dev.codegrey.ai (via Nginx on port 80)"
echo "App Port: 8080 (behind Nginx)"
echo "Auth: DISABLED (for development)"
echo ""

# Setup Nginx if not already done
if [ ! -f /etc/nginx/sites-enabled/codegrey-soc ]; then
    echo "  Setting up Nginx reverse proxy..."
    chmod +x setup_nginx.sh
    ./setup_nginx.sh
    echo ""
fi

# Update server config to use port 8080
echo " Updating server configuration for port 8080..."
sed -i 's/port: 80/port: 8080/' config/server_config.yaml

# Install missing packages if needed
echo "📦 Installing required packages..."
pip3 install --user psutil aiohttp fastapi uvicorn pydantic

# Start the application on port 8080
echo " Starting AI SOC Platform on port 8080..."
echo "   (Nginx will proxy from port 80 to 8080)"
echo ""

# Set Python path and start server
export PYTHONPATH="/home/krithika/.local/lib/python3.9/site-packages:/usr/lib/python3.9/site-packages:$PYTHONPATH"

echo " Application starting..."
echo ""
echo " Your clean URLs (NO PORT NUMBERS):"
echo "   http://dev.codegrey.ai/health"
echo "   http://dev.codegrey.ai/api/backend/agents"
echo "   http://dev.codegrey.ai/api/backend/network-topology"
echo ""

# Start the server
python3 main.py server --host 0.0.0.0 --port 8080
