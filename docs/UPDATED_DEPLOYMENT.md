# CodeGrey AI SOC Platform - Updated Deployment

##  UPDATED FOR PORT 8080

###  Configuration Updated
- **Server**: Port 8080 (leaves Nginx untouched)
- **Client**: Updated to connect to `:8080`
- **Tests**: Updated to use port 8080
- **Auth**: Still disabled for development

###  Simple Deployment

**Run this command:**
```bash
chmod +x start_simple.sh
./start_simple.sh
```

###  Your API URLs (with port 8080)

**Base URL**: `http://dev.codegrey.ai:8080/api/backend`

**API Endpoints** (NO API KEY REQUIRED):
- `http://dev.codegrey.ai:8080/health`
- `http://dev.codegrey.ai:8080/api/backend/agents`
- `http://dev.codegrey.ai:8080/api/backend/network-topology`
- `http://dev.codegrey.ai:8080/api/backend/software-download`
- `http://dev.codegrey.ai:8080/api/backend/langgraph/attack/start`
- `http://dev.codegrey.ai:8080/api/backend/langgraph/detection/status`

###  Frontend Integration

```javascript
// Simple fetch - no authentication needed
fetch('http://dev.codegrey.ai:8080/api/backend/agents')
  .then(response => response.json())
  .then(data => console.log('Agents:', data));

// POST request
fetch('http://dev.codegrey.ai:8080/api/backend/langgraph/attack/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_request: "Plan APT simulation",
    attack_type: "apt",
    complexity: "simple"
  })
});
```

### 🔍 AWS Security Group

**Add inbound rule:**
- **Port**: 8080
- **Source**: 0.0.0.0/0
- **Protocol**: TCP

###  Benefits of This Approach

-  **No Nginx changes** - leaves existing setup intact
-  **Simple deployment** - just run one script
-  **Clear separation** - your app on 8080, other services on 80
-  **Easy debugging** - direct access to your application
-  **Production ready** - can add Nginx proxy later if needed

**Just run `./start_simple.sh` and you're good to go!**
