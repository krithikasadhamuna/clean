# Deploy AI SOC Platform to Amazon Linux 2023

## Quick Deployment Steps

### 1. Copy Files to Server
```bash
# From Windows machine
scp -r C:\Users\krith\Desktop\clean ec2-user@15.207.6.45:~/ai-soc-platform
```

### 2. SSH and Install
```bash
ssh ec2-user@15.207.6.45
cd ~/ai-soc-platform
chmod +x install_linux.sh
./install_linux.sh
```

### 3. Start Platform
```bash
chmod +x start_platform.sh
./start_platform.sh
```

### 4. Test Deployment
```bash
# From server
curl "http://localhost:8080/health"
curl -H "X-API-Key: api_codegrey_2024" "http://localhost:8080/api/backend/agents"

# From external (your Windows machine)
curl "http://15.207.6.45:8080/health"
curl -H "X-API-Key: api_codegrey_2024" "http://15.207.6.45:8080/api/backend/agents"
```

## AWS Security Group Settings

Add these inbound rules:
- **Port 8080**: Source 0.0.0.0/0 (HTTP)
- **Port 22**: Source YOUR_IP/32 (SSH)

## Platform URLs (External Access)

- **Base URL**: `http://15.207.6.45:8080/api/backend`
- **Health Check**: `http://15.207.6.45:8080/health`
- **Agents API**: `http://15.207.6.45:8080/api/backend/agents`
- **Network Topology**: `http://15.207.6.45:8080/api/backend/network-topology`
- **Software Download**: `http://15.207.6.45:8080/api/backend/software-download`
- **Attack Operations**: `http://15.207.6.45:8080/api/backend/langgraph/attack/start`
- **Detection Status**: `http://15.207.6.45:8080/api/backend/langgraph/detection/status`

## API Authentication

**Header**: `X-API-Key: api_codegrey_2024`

## Expected Features on Linux

 **Better Performance**: Native Linux performance
 **eBPF Monitoring**: Advanced kernel-level monitoring  
 **Docker Support**: Better container support than Windows
 **Log Access**: Full system log access without admin privileges
 **Stability**: More stable for long-running SOC operations

## Troubleshooting

### If pip install fails:
```bash
# Install packages individually
pip3 install --user fastapi uvicorn
pip3 install --user langchain langchain-openai openai
pip3 install --user scikit-learn numpy pandas
```

### If port 8080 is blocked:
```bash
# Check firewall
sudo firewall-cmd --list-all
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### If Docker issues:
```bash
# Start Docker
sudo systemctl start docker
sudo usermod -a -G docker $USER
# Logout and login again
```

## Production Deployment

For production, consider:
- Using a reverse proxy (nginx)
- SSL/TLS certificates
- Process manager (systemd service)
- Log rotation
- Monitoring and alerting

Your AI SOC Platform will work excellently on Amazon Linux 2023!
