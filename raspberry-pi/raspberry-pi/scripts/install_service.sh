#!/bin/bash

# Disaster Response Pi Camera Service Installation Script
# This script installs the camera system as a systemd service

set -e

# Configuration
SERVICE_NAME="disaster-camera"
SERVICE_USER="pi"
INSTALL_DIR="/opt/disaster-camera"
CONFIG_DIR="/etc/disaster-camera"
LOG_DIR="/var/log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Disaster Response Pi Camera Service Installer${NC}"
echo "============================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Check if we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"

# Copy application files
echo "Copying application files..."
cp -r ../src "$INSTALL_DIR/"
cp -r ../config/* "$CONFIG_DIR/"
cp ../main.py "$INSTALL_DIR/"
cp ../requirements.txt "$INSTALL_DIR/"

# Set proper ownership
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chown -R root:root "$CONFIG_DIR"
chmod 644 "$CONFIG_DIR"/*

# Create systemd service file
echo "Creating systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Disaster Response Pi Camera System
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
Environment=GOOGLE_APPLICATION_CREDENTIALS=$CONFIG_DIR/gcp-credentials.json
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py --config $CONFIG_DIR/system.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
MemoryLimit=512M
CPUQuota=50%

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$LOG_DIR /tmp

[Install]
WantedBy=multi-user.target
EOF

# Create log rotation configuration
echo "Setting up log rotation..."
cat > "/etc/logrotate.d/${SERVICE_NAME}" << EOF
/var/log/disaster-camera*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload $SERVICE_NAME 2>/dev/null || true
    endscript
}
EOF

# Install Python dependencies in virtual environment
echo "Setting up Python virtual environment..."
if ! command -v python3-venv &> /dev/null; then
    echo "Installing python3-venv..."
    apt-get update
    apt-get install -y python3-venv
fi

cd "$INSTALL_DIR"
python3 -m venv venv
chown -R "$SERVICE_USER:$SERVICE_USER" venv

# Install dependencies as the service user
sudo -u "$SERVICE_USER" bash << EOF
cd "$INSTALL_DIR"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF

# Update service file to use virtual environment
sed -i "s|ExecStart=/usr/bin/python3|ExecStart=$INSTALL_DIR/venv/bin/python|" "/etc/systemd/system/${SERVICE_NAME}.service"

# Create startup script with proper environment
cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
cd /opt/disaster-camera
source venv/bin/activate
exec python main.py --config /etc/disaster-camera/system.yaml "$@"
EOF

chmod +x "$INSTALL_DIR/start.sh"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/start.sh"

# Update service to use startup script
sed -i "s|ExecStart=.*|ExecStart=$INSTALL_DIR/start.sh|" "/etc/systemd/system/${SERVICE_NAME}.service"

# Enable camera interface if not already enabled
echo "Checking camera interface..."
if ! grep -q "start_x=1" /boot/config.txt; then
    echo "Enabling camera interface..."
    echo "start_x=1" >> /boot/config.txt
    echo "gpu_mem=128" >> /boot/config.txt
    REBOOT_REQUIRED=true
fi

# Check if camera module is loaded
if ! lsmod | grep -q bcm2835_v4l2; then
    echo "Loading camera module..."
    modprobe bcm2835-v4l2
    echo "bcm2835-v4l2" >> /etc/modules
fi

# Reload systemd and enable service
echo "Enabling service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# Create helper scripts
echo "Creating helper scripts..."

# Status script
cat > "/usr/local/bin/disaster-camera-status" << EOF
#!/bin/bash
systemctl status $SERVICE_NAME
echo
echo "Recent logs:"
journalctl -u $SERVICE_NAME -n 20 --no-pager
EOF

# Control script
cat > "/usr/local/bin/disaster-camera" << EOF
#!/bin/bash
case "\$1" in
    start)
        systemctl start $SERVICE_NAME
        ;;
    stop)
        systemctl stop $SERVICE_NAME
        ;;
    restart)
        systemctl restart $SERVICE_NAME
        ;;
    status)
        disaster-camera-status
        ;;
    logs)
        journalctl -u $SERVICE_NAME -f
        ;;
    test)
        cd $INSTALL_DIR
        source venv/bin/activate
        python main.py --config $CONFIG_DIR/system.yaml --test
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart|status|logs|test}"
        exit 1
        ;;
esac
EOF

chmod +x "/usr/local/bin/disaster-camera"
chmod +x "/usr/local/bin/disaster-camera-status"

echo
echo -e "${GREEN}Installation completed successfully!${NC}"
echo
echo "Service commands:"
echo "  disaster-camera start    - Start the service"
echo "  disaster-camera stop     - Stop the service"
echo "  disaster-camera restart  - Restart the service"
echo "  disaster-camera status   - Show service status"
echo "  disaster-camera logs     - Show live logs"
echo "  disaster-camera test     - Run test mode"
echo
echo "Configuration files are in: $CONFIG_DIR"
echo "Application files are in: $INSTALL_DIR"
echo "Logs are in: $LOG_DIR"
echo

# Check if GCP credentials file exists
if [ ! -f "$CONFIG_DIR/gcp-credentials.json" ]; then
    echo -e "${YELLOW}Warning: GCP credentials file not found!${NC}"
    echo "Please copy your service account key to: $CONFIG_DIR/gcp-credentials.json"
    echo
fi

# Check if reboot is required
if [ "$REBOOT_REQUIRED" = true ]; then
    echo -e "${YELLOW}Camera interface was enabled. A reboot is required.${NC}"
    read -p "Reboot now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        reboot
    fi
else
    echo "You can start the service now with:"
    echo "  sudo disaster-camera start"
fi

echo
echo -e "${GREEN}Setup complete!${NC}" 