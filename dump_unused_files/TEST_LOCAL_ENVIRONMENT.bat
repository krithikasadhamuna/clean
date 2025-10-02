@echo off
REM Quick Test Script for Local Development Environment
REM This opens all 3 terminals automatically

echo ================================================================================
echo CODEGREY AI SOC PLATFORM - LOCAL DEVELOPMENT ENVIRONMENT
echo Automated 3-Terminal Test Setup
echo ================================================================================
echo.

echo This will open 3 terminals:
echo   1. Server (Port 8081)
echo   2. Client Agent
echo   3. Attack Simulation Test
echo.

pause

REM Terminal 1: Start Server
echo Opening Terminal 1: Server...
start "CodeGrey Server" cmd /k "python start_local_dev_environment.py"

echo Waiting 15 seconds for server to initialize...
timeout /t 15 /nobreak

REM Terminal 2: Start Client
echo Opening Terminal 2: Client Agent...
start "CodeGrey Client" cmd /k "cd CodeGrey-AI-SOC-Platform-Unified\packages\codegrey-agent-windows-unified && python main.py"

echo Waiting 10 seconds for client to register...
timeout /t 10 /nobreak

REM Terminal 3: Run Test
echo Opening Terminal 3: Attack Test...
start "CodeGrey Test" cmd /k "python test_attack_simulation_local.py && pause"

echo.
echo ================================================================================
echo ALL TERMINALS OPENED!
echo ================================================================================
echo.
echo Check the 3 terminals for:
echo   - Terminal 1: Server logs
echo   - Terminal 2: Client agent logs
echo   - Terminal 3: Test results
echo.
echo To stop:
echo   - Press Ctrl+C in each terminal
echo   - Or close the terminal windows
echo.
echo ================================================================================

pause

