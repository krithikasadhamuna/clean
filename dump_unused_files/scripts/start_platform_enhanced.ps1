# Enhanced AI SOC Platform Startup Script
# Handles Docker, eBPF, and Windows permissions

param(
    [switch]$InstallDocker,
    [switch]$RunAsAdmin,
    [switch]$SkipClient
)

Write-Host "AI SOC Platform - Enhanced Startup" -ForegroundColor Green
Write-Host "=" * 50

# Check system requirements
Write-Host "`nChecking system requirements..." -ForegroundColor Cyan

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    try {
        docker info | Out-Null
        Write-Host "  Docker: Available and running" -ForegroundColor Green
        $dockerOk = $true
    } catch {
        Write-Host "  Docker: Installed but not running" -ForegroundColor Yellow
        Write-Host "  Please start Docker Desktop" -ForegroundColor White
        $dockerOk = $false
    }
} catch {
    Write-Host "  Docker: Not installed" -ForegroundColor Red
    if ($InstallDocker) {
        Write-Host "  Installing Docker..." -ForegroundColor Yellow
        & .\install_docker.ps1
    } else {
        Write-Host "  Use -InstallDocker to install automatically" -ForegroundColor White
    }
    $dockerOk = $false
}

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

Write-Host "Checking Windows privileges..." -ForegroundColor Yellow
if ($isAdmin) {
    Write-Host "  Privileges: Administrator (Full Windows Event Log access)" -ForegroundColor Green
} else {
    Write-Host "  Privileges: Standard user (Limited Event Log access)" -ForegroundColor Yellow
    if ($RunAsAdmin) {
        Write-Host "  Restarting as Administrator..." -ForegroundColor Yellow
        Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
        exit 0
    } else {
        Write-Host "  Use -RunAsAdmin to restart with admin privileges" -ForegroundColor White
    }
}

# Check Python packages
Write-Host "Checking Python packages..." -ForegroundColor Yellow
try {
    python -c "import langchain_openai; print('LangChain OpenAI: OK')" 2>$null
    Write-Host "  LangChain OpenAI: Available" -ForegroundColor Green
} catch {
    Write-Host "  LangChain OpenAI: Missing" -ForegroundColor Red
    Write-Host "  Installing..." -ForegroundColor Yellow
    pip install langchain-openai openai
}

try {
    python -c "import langserve; print('LangServe: OK')" 2>$null
    Write-Host "  LangServe: Available" -ForegroundColor Green
} catch {
    Write-Host "  LangServe: Missing" -ForegroundColor Red
    Write-Host "  Installing..." -ForegroundColor Yellow
    pip install langserve
}

# Start server
Write-Host "`nStarting AI SOC Platform Server..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 3
    Write-Host "Server already running" -ForegroundColor Green
} catch {
    Write-Host "Starting server..." -ForegroundColor Yellow
    
    # Start server in background
    $serverJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python main.py server --host 0.0.0.0 --port 8080
    }
    
    # Wait for server to start
    $serverReady = $false
    $attempts = 0
    while (-not $serverReady -and $attempts -lt 30) {
        Start-Sleep -Seconds 2
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 3
            $serverReady = $true
            Write-Host "Server started successfully" -ForegroundColor Green
        } catch {
            $attempts++
            Write-Host "  Waiting for server... ($attempts/30)" -ForegroundColor Yellow
        }
    }
    
    if (-not $serverReady) {
        Write-Host "Server failed to start" -ForegroundColor Red
        Stop-Job $serverJob -ErrorAction SilentlyContinue
        exit 1
    }
}

# Display server status
Write-Host "`nServer Status:" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8080/health"
    Write-Host "  Status: $($health.status)" -ForegroundColor Green
    Write-Host "  Version: $($health.version)" -ForegroundColor Green
    Write-Host "  API Type: $($health.api_type)" -ForegroundColor Green
} catch {
    Write-Host "  Could not get server status" -ForegroundColor Yellow
}

# Display AI agents
Write-Host "`nAI Agents Status:" -ForegroundColor Cyan
try {
    $agents = Invoke-RestMethod -Uri "http://localhost:8080/api/frontend/agents"
    foreach ($agent in $agents.agents) {
        $statusColor = switch ($agent.status) {
            "active" { "Green" }
            "inactive" { "Yellow" }
            default { "Red" }
        }
        Write-Host "  $($agent.name): $($agent.status)" -ForegroundColor $statusColor
    }
} catch {
    Write-Host "  Could not get agents status" -ForegroundColor Yellow
}

# Start client
if (-not $SkipClient) {
    Write-Host "`nStarting client agent..." -ForegroundColor Cyan
    
    if ($dockerOk) {
        Write-Host "  Docker available: Container-based attacks enabled" -ForegroundColor Green
    } else {
        Write-Host "  Docker unavailable: Attacks will be simulated" -ForegroundColor Yellow
    }
    
    if ($isAdmin) {
        Write-Host "  Admin privileges: Full Windows Event Log access" -ForegroundColor Green
    } else {
        Write-Host "  Standard privileges: Limited Event Log access" -ForegroundColor Yellow
    }
    
    # Configure eBPF for Linux
    if ([System.Environment]::OSVersion.Platform -eq "Unix") {
        Write-Host "  Linux detected: eBPF monitoring will be attempted" -ForegroundColor Green
    }
    
    Write-Host "  Starting client (Press Ctrl+C to stop)..." -ForegroundColor White
    python main.py client --config config/client_config.yaml
} else {
    Write-Host "`nClient startup skipped (use -SkipClient to skip)" -ForegroundColor Yellow
}

Write-Host "`nCodeGrey AI SOC Platform URLs:" -ForegroundColor Cyan
Write-Host "  Base URL: http://localhost:8080/api/backend" -ForegroundColor White
Write-Host "  Health Check: http://localhost:8080/health" -ForegroundColor White
Write-Host "  Agents API: http://localhost:8080/api/backend/agents" -ForegroundColor White
Write-Host "  Network Topology: http://localhost:8080/api/backend/network-topology" -ForegroundColor White
Write-Host "  Software Download: http://localhost:8080/api/backend/software-download" -ForegroundColor White
Write-Host "  Attack Operations: http://localhost:8080/api/backend/langgraph/attack/start" -ForegroundColor White
Write-Host "  Detection Status: http://localhost:8080/api/backend/langgraph/detection/status" -ForegroundColor White

Write-Host "`nAI SOC Platform is ready!" -ForegroundColor Green
Write-Host "`nUsage examples:" -ForegroundColor Cyan
Write-Host "  .\start_platform_enhanced.ps1                    # Normal startup" -ForegroundColor White
Write-Host "  .\start_platform_enhanced.ps1 -InstallDocker     # Install Docker first" -ForegroundColor White
Write-Host "  .\start_platform_enhanced.ps1 -RunAsAdmin       # Run as Administrator" -ForegroundColor White
Write-Host "  .\start_platform_enhanced.ps1 -SkipClient       # Server only" -ForegroundColor White
