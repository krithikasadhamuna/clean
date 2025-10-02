# CodeGrey AI SOC Platform - Complete Deployment Package

## Overview
This package contains everything needed to deploy the CodeGrey AI SOC Platform with full container-based attack simulation capabilities.

## Contents
- `CodeGrey-Agent-Windows.exe` - Enhanced client agent with Docker support
- `config.yaml` - Pre-configured settings for full capabilities
- `install_docker_simple.bat` - Automatic Docker installation (Windows)
- `install_docker_windows.ps1` - Advanced Docker installation script
- `Run-CodeGrey-Agent.bat` - Easy startup script
- `Check-Docker-Status.bat` - Docker status checker

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

### Core Capabilities
- Log forwarding (Windows Event Logs, Application Logs, System Logs)
- Command execution (Real MITRE ATT&CK techniques)
- Agent registration and heartbeat monitoring
- Network connectivity to SOC server

### Container Capabilities (with Docker)
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
Run `Check-Docker-Status.bat` to verify Docker installation.

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

