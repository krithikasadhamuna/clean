#!/bin/bash
# Setup Nginx reverse proxy for CodeGrey AI SOC Platform

echo "Setting up Nginx reverse proxy for CodeGrey AI SOC Platform"
echo "==========================================================="

# Copy nginx configuration
echo "📋 Installing Nginx configuration..."
sudo cp nginx_config.conf /etc/nginx/sites-available/codegrey-soc

# Enable the site
echo "🔗 Enabling site..."
sudo ln -sf /etc/nginx/sites-available/codegrey-soc /etc/nginx/sites-enabled/

# Remove default nginx site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "🗑️  Removing default Nginx site..."
    sudo rm /etc/nginx/sites-enabled/default
fi

# Test nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    
    # Reload nginx
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "✅ Nginx setup complete!"
    echo ""
    echo "Your application will be available at:"
    echo "  🌐 http://dev.codegrey.ai/"
    echo "  🔍 http://dev.codegrey.ai/health"
    echo "  📡 http://dev.codegrey.ai/api/backend/agents"
    echo ""
    echo "Now start your Python application on port 8080:"
    echo "  python3 main.py server --host 0.0.0.0 --port 8080"
else
    echo "❌ Nginx configuration test failed!"
    echo "Please check the configuration and try again."
    exit 1
fi
