@echo off
REM CodeGrey AI SOC Platform - Windows Client Agent Installer

echo CodeGrey AI SOC Platform - Windows Client Agent
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python detected. Installing dependencies...

REM Install dependencies
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Docker is not installed
    echo Container management features will be disabled
    echo Install Docker Desktop from https://docker.com if needed
    echo.
)

REM Create default config if it doesn't exist
if not exist config.yaml (
    echo Creating default configuration...
    python -c "from config_manager import ConfigManager; ConfigManager().load_config()"
)

echo.
echo Installation complete!
echo.
echo To configure the agent:
echo   python main.py --configure --server=http://15.207.6.45:8080
echo.
echo To start the agent:
echo   python main.py
echo.
pause
