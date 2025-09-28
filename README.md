# CodeGrey AI SOC Platform - Installation Instructions

## Server Setup

### Start Server
```bash
python main.py server --host 0.0.0.0 --port 8080
```

### Server Configuration
- IP Address: 15.207.6.45
- Port: 8080
- Domain: backend.codegrey.ai

## Client Agent Installation

### Windows Systems

#### Option 1: Standalone Executable
1. Download `CodeGrey-Agent-Windows-Fixed.exe`
2. Configure:
   ```cmd
   CodeGrey-Agent-Windows-Fixed.exe --configure
   ```
3. Enter server URL: `http://15.207.6.45:8080`
4. Run:
   ```cmd
   CodeGrey-Agent-Windows-Fixed.exe
   ```

#### Option 2: Dynamic Package
1. Download `codegrey-agent-windows-dynamic-updated.zip`
2. Extract the zip file
3. Run:
   ```cmd
   python main.py
   ```

### Linux Systems

1. Download `codegrey-agent-linux-dynamic.zip`
2. Extract:
   ```bash
   unzip codegrey-agent-linux-dynamic.zip
   cd codegrey-agent-linux-dynamic
   ```
3. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
4. Run:
   ```bash
   python3 main.py
   ```

### macOS Systems

1. Download `codegrey-agent-macos-dynamic.zip`
2. Extract:
   ```bash
   unzip codegrey-agent-macos-dynamic.zip
   cd codegrey-agent-macos-dynamic
   ```
3. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
4. Run:
   ```bash
   python3 main.py
   ```

## Files to Distribute

### Windows
- `CodeGrey-Agent-Windows-Fixed.exe` (standalone executable)
- OR `codegrey-agent-windows-dynamic-updated.zip` (Python package)

### Linux
- `codegrey-agent-linux-dynamic.zip`

### macOS
- `codegrey-agent-macos-dynamic.zip`

## File Locations

### Windows Executable
```
C:\Users\krith\Desktop\clean\build_artifacts\packages\windows\codegrey-agent-windows-v2\dist\CodeGrey-Agent-Windows-Fixed.exe
```

### Windows Dynamic Package
```
C:\Users\krith\Desktop\clean\build_artifacts\updated_packages\codegrey-agent-windows-dynamic-updated.zip
```

### Linux Package
```
C:\Users\krith\Desktop\clean\build_artifacts\updated_packages\codegrey-agent-linux-dynamic.zip
```

### macOS Package
```
C:\Users\krith\Desktop\clean\build_artifacts\updated_packages\codegrey-agent-macos-dynamic.zip
```

## Network Configuration

- Server IP: 15.207.6.45:8080
- Domain: backend.codegrey.ai:8080
- Protocol: HTTP
- Required ports: Outbound 8080

## System Requirements

### Server
- Python 3.8+
- 8GB RAM
- 50GB storage
- Static IP address

### Windows Client
- Windows 10/11 (64-bit)
- 512MB RAM
- Administrator privileges recommended

### Linux Client
- Ubuntu 18.04+, CentOS 7+, RHEL 7+
- Python 3.8+
- 256MB RAM
- Root privileges recommended

### macOS Client
- macOS 10.15+
- Python 3.8+
- 256MB RAM
- Administrator privileges recommended

## Troubleshooting

### Server Issues
```bash
# Check if port is in use
netstat -an | findstr :8080

# Try different port
python main.py server --port 8081
```

### Client Connection Issues
```bash
# Test server connectivity
curl http://15.207.6.45:8080/health
```

### Windows Permission Issues
```cmd
# Run as Administrator
# Or add user to Event Log Readers group
```

### Linux Permission Issues
```bash
# Add user to required groups
sudo usermod -a -G adm,syslog $USER

# Or run with sudo
sudo python3 main.py
```