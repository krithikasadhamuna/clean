@echo off
REM Start the actual client agent for testing

echo ================================================================================
echo STARTING ACTUAL CLIENT AGENT
echo ================================================================================
echo.

cd CodeGrey-AI-SOC-Platform-Unified\packages\codegrey-agent-windows-unified

echo Checking configuration...
python -c "import yaml; config = yaml.safe_load(open('config.yaml')); print(f'Server endpoint: {config.get(\"client\", {}).get(\"server_endpoint\", \"NOT SET\")}')"

echo.
echo Starting client agent...
echo Press Ctrl+C to stop
echo.

python main.py

