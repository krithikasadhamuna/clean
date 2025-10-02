# PowerShell script to test AI SOC Platform APIs

Write-Host "Testing AI SOC Platform APIs..." -ForegroundColor Green

# Test 1: Get Agents List
Write-Host "`n1. Testing Agents API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/frontend/agents" -Method GET
    Write-Host "   Agents found: $($response.agents.Count)" -ForegroundColor Green
    Write-Host "   AI Agents: $($response.metadata.ai_agents)" -ForegroundColor Green
    Write-Host "   Endpoint Agents: $($response.metadata.endpoint_agents)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Get Network Topology
Write-Host "`n2. Testing Network Topology API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/frontend/network-nodes" -Method GET
    Write-Host "   Network nodes: $($response.network_nodes.Count)" -ForegroundColor Green
    Write-Host "   Total agents: $($response.metadata.total_agents)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Test Health Check
Write-Host "`n3. Testing Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method GET
    Write-Host "   Status: $($response.status)" -ForegroundColor Green
    Write-Host "   Version: $($response.version)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Test LangChain Detection (if available)
Write-Host "`n4. Testing LangChain Detection API..." -ForegroundColor Yellow
try {
    $body = @{
        input = "Analyze this suspicious PowerShell command: powershell.exe -EncodedCommand dGVzdA=="
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/detection/invoke" -Method POST -Body $body -ContentType "application/json"
    Write-Host "   Detection response received" -ForegroundColor Green
} catch {
    Write-Host "   LangChain API not available (expected): $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`nAPI Testing Complete!" -ForegroundColor Green
