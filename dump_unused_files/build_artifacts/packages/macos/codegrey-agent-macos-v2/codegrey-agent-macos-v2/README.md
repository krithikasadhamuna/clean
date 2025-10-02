# CodeGrey AI SOC Platform - macOS Client Agent v2.0

## Advanced macOS Endpoint Agent with Privacy-First AI Security

### New Features in v2.0
- ** Privacy-Aware Network Discovery** - Respects macOS privacy controls
- **📍 Location Learning with Privacy** - Learns locations without compromising user privacy
- ** XProtect Integration** - Works with Apple's built-in security
- ** Container Security Testing** - Advanced Red Team capabilities with Docker
- ** Behavioral Analysis** - ML-based detection respecting macOS sandboxing
- ** Adaptive Learning** - Continuously learns from environment within privacy boundaries

### Core Capabilities
- **Privacy-compliant log collection** from system and security logs
- **Dynamic network topology discovery** with user consent
- **ML-powered threat detection** that respects macOS security model
- **Container-based security testing** in isolated environments
- **Behavioral baseline learning** within privacy constraints
- **Geographic inference** from network patterns (privacy-safe)

### System Requirements
- **OS**: macOS 11.0 (Big Sur) or later
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk**: 2 GB free space
- **Network**: Internet connectivity for SOC communication
- **Privileges**: Administrator access for system monitoring
- **Optional**: Docker Desktop for container-based testing

### Privacy and Security
- **Full Disk Access** permission required for comprehensive monitoring
- **Network monitoring** requires user consent
- **All data encrypted** locally and in transit
- **Respects macOS privacy controls** and user preferences
- **No data collection** without explicit user consent

### Installation

#### Quick Installation
```bash
# 1. Extract package
tar -xzf codegrey-agent-macos-v2.tar.gz
cd codegrey-agent-macos-v2

# 2. Run installer
sudo ./install.sh

# 3. Grant permissions in System Preferences
# Go to: System Preferences > Security & Privacy > Privacy
# Grant "Full Disk Access" to CodeGrey Agent

# 4. Configure agent
sudo python3 main.py --configure

# 5. Start agent
sudo python3 main.py
```

#### Manual Installation
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install Homebrew dependencies
brew install nmap

# Configure agent
python3 main.py --configure
```

#### Launch Agent Installation
```bash
# Install as LaunchAgent for auto-start
sudo cp com.codegrey.agent.plist /Library/LaunchAgents/
sudo launchctl load /Library/LaunchAgents/com.codegrey.agent.plist

# Check status
launchctl list | grep codegrey
```

### Configuration

#### Interactive Setup
```bash
python3 main.py --configure
```

#### Configuration File
Edit `~/Library/Application Support/CodeGrey/config.yaml`:
```yaml
server_endpoint: "http://your-soc-server.com:8080"
agent_id: "auto"
heartbeat_interval: 60

# Network Discovery (requires user consent)
network_discovery:
  enabled: true
  scan_interval: 1800
  respect_privacy: true
  user_consent_required: true

# Log Sources (privacy-compliant)
log_forwarding:
  enabled: true
  sources:
    - system_log
    - security_log
    - application_log
    - network_log  # Requires permission
  privacy_mode: true
  anonymize_sensitive_data: true

# macOS Integration
macos_integration:
  xprotect_integration: true
  gatekeeper_monitoring: true
  system_integrity_protection: true
  notarization_checking: true

# Container Management (requires Docker Desktop)
container_management:
  enabled: false
  docker_desktop_required: true
  max_containers: 5
```

### Usage

#### Basic Operations
```bash
# Start agent
sudo python3 main.py

# Start with privacy mode
python3 main.py --privacy-mode

# Run system check
python3 main.py --system-check

# Check permissions
python3 main.py --check-permissions
```

#### Network Discovery
```bash
# Run network scan (requires permission)
sudo python3 main.py --scan-network

# Show network topology
python3 main.py --show-topology

