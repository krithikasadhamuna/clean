#!/bin/bash

# CodeGrey AI SOC Platform - Systemd Service Setup Script
# For Amazon Linux 2023

set -e

echo "=========================================="
echo "CodeGrey AI SOC Platform - Systemd Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as ec2-user."
   exit 1
fi

# Check if we're on Amazon Linux 2023
if ! grep -q "Amazon Linux 2023" /etc/os-release 2>/dev/null; then
    print_warning "This script is designed for Amazon Linux 2023. Proceeding anyway..."
fi

# Get current directory
CURRENT_DIR=$(pwd)
print_status "Current directory: $CURRENT_DIR"

# Check if main.py exists
if [ ! -f "$CURRENT_DIR/main.py" ]; then
    print_error "main.py not found in current directory. Please run this script from the CodeGrey project root."
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

print_status "Python 3 found: $(python3 --version)"

# Create the service file
SERVICE_FILE="/etc/systemd/system/codegrey-soc-platform.service"
SERVICE_CONTENT="[Unit]
Description=CodeGrey AI SOC Platform Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/main.py server --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=codegrey-soc

# Environment variables
Environment=PYTHONPATH=$CURRENT_DIR
Environment=PYTHONUNBUFFERED=1

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$CURRENT_DIR
ReadWritePaths=$CURRENT_DIR/soc_database.db
ReadWritePaths=$CURRENT_DIR/ml_models

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target"

print_status "Creating systemd service file..."

# Create temporary service file
TEMP_SERVICE_FILE="/tmp/codegrey-soc-platform.service"
echo "$SERVICE_CONTENT" > "$TEMP_SERVICE_FILE"

# Copy service file to systemd directory (requires sudo)
print_status "Installing service file (requires sudo)..."
sudo cp "$TEMP_SERVICE_FILE" "$SERVICE_FILE"
sudo chmod 644 "$SERVICE_FILE"

# Clean up temporary file
rm "$TEMP_SERVICE_FILE"

print_success "Service file created: $SERVICE_FILE"

# Reload systemd daemon
print_status "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
print_status "Enabling service to start on boot..."
sudo systemctl enable codegrey-soc-platform.service

print_success "Service enabled successfully!"

# Check if service is already running
if sudo systemctl is-active --quiet codegrey-soc-platform.service; then
    print_warning "Service is already running. Stopping it first..."
    sudo systemctl stop codegrey-soc-platform.service
fi

# Start the service
print_status "Starting CodeGrey AI SOC Platform service..."
sudo systemctl start codegrey-soc-platform.service

# Wait a moment for the service to start
sleep 3

# Check service status
print_status "Checking service status..."
if sudo systemctl is-active --quiet codegrey-soc-platform.service; then
    print_success "Service started successfully!"
else
    print_error "Service failed to start. Checking status..."
    sudo systemctl status codegrey-soc-platform.service
    exit 1
fi

# Show service status
echo ""
print_status "Service Status:"
sudo systemctl status codegrey-soc-platform.service --no-pager

echo ""
print_status "Service Management Commands:"
echo "  Check status:    sudo systemctl status codegrey-soc-platform.service"
echo "  Start service:   sudo systemctl start codegrey-soc-platform.service"
echo "  Stop service:    sudo systemctl stop codegrey-soc-platform.service"
echo "  Restart service: sudo systemctl restart codegrey-soc-platform.service"
echo "  View logs:       sudo journalctl -u codegrey-soc-platform.service -f"
echo "  Disable service: sudo systemctl disable codegrey-soc-platform.service"

echo ""
print_status "Service will automatically start on system boot."
print_success "CodeGrey AI SOC Platform is now running as a systemd service!"

# Check if the service is listening on port 8080
print_status "Checking if service is listening on port 8080..."
if netstat -tlnp 2>/dev/null | grep -q ":8080 "; then
    print_success "Service is listening on port 8080"
else
    print_warning "Service may not be listening on port 8080 yet. Check logs with:"
    echo "  sudo journalctl -u codegrey-soc-platform.service -f"
fi

echo ""
print_status "Setup complete! The CodeGrey AI SOC Platform is now running as a systemd service."

