#!/bin/bash

# Script to fix nginx configuration conflicts for CodeGrey AI SOC Platform
# This script removes conflicting server blocks and enables the correct site configuration

echo "Fixing nginx configuration conflicts..."

# Backup the current nginx.conf
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)
echo "Backed up current nginx.conf"

# Create a new nginx.conf without the conflicting server block
sudo tee /etc/nginx/nginx.conf > /dev/null << 'EOF'
# For more information on configuration, see:
#   * Official English Documentation: http://nginx.org/en/docs/
#   * Official Russian Documentation: http://nginx.org/ru/docs/

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /run/nginx.pid;

# Load dynamic modules. See /usr/share/doc/nginx/README.dynamic.
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    # See http://nginx.org/en/docs/ngx_core_module.html#include
    # for more information.
    # include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;

    # Default server block for port 80 (frontend)
    server {
        listen       80;
        listen       [::]:80;
        server_name  dev.codegrey.ai;
        root         /var/www/html;
        index index.html index.htm index.php;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        error_page 404 /404.html;
        location = /404.html {
        }

        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
        }

        # Frontend proxy (Next.js app on port 3000)
        location / {
            proxy_pass http://127.0.0.1:3000/;
            proxy_http_version 1.1;
            proxy_set_header   X-Real-IP        $remote_addr;
            proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
            proxy_set_header   Host             $host;
            
            # CORS headers for frontend
            add_header 'Access-Control-Allow-Origin' 'http://dev.codegrey.ai' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, HEAD, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, X-Requested-With' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
        }
    }

    # Settings for a TLS enabled server.
    #
    #    server {
    #        listen       443 ssl;
    #        listen       [::]:443 ssl;
    #        http2        on;
    #        server_name  _;
    #        root         /usr/share/nginx/html;
    #
    #        ssl_certificate "/etc/pki/nginx/server.crt";
    #        ssl_certificate_key "/etc/pki/nginx/private/server.key";
    #        ssl_session_cache shared:SSL:1m;
    #        ssl_session_timeout  10m;
    #        ssl_ciphers PROFILE=SYSTEM;
    #        ssl_prefer_server_ciphers on;
    #
    #        # Load configuration files for the default server block.
    #        include /etc/nginx/default.d/*.conf;
    #
    #        error_page 404 /404.html;
    #        location = /404.html {
    #        }
    #
    #        error_page 500 502 503 504 /50x.html;
    #        location = /50x.html {
    #        }
    #    }
}
EOF

echo "Updated main nginx.conf (removed conflicting port 8080 server block)"

# Copy the complete-soc configuration
sudo cp nginx/nginx_config.conf /etc/nginx/sites-available/complete-soc
echo "Updated complete-soc configuration"

# Enable the complete-soc site
sudo ln -sf /etc/nginx/sites-available/complete-soc /etc/nginx/sites-enabled/complete-soc
echo "Enabled complete-soc site"

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration test passed!"
    
    # Reload nginx
    echo "Reloading nginx..."
    sudo systemctl reload nginx
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "Nginx configuration conflicts fixed successfully!"
        echo ""
        echo "Current setup:"
        echo "  Frontend (dev.codegrey.ai:80) -> http://127.0.0.1:3000"
        echo "  Backend API (backend.codegrey.ai:8080) -> http://127.0.0.1:8081"
        echo ""
        echo "CORS Configuration:"
        echo "  Frontend: http://dev.codegrey.ai"
        echo "  Backend: localhost:3000, dev.codegrey.ai"
        echo "  Headers: Authorization, X-API-Key, Content-Type"
        echo "  Credentials: Enabled"
        echo ""
        echo "Test your setup:"
        echo "  1. Frontend: http://dev.codegrey.ai"
        echo "  2. Backend API: http://backend.codegrey.ai:8080/api/backend/"
        echo "  3. Check browser dev tools for CORS errors"
    else
        echo "Failed to reload nginx. Check the logs:"
        echo "sudo journalctl -u nginx -f"
    fi
else
    echo "Nginx configuration test failed!"
    echo "Restoring backup..."
    sudo cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf
    echo "Please check the configuration and try again."
fi

echo ""
echo "Configuration files:"
echo "  Main config: /etc/nginx/nginx.conf"
echo "  Site config: /etc/nginx/sites-available/complete-soc"
echo "  Enabled sites: /etc/nginx/sites-enabled/"

