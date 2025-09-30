# PowerShell script to update nginx CORS configuration for CodeGrey AI SOC Platform
# This script updates the nginx configuration to allow only specific domains

Write-Host "Updating nginx CORS configuration..." -ForegroundColor Green

# Backup the current configuration
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "/etc/nginx/sites-available/complete-soc.backup.$timestamp"

Write-Host "Creating backup of current configuration..." -ForegroundColor Yellow
sudo cp /etc/nginx/sites-available/complete-soc $backupPath

# Copy the new configuration
Write-Host "Copying new configuration..." -ForegroundColor Yellow
sudo cp nginx/nginx_config.conf /etc/nginx/sites-available/complete-soc

# Test nginx configuration
Write-Host "Testing nginx configuration..." -ForegroundColor Yellow
$testResult = sudo nginx -t

if ($LASTEXITCODE -eq 0) {
    Write-Host "Nginx configuration test passed!" -ForegroundColor Green
    
    # Reload nginx
    Write-Host "Reloading nginx..." -ForegroundColor Yellow
    $reloadResult = sudo systemctl reload nginx
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Nginx CORS configuration updated successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "CORS is now configured to allow only:" -ForegroundColor Cyan
        Write-Host "  - http://localhost:3000" -ForegroundColor White
        Write-Host "  - http://dev.codegrey.ai" -ForegroundColor White
        Write-Host ""
        Write-Host "The configuration includes:" -ForegroundColor Cyan
        Write-Host "  - Authorization header support" -ForegroundColor White
        Write-Host "  - X-API-Key header support" -ForegroundColor White
        Write-Host "  - Credentials support" -ForegroundColor White
        Write-Host "  - Proper preflight OPTIONS handling" -ForegroundColor White
    } else {
        Write-Host "Failed to reload nginx. Check the logs:" -ForegroundColor Red
        Write-Host "sudo journalctl -u nginx -f" -ForegroundColor Yellow
    }
} else {
    Write-Host "Nginx configuration test failed!" -ForegroundColor Red
    Write-Host "Please check the configuration file and try again." -ForegroundColor Yellow
    Write-Host "Restoring backup..." -ForegroundColor Yellow
    sudo cp $backupPath /etc/nginx/sites-available/complete-soc
}

Write-Host ""
Write-Host "To test CORS from your frontend:" -ForegroundColor Cyan
Write-Host "1. Make sure your frontend is running on http://dev.codegrey.ai:3000" -ForegroundColor White
Write-Host "2. Try making a request to http://backend.codegrey.ai:8080/api/backend/" -ForegroundColor White
Write-Host "3. Check browser developer tools for CORS errors" -ForegroundColor White
Write-Host ""
Write-Host "If you still have CORS issues, you can temporarily install a CORS browser extension" -ForegroundColor Yellow
Write-Host "to bypass CORS and see if the API is working correctly." -ForegroundColor Yellow

