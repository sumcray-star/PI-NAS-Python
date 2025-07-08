# Raspberry Pi OpenMediaVault (OMV) Detailed Setup Guide

## Overview
This comprehensive guide covers setting up a Raspberry Pi with OpenMediaVault (OMV) from scratch, configuring it for network storage, and integrating it with PI-NAS for seamless media management and streaming.

## Hardware Setup and Requirements

### Essential Hardware
- **Raspberry Pi 4 Model B** (4GB RAM minimum, 8GB recommended for heavy loads)
- **High-quality MicroSD card** (64GB minimum, Class 10/U3, SanDisk Extreme recommended)
- **External storage** (USB 3.0 HDD/SSD, 1TB+ recommended)
- **Ethernet cable** (Cat5e/Cat6 for stable network connection)
- **Official power supply** (Pi 4 power adapter, 3A minimum)
- **Case with cooling** (Active cooling recommended for 24/7 operation)

### Optional Hardware
- **UPS (Uninterruptible Power Supply)** for data protection
- **Multiple drives** for RAID configuration
- **USB hub** (powered) for multiple drives

---

## Phase 1: OpenMediaVault Installation

### Step 1.1: Download Required Software
```bash
# Download from official sources:
# 1. Raspberry Pi Imager: https://www.raspberrypi.org/software/
# 2. OMV for Raspberry Pi: https://www.openmediavault.org/download.html

# For advanced users - manual installation:
wget https://github.com/OpenMediaVault-Plugin-Developers/installScript/raw/master/install
chmod +x install
sudo ./install
```

### Step 1.2: Prepare SD Card
```bash
# Using Raspberry Pi Imager:
# 1. Select "Use custom image"
# 2. Choose downloaded OMV image (.img or .xz file)
# 3. Click gear icon for advanced options:
#    - Enable SSH
#    - Set username: omv
#    - Set password: [strong password]
#    - Configure Wi-Fi if needed
#    - Set locale settings
# 4. Write to SD card

# Verify SD card integrity after writing
```

### Step 1.3: First Boot Configuration
```bash
# Connect Pi to network via ethernet
# Power on and wait 2-3 minutes for first boot

# Find Pi IP address:
# Method 1: Check router admin panel
# Method 2: Network scan
nmap -sn 192.168.1.0/24

# Method 3: Use router's DHCP client list
# Method 4: Connect monitor and check IP with:
ip addr show
```

---

## Phase 2: Initial OMV Configuration

### Step 2.1: SSH Access Setup
```bash
# Connect via SSH (replace with your Pi's IP)
ssh omv@192.168.1.XXX

# If using root (older OMV versions):
ssh root@192.168.1.XXX
# Default password: openmediavault

# First login security steps:
# 1. Change password immediately
passwd

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Set timezone
sudo timedatectl set-timezone America/New_York
# Replace with your timezone from: timedatectl list-timezones

# 4. Configure hostname
sudo hostnamectl set-hostname pi-nas-server
```

### Step 2.2: Web Interface Access
```bash
# Access OMV web interface
# URL: http://[PI_IP_ADDRESS]
# Default credentials:
# Username: admin
# Password: openmediavault

# IMPORTANT: Change admin password immediately!
```

### Step 2.3: Essential Security Configuration
```bash
# In OMV Web Interface:

# 1. System → General Settings → Web Administrator Password
#    - Set strong password
#    - Enable auto logout
#    - Set session timeout: 30 minutes

# 2. System → General Settings → Web Administrator Panel
#    - Enable Force SSL: Yes (if using HTTPS)
#    - Change port from 80 to custom (e.g., 8080)

# 3. System → Network → Interfaces
#    - Configure static IP for stability
#    - Example static IP: 192.168.1.100

# 4. System → Date & Time
#    - Set correct timezone
#    - Enable NTP
#    - NTP servers: pool.ntp.org
```

---

## Phase 3: Storage Configuration

### Step 3.1: Prepare External Storage
```bash
# Connect external drive(s) to Pi
# Power on external drive if required

# In OMV Web Interface:
# 1. Storage → Disks
#    - Verify drives are detected
#    - Check drive health
#    - Note drive identifiers (/dev/sda, /dev/sdb, etc.)

# Optional: Secure drive wipe (for new drives)
# 2. Storage → Disks → [Select Drive] → Wipe
#    - Choose "Quick" for basic wipe
#    - Choose "Secure" for sensitive data
```

### Step 3.2: Create File Systems
```bash
# In OMV Web Interface:
# 1. Storage → File Systems → Create
#    - Device: Select your external drive
#    - Type: ext4 (recommended for Linux)
#    - Alternative: NTFS (for Windows compatibility)
#    - Label: MediaStorage (or preferred name)

# 2. Apply Configuration Changes
#    - Click yellow notification bar
#    - Click "Apply" to save changes

# 3. Mount the file system
#    - Storage → File Systems
#    - Select created file system
#    - Click "Mount"
```

