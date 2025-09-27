# CodeGrey AI SOC Platform - Linux Client Agent v2.0

## Advanced Linux Endpoint Agent with AI-Powered Security

### New Features in v2.0
- **🌐 Intelligent Network Discovery** - Learns network topology dynamically
- **📍 Geographic Location Learning** - Infers physical locations from traffic patterns
- **🛡️ Zero-Pattern Threat Detection** - ML-based detection without hardcoded rules
- **🐳 Container Security Testing** - Advanced Red Team capabilities
- **📊 Behavioral Analysis** - Learns normal vs. anomalous activity
- **🔄 Self-Adaptive System** - Continuously learns from environment

### Core Capabilities
- **Real-time log collection** from system, security, and application logs
- **Dynamic network topology mapping** with service discovery
- **ML-powered threat detection** that learns from your environment
- **Container-based attack simulation** for security testing
- **Behavioral baseline establishment** for accurate anomaly detection
- **Geographic and network zone inference** from traffic analysis

### System Requirements
- **OS**: Ubuntu 18.04+, CentOS 7+, RHEL 8+, Debian 10+
- **RAM**: 2 GB minimum, 4 GB recommended
- **Disk**: 1 GB free space
- **Network**: Internet connectivity for SOC communication
- **Privileges**: Root access for system monitoring
- **Optional**: Docker for container-based security testing

### Installation

#### Quick Installation
```bash
# 1. Extract package
tar -xzf codegrey-agent-linux-v2.tar.gz
cd codegrey-agent-linux-v2

# 2. Run installer
sudo ./install.sh

# 3. Configure agent
sudo python3 main.py --configure

# 4. Start agent
sudo python3 main.py
```

#### Manual Installation
```bash
# Install Python dependencies
sudo pip3 install -r requirements.txt

# Install system dependencies
sudo apt-get update
sudo apt-get install -y nmap tcpdump python3-dev

# For Red Hat/CentOS
sudo yum install -y nmap tcpdump python3-devel

# Configure agent
python3 main.py --configure
```

#### Service Installation
```bash
# Install as systemd service
sudo cp codegrey-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable codegrey-agent
sudo systemctl start codegrey-agent

# Check service status
sudo systemctl status codegrey-agent
```

### Configuration

#### Interactive Configuration
```bash
python3 main.py --configure
```

#### Configuration File
Edit `/etc/codegrey/config.yaml`:
```yaml
server_endpoint: "http://your-soc-server.com:8080"
agent_id: "auto"
heartbeat_interval: 60

# Network Discovery
network_discovery:
  enabled: true
  scan_interval: 1800
  interfaces: "auto"  # Auto-detect network interfaces
  scan_techniques:
    - ping_sweep
    - port_scan
    - service_detection

# Log Sources
log_forwarding:
  enabled: true
  sources:
    - syslog
    - auth_log
    - kernel_log
    - application_log
    - security_log
  batch_size: 100

# Security Settings
security:
  run_as_service: true
  log_encryption: true
  certificate_validation: true

# Container Management
container_management:
  enabled: false  # Enable for Red Team capabilities
  docker_socket: "/var/run/docker.sock"
  max_containers: 10
```

### Usage

#### Basic Operations
```bash
# Start agent
sudo python3 main.py

# Start with custom config
sudo python3 main.py --config /path/to/config.yaml

# Run in foreground with debug
python3 main.py --debug --foreground

# Check agent status
python3 main.py --status
```

#### Network Discovery
```bash
# Run immediate network scan
sudo python3 main.py --scan-network

# Show discovered topology
python3 main.py --show-topology

# Export topology to JSON
python3 main.py --export-topology topology.json
```

#### Security Testing
```bash
# Enable Red Team mode (requires Docker)
sudo python3 main.py --red-team

# Run security assessment
sudo python3 main.py --security-test

# Generate security report
python3 main.py --security-report
```

### Monitoring

#### Log Files
- **Agent Logs**: `/var/log/codegrey/agent.log`
- **Network Discovery**: `/var/log/codegrey/network.log`
- **Security Events**: `/var/log/codegrey/security.log`
- **Attack Logs**: `/var/log/codegrey/attacks/`

#### Real-time Monitoring
```bash
# Monitor agent activity
tail -f /var/log/codegrey/agent.log

# Monitor network discovery
tail -f /var/log/codegrey/network.log

# Monitor security events
tail -f /var/log/codegrey/security.log

# View agent metrics
python3 main.py --metrics
```

### Security Features

#### Advanced Threat Detection
- **Dynamic pattern learning** from environment-specific data
- **Behavioral anomaly detection** using ML models
- **Zero-signature detection** - no hardcoded threat patterns
- **Adaptive threat scoring** based on context and history

#### System Security
- **Privilege separation** - runs with minimal required privileges
- **Log encryption** - sensitive data encrypted at rest
- **Secure communication** - TLS encryption to SOC server
- **Container isolation** - attack testing in isolated environments

### Troubleshooting

#### Permission Issues
```bash
# Fix permission issues
sudo chown -R root:root /opt/codegrey
sudo chmod +x main.py

# Check SELinux (if applicable)
sudo setsebool -P container_manage_cgroup on
```

#### Network Issues
```bash
# Check connectivity
curl -I http://your-soc-server.com:8080/health

# Test network discovery
sudo nmap -sn 192.168.1.0/24

# Check firewall
sudo iptables -L
sudo ufw status
```

#### Container Issues
```bash
# Check Docker
sudo docker version
sudo docker ps

# Fix Docker permissions
sudo usermod -aG docker $USER
sudo systemctl restart docker
```

### Performance Tuning

#### Resource Optimization
```bash
# Reduce CPU usage
# Edit config.yaml:
network_discovery:
  scan_interval: 3600  # Scan every hour instead of 30 minutes
  max_threads: 20      # Reduce concurrent threads

# Reduce memory usage
log_forwarding:
  batch_size: 50       # Smaller batches
  flush_interval: 10   # More frequent flushes
```

#### Network Optimization
```bash
# For high-traffic environments
network_discovery:
  enabled: false       # Disable if not needed
  
# For low-bandwidth environments  
log_forwarding:
  compression: true    # Enable log compression
  batch_size: 200      # Larger batches, less frequent sends
```

---

**CodeGrey AI SOC Platform - Intelligent Linux Security Agent**
