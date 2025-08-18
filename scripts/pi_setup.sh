#!/bin/bash

# PI-NAS Raspberry Pi Setup Script
# Run this script on your Raspberry Pi to set up the NAS server

set -e

echo "==================================="
echo "PI-NAS Raspberry Pi Setup Script"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Run as pi user instead."
   exit 1
fi

print_status "Starting PI-NAS setup on Raspberry Pi..."

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install -y samba samba-common-bin ntfs-3g exfat-fuse ufw

# Create media storage directory
print_status "Creating media storage directories..."
sudo mkdir -p /mnt/media-storage/media/{videos,images,audio,documents}
sudo chown -R pi:pi /mnt/media-storage/media
sudo chmod -R 755 /mnt/media-storage/media

# Configure Samba
print_status "Configuring Samba..."

# Backup original config
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.backup

# Add media share configuration
sudo tee -a /etc/samba/smb.conf > /dev/null <<EOF

[media]
   comment = PI-NAS Media Storage
   path = /mnt/media-storage/media
   browseable = yes
   writeable = yes
   only guest = no
   create mask = 0777
   directory mask = 0777
   public = no
   valid users = pi
EOF

# Set up Samba user
print_status "Setting up Samba user..."
echo "Please set a password for the Samba 'pi' user:"
sudo smbpasswd -a pi

# Restart and enable Samba services
print_status "Starting Samba services..."
sudo systemctl restart smbd
sudo systemctl restart nmbd
sudo systemctl enable smbd
sudo systemctl enable nmbd

# Configure firewall
print_status "Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow samba
echo "y" | sudo ufw enable

# Get current IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

print_status "Setup completed successfully!"
print_status "Your Raspberry Pi is now configured as a NAS server."
echo ""
echo "==================================="
echo "Connection Details:"
echo "==================================="
echo "IP Address: $IP_ADDRESS"
echo "Share Name: media"
echo "Username: pi"
echo "Password: [the password you just set]"
echo ""
echo "Media Storage Path: /mnt/media-storage/media"
echo "Directory Structure:"
echo "  - Videos: /mnt/media-storage/media/videos"
echo "  - Images: /mnt/media-storage/media/images"
echo "  - Audio: /mnt/media-storage/media/audio"
echo "  - Documents: /mnt/media-storage/media/documents"
echo ""
echo "==================================="
echo "Next Steps:"
echo "==================================="
echo "1. Note down the IP address: $IP_ADDRESS"
echo "2. Use these details in your PI-NAS web interface"
echo "3. Test connection from your computer:"
echo "   smbclient -L //$IP_ADDRESS -U pi"
echo ""
echo "Optional: Set up static IP address"
echo "sudo nano /etc/dhcpcd.conf"
echo ""
print_status "Setup complete! Your Raspberry Pi NAS is ready to use."