# Export topology (anonymized)
python3 main.py --export-topology --anonymize
```

#### Security Testing
```bash
# Enable Red Team mode (requires Docker Desktop)
sudo python3 main.py --red-team

# Run security assessment
sudo python3 main.py --security-test

# Generate privacy-compliant security report
python3 main.py --security-report --privacy-safe
```

### Monitoring

#### Log Files
- **Agent Logs**: `~/Library/Logs/CodeGrey/agent.log`
- **Network Discovery**: `~/Library/Logs/CodeGrey/network.log`
- **Security Events**: `~/Library/Logs/CodeGrey/security.log`
- **System Logs**: Integration with Console.app

#### Real-time Monitoring
```bash
# Monitor agent activity
tail -f ~/Library/Logs/CodeGrey/agent.log

# Monitor network discovery
tail -f ~/Library/Logs/CodeGrey/network.log

# View agent status
python3 main.py --status

# Monitor with Console.app
open -a Console
```

### Security Features

#### macOS-Specific Security
- **XProtect integration** - Works with Apple's malware detection
- **Gatekeeper monitoring** - Tracks app notarization status
- **SIP compliance** - Respects System Integrity Protection
- **Privacy-first design** - Minimal data collection with user consent

#### Advanced Threat Detection
- **Dynamic pattern learning** from macOS-specific logs
- **Behavioral analysis** using Core ML frameworks
- **Zero-signature detection** - no hardcoded threat patterns
- **Privacy-safe threat scoring** - analysis without data exposure

### Troubleshooting

#### Permission Issues
```bash
# Check Full Disk Access permission
python3 main.py --check-permissions

# Reset permissions
sudo python3 main.py --reset-permissions

# Check System Preferences
open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
```

#### Network Issues
```bash
# Test connectivity
curl -I http://your-soc-server.com:8080/health

# Check network permissions
python3 main.py --check-network-permissions

# Test network discovery
sudo nmap -sn 192.168.1.0/24
```

#### Container Issues
```bash
# Check Docker Desktop
docker version

# Install Docker Desktop if needed
open https://desktop.docker.com/mac/main/amd64/Docker.dmg

# Fix Docker permissions
sudo dscl . append /Groups/docker GroupMembership $USER
```

### Performance Optimization

#### Resource Management
```bash
# For MacBook battery optimization
network_discovery:
  scan_interval: 7200  # Scan every 2 hours
  max_threads: 10      # Reduce CPU usage

# For high-performance Macs
network_discovery:
  scan_interval: 900   # Scan every 15 minutes
  max_threads: 100     # Higher performance
```

#### Privacy Optimization
```yaml
# Maximum privacy mode
log_forwarding:
  anonymize_sensitive_data: true
  exclude_personal_info: true
  hash_identifiers: true

privacy_settings:
  minimal_data_collection: true
  local_processing_only: true
  no_cloud_analysis: true
```

### macOS Integration

#### System Integration
- **Menu bar status indicator** - Shows agent status
- **Notification Center** - Security alerts and status updates
- **Spotlight integration** - Search agent logs and reports
- **Quick Actions** - Shortcuts for common operations

#### Apple Silicon Support
- **Native M1/M2 support** - Optimized for Apple Silicon
- **Rosetta compatibility** - Works on Intel Macs too
- **Universal binary** - Single package for all Mac architectures

### Privacy Compliance

#### Data Handling
- **Local processing** - Analysis happens on-device when possible
- **Encrypted storage** - All local data encrypted with FileVault integration
- **Minimal data transmission** - Only essential security data sent to SOC
- **User control** - Users can disable any monitoring feature

#### Compliance Features
- **GDPR compliant** - Right to deletion and data portability
- **SOC 2 Type II** - Enterprise security controls
- **Apple privacy guidelines** - Follows Apple's privacy principles
- **Transparency reports** - Users can see what data is collected

---

**CodeGrey AI SOC Platform - Intelligent macOS Security with Privacy First**
