#!/bin/bash

# Wazo IVR System Plugin Installation Script
# Compatible with Wazo 22+

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PLUGIN_NAME="wazo-ivr-system-plugin"
PLUGIN_VERSION="1.0.0"
WAZO_VERSION="22.0"
INSTALL_DIR="/var/lib/wazo/plugins"
PLUGIN_DIR="${INSTALL_DIR}/${PLUGIN_NAME}"
SERVICE_USER="wazo"
SERVICE_GROUP="wazo"

# Logging
LOG_FILE="/var/log/wazo-ivr-install.log"
exec > >(tee -a ${LOG_FILE})
exec 2>&1

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Wazo IVR System Plugin Installation${NC}"
echo -e "${BLUE}Version: ${PLUGIN_VERSION}${NC}"
echo -e "${BLUE}Compatible with Wazo: ${WAZO_VERSION}+${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Check Wazo version
print_status "Checking Wazo version..."
if command -v wazo-version &> /dev/null; then
    WAZO_CURRENT_VERSION=$(wazo-version)
    print_status "Current Wazo version: ${WAZO_CURRENT_VERSION}"
    
    # Extract major version number
    WAZO_MAJOR_VERSION=$(echo ${WAZO_CURRENT_VERSION} | cut -d. -f1)
    if [ "${WAZO_MAJOR_VERSION}" -lt 22 ]; then
        print_error "Wazo version ${WAZO_CURRENT_VERSION} is not supported. Required: ${WAZO_VERSION}+"
        exit 1
    fi
else
    print_warning "Could not determine Wazo version. Proceeding with installation..."
fi

# Check if Wazo services are running
print_status "Checking Wazo services..."
if ! systemctl is-active --quiet wazo-calld wazo-confd wazo-dird; then
    print_warning "Some Wazo services are not running. Please ensure Wazo is properly installed and running."
fi

# Install system dependencies
print_status "Installing system dependencies..."
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    sox \
    flite \
    espeak \
    festival \
    asterisk \
    wazo-calld \
    wazo-confd \
    wazo-dird \
    curl \
    wget \
    git

# Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install \
    boto3 \
    flask \
    flask-cors \
    requests \
    pyyaml \
    jinja2 \
    urllib3

# Create plugin directory structure
print_status "Creating plugin directory structure..."
mkdir -p ${PLUGIN_DIR}
mkdir -p /var/lib/wazo-ivr/flows
mkdir -p /var/lib/wazo/sounds/ivr
mkdir -p /var/cache/wazo-ivr/tts
mkdir -p /etc/wazo-ivr
mkdir -p /var/log/wazo-ivr

# Copy plugin files
print_status "Installing plugin files..."
cp -r src/wazo_ivr_plugin ${PLUGIN_DIR}/
cp -r examples ${PLUGIN_DIR}/
cp -r etc ${PLUGIN_DIR}/
cp wazo/plugin.yml ${PLUGIN_DIR}/
cp README.md ${PLUGIN_DIR}/
cp LICENSE ${PLUGIN_DIR}/

# Set permissions
print_status "Setting permissions..."
chown -R ${SERVICE_USER}:${SERVICE_GROUP} ${PLUGIN_DIR}
chown -R ${SERVICE_USER}:${SERVICE_GROUP} /var/lib/wazo-ivr
chown -R ${SERVICE_USER}:${SERVICE_GROUP} /var/cache/wazo-ivr
chown -R ${SERVICE_USER}:${SERVICE_GROUP} /var/log/wazo-ivr
chmod -R 755 ${PLUGIN_DIR}
chmod -R 755 /var/lib/wazo-ivr
chmod -R 755 /var/cache/wazo-ivr

# Create systemd service for REST API
print_status "Creating systemd service..."
cat > /etc/systemd/system/wazo-ivr-api.service << EOF
[Unit]
Description=Wazo IVR System Plugin REST API
After=network.target wazo-calld.service wazo-confd.service wazo-dird.service
Wants=wazo-calld.service wazo-confd.service wazo-dird.service

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${PLUGIN_DIR}
Environment=PYTHONPATH=${PLUGIN_DIR}
ExecStart=/usr/bin/python3 -m wazo_ivr_plugin.rest_api
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create configuration file
print_status "Creating configuration file..."
cat > /etc/wazo-ivr/config.yml << EOF
# Wazo IVR System Plugin Configuration

# REST API Configuration
api:
  host: "0.0.0.0"
  port: 5000
  debug: false

# TTS Configuration
tts:
  default_backend: "polly"  # or "local"
  cache_enabled: true
  cache_max_age_days: 30

# AWS Polly Configuration (if using Polly)
aws:
  region: "us-east-1"
  # Set these via environment variables:
  # AWS_ACCESS_KEY_ID
  # AWS_SECRET_ACCESS_KEY

# Local TTS Configuration
local_tts:
  default_engine: "flite"  # or "espeak", "festival"
  default_voice: "slt"

# Flow Configuration
flows:
  storage_path: "/var/lib/wazo-ivr/flows"
  auto_deploy: false

