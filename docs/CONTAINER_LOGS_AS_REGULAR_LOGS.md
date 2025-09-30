# CodeGrey AI SOC Platform - Container Logs as Regular Logs

## CONTAINER LOGS SENT AS REGULAR LOGS + ATTACK AGENTS API

###  Changes Made

#### 1. Container Logs Integration
**Container logs are now sent as regular logs through the existing log ingestion system:**

**File: `packages/{os}/codegrey-agent-{os}-v2/container_orchestrator.py`**
```python
def _send_container_log_as_regular_log(self, log_message: str):
    """Send container log as regular log entry through the log ingestion system"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': 'INFO',
        'source': 'AttackContainer',
        'message': log_message,
        'hostname': self.agent.agent_id,
        'platform': 'Container',
        'agent_type': 'attack_agent',
        'container_context': True,
        'network_info': self._get_network_context()
    }
    
    # Send to regular log ingestion endpoint
    url = f"{self.agent.server_url}/api/logs/ingest"
    logs_data = {
        'agent_id': self.agent.agent_id,
        'logs': [log_entry]
    }
```

#### 2. Attack Agents API (PhantomStrike Format)
**New API endpoint that returns running attack agents in the exact format you specified:**

**Server Endpoint: `/api/backend/attack-agents`**
```json
{
    "status": "success",
    "agents": [
        {
            "id": "phantomstrike_web_ai_attack-1234567890",
            "name": "PhantomStrike Web AI",
            "type": "attack",
            "status": "active",
            "location": "Client Network",
            "lastActivity": "Active - Uptime: 0:05:23",
            "capabilities": ["Web Vulnerability Scanning", "SQL Injection", "XSS Testing"],
            "platform": "Container Agent",
            "container_id": "attack-1234567890",
            "attack_type": "web_attack"
        },
        {
            "id": "phantomstrike_network_ai_attack-1234567891",
            "name": "PhantomStrike Network AI",
            "type": "attack",
            "status": "active",
            "location": "Client Network",
            "lastActivity": "Active - Uptime: 0:03:15",
            "capabilities": ["Network Scanning", "Port Discovery", "Service Enumeration"],
            "platform": "Container Agent",
            "container_id": "attack-1234567891",
            "attack_type": "network_attack"
        }
    ]
}
```

#### 3. Agent Types and Capabilities

**PhantomStrike Web AI:**
- Web Vulnerability Scanning
- SQL Injection Testing
- XSS Testing
- Directory Traversal

**PhantomStrike Network AI:**
- Network Scanning
- Port Discovery
- Service Enumeration
- Network Topology Mapping

**PhantomStrike Phishing AI:**
- Email Campaigns
- Credential Harvesting
- Social Engineering
- Fake Domain Setup

**PhantomStrike Lateral AI:**
- Privilege Escalation
- Lateral Movement
- Persistence Mechanisms
- Domain Enumeration

###  Log Flow Architecture

```
+-------------------------------------+
|         CLIENT AGENT                |
+-------------------------------------+
|  +-----------------------------+    |
|  |    Attack Container         |    |
|  |  +---------------------+    |    |
|  |  |  nmap -sS target    |    |    |
|  |  |  sqlmap -u url      |    |    |
|  |  |  nikto -h target    |    |    |
|  |  +---------------------+    |    |
|  |           |                 |    |
|  |           v                 |    |
|  |    Container Logs           |    |
|  +-----------------------------+    |
|                |                    |
|                v                    |
|  +-----------------------------+    |
|  |  Container Orchestrator     |    |
|  |  _send_container_log_as_    |    |
|  |  regular_log()              |    |
|  +-----------------------------+    |
|                |                    |
|                v                    |
|  +-----------------------------+    |
|  |  Regular Log Entry          |    |
|  |  {                          |    |
|  |    source: "AttackContainer"|    |
|  |    message: "nmap scan..."  |    |
|  |    container_context: true  |    |
|  |  }                          |    |
|  +-----------------------------+    |
+-------------------------------------+
                |
                v
        /api/logs/ingest
                |
                v
+-------------------------------------+
|           SOC SERVER                |
+-------------------------------------+
|  +-----------------------------+    |
|  |    Log Ingestion System     |    |
|  |  - Same as regular logs     |    |
|  |  - Attack pattern analysis |    |
|  |  - Threat detection        |    |
|  |  - Database storage        |    |
|  +-----------------------------+    |
+-------------------------------------+
```

