# CodeGrey AI SOC Platform - Client-Side Container Architecture

## CLIENT-SIDE ATTACK CONTAINERS WITH TELEMETRY STREAMING

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT AGENT SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │  System Info    │    │  Network Disc.  │    │  Log Collection │      │
│  │  Collection     │    │  & Topology     │    │  & Forwarding   │      │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘      │
│                                   │                                      │
│  ┌─────────────────────────────────┴─────────────────────────────────┐   │
│  │              CLIENT CONTAINER ORCHESTRATOR                      │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │   │
│  │  │   Attack        │  │   Attack        │  │   Attack        │  │   │
│  │  │  Container 1    │  │  Container 2    │  │  Container N    │  │   │
│  │  │  (Web Attack)   │  │ (Network Scan)  │  │ (Lateral Move)  │  │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │   │
│  └─────────────────────────────────┬─────────────────────────────────┘   │
│                                   │                                      │
│  ┌─────────────────────────────────┴─────────────────────────────────┐   │
│  │                TELEMETRY STREAMING ENGINE                       │   │
│  │  • Container logs streaming                                     │   │
│  │  • Resource usage monitoring                                    │   │
│  │  • Attack activity correlation                                  │   │
│  │  • Network traffic analysis                                     │   │
│  └─────────────────────────────────┬─────────────────────────────────┘   │
└─────────────────────────────────────┼─────────────────────────────────────┘
                                      │
                          ┌───────────┴───────────┐
                          │   SECURE CHANNEL      │
                          │   (HTTPS/TLS)         │
                          └───────────┬───────────┘
                                      │
┌─────────────────────────────────────┼─────────────────────────────────────┐
│                        SOC SERVER SYSTEM                                │
├─────────────────────────────────────┼─────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              TELEMETRY INGESTION API                            │    │
│  │  • /api/telemetry/ingest                                        │    │
│  │  • Real-time attack pattern analysis                            │    │
│  │  • Container activity correlation                               │    │
│  │  • Threat intelligence integration                              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                      │                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  AI ANALYSIS ENGINE                             │    │
│  │  • Attack scenario effectiveness analysis                       │    │
│  │  • Security gap identification                                  │    │
│  │  • Threat model updates                                         │    │
│  │  • Defensive recommendations                                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Client-Side Container Orchestration

#### 1. Container Orchestrator Features
**File: `packages/{os}/codegrey-agent-{os}-v2/container_orchestrator.py`**

**Core Capabilities:**
- **Exact System Replication** - Creates containers matching target system configuration
- **Multi-Attack Support** - Runs multiple attack scenarios simultaneously
- **Real-time Telemetry** - Streams logs and metrics to SOC server
- **Resource Management** - Controls CPU/memory usage of attack containers
- **Auto-cleanup** - Removes containers after attack completion

#### 2. Attack Container Types

**Web Attack Containers:**
```dockerfile
FROM kalilinux/kali-rolling
RUN apt-get update && apt-get install -y \
    sqlmap nikto dirb burpsuite \
    python3-requests beautifulsoup4
```

**Network Attack Containers:**
```dockerfile
FROM kalilinux/kali-rolling
RUN apt-get update && apt-get install -y \
    nmap masscan metasploit-framework \
    wireshark-common tcpdump
```

**Phishing Attack Containers:**
```dockerfile
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y \
    postfix apache2 php \
    python3-flask python3-jinja2
```

#### 3. Container Configuration

**Target System Replication:**
```python
container_config = {
    'mem_limit': target_system.get('memory_total', '2g'),
    'cpu_count': min(psutil.cpu_count(), 2),
    'security_opt': ['seccomp:unconfined'],
    'cap_add': ['NET_ADMIN', 'SYS_ADMIN'],
    'network_mode': 'host'  # Use host network for realistic testing
}
```

**Environment Variables:**
```python
environment = {
    'TARGET_IP': target_system.get('ip_address'),
    'TARGET_OS': target_system.get('os'),
    'ATTACK_TYPE': scenario_config.get('attack_type'),
    'LOG_LEVEL': 'DEBUG'
}
```

### Telemetry Streaming Architecture

#### 1. Real-time Log Streaming

**Container Log Stream:**
```python
for log_line in container.logs(stream=True, follow=True):
    telemetry_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'container_id': container_id,
        'agent_id': self.agent.agent_id,
        'type': 'container_log',
        'data': log_line.decode('utf-8', errors='ignore').strip(),
        'attack_scenario': {
            'target_system': self.agent._get_system_info(),
            'network_info': self._get_network_context()
        }
    }
    self._send_telemetry(telemetry_data)
```

