# CodeGrey AI SOC Platform - Running Instructions

## QUICK START

### 1. SERVER SETUP
```bash
# Install dependencies
pip3 install -r requirements.txt

# Start server
python main.py server --host 0.0.0.0 --port 8080
```

### 2. CLIENT AGENT SETUP
```bash
# Extract package
unzip codegrey-agent-windows-v2.zip
cd codegrey-agent-windows-v2

# Install dependencies
install.bat  # Windows
# OR
./install.sh  # Linux/macOS

# Configure
python main.py --configure
# Enter server URL: http://your-server-ip:8080

# Run agent
python main.py
```

## WHAT'S FIXED

### Database Issues
- Changed from dev_soc_database.db to soc_database.db
- Server will start with clean database
- No test data will appear in network topology

### API Issues
- Removed "generatedFromDatabase" from metadata
- Attack agents API working properly
- Container logs sent as regular logs

### Test Data Cleanup
- Development database deleted
- Server will show only real client agents
- Network topology will be clean

## EXPECTED BEHAVIOR

### Clean Server Start
```
Starting AI SOC Platform Server (LangChain-based)
SQLite database initialized successfully
LangServe routes added successfully
Server running on http://0.0.0.0:8080
```

### Clean Network Topology (No Test Data)
```json
{
  "status": "success",
  "data": [],
  "metadata": {
    "totalEndpoints": 0,
    "activeEndpoints": 0,
    "inactiveEndpoints": 0,
    "lastUpdated": "2025-09-27T10:30:00"
  }
}
```

### Real Client Agent Connection
```json
{
  "status": "success",
  "data": [
    {
      "hostname": "REAL-CLIENT-HOST",
      "ipAddress": "192.168.1.50",
      "platform": "Windows",
      "location": "Corporate Network",
      "status": "active",
      "services": ["IIS", "SQL Server"],
      "lastSeen": "2025-09-27T10:30:00",
      "agentType": "clientEndpoint",
      "importance": "high"
    }
  ]
}
```

## FILES TO UPDATE ON SERVER

### Only These 3 Files Need Updates:
1. **log_forwarding/server/langserve_api.py** - Attack agents API, database path
2. **log_forwarding/server/api/api_utils.py** - Removed generatedFromDatabase, database path
3. **requirements.txt** - Added sse_starlette

### All Other Files Stay The Same:
- main.py (unchanged)
- config files (unchanged)
- Other server files (unchanged)

## CLIENT PACKAGES READY

### Download Links for Users:
- **Windows:** codegrey-agent-windows-v2.zip
- **Linux:** codegrey-agent-linux-v2.zip  
- **macOS:** codegrey-agent-macos-v2.zip

### Each Package Contains:
- Complete client agent with container orchestration
- Network discovery capabilities
- System profiling for exact container replication
- Installation and configuration scripts
- Full documentation

## VERIFICATION

### Test Commands:
```bash
# Check server health
curl http://localhost:8080/health

# Check clean network topology
curl http://localhost:8080/api/backend/network-topology

# Check attack agents
curl http://localhost:8080/api/backend/attack-agents
```

### Expected Results:
- Server health: 200 OK
- Network topology: Empty data array (clean start)
- Attack agents: 4 PhantomStrike agents in standby mode

## SUMMARY

The platform is now configured to:
- Use production database (soc_database.db)
- Show clean network topology without test data
- Properly handle container logs as regular logs
- Provide PhantomStrike attack agents API
- Support client-side container orchestration

**Ready for production deployment with clean database!**
