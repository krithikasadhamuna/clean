#!/bin/bash
# CodeGrey AI SOC Platform - Apply CORS Fix
# This script applies the permanent CORS fix to the server

echo "CodeGrey AI SOC Platform - Applying CORS Fix"
echo "============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Backup current nginx configuration
echo "1. Backing up current Nginx configuration..."
cp /etc/nginx/sites-available/complete-soc /etc/nginx/sites-available/complete-soc.backup.$(date +%Y%m%d_%H%M%S)
echo "    Backup created"

# Update nginx configuration
echo "2. Updating Nginx configuration with CORS fix..."
cat > /etc/nginx/sites-available/complete-soc << 'EOF'
# Nginx configuration for CodeGrey AI SOC Platform
# Place this in /etc/nginx/sites-available/complete-soc

# Map for CORS origins
map $http_origin $cors_origin {
    default "";
    "http://localhost:3000" "http://localhost:3000";
    "http://dev.codegrey.ai" "http://dev.codegrey.ai";
    "https://dev.codegrey.ai" "https://dev.codegrey.ai";
}

server {
    listen 8080;
    server_name backend.codegrey.ai;
    client_max_body_size 100M;

    # Handle preflight OPTIONS requests
    location / {
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' $cors_origin always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-Requested-With, Accept, Origin, X-API-Key, Access-Control-Request-Method, Access-Control-Request-Headers' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Max-Age' 86400 always;
            add_header 'Content-Length' 0;
            add_header 'Content-Type' 'text/plain charset=UTF-8';
            return 204;
        }

        # Add CORS headers to all responses
        add_header 'Access-Control-Allow-Origin' $cors_origin always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Expose-Headers' 'X-Total-Count, X-Page-Count, X-API-Version' always;

        # Proxy to backend
        proxy_pass http://127.0.0.1:8081;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' $cors_origin always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-Requested-With, Accept, Origin, X-API-Key' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Max-Age' 86400 always;
            add_header 'Content-Length' 0;
            add_header 'Content-Type' 'text/plain charset=UTF-8';
            return 204;
        }

        add_header 'Access-Control-Allow-Origin' $cors_origin always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;

        proxy_pass http://127.0.0.1:8081/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API endpoints with CORS
    location /api/ {
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' $cors_origin always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-Requested-With, Accept, Origin, X-API-Key, Access-Control-Request-Method, Access-Control-Request-Headers' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Max-Age' 86400 always;
            add_header 'Content-Length' 0;
            add_header 'Content-Type' 'text/plain charset=UTF-8';
            return 204;
        }

        add_header 'Access-Control-Allow-Origin' $cors_origin always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Expose-Headers' 'X-Total-Count, X-Page-Count, X-API-Version' always;

        proxy_pass http://127.0.0.1:8081/api/;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Logs
    access_log /var/log/nginx/codegrey-soc.access.log;
    error_log /var/log/nginx/codegrey-soc.error.log;
}
EOF

echo "    Nginx configuration updated"

# Test nginx configuration
echo "3. Testing Nginx configuration..."
if nginx -t; then
    echo "    Nginx configuration is valid"
else
    echo "   x Nginx configuration has errors"
    echo "   Restoring backup..."
    cp /etc/nginx/sites-available/complete-soc.backup.* /etc/nginx/sites-available/complete-soc
    exit 1
fi

# Reload nginx
echo "4. Reloading Nginx..."
if systemctl reload nginx; then
    echo "    Nginx reloaded successfully"
else
    echo "   x Failed to reload Nginx"
    exit 1
fi

# Test CORS
echo "5. Testing CORS fix..."
echo "   Testing OPTIONS request..."
response=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
    -H "Origin: http://dev.codegrey.ai" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" \
    http://backend.codegrey.ai:8080/api/agents)

if [ "$response" = "204" ]; then
    echo "    OPTIONS request successful (204)"
else
    echo "   x OPTIONS request failed ($response)"
fi

echo "   Testing GET request..."
response=$(curl -s -o /dev/null -w "%{http_code}" -H "Origin: http://dev.codegrey.ai" \
    http://backend.codegrey.ai:8080/api/agents)

if [ "$response" = "200" ]; then
    echo "    GET request successful (200)"
else
    echo "   x GET request failed ($response)"
fi

echo ""
echo "============================================="
echo "CORS Fix Applied Successfully!"
echo "============================================="
echo ""
echo " Nginx configuration updated with CORS headers"
echo " CORS preflight requests handled"
echo " Allowed origins: http://localhost:3000, http://dev.codegrey.ai, https://dev.codegrey.ai"
echo " Credentials allowed"
echo " All HTTP methods supported"
echo ""
echo "Your frontend should now work without CORS errors!"
echo ""
echo "To test from your frontend:"
echo "1. Remove any CORS browser extensions"
echo "2. Try making requests to http://backend.codegrey.ai:8080/api/"
echo "3. Check browser developer tools for CORS errors"
echo ""
echo "If you still have issues:"
echo "1. Check browser console for errors"
echo "2. Verify your frontend is running on http://dev.codegrey.ai or http://localhost:3000"
echo "3. Check Nginx logs: sudo tail -f /var/log/nginx/error.log"

