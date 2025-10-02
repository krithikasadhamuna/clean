    # CodeGrey AI SOC Platform - Windows Agent

## Installation Guide

### Quick Start

1. **Run the Agent**: Double-click `Run-CodeGrey-Agent.bat`
2. **Configure Server**: Double-click `Configure-CodeGrey-Agent.bat` (if needed)

### Manual Installation

1. **Extract Files**: Extract all files to a folder on your Windows system
2. **Run Executable**: Double-click `CodeGrey-Agent-Windows-Final.exe`
3. **Configure**: Use `--configure` flag to set server details

### Configuration

The agent is pre-configured to connect to:
- **Server**: `http://backend.codegrey.ai:8080`
- **Agent ID**: Auto-generated based on system information

### Features

 **Windows Event Logs**: Security, System, Application, Sysmon, PowerShell, Defender
 **WMI Monitoring**: Process creation and system changes
 **Command Execution**: MITRE ATT&CK techniques support
 **Container Attacks**: Docker-based attack execution
 **Real-time Logging**: Continuous log forwarding
 **Auto Registration**: Automatic server registration

### Requirements

- **Windows 10/11** (64-bit)
- **PowerShell** (for event log access)
- **Docker** (optional, for container attacks)
- **Internet Connection** (for server communication)

### Troubleshooting

1. **PowerShell Access**: Run as Administrator for full event log access
2. **Docker Issues**: Install Docker Desktop for container features
3. **Server Connection**: Check firewall and network connectivity
4. **Logs**: Check `codegrey-agent.log` for detailed information

### Support

For issues or questions, check the logs or contact the SOC team.

---
**Version**: 2.0.0  
**Build Date**: September 29, 2025  
**Platform**: Windows 10/11 (64-bit)

