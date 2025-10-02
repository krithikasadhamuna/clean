#!/usr/bin/env python3
"""
Create Complete Deployment Package for CodeGrey AI SOC Platform
Includes Docker installation, enhanced executable, and all configurations
"""

import os
import shutil
from pathlib import Path

def create_deployment_package():
    """Create complete deployment package"""
    
    print("CodeGrey AI SOC Platform - Creating Deployment Package")
    print("=" * 60)
    
    # Create deployment directory
    deploy_dir = Path("CodeGrey-AI-SOC-Platform-Complete")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    
    deploy_dir.mkdir()
    
    # Copy enhanced executable
    exe_source = Path("build_artifacts/packages/windows/codegrey-agent-windows-v2/dist/CodeGrey-Agent-Windows-Enhanced.exe")
    if exe_source.exists():
        shutil.copy2(exe_source, deploy_dir / "CodeGrey-Agent-Windows.exe")
        print(f" Copied enhanced executable: {exe_source.name}")
    else:
        print(f" Enhanced executable not found: {exe_source}")
        return False
    
    # Copy configuration files
    config_source = Path("build_artifacts/packages/windows/codegrey-agent-windows-v2/config.yaml")
    if config_source.exists():
        shutil.copy2(config_source, deploy_dir / "config.yaml")
        print(f" Copied configuration: config.yaml")
    
    # Copy Docker installation scripts
    docker_scripts = [
        "install_docker_simple.bat",
        "install_docker_windows.ps1"
    ]
    
    for script in docker_scripts:
        if Path(script).exists():
            shutil.copy2(script, deploy_dir / script)
            print(f" Copied Docker installer: {script}")
    
    # Create README
    readme_content = """# CodeGrey AI SOC Platform - Complete Deployment Package

## Overview
This package contains everything needed to deploy the CodeGrey AI SOC Platform with full container-based attack simulation capabilities.

## Contents
- `CodeGrey-Agent-Windows.exe` - Enhanced client agent with Docker support
- `config.yaml` - Pre-configured settings for full capabilities
- `install_docker_simple.bat` - Automatic Docker installation (Windows)
- `install_docker_windows.ps1` - Advanced Docker installation script
- `Run-CodeGrey-Agent.bat` - Easy startup script
- `Test-CodeGrey-Agent.bat` - Capability testing script

## Quick Start

### Option 1: Automatic Setup (Recommended)
1. Right-click `install_docker_simple.bat` and select "Run as Administrator"
2. Wait for Docker installation to complete (10-15 minutes)
3. Restart your computer when prompted
4. Run `Run-CodeGrey-Agent.bat` to start the agent

### Option 2: Manual Setup
1. Install Docker Desktop manually from https://docker.com
2. Run `CodeGrey-Agent-Windows.exe` directly

## Features Enabled

###  Core Capabilities
- Log forwarding (Windows Event Logs, Application Logs, System Logs)
- Command execution (Real MITRE ATT&CK techniques)
- Agent registration and heartbeat monitoring
- Network connectivity to SOC server

###  Container Capabilities (with Docker)
- Container-based attack simulation
- Golden image snapshots
- Isolated attack execution environments
- Multi-platform attack scenarios (Windows, Linux, Web, Database)
- Advanced MITRE ATT&CK technique execution
- Container log monitoring and forwarding

## Configuration
The agent is pre-configured to connect to:
- Server: http://backend.codegrey.ai:8080
- All container capabilities enabled
- Enhanced security settings
- Performance optimizations

## Testing
Run `Test-CodeGrey-Agent.bat` to verify all capabilities are working.

## Support
For issues or questions, check the logs in `codegrey-agent.log`.

## System Requirements
- Windows 10/11 (64-bit)
- 4GB RAM minimum (8GB recommended for containers)
- 10GB free disk space
- Internet connection
- Administrator privileges for Docker installation

## Security Note
This agent is designed for authorized security testing and SOC monitoring only.
Ensure you have proper authorization before deploying in any environment.
"""
    
    with open(deploy_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(" Created README.md")
    
    # Create startup script
    startup_script = """@echo off
echo CodeGrey AI SOC Platform - Enhanced Client Agent
echo ================================================
echo.
echo Starting enhanced client agent with full capabilities...
echo Server: http://backend.codegrey.ai:8080
echo.
echo Features enabled:
echo - Log forwarding
echo - Command execution
echo - Container-based attack simulation
echo - Golden image snapshots
echo - Multi-platform attack scenarios
echo.
echo Press Ctrl+C to stop the agent
echo.

CodeGrey-Agent-Windows.exe

echo.
echo Agent stopped. Press any key to exit...
pause >nul
"""
    
    with open(deploy_dir / "Run-CodeGrey-Agent.bat", "w") as f:
        f.write(startup_script)
    print(" Created Run-CodeGrey-Agent.bat")
    
    # Create test script
    test_script = """@echo off
echo CodeGrey AI SOC Platform - Capability Test
echo ==========================================
echo.
echo Testing all client agent capabilities...
echo.

CodeGrey-Agent-Windows.exe --test

echo.
echo Test completed. Press any key to exit...
pause >nul
"""
    
    with open(deploy_dir / "Test-CodeGrey-Agent.bat", "w") as f:
        f.write(test_script)
    print(" Created Test-CodeGrey-Agent.bat")
    
    # Create Docker status checker
    docker_check_script = """@echo off
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
"""
    
    with open(deploy_dir / "Check-Docker-Status.bat", "w") as f:
        f.write(docker_check_script)
    print(" Created Check-Docker-Status.bat")
    
    # Create installation guide
    install_guide = """# Installation Guide

## Step 1: Install Docker (Required for Container Capabilities)

### Automatic Installation (Recommended)
1. Right-click `install_docker_simple.bat`
2. Select "Run as Administrator"
3. Wait for installation to complete (10-15 minutes)
4. Restart your computer when prompted

### Manual Installation
1. Download Docker Desktop from https://docker.com
2. Install Docker Desktop
3. Start Docker Desktop
4. Verify installation by running `Check-Docker-Status.bat`

## Step 2: Deploy CodeGrey Agent

### Quick Start
1. Run `Run-CodeGrey-Agent.bat`
2. The agent will automatically connect to the SOC server
3. All capabilities will be enabled

### Manual Start
1. Run `CodeGrey-Agent-Windows.exe` directly
2. Monitor logs in `codegrey-agent.log`

## Step 3: Verify Installation

1. Run `Test-CodeGrey-Agent.bat`
2. Check that all tests pass
3. Verify connection to server

## Troubleshooting

### Docker Issues
- Run `Check-Docker-Status.bat` to diagnose
- Ensure Docker Desktop is running
- Check Windows features are enabled (Hyper-V, Containers, WSL)

### Connection Issues
- Verify server endpoint: http://backend.codegrey.ai:8080
- Check network connectivity
- Review logs in `codegrey-agent.log`

### Performance Issues
- Ensure sufficient RAM (4GB minimum, 8GB recommended)
- Check available disk space (10GB minimum)
- Monitor CPU usage during container operations

## Support
For additional support, check the logs and ensure all prerequisites are met.
"""
    
    with open(deploy_dir / "INSTALLATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(install_guide)
    print(" Created INSTALLATION_GUIDE.md")
    
    # Get package size
    total_size = sum(f.stat().st_size for f in deploy_dir.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT PACKAGE CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Package: {deploy_dir}")
    print(f"Size: {size_mb:.1f} MB")
    print("\nFiles included:")
    for file in sorted(deploy_dir.iterdir()):
        if file.is_file():
            file_size = file.stat().st_size / (1024 * 1024)
            print(f"  - {file.name} ({file_size:.1f} MB)")
    
    print("\n" + "=" * 60)
    print("READY FOR DEPLOYMENT!")
    print("=" * 60)
    print("Your CodeGrey AI SOC Platform package includes:")
    print(" Enhanced executable with Docker support")
    print(" Automatic Docker installation scripts")
    print(" Pre-configured settings for full capabilities")
    print(" Easy startup and testing scripts")
    print(" Complete documentation")
    print("\nNext steps:")
    print("1. Distribute the package to Windows endpoints")
    print("2. Run install_docker_simple.bat as Administrator")
    print("3. Start the agent with Run-CodeGrey-Agent.bat")
    print("4. Enjoy full container-based attack simulation!")
    
    return True

if __name__ == "__main__":
    create_deployment_package()

