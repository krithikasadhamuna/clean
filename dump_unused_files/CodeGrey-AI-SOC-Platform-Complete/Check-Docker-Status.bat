@echo off
echo CodeGrey AI SOC Platform - Docker Status Check
echo ==============================================
echo.

echo Checking Docker installation...
docker --version
if %errorLevel% == 0 (
    echo.
    echo Docker is installed and working!
    echo.
    echo Checking Docker daemon...
    docker info >nul 2>&1
    if %errorLevel% == 0 (
        echo Docker daemon is running - Container capabilities available!
    ) else (
        echo Docker daemon is not running - Start Docker Desktop
    )
) else (
    echo Docker is not installed - Run install_docker_simple.bat as Administrator
)

echo.
echo Press any key to exit...
pause >nul

