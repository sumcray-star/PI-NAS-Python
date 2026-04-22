#!/bin/bash

##############################################################################
# PI-NAS Media Server - AWS EC2 Automated Deployment Script
#
# This script automates the entire setup process on AWS EC2 t2.micro
#
# Usage:
#   chmod +x deploy-to-aws.sh
#   ./deploy-to-aws.sh
#
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if running on Ubuntu
if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    print_error "This script is designed for Ubuntu. Exiting."
    exit 1
fi

print_header "PI-NAS Media Server - AWS EC2 Deployment"

# Step 1: Update System
print_header "Step 1: Updating System Packages"
sudo apt-get update
sudo apt-get upgrade -y
print_success "System updated"

# Step 2: Install Docker
print_header "Step 2: Installing Docker"
if command -v docker &> /dev/null; then
    print_info "Docker is already installed"
else
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    print_success "Docker installed"
fi

# Add user to docker group
sudo usermod -aG docker ubuntu
print_success "Docker user permissions configured"

# Step 3: Install Docker Compose
print_header "Step 3: Installing Docker Compose"
if command -v docker-compose &> /dev/null; then
    print_info "Docker Compose is already installed"
else
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
fi

# Verify installations
print_header "Step 4: Verifying Installations"
print_info "Docker version:"
docker --version
print_info "Docker Compose version:"
docker-compose --version

# Step 5: Clone Repository (if needed)
print_header "Step 5: Setting Up Application Directory"

if [ -d "PiMediaServer" ]; then
    print_info "PiMediaServer directory already exists"
    cd PiMediaServer
    print_info "Pulling latest changes..."
    git pull
else
    print_info "Enter your GitHub repository URL (or press Enter to skip):"
    read REPO_URL
    if [ ! -z "$REPO_URL" ]; then
        git clone "$REPO_URL" PiMediaServer
        cd PiMediaServer
        print_success "Repository cloned"
    else
        print_info "Skipping repository clone. Please manually add files."
        mkdir -p PiMediaServer
        cd PiMediaServer
    fi
fi

# Step 6: Create necessary directories
print_header "Step 6: Creating Application Directories"
mkdir -p data config media/uploads media/thumbnails logs temp
chmod 777 data config media logs temp
print_success "Directories created"

# Step 7: Create .env file from template
print_header "Step 7: Environment Configuration"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env file created from template"
        print_info "Please edit .env file with your Raspberry Pi details:"
        print_info "  nano .env"
    else
        print_error ".env.example not found"
    fi
else
    print_info ".env file already exists"
fi

# Step 8: Build Docker Image
print_header "Step 8: Building Docker Image"
print_info "This may take 2-3 minutes..."
sudo docker-compose build
print_success "Docker image built successfully"

# Step 9: Start Application
print_header "Step 9: Starting Application"
sudo docker-compose up -d
print_success "Application started in background"

# Wait for startup
sleep 5

# Step 10: Verify Running
print_header "Step 10: Verifying Application"
if sudo docker-compose ps | grep -q "pi-media-server"; then
    print_success "Container is running"
else
    print_error "Container failed to start"
    sudo docker-compose logs
    exit 1
fi

# Get public IP
print_header "Step 11: Application Information"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
if [ -z "$PUBLIC_IP" ]; then
    PUBLIC_IP="YOUR_PUBLIC_IP"
fi

# Summary
echo ""
print_success "Deployment Complete!"
echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  PI-NAS Media Server is Running!${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}Access URL:${NC} http://${PUBLIC_IP}:8501"
echo ""
echo -e "  ${BLUE}Useful Commands:${NC}"
echo "    • View logs:      sudo docker-compose logs -f"
echo "    • Stop:           sudo docker-compose down"
echo "    • Restart:        sudo docker-compose restart"
echo "    • Update code:    git pull && sudo docker-compose up -d --build"
echo ""
echo -e "  ${BLUE}Configuration:${NC}"
echo "    • Edit .env:      nano .env"
echo "    • Restart:        sudo docker-compose restart"
echo ""
echo -e "  ${BLUE}Security:${NC}"
echo "    • Update security group in AWS Console"
echo "    • Restrict SSH access to your IP"
echo "    • Use strong passwords"
echo ""
echo -e "  ${BLUE}Documentation:${NC}"
echo "    • See AWS_EC2_DEPLOYMENT.md for detailed guide"
echo ""

# Optional: Setup auto-start
print_info "Would you like to setup auto-start on reboot? (y/n)"
read -r SETUP_AUTOSTART
if [ "$SETUP_AUTOSTART" = "y" ] || [ "$SETUP_AUTOSTART" = "Y" ]; then
    print_header "Setting Up Auto-start Service"
    
    sudo tee /etc/systemd/system/pi-media-server.service > /dev/null <<EOF
[Unit]
Description=PI-NAS Media Server Docker Application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$PWD
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10
User=ubuntu
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable pi-media-server.service
    print_success "Auto-start service configured"
    print_info "Service will start automatically on EC2 reboot"
fi

echo ""
echo -e "${GREEN}Deployment script completed successfully!${NC}"
echo ""
