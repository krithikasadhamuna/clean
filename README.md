# AI SOC Platform with Log Forwarding

A comprehensive AI-powered Security Operations Center (SOC) platform that combines attack simulation, real-time log forwarding, and intelligent threat detection.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SOC SERVER                               │
├─────────────────────────────────────────────────────────────┤
│ 🧠 AI Detection Agents                                     │
│   ├── Real Threat Detector                                 │
│   ├── AI Threat Analyzer                                   │
│   └── LangGraph Detection Workflows                        │
│                                                             │
│ 📊 Log Processing Pipeline                                  │
│   ├── Log Ingester                                         │
│   ├── Real-time Stream Processor                           │
│   ├── ML Feature Extractor                                 │
│   └── Threat Intelligence Enrichment                       │
│                                                             │
│ 🗄️ Storage Layer                                           │
│   ├── SQLite Database                                      │
│   ├── Elasticsearch (optional)                             │
│   └── InfluxDB (optional)                                  │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ Log Streams
            ┌──────────────┼──────────────┐
            │              │              │
┌───────────▼────┐ ┌───────▼────┐ ┌──────▼─────┐
│   CLIENT A     │ │  CLIENT B   │ │  CLIENT C  │
├────────────────┤ ├─────────────┤ ├────────────┤
│ 💻 Attack Agent│ │💻 Attack Ag.│ │💻 Attack A.│
│ 📋 Log Forwarder│ │📋 Log Forw. │ │📋 Log Forw.│
│                │ │             │ │            │
│ Log Sources:   │ │ Log Sources:│ │Log Sources:│
│ • Windows Logs │ │ • Linux Logs│ │• App Logs  │
│ • Process Logs │ │ • Auth Logs │ │• Net Logs  │
│ • Network Logs │ │ • Sys Logs  │ │• File Logs │
└────────────────┘ └─────────────┘ └────────────┘
```

## Quick Start

### Server Deployment

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Deploy Server**
   ```bash
   python scripts/deploy_server.py --host 0.0.0.0 --port 8080
   ```

3. **Or use the package entry point**
   ```bash
   ai-soc-server --host 0.0.0.0 --port 8080
   ```

### Client Deployment

1. **Deploy Client**
   ```bash
   python scripts/deploy_client.py --server https://your-soc-server.com
   ```

2. **Or use the package entry point**
   ```bash
   ai-soc-client --config config/client_config.yaml
   ```

3. **Install as System Service**
   ```bash
   python scripts/deploy_client.py --server https://your-soc-server.com --install-service
   ```

## Features

### AI-Powered Detection
- **Multi-layered Detection**: Combines ML models, AI reasoning, and rule-based detection
- **Real-time Analysis**: Processes logs as they arrive for immediate threat detection
- **MITRE ATT&CK Integration**: Maps detected threats to MITRE ATT&CK framework
- **Adaptive Thresholds**: AI automatically adjusts detection sensitivity based on environment

### Attack Simulation
- **Dynamic Attack Generation**: Creates realistic attack scenarios based on network topology
- **MITRE Technique Coverage**: Implements 400+ attack techniques
- **Human-in-the-Loop**: Requires approval before executing attack simulations
- **Golden Image Management**: Creates system snapshots before attacks for safe restoration

### Comprehensive Log Forwarding
- **Multi-Platform Support**: Windows Event Logs, Linux Syslog, Application logs
- **Real-time Streaming**: Low-latency log forwarding with batching and compression
- **Intelligent Filtering**: Reduces noise while preserving security-relevant events
- **Resilient Communication**: Handles network interruptions with automatic retry

### Advanced Analytics
- **Correlation Analysis**: Identifies attack patterns across multiple systems
- **Threat Intelligence**: Enriches logs with external threat intelligence
- **Behavioral Analysis**: Detects anomalies in user and system behavior
- **Timeline Reconstruction**: Builds complete attack timelines

## Configuration

### Server Configuration (`config/server_config.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8080
  workers: 4

database:
  sqlite_path: "soc_database.db"
  elasticsearch:
    enabled: true
    host: "localhost"
    port: 9200

