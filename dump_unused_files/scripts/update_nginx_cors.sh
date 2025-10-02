#!/bin/bash

# Script to update nginx CORS configuration for CodeGrey AI SOC Platform
# This script updates the nginx configuration to allow only specific domains

echo "Updating nginx CORS configuration..."

# Backup the current configuration
sudo cp /etc/nginx/sites-available/complete-soc /etc/nginx/sites-available/complete-soc.backup.$(date +%Y%m%d_%H%M%S)

# Copy the new configuration
sudo cp nginx/nginx_config.conf /etc/nginx/sites-available/complete-soc

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration test passed!"
    
    # Reload nginx
    echo "Reloading nginx..."
    sudo systemctl reload nginx
    
    if [ $? -eq 0 ]; then
        echo "Nginx CORS configuration updated successfully!"
        echo ""
        echo "CORS is now configured to allow only:"
        echo "  - http://localhost:3000"
        echo "  - http://dev.codegrey.ai"
        echo ""
        echo "The configuration includes:"
        echo "  - Authorization header support"
        echo "  - X-API-Key header support"
        echo "  - Credentials support"
        echo "  - Proper preflight OPTIONS handling"
    else
        echo "Failed to reload nginx. Check the logs:"
        echo "sudo journalctl -u nginx -f"
    fi
else
    echo "Nginx configuration test failed!"
    echo "Please check the configuration file and try again."
    echo "Restoring backup..."
    sudo cp /etc/nginx/sites-available/complete-soc.backup.* /etc/nginx/sites-available/complete-soc
fi

echo ""
echo "To test CORS from your frontend:"
echo "1. Make sure your frontend is running on http://dev.codegrey.ai:3000"
echo "2. Try making a request to http://backend.codegrey.ai:8080/api/backend/"
echo "3. Check browser developer tools for CORS errors"
echo ""
echo "If you still have CORS issues, you can temporarily install a CORS browser extension"
echo "to bypass CORS and see if the API is working correctly."

