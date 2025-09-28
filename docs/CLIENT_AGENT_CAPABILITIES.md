# CodeGrey AI SOC Platform - Client Agent Capabilities v2.0

## COMPLETE SYSTEM PROFILING FOR EXACT CONTAINER REPLICATION

### Enhanced System Information Collection

#### Windows Client Agent v2.0
**Collects complete system profile for exact attack container replication:**

**Basic System Info:**
- Hostname, OS version, architecture, processor
- Memory and disk usage across all drives
- Network interfaces and IP configurations

**Installed Software Profile:**
- Complete list of installed applications with versions
- Registry-based software enumeration
- System features (Hyper-V, WSL, Docker)

**Running Services:**
- All Windows services with status
- Service names and display names
- Running/stopped status for each service

**Network Configuration:**
- Open ports and listening services
- DNS server configurations
- Default gateway settings
- Network adapter details with MAC addresses

**Security Settings:**
- Windows Defender status and configuration
- Windows Firewall status
- UAC (User Account Control) settings
- Real-time protection status

**System Configuration:**
- Windows build number and edition
- Installed patches and security updates
- Critical registry settings
- Environment variables (non-sensitive)

**User Account Information:**
- Local user accounts (non-sensitive data)
- Account types and privileges

#### Linux Client Agent v2.0
**Enhanced for Linux system profiling:**

**System Information:**
- Distribution, kernel version, architecture
- Package manager type (apt, yum, dnf)
- Installed packages with versions
- Running processes and services

**Network Configuration:**
- Network interfaces and routing tables
- Firewall rules (iptables/ufw)
- DNS configuration (/etc/resolv.conf)
- Open ports and listening services

**Security Settings:**
- SELinux/AppArmor status
- Sudo configuration
- SSH configuration
- System hardening settings

#### macOS Client Agent v2.0
**Privacy-compliant macOS profiling:**

**System Information:**
- macOS version, build number
- Installed applications (with user consent)
- System preferences and settings
- Hardware configuration

**Security Settings:**
- XProtect status
- Gatekeeper configuration
- System Integrity Protection (SIP)
- FileVault encryption status

### Attack Container Replication Process

#### 1. System Analysis
```
Client Agent → Collects complete system profile
             → Sends to SOC server
             → Server analyzes target configuration
```

#### 2. Container Creation
```
SOC Server → Creates exact replica container
          → Installs same OS version
          → Replicates installed software
          → Configures same services
          → Sets up identical network configuration
```

#### 3. Attack Execution
```
Attack Container → Executes attack scenarios
                → Logs all activities
                → Captures network traffic
                → Records system changes
```

#### 4. Log Extraction
```
Attack Container → Generates comprehensive logs
                → Extracts forensic data
                → Sends results to SOC server
                → Cleans up container environment
```

### Container Replication Examples

#### Windows Target System
```
Target: Windows 10 Pro (Build 19044)
- IIS Web Server 10.0
- SQL Server 2019
- .NET Framework 4.8
- Windows Defender enabled
- Firewall enabled

Container Replica:
- Windows Server Core (Build 19044)
- IIS 10.0 installed and configured
- SQL Server 2019 with same configuration
- .NET Framework 4.8
- Security settings replicated
- Network configuration mirrored
```

#### Linux Target System
```
Target: Ubuntu 20.04 LTS
- Apache 2.4.41
- MySQL 8.0
- PHP 7.4
- UFW firewall enabled
- SSH service running

Container Replica:
- Ubuntu 20.04 LTS base image
- Apache 2.4.41 with same modules
- MySQL 8.0 with identical configuration
- PHP 7.4 with same extensions
- UFW rules replicated
- SSH configuration mirrored
```

### Attack Scenario Capabilities

#### 1. Web Application Testing
- Exact web server configuration replication
- Database connection string duplication
- Application framework matching
- Security setting replication

#### 2. Network Penetration Testing
- Network topology replication
- Service configuration matching
- Firewall rule duplication
- Routing table replication

#### 3. Phishing Infrastructure
- Email server configuration matching
- DNS setting replication
- SSL certificate generation
- Web server configuration duplication

#### 4. Lateral Movement Testing
- Domain configuration replication
- User account structure matching
- Service account duplication
- Network access control replication

### Data Transmission to Server

#### Heartbeat Data Includes:
```json
{
  "agent_id": "auto",
  "system_info": {
    "hostname": "TARGET-SYSTEM",
    "os_version": "Windows 10 Pro 19044",
    "installed_software": [...],
    "running_services": [...],
    "open_ports": [...],
    "security_settings": {...},
    "network_configuration": {...}
  },
  "network_discovery": {
    "discovered_hosts": {...},
    "network_topology": {...}
  }
}
```

#### Log Data Includes:
- Real-time system activity
- Process execution logs
- Network traffic logs
- Security event logs
- Application logs

### Container Orchestration Flow

#### 1. Target Selection
```
SOC Platform → Analyzes discovered network topology
             → Selects target system for testing
             → Retrieves complete system profile
```

#### 2. Container Generation
```
Red Team Orchestrator → Creates Dockerfile from system profile
                     → Builds exact replica container
                     → Configures network access
                     → Sets up attack tools
```

#### 3. Attack Execution
```
Attack Container → Executes specific attack scenarios
                → Monitors all activities
                → Captures comprehensive logs
                → Records attack success/failure
```

#### 4. Results Analysis
```
SOC Platform → Analyzes attack logs
             → Identifies detection gaps
             → Generates security recommendations
             → Updates threat models
```

## DEPLOYMENT READY

**All client agents now collect complete system information for:**
- **Exact container replication** of target systems
- **Precise attack scenario execution** in replicated environments
- **Comprehensive forensic analysis** of attack activities
- **Accurate security testing** with real-world configurations

**The attack containers will be EXACT replicas of the target systems, ensuring realistic and accurate security testing.**