### Step 3.3: Create Shared Folders
```bash
# In OMV Web Interface:
# 1. Storage → Shared Folders → Create
#    - Name: Media
#    - Device: Select your mounted storage
#    - Path: /Media (will be created automatically)
#    - Comment: PI-NAS Media Storage
#    - Permissions: Administrator: read/write, Users: read/write, Others: none

# 2. Create additional folders:
#    - Name: Uploads
#    - Name: Backups
#    - Name: Documents

# 3. Apply configuration changes
```

---

## Phase 4: Network Services Configuration

### Step 4.1: SMB/CIFS Setup for PI-NAS Integration
```bash
# In OMV Web Interface:
# 1. Services → SMB/CIFS → Settings
#    - Enable: Yes
#    - Workgroup: WORKGROUP
#    - Server string: PI-NAS Media Server
#    - Extra options:
      min protocol = SMB2
      max protocol = SMB3
      security = user
      map to guest = bad user
      guest account = nobody

# 2. Services → SMB/CIFS → Shares → Create
#    - Shared folder: Media
#    - Comment: Media files for PI-NAS
#    - Public: No
#    - Only guest: No
#    - Browseable: Yes
#    - Honor existing ACLs: Yes
#    - Extra options:
      create mask = 0664
      directory mask = 0775
      force user = pi-nas
      force group = users

# 3. Apply configuration changes
```

### Step 4.2: User Management for Network Access
```bash
# In OMV Web Interface:
# 1. Access Rights Management → User → Create
#    - Name: pi-nas
#    - Password: [secure password]
#    - Comment: PI-NAS service account
#    - Groups: users
#    - Shell: /usr/sbin/nologin

# 2. Create media user (for personal access):
#    - Name: media
#    - Password: [your password]
#    - Comment: Media access user
#    - Groups: users
#    - Shell: /bin/bash

# 3. Access Rights Management → Shared Folders → [Media] → Privileges
#    - User pi-nas: Read/Write
#    - User media: Read/Write
#    - Group users: Read/Write
```

### Step 4.3: Additional Network Services
```bash
# Optional Services (enable as needed):

# SSH Service:
# 1. Services → SSH
#    - Enable: Yes
#    - Port: 2222 (security through obscurity)
#    - Permit root login: No
#    - Password authentication: Yes (or use keys)

# FTP Service (if needed):
# 1. Services → FTP
#    - Enable: Yes
#    - Port: 21
#    - Max clients: 10
#    - Anonymous login: No

# DLNA/UPnP Media Server:
# 1. Services → DLNA
#    - Enable: Yes
#    - Name: PI-NAS DLNA Server
#    - Shared folders: Media
```

---

## Phase 5: Security and Optimization

### Step 5.1: Firewall Configuration
```bash
# Via SSH on Raspberry Pi:
# Install and configure UFW
sudo apt install ufw -y

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow essential services
sudo ufw allow ssh
sudo ufw allow 80/tcp    # OMV web interface
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 445/tcp   # SMB
sudo ufw allow 5000/tcp  # PI-NAS application

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### Step 5.2: Performance Optimization
```bash
# In OMV Web Interface:
# 1. System → Power Management
#    - Standby: Never
#    - Suspend: Never
#    - HDMI: Off (if headless)

# 2. System → Monitoring
#    - Enable performance stats collection
#    - Set appropriate intervals

# Via SSH - System optimization:
# GPU memory split (for headless operation)
echo 'gpu_mem=16' | sudo tee -a /boot/config.txt

# USB performance
echo 'dwc_otg.speed=1' | sudo tee -a /boot/cmdline.txt

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-powersave
```

### Step 5.3: Backup and Monitoring Setup
```bash
# Create backup script
sudo tee /usr/local/bin/omv-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/srv/dev-disk-by-uuid-[YOUR-UUID]/Backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup OMV configuration
omv-confdbadm read > "$BACKUP_DIR/omv-config-$DATE.json"

# Backup important system files
tar -czf "$BACKUP_DIR/system-config-$DATE.tar.gz" \
    /etc/hostname \
    /etc/hosts \
    /etc/fstab \
    /etc/network/interfaces

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.json" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/omv-backup.sh

# Schedule daily backups
echo "0 2 * * * root /usr/local/bin/omv-backup.sh" | sudo tee -a /etc/crontab
```

---

## Phase 6: PI-NAS Integration Testing

### Step 6.1: Connection Testing
```bash
# From PI-NAS server, test SMB connection:
# Install SMB client tools
sudo apt install cifs-utils smbclient -y

# List available shares
smbclient -L //192.168.1.100 -U pi-nas

# Test mounting
sudo mkdir -p /mnt/test-mount
sudo mount -t cifs //192.168.1.100/Media /mnt/test-mount \
    -o username=pi-nas,password=[password],uid=$(id -u),gid=$(id -g)

# Test write access
echo "Test file from PI-NAS" | sudo tee /mnt/test-mount/test.txt

# Verify in OMV web interface under Media share

# Unmount test
sudo umount /mnt/test-mount
```

### Step 6.2: Performance Testing
```bash
# Network speed test
iperf3 -s  # On OMV Pi
iperf3 -c 192.168.1.100  # From PI-NAS server

