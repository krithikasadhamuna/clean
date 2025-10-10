@echo off
REM Start Windows client agent for testing

echo ==========================================
echo Starting Windows Client Agent
echo ==========================================
echo.

cd CodeGrey-AI-SOC-Platform-Unified\packages\codegrey-agent-windows-unified

echo Client agent directory: %CD%
echo Server URL: http://127.0.0.1:8000
echo.

python unified_client_agent_clean.py --server-url http://127.0.0.1:8000


