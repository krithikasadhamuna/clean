# CodeGrey AI SOC Platform - Windows Client Agent v2.0

## Advanced Windows Endpoint Agent with AI-Powered Capabilities

### New Features in v2.0
- **Dynamic Network Discovery** - Automatically discovers and maps network topology
- **Real-Time Location Detection** - Learns physical locations from environment data
- **Enhanced Threat Detection** - ML-based threat analysis with zero hardcoded patterns
- **Container Orchestration** - Red Team attack container management
- **Advanced Logging** - Comprehensive activity monitoring and forensics
- **Self-Learning System** - Adapts to environment without predefined rules

### Core Capabilities
- **Real-time log forwarding** to SOC platform
- **Network topology discovery** and service enumeration
- **Behavioral anomaly detection** using machine learning
- **Attack scenario execution** in isolated containers
- **Dynamic threat pattern learning** from environment
- **Physical location inference** from network traffic analysis

### System Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk**: 2 GB free space
- **Network**: Internet connectivity for SOC communication
- **Privileges**: Administrator rights for full functionality
- **Optional**: Docker Desktop for container-based attack testing

### Installation

#### Quick Start
```powershell
# 1. Extract the package
Expand-Archive codegrey-agent-windows-v2.zip -DestinationPath C:\CodeGrey

# 2. Navigate to directory
cd C:\CodeGrey\codegrey-agent-windows-v2

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure agent
python main.py --configure

# 5. Start agent
python main.py
```

#### Advanced Installation
```powershell
# Install with Docker support for Red Team capabilities
# 1. Install Docker Desktop
# 2. Enable Windows containers (optional)
# 3. Run installation script
.\install.bat
```

### Configuration

#### Basic Configuration
```powershell
python main.py --configure
```
You'll be prompted for:
- **SOC Server URL** (e.g., http://your-soc-server.com:8080)
- **API Token** (optional, leave blank for development)

#### Advanced Configuration
Edit `config.yaml` for advanced settings:
```yaml
server_endpoint: "http://your-soc-server.com:8080"
agent_id: "auto"  # Auto-generate from hostname
heartbeat_interval: 60

# Network Discovery Settings
network_discovery:
  enabled: true
  scan_interval: 1800  # 30 minutes
  max_threads: 50
  timeout: 3

# Log Forwarding
log_forwarding:
  enabled: true
  batch_size: 100
  sources:
    - windows_events
    - process_monitor
    - network_monitor
    - file_monitor

# Container Management (requires Docker)
container_management:
  enabled: true
  max_containers: 10
  auto_cleanup: true
```

### Usage

#### Standard Monitoring
```powershell
# Start with default configuration
python main.py

# Start with custom config
python main.py --config custom_config.yaml

# Start with verbose logging
python main.py --debug
```

#### Network Discovery
```powershell
# Run immediate network scan
python main.py --scan-network

# View discovered hosts
python main.py --show-topology
```

#### Attack Testing (Red Team Mode)
```powershell
# Enable Red Team capabilities
python main.py --red-team

# Execute specific attack scenario
python main.py --attack-scenario phishing_test
```

### Monitoring and Logs

#### Log Files
- **Agent Activity**: `codegrey-agent.log`
- **Network Discovery**: `network_discovery.log`
- **Attack Logs**: `attack_logs/` directory
- **Detection Results**: Sent to SOC server

#### Real-time Monitoring
```powershell
# View real-time agent status
python main.py --status

# Monitor network discovery
python main.py --monitor-network

# View threat detection results
python main.py --show-threats
```

### Security Features

#### Dynamic Threat Detection
- **Zero hardcoded patterns** - All threat detection learned from environment
- **Behavioral analysis** - Compares current activity to historical patterns
- **ML-based classification** - Uses machine learning for threat categorization
- **Adaptive thresholds** - Adjusts sensitivity based on log source and level

#### Network Security
- **Encrypted communication** with SOC server
- **Certificate validation** for secure connections
- **Local data encryption** for sensitive logs
- **Privilege escalation detection** and prevention

### Troubleshooting

#### Common Issues

**Agent won't start:**
```powershell
# Check Python version (3.8+ required)
python --version

# Install missing dependencies
pip install -r requirements.txt

# Run with debug output
python main.py --debug
```

**Network discovery not working:**
```powershell
# Check firewall settings
# Run as Administrator
# Verify network connectivity
ping 8.8.8.8
```

**Container features not available:**
```powershell
# Install Docker Desktop
# Start Docker service
# Verify Docker is running
docker version
```

#### Log Analysis
```powershell
# Check agent logs
type codegrey-agent.log

# Check network discovery logs
type network_discovery.log

# View last 50 log entries
python -c "with open('codegrey-agent.log') as f: print(''.join(f.readlines()[-50:]))"
```

### Support

#### Getting Help
- **Documentation**: Check README files in each module
- **Logs**: Review `codegrey-agent.log` for detailed information
- **Debug Mode**: Run with `--debug` flag for verbose output
- **SOC Dashboard**: Check server dashboard for agent status

#### Performance Optimization
- **Reduce scan frequency** if network discovery causes performance issues
- **Adjust batch sizes** for log forwarding based on network capacity
- **Enable container cleanup** to manage disk space usage

### Updates and Maintenance

#### Automatic Updates
The agent automatically checks for updates and applies them without disrupting operations.

#### Manual Updates
```powershell
# Download new version
# Stop current agent
python main.py --stop

# Replace files
# Restart agent
python main.py
```

### Advanced Features

#### Red Team Integration
- **Attack container orchestration** for security testing
- **Phishing infrastructure setup** with SMTP servers
- **Dynamic attack resource creation** based on discovered topology
- **Comprehensive attack logging** and forensic analysis

#### AI-Powered Analysis
- **Machine learning models** trained on your specific environment
- **Behavioral baseline establishment** for accurate anomaly detection
- **Dynamic pattern recognition** without predefined rules
- **Continuous learning** and adaptation to new threats

---

**CodeGrey AI SOC Platform - Intelligent, Adaptive, Dynamic Security**
