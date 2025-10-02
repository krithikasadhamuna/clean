@echo off
echo ========================================
echo CodeGrey AI SOC Platform - Windows Agent v2.0
echo Dynamic Installation Script
echo ========================================
echo.

echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    echo Download from: https://python.org/downloads
    pause
    exit /b 1
)

echo [2/5] Checking Python version...
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Setting up configuration...
if not exist config.yaml (
    echo Creating default configuration...
    python -c "
import yaml
config = {
    'server_endpoint': 'http://localhost:8080',
    'agent_id': 'auto',
    'heartbeat_interval': 60,
    'network_discovery': {
        'enabled': True,
        'scan_interval': 1800,
        'max_threads': 50,
        'timeout': 3
    },
    'log_forwarding': {
        'enabled': True,
        'batch_size': 100,
        'sources': ['windows_events', 'process_monitor', 'network_monitor']
    },
    'container_management': {
        'enabled': False,
        'max_containers': 10
    },
    'security': {
        'encryption_enabled': True,
        'validate_certificates': True
    }
}
with open('config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
print('Default configuration created')
"
)

echo [5/5] Installation complete!
echo.
echo ========================================
echo NEXT STEPS:
echo ========================================
echo 1. Configure the agent:
echo    python main.py --configure
echo.
echo 2. Start the agent:
echo    python main.py
echo.
echo 3. For advanced features:
echo    python main.py --help
echo.
echo  Features included:
echo  Dynamic network discovery
echo  ML-powered threat detection  
echo  Real-time location learning
echo  Behavioral anomaly detection
echo  Container orchestration (with Docker)
echo  Zero hardcoded patterns
echo.
echo  Your endpoint is now protected by AI!
echo ========================================
pause