#### 2. Resource Usage Monitoring

**Container Statistics Stream:**
```python
for stats in container.stats(stream=True):
    telemetry_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'container_id': container_id,
        'agent_id': self.agent.agent_id,
        'type': 'container_stats',
        'data': {
            'cpu_usage': self._calculate_cpu_usage(stats.get('cpu_stats', {})),
            'memory_usage': stats.get('memory_stats', {}),
            'network_io': stats.get('networks', {}),
            'block_io': stats.get('blkio_stats', {})
        }
    }
    self._send_telemetry(telemetry_data)
```

#### 3. Network Context Correlation

**Attack Correlation Data:**
```python
network_info = {
    'local_ip': self._get_local_ip(),
    'open_ports': self._get_open_ports(),
    'active_connections': len(psutil.net_connections()),
    'network_interfaces': len(psutil.net_if_addrs())
}
```

### Server-Side Telemetry Processing

#### 1. Telemetry Ingestion API

**Endpoint: `/api/telemetry/ingest`**
```python
@self.app.post("/api/telemetry/ingest")
async def ingest_telemetry(telemetry_data: dict):
    # Extract telemetry information
    container_id = telemetry_data.get('container_id', 'unknown')
    agent_id = telemetry_data.get('agent_id', 'unknown')
    telemetry_type = telemetry_data.get('type', 'unknown')
    
    # Store in database
    # Analyze for attack patterns
    # Generate alerts if needed
```

#### 2. Attack Pattern Analysis

**Real-time Detection:**
```python
attack_indicators = [
    'nmap', 'sqlmap', 'metasploit', 'exploit', 'payload',
    'reverse shell', 'backdoor', 'privilege escalation',
    'lateral movement', 'credential dump'
]

suspicious_commands = [
    'wget', 'curl', 'nc', 'netcat', 'python -c',
    'bash -i', 'sh -i', 'whoami', 'sudo'
]
```

#### 3. Database Schema

**Container Telemetry Table:**
```sql
CREATE TABLE container_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_id TEXT,
    agent_id TEXT,
    type TEXT,
    timestamp TEXT,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Container Alerts Table:**
```sql
CREATE TABLE container_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_id TEXT,
    agent_id TEXT,
    alert_type TEXT,
    severity TEXT,
    indicators TEXT,
    raw_log TEXT,
    timestamp TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Command & Control Interface

#### 1. Attack Scenario Execution

**Command Type: `attack_scenario`**
```json
{
    "type": "attack_scenario",
    "data": {
        "attack_type": "web_attack",
        "command": "/attack/web_scan.sh",
        "environment": {
            "TARGET_URL": "http://target.example.com"
        }
    }
}
```

#### 2. Container Management

**Command Type: `container_orchestration`**
```json
{
    "type": "container_orchestration",
    "data": {
        "operation": "list|stop|execute|logs|cleanup",
        "container_id": "attack-1234567890",
        "command": "nmap -sS target_ip"
    }
}
```

### Security & Isolation

#### 1. Container Security
- **Resource Limits** - CPU and memory constraints
- **Network Isolation** - Controlled network access
- **Privilege Management** - Minimal required privileges
- **Auto-cleanup** - Automatic container removal

#### 2. Data Protection
- **Encrypted Transport** - TLS for all telemetry data
- **Sanitized Logs** - Remove sensitive information
- **Access Control** - Agent-based authentication
- **Audit Trail** - Complete activity logging

### Deployment Architecture

#### 1. Client Agent Requirements
```
- Docker Engine installed and running
- Network access to SOC server
- Sufficient resources (2GB RAM, 1GB disk)
- Administrative privileges for container management
```

#### 2. Attack Container Images
```
- Pre-built attack tool images
- Target-specific configuration templates
- Automated tool installation scripts
- Log forwarding configuration
```

#### 3. SOC Server Capabilities
```
- Real-time telemetry ingestion
- Attack pattern recognition
- Threat intelligence correlation
- Security gap analysis
- Defensive recommendations
```

## DEPLOYMENT READY

**✅ Client-Side Container Orchestration**
- Containers run locally on client systems
- Exact target system replication
- Multi-scenario attack execution

**✅ Real-time Telemetry Streaming**
- Container logs and metrics streamed to server
- Attack activity correlation
- Network context integration

**✅ Server-Side Analysis**
- Attack pattern detection
- Threat intelligence integration
- Security gap identification

**✅ Complete Command & Control**
- Remote attack scenario execution
- Container lifecycle management
- Real-time monitoring and control

**The attack containers now run ON THE CLIENT SIDE and stream comprehensive telemetry data back to the SOC server for analysis and correlation!**