# Logging Configuration
logging:
  level: "INFO"
  file: "/var/log/wazo-ivr/plugin.log"
  max_size: "10MB"
  backup_count: 5
EOF

chown ${SERVICE_USER}:${SERVICE_GROUP} /etc/wazo-ivr/config.yml
chmod 644 /etc/wazo-ivr/config.yml

# Create CLI wrapper script
print_status "Creating CLI wrapper script..."
cat > /usr/local/bin/wazo-ivr << EOF
#!/bin/bash
cd ${PLUGIN_DIR}
python3 -m wazo_ivr_plugin.api "\$@"
EOF

chmod +x /usr/local/bin/wazo-ivr

# Create webhook configuration
print_status "Configuring webhooks..."
if [ -d "/etc/wazo-webhookd/conf.d" ]; then
    cp etc/wazo-webhookd/conf.d/acd-webhooks.yml /etc/wazo-webhookd/conf.d/
    systemctl reload wazo-webhookd
fi

# Configure Asterisk
print_status "Configuring Asterisk..."
if [ -d "/etc/asterisk/extensions_extra.d" ]; then
    cp etc/asterisk/extensions_extra.d/50-acd.conf /etc/asterisk/extensions_extra.d/
    asterisk -rx "dialplan reload"
fi

# Configure Wazo confd
print_status "Configuring Wazo confd..."
if [ -d "/etc/wazo-conf/conf.d" ]; then
    cp etc/wazo-conf/conf.d/acd-queues.yml /etc/wazo-conf/conf.d/
    cp etc/wazo-conf/conf.d/acd-schedules.yml /etc/wazo-conf/conf.d/
    systemctl reload wazo-confd
fi

# Enable and start services
print_status "Enabling and starting services..."
systemctl daemon-reload
systemctl enable wazo-ivr-api
systemctl start wazo-ivr-api

# Wait for service to start
sleep 5

# Check service status
if systemctl is-active --quiet wazo-ivr-api; then
    print_status "Wazo IVR API service started successfully"
else
    print_error "Failed to start Wazo IVR API service"
    systemctl status wazo-ivr-api
    exit 1
fi

# Create sample flow
print_status "Creating sample flow..."
cp examples/flows/sales.yml /var/lib/wazo-ivr/flows/
chown ${SERVICE_USER}:${SERVICE_GROUP} /var/lib/wazo-ivr/flows/sales.yml

# Test installation
print_status "Testing installation..."
if command -v wazo-ivr &> /dev/null; then
    print_status "CLI tool installed successfully"
    wazo-ivr status
else
    print_warning "CLI tool not found in PATH"
fi

# Create uninstall script
print_status "Creating uninstall script..."
cat > /usr/local/bin/wazo-ivr-uninstall << EOF
#!/bin/bash
echo "Uninstalling Wazo IVR System Plugin..."

# Stop and disable services
systemctl stop wazo-ivr-api
systemctl disable wazo-ivr-api

# Remove service file
rm -f /etc/systemd/system/wazo-ivr-api.service

# Remove plugin files
rm -rf ${PLUGIN_DIR}
rm -rf /var/lib/wazo-ivr
rm -rf /var/cache/wazo-ivr
rm -rf /var/log/wazo-ivr
rm -rf /etc/wazo-ivr

# Remove CLI tools
rm -f /usr/local/bin/wazo-ivr
rm -f /usr/local/bin/wazo-ivr-uninstall

# Remove configuration files
rm -f /etc/asterisk/extensions_extra.d/50-acd.conf
rm -f /etc/wazo-webhookd/conf.d/acd-webhooks.yml
rm -f /etc/wazo-conf/conf.d/acd-queues.yml
rm -f /etc/wazo-conf/conf.d/acd-schedules.yml

# Reload services
systemctl daemon-reload
systemctl reload asterisk
systemctl reload wazo-webhookd
systemctl reload wazo-confd

echo "Uninstallation complete."
EOF

chmod +x /usr/local/bin/wazo-ivr-uninstall

# Final status
print_status "Installation completed successfully!"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Summary:${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Plugin installed to: ${PLUGIN_DIR}"
echo -e "REST API service: wazo-ivr-api"
echo -e "CLI tool: wazo-ivr"
echo -e "Configuration: /etc/wazo-ivr/config.yml"
echo -e "Logs: /var/log/wazo-ivr/"
echo -e "Sample flow: /var/lib/wazo-ivr/flows/sales.yml"
echo -e ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "1. Configure AWS credentials for Polly TTS (if using):"
echo -e "   export AWS_ACCESS_KEY_ID=your_key"
echo -e "   export AWS_SECRET_ACCESS_KEY=your_secret"
echo -e "2. Test the installation:"
echo -e "   wazo-ivr status"
echo -e "3. Deploy a sample flow:"
echo -e "   wazo-ivr deploy --flow-id sales --wazo-host your-wazo-host --token your-token"
echo -e "4. Access REST API: http://your-server:5000/api/ivr/"
echo -e ""
echo -e "${YELLOW}To uninstall: wazo-ivr-uninstall${NC}"
echo -e "${GREEN}========================================${NC}"