# File transfer speed test
# Copy large file to test throughput
time rsync -avh --progress largefile.mp4 pi-nas@192.168.1.100:/srv/dev-disk-by-uuid-[UUID]/Media/

# SMB performance test
time cp largefile.mp4 /mnt/test-mount/
```

---

## Phase 7: Advanced Configuration

### Step 7.1: RAID Configuration (Optional)
```bash
# For multiple drives - RAID 1 (mirror) setup:
# In OMV Web Interface:
# 1. Storage → RAID Management → Create
#    - Name: media-raid1
#    - Level: RAID 1
#    - Devices: Select 2 drives
#    - 
# 2. Wait for sync completion
# 3. Create file system on RAID array
# 4. Update shared folder to use RAID storage
```

### Step 7.2: Automatic Updates
```bash
# In OMV Web Interface:
# 1. System → Update Management
#    - Enable automatic updates
#    - Schedule: Daily at 2 AM
#    - Email notifications: Enable

# 2. Plugins → Available → Install:
#    - openmediavault-backup
#    - openmediavault-diskstats
#    - openmediavault-filebrowser
```

### Step 7.3: Remote Access Setup
```bash
# Dynamic DNS setup (if needed)
# 1. Register with No-IP, DuckDNS, or Cloudflare
# 2. Install ddclient:
sudo apt install ddclient -y

# Configure ddclient for your provider
sudo nano /etc/ddclient.conf

# Example for No-IP:
# protocol=noip
# use=web
# server=dynupdate.no-ip.com
# login=your-email
# password='your-password'
# hostname.no-ip.info

# Restart ddclient
sudo systemctl restart ddclient
sudo systemctl enable ddclient
```

---

## Phase 8: Integration with PI-NAS Application

### Step 8.1: Configure PI-NAS Connection
```bash
# On PI-NAS server, update config file:
cat > config/storage_config.json << 'EOF'
{
  "server_ip": "192.168.1.100",
  "share_name": "Media",
  "username": "pi-nas",
  "mount_point": "/mnt/pi-omv",
  "protocol": "smb",
  "port": 445,
  "auto_mount": true,
  "mount_timeout": 30,
  "enabled": true,
  "smb_version": "3.0"
}
EOF
```

### Step 8.2: Test Integration
```bash
# Use PI-NAS mount script
./scripts/mount_network_drive.sh test

# Mount the share
./scripts/mount_network_drive.sh mount

# Check mount status
./scripts/mount_network_drive.sh status

# Test upload through PI-NAS interface
# Navigate to Upload Media page
# Upload test file
# Verify file appears in OMV Media share
```

---

## Troubleshooting Common Issues

### Issue: Cannot access OMV web interface
```bash
# Check if OMV services are running
sudo systemctl status openmediavault-webgui

# Check network configuration
ip addr show
ping 8.8.8.8

# Reset web interface
sudo omv-firstaid
# Select "Configure web control panel"
```

### Issue: SMB share not accessible
```bash
# Check SMB service status
sudo systemctl status smbd nmbd

# Test SMB configuration
sudo testparm

# Check firewall
sudo iptables -L
sudo ufw status

# Check user permissions
sudo smbpasswd -a pi-nas
```

### Issue: Poor performance
```bash
# Check system resources
htop
iotop
df -h

# Check for overheating
vcgencmd measure_temp

# Optimize SMB settings
# Add to [global] section in /etc/samba/smb.conf:
socket options = TCP_NODELAY SO_RCVBUF=131072 SO_SNDBUF=131072
```

### Issue: Storage not mounting
```bash
# Check drive health
sudo smartctl -a /dev/sda

# Check file system
sudo fsck /dev/sda1

# Manual mount test
sudo mount /dev/sda1 /mnt/test

# Check OMV logs
sudo journalctl -u openmediavault-engined
```

---

## Maintenance Schedule

### Daily Tasks (Automated)
- Configuration backup
- Log rotation
- Health monitoring

### Weekly Tasks
- Check system updates
- Review security logs
- Test backup restoration

### Monthly Tasks
- Full system backup
- Performance review
- Security audit
- Drive health check

---

## Security Best Practices

### Network Security
- Change default passwords immediately
- Use strong, unique passwords
- Enable firewall with minimal required ports
- Regular security updates
- Monitor access logs

### Physical Security
- Secure physical access to Pi
- Use quality power supply with surge protection
- Ensure adequate cooling
- Consider UPS for power stability

### Data Security
- Regular backups to separate location
- Encrypt sensitive data
- Monitor drive health
- Test disaster recovery procedures

---

## Quick Reference Commands

```bash
# OMV Status Check
sudo systemctl status openmediavault-*

# Storage Information
df -h
lsblk

# Network Services
sudo systemctl status smbd nmbd ssh

# Performance Monitoring
htop
iotop
vcgencmd measure_temp

# Log Checking
sudo journalctl -f
tail -f /var/log/samba/log.smbd

# Configuration Backup
omv-confdbadm read > omv-backup.json

# Emergency Reset
sudo omv-firstaid
```

This comprehensive guide should get your Raspberry Pi OMV setup fully configured and integrated with PI-NAS. The setup typically takes 2-3 hours for a complete installation and configuration.
