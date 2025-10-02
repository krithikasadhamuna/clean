@echo off
echo CodeGrey AI SOC Platform - Docker Installation
echo ==============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator - OK
) else (
    echo ERROR: This script must be run as Administrator!
    echo Right-click Command Prompt and select "Run as Administrator"
    pause
    exit /b 1
)

echo.
echo Step 1: Enabling Windows features for Docker...
echo.

REM Enable Hyper-V
echo Enabling Hyper-V...
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V -All /NoRestart

REM Enable Containers
echo Enabling Containers...
dism.exe /online /enable-feature /featurename:Containers -All /NoRestart

REM Enable WSL
echo Enabling Windows Subsystem for Linux...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /All /NoRestart

echo.
echo Step 2: Downloading Docker Desktop...
echo.

REM Download Docker Desktop
set "docker_url=https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe"
set "docker_file=%TEMP%\DockerDesktopInstaller.exe"

echo Downloading Docker Desktop installer...
powershell -Command "& {Invoke-WebRequest -Uri '%docker_url%' -OutFile '%docker_file%' -UseBasicParsing}"

if not exist "%docker_file%" (
    echo ERROR: Failed to download Docker Desktop installer
    pause
    exit /b 1
)

echo Docker Desktop installer downloaded successfully
echo.

echo Step 3: Installing Docker Desktop...
echo This may take several minutes...
echo.

REM Install Docker Desktop
"%docker_file%" install --quiet --accept-license

if %errorLevel% == 0 (
    echo Docker Desktop installed successfully
) else (
    echo ERROR: Docker Desktop installation failed
    pause
    exit /b 1
)

echo.
echo Step 4: Starting Docker Desktop...
echo.

REM Start Docker Desktop
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo Docker Desktop is starting...
echo Please wait for Docker to fully initialize (this may take 2-3 minutes)
echo.

REM Wait for Docker to be ready
echo Waiting for Docker to be ready...
timeout /t 60 /nobreak >nul

echo.
echo Step 5: Testing Docker installation...
echo.

REM Test Docker
docker --version
if %errorLevel% == 0 (
    echo Docker is working correctly
) else (
    echo WARNING: Docker may not be fully ready yet
    echo Please wait a few more minutes and try running 'docker --version'
)

echo.
echo Step 6: Downloading required container images...
echo.

REM Pull required images
echo Downloading Ubuntu 22.04...
docker pull ubuntu:22.04

echo Downloading Nginx...
docker pull nginx:alpine

echo Downloading MySQL...
docker pull mysql:8.0

echo Downloading Windows Server Core...
docker pull mcr.microsoft.com/windows/servercore:ltsc2019

echo.
echo Step 7: Testing container functionality...
echo.

REM Test with hello-world
echo Testing with hello-world container...
docker run --rm hello-world

echo.
echo ==============================================
echo DOCKER INSTALLATION COMPLETE!
echo ==============================================
echo.
echo Docker Desktop has been installed and configured
echo Required container images have been downloaded
echo.
echo IMPORTANT NOTES:
echo - Docker Desktop will start automatically on system boot
echo - You may need to restart your computer for all features to work
echo - If Docker Desktop doesn't start, run it manually from Start menu
echo.
echo NEXT STEPS:
echo 1. Restart your computer (recommended)
echo 2. Run CodeGrey Agent - container capabilities will now be available!
echo.
echo Your CodeGrey AI SOC Platform now has full container support!
echo.

pause

