# Raspberry Pi Edge Device - Disaster Response System

## Overview
This module contains the code for the Raspberry Pi 4 edge device that captures real-time imagery using the Pi Camera V3 and transmits it to Google Cloud Platform for AI processing. This device is designed to be mounted on drones for aerial disaster assessment.

## Hardware Requirements

### Core Components
- **Raspberry Pi 4 Model B (4GB RAM)** - Main processing unit
- **Pi Camera V3 (12MP)** - Image capture with HDR support
- **USB 4G/LTE Dongle** - Cellular connectivity for data transmission
- **32GB microSD Card (U3)** - Local storage and OS
- **LM2596 DC-DC Converter** - Power regulation from drone battery

### Optional Components
- **Low-profile heatsink** - Temperature management
- **5V micro-fan** - Active cooling
- **3D-printed mounting sled** - Vibration isolation
- **External GPS module** - Enhanced location accuracy

## Software Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Pi Camera V3  │ -> │   Raspberry Pi   │ -> │   4G/LTE Link   │
│   (Image Capture│    │   (Processing)   │    │  (Transmission) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Local Storage  │
                       │  (Offline Mode) │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Google Cloud  │
                       │   (Processing)  │
                       └─────────────────┘
```

## Features

### Real-time Image Capture
- **High-resolution imaging**: 4608×2592 stills, 1080p 60fps video
- **HDR support**: Enhanced dynamic range for disaster scenarios
- **Configurable capture intervals**: Adaptive based on flight mission
- **GPS metadata embedding**: Location tagging for each image

### Intelligent Transmission
- **Bandwidth optimization**: Adaptive quality based on connection strength
- **Retry mechanism**: Robust upload with exponential backoff
- **Offline buffering**: Local storage when connectivity is lost
- **Compression**: On-device image optimization

### Network Management
- **Multi-network support**: 4G/LTE with WiFi fallback
- **Connection monitoring**: Real-time signal strength tracking
- **Data usage tracking**: Bandwidth consumption monitoring
- **Network switching**: Automatic failover between connections

### System Monitoring
- **Health checks**: CPU, memory, temperature monitoring
- **Battery status**: Power level tracking (when available)
- **Storage management**: Automatic cleanup of transmitted images
- **Error logging**: Comprehensive debug information

## Installation

### 1. Raspberry Pi OS Setup
```bash
# Flash Raspberry Pi OS Lite (64-bit) to microSD card
# Enable SSH and camera interface through raspi-config

sudo raspi-config
# -> Interface Options -> Camera -> Enable
# -> Interface Options -> SSH -> Enable
```

### 2. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv git

# Install camera and GPIO libraries
sudo apt install -y python3-picamera2 python3-libcamera python3-gpiozero

# Install network utilities
sudo apt install -y network-manager wvdial usb-modeswitch
```

### 3. Clone and Setup
```bash
git clone <repository-url>
cd disaster-mapping-segmentation/raspberry-pi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 4. Configure GCP Credentials
```bash
# Copy service account key
cp /path/to/service-account-key.json config/gcp-credentials.json

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="config/gcp-credentials.json"
```

## Configuration

### System Configuration (`config/system.yaml`)
```yaml
camera:
  resolution: [4608, 2592]
  capture_interval: 5  # seconds
  video_mode: false
  hdr_enabled: true

network:
  primary: "4g"
  fallback: "wifi"
  retry_attempts: 3
  timeout: 30

storage:
  max_local_images: 100
  cleanup_after_upload: true
  compression_quality: 85

gcp:
  bucket_name: "disaster-images"
  project_id: "your-project-id"
  api_endpoint: "https://your-api-endpoint.com"
```

### Network Configuration (`config/network.yaml`)
```yaml
4g_modem:
  device: "/dev/ttyUSB0"
  apn: "internet"
  username: ""
  password: ""

wifi:
  ssid: "backup-network"
  password: "backup-password"
```

## Usage

### Quick Start
```bash
# Activate environment
source venv/bin/activate

# Start the main capture service
python main.py

# Or run as systemd service
sudo systemctl start disaster-camera
```

### Manual Testing
```bash
# Test camera capture
python scripts/test_camera.py

# Test GCP upload
python scripts/test_upload.py

# Test network connectivity
python scripts/test_network.py

# Monitor system health
python scripts/monitor.py
```

### Service Management
```bash
# Install as system service
sudo ./scripts/install_service.sh

# Service controls
sudo systemctl start disaster-camera
sudo systemctl stop disaster-camera
sudo systemctl status disaster-camera
sudo systemctl enable disaster-camera  # Auto-start on boot
```

## API Integration

The Pi communicates with the disaster response dashboard via REST API:

### Image Upload Endpoint
```python
POST /api/upload-image
Headers:
  - Content-Type: multipart/form-data
  - Authorization: Bearer <token>

Form Data:
  - image: (file) - Captured image
  - latitude: (float) - GPS latitude
  - longitude: (float) - GPS longitude
  - timestamp: (string) - ISO format timestamp
  - device_id: (string) - Unique Pi identifier
  - altitude: (float) - Drone altitude (optional)
```

### Health Status Endpoint
```python
POST /api/device-status
Headers:
  - Content-Type: application/json

Body:
{
  "device_id": "pi-001",
  "timestamp": "2024-01-01T12:00:00Z",
  "battery_level": 85,
  "signal_strength": -65,
  "temperature": 45.2,
  "storage_used": 25.5,
  "images_pending": 3
}
```

## Monitoring and Debugging

### Log Files
- **System logs**: `/var/log/disaster-camera.log`
- **Error logs**: `/var/log/disaster-camera-error.log`
- **Network logs**: `/var/log/network.log`
- **Upload logs**: `/var/log/uploads.log`

### Performance Monitoring
```bash
# Real-time monitoring
tail -f /var/log/disaster-camera.log

# System resources
htop
vcgencmd measure_temp  # Pi temperature
vcgencmd get_throttled  # Throttling status
```

### Troubleshooting
- **Camera not detected**: Check cable connections, enable camera in raspi-config
- **Network issues**: Verify APN settings, check SIM card data plan
- **Upload failures**: Check GCP credentials, network connectivity
- **High temperature**: Ensure proper ventilation, consider adding heatsink

## Power Management

### Battery Optimization
```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-powersave

# CPU frequency scaling
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Power Consumption
- **Idle**: ~2.5W
- **Camera active**: ~4W
- **4G transmission**: ~5W
- **Total estimated**: 4-5W average

## Field Deployment

### Pre-flight Checklist
1. ✅ Verify camera functionality
2. ✅ Check 4G signal strength
3. ✅ Confirm GCP connectivity
4. ✅ Test GPS accuracy
5. ✅ Validate power connections
6. ✅ Clear local storage
7. ✅ Update flight mission config

### Mission Configuration
```yaml
mission:
  id: "myanmar-earthquake-001"
  zone: "mandalay-urban"
  flight_pattern: "grid"
  altitude: 100  # meters
  speed: 5       # m/s
  capture_interval: 3  # seconds
  duration: 30   # minutes
```

## Development

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Integration tests
python tests/integration_test.py

# Hardware-in-loop tests (requires actual Pi)
python tests/hardware_test.py
```

### Contributing
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## Security Considerations

- **Encrypted transmission**: All data sent over HTTPS/TLS
- **Credential management**: Service account keys stored securely
- **Network security**: VPN support for sensitive operations
- **Local encryption**: Optional local storage encryption

## Performance Specifications

### Image Processing
- **Capture latency**: <200ms
- **Compression time**: <500ms per image
- **Upload speed**: Depends on cellular signal (1-10 Mbps typical)

### System Requirements
- **CPU**: ARM Cortex-A72 (Pi 4)
- **RAM**: 4GB minimum
- **Storage**: 32GB microSD (Class 10/U3)
- **Network**: 4G/LTE modem with data plan

## License
This project is part of the disaster response mapping system. See main repository for license details. 