###  API Endpoints

#### 1. Container Logs (Regular Log Ingestion)
**Endpoint:** `POST /api/logs/ingest`
```json
{
    "agent_id": "client-agent-id",
    "logs": [
        {
            "timestamp": "2025-09-27T12:34:56",
            "level": "INFO",
            "source": "AttackContainer",
            "message": "Starting nmap scan on 192.168.1.0/24",
            "hostname": "client-agent-id",
            "platform": "Container",
            "agent_type": "attack_agent",
            "container_context": true
        }
    ]
}
```

#### 2. Attack Agents API
**Endpoint:** `GET /api/backend/attack-agents`
```json
{
    "status": "success",
    "agents": [
        {
            "id": "phantomstrike_ai",
            "name": "PhantomStrike AI",
            "type": "attack",
            "status": "active|inactive",
            "location": "Client Network",
            "lastActivity": "Active - Uptime: 0:05:23",
            "capabilities": ["Attack Planning", "Scenario Generation"],
            "platform": "Container Agent"
        }
    ]
}
```

###  Client Agent Commands

#### 1. Get Attack Agents
**Command Type:** `get_attack_agents`
```json
{
    "type": "get_attack_agents",
    "data": {}
}
```

#### 2. Execute Attack Scenario
**Command Type:** `attack_scenario`
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

###  Container Log Examples

**Web Attack Container Logs:**
```
Starting sqlmap against target: http://example.com/login.php
Testing parameter 'username' for SQL injection
Found potential SQL injection in parameter 'username'
Extracting database information...
Database: mysql
Tables found: users, products, orders
```

**Network Attack Container Logs:**
```
Starting Nmap 7.80 scan against 192.168.1.0/24
Discovered open port 22/tcp on 192.168.1.10
Discovered open port 80/tcp on 192.168.1.10
Discovered open port 443/tcp on 192.168.1.10
Service detection completed. Found 15 hosts up.
```

**Phishing Attack Container Logs:**
```
Setting up phishing infrastructure
Starting Apache web server on port 8080
Configuring fake login page for target domain
SMTP server configured for credential harvesting
Phishing campaign ready for deployment
```

###  Testing

**Run the test script:**
```bash
python test_attack_agents_api.py
```

**Expected Output:**
```
 CodeGrey AI SOC Platform - Attack Agents API Test
============================================================
 Testing Attack Agents API
==================================================
 Making request to: http://localhost:8080/api/backend/attack-agents
 Response Status: 200
 Attack Agents API Response:
{
  "status": "success",
  "agents": [
    {
      "id": "phantomstrike_ai",
      "name": "PhantomStrike AI",
      "type": "attack",
      "status": "inactive",
      "location": "Client Network",
      "lastActivity": "Ready for deployment",
      "capabilities": ["Attack Planning", "Scenario Generation", "Red Team Operations"],
      "platform": "Container Agent (Standby)"
    }
  ]
}
 Found 1 attack agents
```

##  DEPLOYMENT READY

**The system now:**
-  **Sends container logs as regular logs** through `/api/logs/ingest`
-  **Provides attack agents API** at `/api/backend/attack-agents`
-  **Uses PhantomStrike AI format** exactly as you specified
-  **Shows running attack agents** from client-side containers
-  **Integrates with existing log analysis** and threat detection

**Container logs are treated as regular logs and flow through the same analysis pipeline as other agent logs!**
