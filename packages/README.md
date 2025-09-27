# CodeGrey AI SOC Platform - Client Agent Packages v2.0

## Next-Generation Endpoint Agents with Zero Hardcoded Elements

### Available Packages

| Package | Platform | Version | Features |
|---------|----------|---------|----------|
| **Windows v2.0** | Windows 10/11 | 2024.2.0 | Network Discovery, Container Orchestration, ML Detection |
| **Linux v2.0** | Ubuntu/CentOS/RHEL | 2024.2.0 | Systemd Integration, Advanced Monitoring, Red Team Capabilities |
| **macOS v2.0** | macOS 11.0+ | 2024.2.0 | Privacy-First, XProtect Integration, Apple Silicon Support |

### What's New in v2.0

#### Completely Dynamic System
- **❌ ZERO hardcoded patterns** - All detection learned from environment
- **🔄 Self-learning** - Adapts to your specific network and threats
- **📊 ML-powered analysis** - Uses machine learning for all decisions
- **🌐 Environment-aware** - Learns network topology and locations dynamically

#### Advanced Network Discovery
- **Intelligent subnet scanning** with service enumeration
- **Physical location inference** from traffic patterns
- **Network zone classification** from behavioral analysis
- **Real-time topology mapping** with relationship discovery

#### Next-Gen Threat Detection
- **Behavioral baseline learning** - Establishes normal patterns for each endpoint
- **Anomaly detection** - Identifies deviations from learned behavior
- **Context-aware scoring** - Adjusts threat scores based on environment
- **Historical pattern learning** - Builds threat models from past detections

#### Red Team Integration
- **Container orchestration** for security testing
- **Exact system replication** - Attack containers mirror target systems
- **Dynamic attack resource creation** - Generates required tools on-demand
- **Comprehensive attack logging** - Forensic analysis of all activities

### Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SOC Server                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │ PhantomStrike AI│ │ GuardianAlpha AI│ │   SOC           ││
│  │ (Attack Agent)  │ │ (Detection)     │ │ Orchestrator    ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
            ┌───────▼────┐ ┌───▼────┐ ┌───▼─────┐
            │ Windows    │ │ Linux  │ │ macOS   │
            │ Agent v2.0 │ │Agent v2│ │Agent v2 │
            └────────────┘ └────────┘ └─────────┘
```

### Installation Guide

#### Windows
```powershell
# Download and extract
Expand-Archive codegrey-agent-windows-v2.zip
cd codegrey-agent-windows-v2

# Run installer
.\install.bat

# Configure and start
python main.py --configure
python main.py
```

#### Linux
```bash
# Extract and install
tar -xzf codegrey-agent-linux-v2.tar.gz
cd codegrey-agent-linux-v2
sudo ./install.sh

# Configure and start
sudo python3 main.py --configure
sudo systemctl start codegrey-agent
```

#### macOS
```bash
# Extract and install
tar -xzf codegrey-agent-macos-v2.tar.gz
cd codegrey-agent-macos-v2
sudo ./install.sh

# Grant permissions in System Preferences
# Configure and start
python3 main.py --configure
sudo launchctl load /Library/LaunchAgents/com.codegrey.agent.plist
```

### Feature Comparison

| Feature | Windows v2.0 | Linux v2.0 | macOS v2.0 |
|---------|-------------|------------|------------|
| **Network Discovery** | ✅ Full | ✅ Full | ✅ Privacy-Safe |
| **ML Threat Detection** | ✅ | ✅ | ✅ Core ML |
| **Container Orchestration** | ✅ Docker | ✅ Docker | ✅ Docker Desktop |
| **Behavioral Analysis** | ✅ | ✅ | ✅ Privacy-First |
| **Real-time Logging** | ✅ Event Logs | ✅ Syslog | ✅ Unified Logging |
| **Service Integration** | ✅ Windows Service | ✅ Systemd | ✅ LaunchAgent |
| **Red Team Capabilities** | ✅ Full | ✅ Full | ✅ Consent-Based |

### Security and Privacy

#### Data Protection
- **End-to-end encryption** for all SOC communication
- **Local data encryption** using platform-native methods
- **Minimal data collection** - only essential security information
- **User consent** required for advanced monitoring features

#### Privacy Compliance
- **GDPR compliant** - Right to deletion and data portability
- **SOC 2 Type II** - Enterprise security controls
- **Platform-specific privacy** - Respects OS privacy models
- **Transparency** - Users can see exactly what data is collected

### Deployment Scenarios

#### Enterprise Deployment
- **Centralized configuration** via SOC server
- **Group policy integration** (Windows)
- **Automated deployment** via configuration management
- **Fleet monitoring** and management

#### Development/Testing
- **Local SOC server** for testing
- **Container-based testing** environments
- **Red Team exercises** in isolated networks
- **Security research** and threat hunting

#### Managed Security Services
- **Multi-tenant support** for MSPs
- **Client isolation** and data segregation
- **Custom branding** and configuration
- **SLA monitoring** and reporting

### Advanced Configuration

#### Network Discovery Tuning
```yaml
network_discovery:
  scan_techniques:
    - ping_sweep: true
    - tcp_syn_scan: true
    - udp_scan: false
    - service_detection: true
  performance_mode: "balanced"  # low, balanced, aggressive
  stealth_mode: true
```

#### ML Model Configuration
```yaml
machine_learning:
  model_training:
    enabled: true
    training_interval: 86400  # 24 hours
    min_training_samples: 1000
  threat_detection:
    sensitivity: "adaptive"  # low, medium, high, adaptive
    false_positive_tolerance: 0.05
```

### Support and Documentation

#### Getting Help
- **Comprehensive README** in each package
- **Debug logging** with `--debug` flag
- **System diagnostics** with `--check-system`
- **SOC server dashboard** for centralized monitoring

#### Troubleshooting
- **Permission issues** - Check platform-specific guides
- **Network connectivity** - Test with built-in diagnostics
- **Performance issues** - Adjust configuration parameters
- **Container problems** - Verify Docker installation

---

## 🎉 Ready for Deployment

**All packages are:**
- ✅ **Completely dynamic** - Zero hardcoded elements
- ✅ **ML-powered** - Learns from your specific environment  
- ✅ **Privacy-compliant** - Respects user privacy and platform security models
- ✅ **Enterprise-ready** - Production-grade security and monitoring
- ✅ **Self-adapting** - Continuously improves threat detection accuracy

**Deploy with confidence - Your AI SOC Platform is ready for real-world security operations!**
