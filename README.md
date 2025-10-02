# CodeGrey AI SOC Client Agent - macOS

**Version:** 2.0 Clean Edition  
**Platform:** macOS 10.15+ (Catalina and later)  
**Status:** Production Ready

---

## Quick Start

### Option 1: Run from Source
1. Install Python 3.8+ if not already installed
2. Open Terminal
3. Navigate to this folder
4. Run: `sudo python3 main.py`

### Option 2: Build Executable
1. Install build dependencies: `pip3 install -r requirements.txt`
2. Build executable: `python3 build_macos_executable.py`
3. Run: `sudo ./CodeGrey-Agent-macOS-Clean`

---

## Installation

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3

# Install dependencies
pip3 install -r requirements.txt

# Run agent
sudo python3 main.py
```

---

## Configuration

Edit `config.yaml` before running:

```yaml
client:
  server_endpoint: "http://your-server:8080"  # Change to your server
  agent_id: "auto-generated"
  heartbeat_interval: 30
```

**Important:** Replace `http://your-server:8080` with your actual server address.

---

## System Requirements

- **OS:** macOS 10.15 (Catalina) or later
- **Python:** 3.8 or higher
- **RAM:** 256 MB minimum
- **Disk:** 30 MB free space
- **Network:** Internet connection to SOC server
- **Privileges:** Administrator access (for system logs)

---

## What It Does

The agent automatically:
- Collects macOS system logs via `log show`
- Monitors Console app logs and system events
- Scans local network for topology mapping
- Sends log data to your SOC server
- Executes security commands from the server

---

## macOS Permissions

macOS requires special permissions for log access:

1. **Grant Full Disk Access:**
   - System Preferences → Security & Privacy → Privacy
   - Select "Full Disk Access"
   - Click the lock to make changes
   - Add Terminal or your Python executable

2. **Allow Network Access:**
   - System Preferences → Security & Privacy → Privacy
   - Select "Network"
   - Add Terminal or Python if prompted

---

## Running as Launch Daemon

Create a launch daemon for automatic startup:

```bash
# Create plist file
sudo nano /Library/LaunchDaemons/com.codegrey.agent.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.codegrey.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/agent/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/agent</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/codegrey-agent.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/codegrey-agent-error.log</string>
</dict>
</plist>
```

```bash
# Load and start daemon
sudo launchctl load /Library/LaunchDaemons/com.codegrey.agent.plist
sudo launchctl start com.codegrey.agent

# Check status
sudo launchctl list | grep codegrey
```

---

## Troubleshooting

**Agent won't start:**
- Check Python version: `python3 --version`
- Install Xcode Command Line Tools: `xcode-select --install`
- Install dependencies: `pip3 install -r requirements.txt`

**Can't connect to server:**
- Check `server_endpoint` in `config.yaml`
- Test connectivity: `curl http://your-server:8080/health`
- Check macOS Firewall in System Preferences

**Permission errors:**
- Run with sudo: `sudo python3 main.py`
- Grant Full Disk Access in System Preferences
- Check Console app for permission prompts

**Launch daemon issues:**
- Check daemon status: `sudo launchctl list | grep codegrey`
- View logs: `tail -f /var/log/codegrey-agent.log`
- Reload daemon: `sudo launchctl unload` then `load`

---

## Files

**Essential Files:**
- `main.py` - Python entry point
- `unified_client_agent_clean.py` - Core agent code
- `config.yaml` - Configuration file
- `macos_forwarder.py` - macOS log collection

**Build Files:**
- `build_macos_executable.py` - Create standalone executable
- `requirements.txt` - Python dependencies

---

## Log Sources

The agent collects logs from:
- System log via `log show --predicate`
- Console application logs
- Security and authentication events
- Network and system daemon logs
- Application crash reports

---

## Support

For issues or questions:
1. Check server connectivity with `curl`
2. Verify configuration in `config.yaml`
3. Grant necessary permissions in System Preferences
4. Run with sudo for full system access
5. Check Console app for system messages

---

**CodeGrey AI SOC Platform - Intelligent Security Operations**