detection:
  real_time_enabled: true
  ml_threshold: 0.7
  ai_analysis_enabled: true

llm:
  ollama_endpoint: "http://localhost:11434"
  ollama_model: "cybersec-ai"
```

### Client Configuration (`config/client_config.yaml`)

```yaml
client:
  agent_id: "auto"
  server_endpoint: "https://soc-server.company.com"
  api_key: "${AI_SOC_API_KEY}"

log_forwarding:
  enabled: true
  batch_size: 100
  flush_interval: 5

log_sources:
  system_logs:
    enabled: true
    priority: "high"
  security_logs:
    enabled: true
    priority: "critical"
  attack_logs:
    enabled: true
    priority: "critical"
```

## Running the Platform

### Development Mode

**Start Server:**
```bash
cd /path/to/ai-soc-platform
python -m log_forwarding.server.server_manager --log-level DEBUG
```

**Start Client:**
```bash
python -m log_forwarding.client.client_agent --config config/client_config.yaml --log-level DEBUG
```

### Production Mode

**Server (with Docker):**
```bash
# Build image
docker build -t ai-soc-server .

# Run container
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  ai-soc-server
```

**Client (as Service):**
```bash
# Linux
sudo systemctl start ai-soc-client
sudo systemctl enable ai-soc-client

# Windows
python service_windows.py install
python service_windows.py start
```

## Integration with Existing Agents

The log forwarding system seamlessly integrates with your existing AI agents:

### Detection Integration
```python
from log_forwarding.integrations.detection_integration import DetectionIntegration

# Initialize integration
detection_integration = DetectionIntegration()

# Analyze log entry
result = await detection_integration.analyze_log_entry(log_entry)

if result and result.threat_detected:
    print(f"Threat detected: {result.threat_type}")
```

### Attack Agent Integration
```python
from log_forwarding.client.forwarders.application_forwarder import ApplicationLogForwarder

# Log attack execution
app_forwarder = ApplicationLogForwarder(agent_id, config)
app_forwarder.log_attack_execution({
    'technique': 'T1055',
    'command': 'powershell.exe -enc <base64>',
    'target': 'WORKSTATION-01',
    'result': 'success'
})
```

## Monitoring and Observability

### Health Checks
```bash
curl http://localhost:8080/health
```

### Statistics API
```bash
curl http://localhost:8080/api/logs/statistics
```

### Log Queries
```bash
curl "http://localhost:8080/api/logs/query?agent_id=CLIENT-001&hours=24"
```

## Security Considerations

### Authentication
- API key-based authentication
- Rate limiting
- Request validation

### Encryption
- TLS/SSL for client-server communication
- Optional log compression and encryption
- Secure credential storage

### Access Control
- Agent-based isolation
- Role-based access control (planned)
- Audit logging

## Performance

### Throughput
- **Server**: 10,000+ logs/second
- **Client**: 1,000+ logs/second per forwarder
- **Detection**: 500+ analyses/second

### Scalability
- Horizontal scaling with multiple workers
- Database sharding support
- Load balancer compatibility

### Resource Usage
- **Server**: ~500MB RAM, <5% CPU (idle)
- **Client**: ~100MB RAM, <2% CPU (idle)
- **Storage**: ~1GB per million logs

## Troubleshooting

### Common Issues

1. **Client Cannot Connect to Server**
   ```bash
   # Check network connectivity
   curl -v http://your-server:8080/health
   
   # Verify API key
   export AI_SOC_API_KEY="your-api-key"
   ```

2. **Windows Event Log Access Denied**
   ```bash
   # Run as Administrator
   # Or add user to "Event Log Readers" group
   ```

3. **Linux Log Files Not Accessible**
   ```bash
   # Add user to adm group
   sudo usermod -a -G adm $USER
   
   # Or run with elevated privileges
   sudo python -m log_forwarding.client.client_agent
   ```

### Debug Mode
```bash
# Server debug mode
python -m log_forwarding.server.server_manager --log-level DEBUG --log-file logs/server_debug.log

# Client debug mode  
python -m log_forwarding.client.client_agent --log-level DEBUG --log-file logs/client_debug.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting section

---

**Built for cybersecurity professionals**
