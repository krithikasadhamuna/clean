# Docker Installation Helper for AI SOC Platform

Write-Host "Docker Installation Helper for AI SOC Platform" -ForegroundColor Green
Write-Host "=" * 50

# Check if Docker is already installed
try {
    $dockerVersion = docker --version
    Write-Host "Docker is already installed: $dockerVersion" -ForegroundColor Green
    
    # Check if Docker is running
    try {
        docker info | Out-Null
        Write-Host "Docker is running and ready!" -ForegroundColor Green
        exit 0
    } catch {
        Write-Host "Docker is installed but not running" -ForegroundColor Yellow
        Write-Host "Please start Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "Docker is not installed" -ForegroundColor Yellow
}

Write-Host "`nInstalling Docker Desktop..." -ForegroundColor Yellow

# Download Docker Desktop installer
$dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$installerPath = "$env:TEMP\DockerDesktopInstaller.exe"

try {
    Write-Host "Downloading Docker Desktop..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $dockerUrl -OutFile $installerPath -UseBasicParsing
    
    Write-Host "Starting Docker Desktop installation..." -ForegroundColor Yellow
    Write-Host "Please follow the installation wizard" -ForegroundColor Cyan
    
    # Start installer
    Start-Process -FilePath $installerPath -Wait
    
    Write-Host "Docker Desktop installation completed!" -ForegroundColor Green
    Write-Host "Please:" -ForegroundColor Cyan
    Write-Host "1. Restart your computer if prompted" -ForegroundColor White
    Write-Host "2. Start Docker Desktop" -ForegroundColor White  
    Write-Host "3. Restart the AI SOC Platform client" -ForegroundColor White
    
    # Clean up
    Remove-Item $installerPath -ErrorAction SilentlyContinue
    
} catch {
    Write-Host "Docker installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nManual installation:" -ForegroundColor Yellow
    Write-Host "1. Go to https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host "2. Download Docker Desktop for Windows" -ForegroundColor White
    Write-Host "3. Run the installer" -ForegroundColor White
    Write-Host "4. Restart your computer" -ForegroundColor White
    Write-Host "5. Start Docker Desktop" -ForegroundColor White
}
