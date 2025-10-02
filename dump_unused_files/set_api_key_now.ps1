# PowerShell script to set OpenAI API Key immediately
Write-Host "Setting OpenAI API Key as Global Environment Variable..." -ForegroundColor Green

# Set for current user (persistent)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "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", "User")

# Set for current session
$env:OPENAI_API_KEY = "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"

Write-Host "SUCCESS: OpenAI API Key has been set!" -ForegroundColor Green
Write-Host "Current session API Key: $env:OPENAI_API_KEY" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now start the server with:" -ForegroundColor Yellow
Write-Host "python main.py server --host 127.0.0.1 --port 8081" -ForegroundColor White
