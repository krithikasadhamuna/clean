# AI SOC Platform Startup Script
# Handles common issues and provides production-ready startup

Write-Host "Starting AI SOC Platform..." -ForegroundColor Green

# Check if server is already running
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 3
    Write-Host "Server already running" -ForegroundColor Green
} catch {
    Write-Host "Starting server..." -ForegroundColor Yellow
    
    # Start server in background
    Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; python main.py server --host 0.0.0.0 --port 8080" -WindowStyle Minimized
    
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
            Write-Host "   Waiting for server... ($attempts/30)" -ForegroundColor Yellow
        }
    }
    
    if (-not $serverReady) {
        Write-Host "Server failed to start" -ForegroundColor Red
        exit 1
    }
}

# Display server status
Write-Host "`nServer Status:" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8080/health"
    Write-Host "   Status: $($health.status)" -ForegroundColor Green
    Write-Host "   Version: $($health.version)" -ForegroundColor Green
    Write-Host "   API Type: $($health.api_type)" -ForegroundColor Green
} catch {
    Write-Host "   Could not get server status" -ForegroundColor Yellow
}

# Display AI agents status
Write-Host "`nAI Agents:" -ForegroundColor Cyan
try {
    $agents = Invoke-RestMethod -Uri "http://localhost:8080/api/frontend/agents"
    foreach ($agent in $agents.agents) {
        $statusColor = if ($agent.status -eq "active") { "Green" } elseif ($agent.status -eq "inactive") { "Yellow" } else { "Red" }
        Write-Host "   $($agent.name): $($agent.status)" -ForegroundColor $statusColor
    }
    Write-Host "   Total AI Agents: $($agents.metadata.ai_agents)" -ForegroundColor Green
} catch {
    Write-Host "   Could not get agents status" -ForegroundColor Yellow
}

# Start client (optional)
$startClient = Read-Host "`nStart client agent? (y/n)"
if ($startClient -eq "y" -or $startClient -eq "Y") {
    Write-Host "Starting client agent..." -ForegroundColor Yellow
    Write-Host "   Note: Docker and admin privileges not required for basic functionality" -ForegroundColor Cyan
    
    # Start client
    python main.py client --config config/client_config.yaml
}

Write-Host "`nAI SOC Platform URLs:" -ForegroundColor Cyan
Write-Host "   Health Check: http://localhost:8080/health" -ForegroundColor White
Write-Host "   Agents API: http://localhost:8080/api/frontend/agents" -ForegroundColor White
Write-Host "   Network Topology: http://localhost:8080/api/frontend/network-nodes" -ForegroundColor White
Write-Host "   LangChain SOC: http://localhost:8080/api/soc/playground" -ForegroundColor White

Write-Host "`nAI SOC Platform is ready for use!" -ForegroundColor Green
