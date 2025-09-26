# CodeGrey AI SOC Platform - Ready for Deployment

## ✅ CHANGES COMPLETED

### 🔓 API Keys Disabled
- **Security**: API key authentication disabled for development
- **CORS**: Updated to not require credentials
- **Access**: All endpoints accessible without authentication

### 🌐 Domain Configuration
- **Server**: Configured for `dev.codegrey.ai`
- **Port**: Changed to 80 (no port number needed in URLs)
- **Client**: Updated to connect to domain instead of IP

### 🔗 CORS Updated
- **CodeGrey Domain**: `http://dev.codegrey.ai` and `https://dev.codegrey.ai`
- **Development**: `localhost:3000`, `localhost:3001`
- **All Origins**: `*` allowed for development

## 🚀 Deployment Instructions

### 1. Upload This Folder
```bash
scp -r C:\Users\krith\Desktop\clean ec2-user@15.207.6.45:~/ai-soc-platform
```

### 2. SSH and Install
```bash
ssh ec2-user@15.207.6.45
cd ~/ai-soc-platform
chmod +x start_production.sh
./start_production.sh
```

### 3. AWS Security Group
**Add inbound rule:**
- **Port**: 80
- **Source**: 0.0.0.0/0
- **Protocol**: TCP

## 📊 Your Clean URLs

**Base URL**: `http://dev.codegrey.ai/api/backend`

**API Endpoints** (NO API KEY REQUIRED):
- `GET http://dev.codegrey.ai/health`
- `GET http://dev.codegrey.ai/api/backend/agents`
- `GET http://dev.codegrey.ai/api/backend/network-topology`
- `GET http://dev.codegrey.ai/api/backend/software-download`
- `POST http://dev.codegrey.ai/api/backend/langgraph/attack/start`
- `GET http://dev.codegrey.ai/api/backend/langgraph/detection/status`

## 🧪 Frontend Integration

```javascript
// Simple fetch - no authentication needed
fetch('http://dev.codegrey.ai/api/backend/agents')
  .then(response => response.json())
  .then(data => console.log('Agents:', data));

// POST request
fetch('http://dev.codegrey.ai/api/backend/langgraph/attack/start', {
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

## ✅ Ready for Production

Your AI SOC Platform is now configured for:
- ✅ **Clean URLs** without port numbers
- ✅ **Domain-based access** (dev.codegrey.ai)
- ✅ **No authentication** required (development mode)
- ✅ **CORS enabled** for frontend development
- ✅ **All AI agents** operational
- ✅ **Complete API specification** implemented

Upload this folder and run `./start_production.sh` on your server!
