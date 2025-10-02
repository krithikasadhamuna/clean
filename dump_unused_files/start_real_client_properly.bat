@echo off
echo ================================================================================
echo STARTING REAL CLIENT AGENT
echo ================================================================================
echo.

cd /d "c:\Users\krith\Desktop\clean\CodeGrey-AI-SOC-Platform-Unified\packages\codegrey-agent-windows-unified"

echo Current directory: %CD%
echo.
echo Checking files...
if exist "main.py" (
    echo [OK] main.py found
) else (
    echo [ERROR] main.py not found!
    pause
    exit /b 1
)

if exist "config.yaml" (
    echo [OK] config.yaml found
) else (
    echo [ERROR] config.yaml not found!
    pause
    exit /b 1
)

echo.
echo Checking configuration...
python -c "import yaml; config = yaml.safe_load(open('config.yaml')); print(f'Server endpoint: {config[\"client\"][\"server_endpoint\"]}')"

echo.
echo ================================================================================
echo STARTING CLIENT AGENT NOW
echo ================================================================================
echo Server: http://127.0.0.1:8081
echo Press Ctrl+C to stop
echo ================================================================================
echo.

python main.py

pause

