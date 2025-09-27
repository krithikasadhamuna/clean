@echo off
REM CodeGrey AI SOC Platform - Local Development Environment

echo CodeGrey AI SOC Platform - Development Environment
echo ====================================================
echo.

REM Set development environment
set SOC_ENV=development
set PYTHONPATH=%CD%

echo Starting development server on localhost:8080...
echo.
echo Development Features:
echo   - Debug logging enabled
echo   - CORS fully open
echo   - No authentication required
echo   - Hot reload enabled
echo   - API docs: http://localhost:8080/docs
echo.

REM Start development server
python start_dev_server.py

pause

