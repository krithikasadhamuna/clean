# CodeGrey AI SOC Platform - Development Environment Guide

## 🏗️ Local Development Setup

###  Why Local Development?

- **Fast iteration** - Test changes instantly
- **No deployment delays** - Develop and test locally
- **Safe experimentation** - Won't affect production
- **Different IPs handled** - Separate dev and production configs

##  Quick Start

### Windows Development:
```bash
# Start development server
start_dev.bat

# In another terminal, start development client
python start_dev_client.py
```

### Linux/macOS Development:
```bash
# Start development server
chmod +x start_dev.sh
./start_dev.sh

# In another terminal, start development client  
python3 start_dev_client.py
```

##  Network Topology - Tabular Format (Dynamic)

### API Response Structure:
```json
{
  "status": "success",
  "network_topology": {
    "table_format": true,
    "columns": [
      "hostname",
      "ip_address", 
      "platform",
      "location", 
      "status",
      "services",
      "last_seen",
      "agent_type",
      "importance"
    ],
    "rows": [
      {
        "hostname": "DEV-MACHINE-001",
        "ip_address": "127.0.0.1",
        "platform": "Windows 11",
        "location": "Development Network",
        "status": "active",
        "services": ["HTTP", "SSH"],
        "last_seen": "2024-09-26T15:30:00Z",
        "agent_type": "endpoint",
        "importance": "medium"
      }
    ]
  },
  "metadata": {
    "total_endpoints": 1,
    "active_endpoints": 1,
    "network_zones": ["Development Network"],
    "generated_from_logs": true
  }
}
```

### 🔍 Data Sources (Completely Dynamic):

1. **Logs from client agents** -> Database
2. **NetworkTopologyMapper** builds topology from logs
3. **API converts** topology to tabular format
4. **No hardcoded data** - all from actual network discovery

##  Development vs Production

### Development Environment:
- **Server**: `http://localhost:8080`
- **Database**: `dev_soc_database.db`
- **Config**: `config/dev_config.yaml`
- **Client Config**: `config/client_dev_config.yaml`
- **Logging**: Debug level
- **CORS**: Fully open

### Production Environment:
- **Server**: `http://15.207.6.45:8080`
- **Database**: `soc_database.db`
- **Config**: `config/server_config.yaml`
- **Client Config**: `config/client_config.yaml`
- **Logging**: Info level
- **CORS**: Restricted

##  Testing Workflow

### 1. Local Development:
```bash
# Terminal 1: Start dev server
./start_dev.sh

# Terminal 2: Start dev client
python3 start_dev_client.py

# Terminal 3: Test APIs
curl http://localhost:8080/api/backend/agents
curl http://localhost:8080/api/backend/network-topology
```

### 2. Test Changes:
- Modify code
- Restart dev server
- Test endpoints
- Verify functionality

### 3. Deploy to Production:
```bash
# Upload to production server
scp -r . krithika@15.207.6.45:~/ai-soc-platform/

# SSH and restart production
ssh krithika@15.207.6.45
cd ~/ai-soc-platform
python3 main.py server --host 0.0.0.0 --port 8080
```

##  Frontend Development

### Local Frontend Setup:
```bash
cd codegrey-main

# Development environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.development

# Start frontend
npm run dev:development
```

### API Endpoints for Frontend:
- **Local Dev**: `http://localhost:8080/api/backend/*`
- **Production**: `http://15.207.6.45:8080/api/backend/*`

##  Benefits

###  Advantages:
- **Fast development cycle**
- **No production impact**
- **Easy debugging**
- **Separate databases**
- **Different IP handling**

###  Development Flow:
1. **Develop locally** on `localhost:8080`
2. **Test thoroughly** with local client agents
3. **Deploy to production** on `15.207.6.45:8080`
4. **Frontend can target either** environment

##  Start Developing

```bash
# Start local development
./start_dev.sh

# Your local URLs:
# - API: http://localhost:8080/api/backend/agents
# - Docs: http://localhost:8080/docs
# - Health: http://localhost:8080/health
```

**Now you can develop locally and deploy when ready!**

