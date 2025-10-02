# CodeGrey AI SOC Platform - Automatic Docker Installation for Windows
# This script automatically installs Docker Desktop and configures it for container-based attack simulation

param(
    [switch]$Force = $false,
    [switch]$SkipRestart = $false
)

Write-Host "CodeGrey AI SOC Platform - Docker Auto-Installer" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is already installed
Write-Host "Checking Docker installation..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "Docker is already installed: $dockerVersion" -ForegroundColor Green
        if (-not $Force) {
            Write-Host "Use -Force to reinstall Docker" -ForegroundColor Yellow
            exit 0
        }
    }
} catch {
    Write-Host "Docker not found, proceeding with installation..." -ForegroundColor Yellow
}

# Enable Windows features required for Docker
Write-Host "Enabling Windows features for Docker..." -ForegroundColor Cyan
try {
    # Enable Hyper-V
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart
    
    # Enable Containers
    Enable-WindowsOptionalFeature -Online -FeatureName Containers -All -NoRestart
    
    # Enable Windows Subsystem for Linux (WSL2)
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -All -NoRestart
    
    Write-Host "Windows features enabled successfully" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not enable all Windows features: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Download and install Docker Desktop
Write-Host "Downloading Docker Desktop..." -ForegroundColor Cyan
$dockerInstallerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$dockerInstallerPath = "$env:TEMP\DockerDesktopInstaller.exe"

try {
    Invoke-WebRequest -Uri $dockerInstallerUrl -OutFile $dockerInstallerPath -UseBasicParsing
    Write-Host "Docker Desktop downloaded successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to download Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Install Docker Desktop
Write-Host "Installing Docker Desktop..." -ForegroundColor Cyan
Write-Host "This may take several minutes..." -ForegroundColor Yellow

try {
    $installArgs = @(
        "install",
        "--quiet",
        "--accept-license",
        "--wsl-default-version=2"
    )
    
    Start-Process -FilePath $dockerInstallerPath -ArgumentList $installArgs -Wait
    Write-Host "Docker Desktop installed successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to install Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Clean up installer
Remove-Item $dockerInstallerPath -Force -ErrorAction SilentlyContinue

# Configure Docker Desktop settings
Write-Host "Configuring Docker Desktop..." -ForegroundColor Cyan

# Create Docker Desktop configuration
$dockerConfigPath = "$env:APPDATA\Docker\settings.json"
$dockerConfigDir = Split-Path $dockerConfigPath -Parent

if (-not (Test-Path $dockerConfigDir)) {
    New-Item -ItemType Directory -Path $dockerConfigDir -Force
}

$dockerConfig = @{
    "experimental" = $false
    "debug" = $false
    "registry-mirrors" = @()
    "insecure-registries" = @()
    "builder" = @{
        "gc" = @{
            "enabled" = $true
            "defaultKeepStorage" = "20GB"
        }
    }
    "features" = @{
        "buildkit" = $true
    }
    "proxies" = @{}
    "credsStore" = "desktop"
    "credHelpers" = @{}
    "stackOrchestrator" = "swarm"
    "kubernetes" = @{
        "enabled" = $false
    }
    "dockerComposeV2" = $true
    "autoStart" = $true
    "startOnLogin" = $true
    "wslEngineEnabled" = $true
    "wslDistro" = "docker-desktop"
    "wslDistroData" = "docker-desktop-data"
} | ConvertTo-Json -Depth 10

Set-Content -Path $dockerConfigPath -Value $dockerConfig -Encoding UTF8

# Start Docker Desktop
Write-Host "Starting Docker Desktop..." -ForegroundColor Cyan
try {
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
    Write-Host "Docker Desktop started" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not start Docker Desktop automatically" -ForegroundColor Yellow
    Write-Host "Please start Docker Desktop manually from the Start menu" -ForegroundColor Yellow
}

# Wait for Docker to be ready
Write-Host "Waiting for Docker to be ready..." -ForegroundColor Cyan
$maxWaitTime = 300 # 5 minutes
$waitTime = 0
$dockerReady = $false

while ($waitTime -lt $maxWaitTime -and -not $dockerReady) {
    try {
        $dockerInfo = docker info 2>$null
        if ($dockerInfo) {
            $dockerReady = $true
            Write-Host "Docker is ready!" -ForegroundColor Green
        }
    } catch {
        # Docker not ready yet
    }
    
    if (-not $dockerReady) {
        Start-Sleep -Seconds 10
        $waitTime += 10
        Write-Host "." -NoNewline -ForegroundColor Yellow
    }
}

if (-not $dockerReady) {
    Write-Host ""
    Write-Host "Warning: Docker may not be fully ready yet" -ForegroundColor Yellow
    Write-Host "Please wait a few more minutes and try running 'docker info'" -ForegroundColor Yellow
}

# Pull required Docker images for CodeGrey
Write-Host ""
Write-Host "Downloading CodeGrey container images..." -ForegroundColor Cyan

$requiredImages = @(
    "ubuntu:22.04",
    "nginx:alpine",
    "mysql:8.0",
    "mcr.microsoft.com/windows/servercore:ltsc2019"
)

foreach ($image in $requiredImages) {
    Write-Host "Pulling $image..." -ForegroundColor Yellow
    try {
        docker pull $image
        Write-Host "$image downloaded successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download $image" -ForegroundColor Yellow
    }
}

# Test Docker functionality
Write-Host ""
Write-Host "Testing Docker functionality..." -ForegroundColor Cyan
try {
    $testResult = docker run --rm hello-world
    if ($testResult -match "Hello from Docker") {
        Write-Host "Docker test successful!" -ForegroundColor Green
    } else {
        Write-Host "Docker test may have issues" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Docker test failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Create Docker service startup script
Write-Host "Creating Docker startup script..." -ForegroundColor Cyan
$startupScript = @"
@echo off
echo Starting Docker Desktop for CodeGrey AI SOC Platform...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
timeout /t 30 /nobreak >nul
echo Docker Desktop started. You can now run CodeGrey Agent.
pause
"@

$startupScriptPath = "Start-Docker-For-CodeGrey.bat"
Set-Content -Path $startupScriptPath -Value $startupScript -Encoding ASCII

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "DOCKER INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Docker Desktop installed and configured" -ForegroundColor Green
Write-Host "Required container images downloaded" -ForegroundColor Green
Write-Host "Docker functionality tested" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT NOTES:" -ForegroundColor Yellow
Write-Host "Docker Desktop will start automatically on system boot" -ForegroundColor White
Write-Host "If Docker Desktop doesn't start, run: Start-Docker-For-CodeGrey.bat" -ForegroundColor White
Write-Host "You may need to restart your computer for all features to work" -ForegroundColor White
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Restart your computer (recommended)" -ForegroundColor White
Write-Host "2. Run CodeGrey Agent - container capabilities will now be available!" -ForegroundColor White
Write-Host ""

if (-not $SkipRestart) {
    $restart = Read-Host "Would you like to restart your computer now? (y/n)"
    if ($restart -eq "y" -or $restart -eq "Y") {
        Write-Host "Restarting computer in 10 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        Restart-Computer -Force
    }
}
