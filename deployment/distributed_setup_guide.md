# Distributed PI-NAS Setup Guide
## Web Server on Computer + Raspberry Pi Storage

This guide shows how to set up PI-NAS in a distributed architecture where your main computer runs the web interface and the Raspberry Pi handles storage - exactly like Plex Media Server.

---

## Architecture Overview

```
┌─────────────────────┐    Network    ┌─────────────────────┐
│   Your Computer     │◄──────────────►│   Raspberry Pi      │
│                     │               │                     │
│ ┌─────────────────┐ │               │ ┌─────────────────┐ │
│ │   PI-NAS Web    │ │               │ │  File Storage   │ │
│ │   Interface     │ │               │ │   (OpenMediaVault│ │
│ │   (Streamlit)   │ │               │ │    or Samba)    │ │
│ └─────────────────┘ │               │ └─────────────────┘ │
│                     │               │                     │
│ ┌─────────────────┐ │               │ ┌─────────────────┐ │
│ │ Thumbnail       │ │               │ │  Media Files    │ │
│ │ Generation      │ │               │ │  Documents      │ │
│ │ Processing      │ │               │ │  Uploads        │ │
│ └─────────────────┘ │               │ └─────────────────┘ │
└─────────────────────┘               └─────────────────────┘
```

**Benefits of this setup:**
- **Better performance** - Web interface on powerful computer
- **Dedicated storage** - Raspberry Pi optimized for file serving
- **24/7 availability** - Pi stays on, computer can sleep
- **Scalability** - Easy to add more storage to Pi
- **Cost effective** - Use existing computer + cheap Pi

---

## Part 1: Raspberry Pi Storage Setup

### Step 1: Install Raspberry Pi OS
```bash
# Download and flash Raspberry Pi OS Lite
# Enable SSH and configure WiFi/Ethernet
# Boot and connect via SSH

ssh pi@192.168.1.100  # Replace with your Pi's IP
```

### Step 2: Update and Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y samba samba-common-bin cifs-utils

# Optional: Install OpenMediaVault for web management
wget -O - https://github.com/OpenMediaVault-Plugin-Developers/packages/raw/master/install | sudo bash
```

### Step 3: Configure Storage
```bash
# Connect external USB drive/SSD
# Check available drives
sudo fdisk -l

# Format drive (replace /dev/sda1 with your drive)
sudo mkfs.ext4 /dev/sda1

# Create mount point
sudo mkdir -p /mnt/pi-nas-storage

# Mount drive
sudo mount /dev/sda1 /mnt/pi-nas-storage

# Make mount permanent
echo '/dev/sda1 /mnt/pi-nas-storage ext4 defaults 0 0' | sudo tee -a /etc/fstab
```

### Step 4: Create Directory Structure
```bash
# Create media directories
sudo mkdir -p /mnt/pi-nas-storage/media/{uploads,images,documents,videos,audio}
sudo mkdir -p /mnt/pi-nas-storage/media/thumbnails

# Set permissions
sudo chown -R pi:pi /mnt/pi-nas-storage
sudo chmod -R 755 /mnt/pi-nas-storage
```

### Step 5: Configure Samba Shares
```bash
# Backup original config
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.backup

# Edit Samba configuration
sudo nano /etc/samba/smb.conf

# Add these sections at the end:
```

```ini
[global]
   workgroup = WORKGROUP
   server string = Pi-NAS Storage Server
   netbios name = PI-NAS
   security = user
   map to guest = bad user
   dns proxy = no
   
[media]
   comment = PI-NAS Media Storage
   path = /mnt/pi-nas-storage/media
   browseable = yes
   writeable = yes
   guest ok = no
   read only = no
   valid users = pi
   create mask = 0777
   directory mask = 0777
   force user = pi
   force group = pi

[uploads]
   comment = PI-NAS Upload Directory
   path = /mnt/pi-nas-storage/media/uploads
   browseable = yes
   writeable = yes
   guest ok = no
   read only = no
   valid users = pi
   create mask = 0777
   directory mask = 0777
   force user = pi
   force group = pi
```

### Step 6: Set Up Samba User
```bash
# Create Samba user (use strong password)
sudo smbpasswd -a pi

# Restart Samba service
sudo systemctl restart smbd
sudo systemctl enable smbd

# Test configuration
sudo testparm
```

### Step 7: Configure Static IP (Recommended)
```bash
# Edit dhcpcd configuration
sudo nano /etc/dhcpcd.conf

# Add at the end (adjust for your network):
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Restart networking
sudo systemctl restart dhcpcd
```

---

## Part 2: Computer Setup (Web Interface)

### Step 1: Install PI-NAS
```bash
# Clone or download PI-NAS
git clone https://github.com/[username]/pi-nas.git
cd pi-nas

# Install Python dependencies
pip install streamlit pandas pillow psutil requests opencv-python
```

### Step 2: Configure Network Storage
```bash
# Edit storage configuration
nano config/storage_config.json
```

Update with your Raspberry Pi details:
```json
{
  "server_ip": "192.168.1.100",
  "share_name": "media",
  "username": "pi",
  "password": "your_samba_password",
  "mount_point": "/mnt/pi-nas",
  "protocol": "smb",
  "port": 445,
  "auto_mount": true,
  "mount_timeout": 30,
  "enabled": true,
  "description": "Raspberry Pi storage server for media files",
  "sync_enabled": true
}
```

### Step 3: Test Network Connection
```bash
# Test SMB connection
smbclient -L //192.168.1.100 -U pi

# Mount network drive (Linux/Mac)
sudo mkdir -p /mnt/pi-nas
sudo mount -t cifs //192.168.1.100/media /mnt/pi-nas -o username=pi,password=your_password

# For Windows, map network drive to \\192.168.1.100\media
```

### Step 4: Configure Streamlit
```bash
# Create streamlit config
mkdir -p .streamlit
cat > .streamlit/config.toml << 'EOF'
[server]
headless = true
address = "0.0.0.0"
port = 5000

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
EOF
```

### Step 5: Start PI-NAS
```bash
# Start the application
streamlit run app.py --server.port 5000 --server.address 0.0.0.0

# Access at: http://localhost:5000
```

---

## Part 3: Advanced Configuration

### Automatic Mount on Computer Startup

#### Linux/Mac
```bash
# Add to /etc/fstab for permanent mounting
echo '//192.168.1.100/media /mnt/pi-nas cifs username=pi,password=your_password,uid=1000,gid=1000,iocharset=utf8 0 0' | sudo tee -a /etc/fstab

# Test mount
sudo mount -a
```

#### Windows
```batch
# Create batch file for auto-mount
@echo off
net use Z: \\192.168.1.100\media your_password /user:pi /persistent:yes
```

### Set Up as System Service

#### Linux (systemd)
```bash
# Create service file
sudo tee /etc/systemd/system/pi-nas.service << 'EOF'
[Unit]
Description=PI-NAS Media Server
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/pi-nas
ExecStart=/usr/bin/python3 -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable pi-nas
sudo systemctl start pi-nas
```

#### Windows (NSSM)
```batch
# Download NSSM (Non-Sucking Service Manager)
# Install PI-NAS as Windows service
nssm install "PI-NAS" "C:\Python39\Scripts\streamlit.exe" "run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true"
nssm set "PI-NAS" AppDirectory "C:\path\to\pi-nas"
nssm start "PI-NAS"
```

---

## Part 4: Performance Optimization

### Raspberry Pi Optimization
```bash
# Increase GPU memory split
sudo nano /boot/config.txt
# Add: gpu_mem=128

# Optimize for USB storage
echo 'vm.dirty_ratio = 15' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_background_ratio = 5' | sudo tee -a /etc/sysctl.conf

# USB storage optimization
echo 'options usb-storage quirks=152d:2329:u' | sudo tee -a /etc/modprobe.d/usb-storage-quirks.conf
```

### Network Performance
```bash
# On Pi: Optimize Samba performance
sudo nano /etc/samba/smb.conf

# Add to [global] section:
socket options = TCP_NODELAY IPTOS_LOWDELAY SO_RCVBUF=65536 SO_SNDBUF=65536
read raw = yes
write raw = yes
max xmit = 65536
dead time = 15
getwd cache = yes
```

### Computer Optimization
```bash
# Increase network buffer sizes (Linux)
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 87380 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 16777216' | sudo tee -a /etc/sysctl.conf
```

---

## Part 5: Monitoring and Maintenance

### Health Check Scripts
```bash
# Create monitoring script
cat > ~/check_pi_nas.sh << 'EOF'
#!/bin/bash

PI_IP="192.168.1.100"
MOUNT_POINT="/mnt/pi-nas"

# Check if Pi is reachable
if ping -c 1 $PI_IP >/dev/null 2>&1; then
    echo "✓ Raspberry Pi is reachable"
else
    echo "✗ Raspberry Pi is unreachable"
    exit 1
fi

# Check if mount point is accessible
if [ -d "$MOUNT_POINT" ] && [ "$(ls -A $MOUNT_POINT)" ]; then
    echo "✓ Storage is mounted and accessible"
else
    echo "✗ Storage mount failed"
    # Attempt to remount
    sudo mount -a
fi

# Check PI-NAS web interface
if curl -s http://localhost:5000 >/dev/null; then
    echo "✓ PI-NAS web interface is running"
else
    echo "✗ PI-NAS web interface is down"
fi
EOF

chmod +x ~/check_pi_nas.sh

# Run check every 5 minutes
echo "*/5 * * * * ~/check_pi_nas.sh" | crontab -
```

### Backup Strategy
```bash
# On Raspberry Pi: Create backup script
cat > ~/backup_pi_nas.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/mnt/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup of media files
tar -czf "$BACKUP_DIR/pi-nas-backup-$DATE.tar.gz" \
    /mnt/pi-nas-storage/media \
    --exclude='*/thumbnails/*' \
    --exclude='*/temp/*'

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x ~/backup_pi_nas.sh

# Schedule daily backups
echo "0 2 * * * ~/backup_pi_nas.sh" | crontab -
```

---

## Troubleshooting Common Issues

### Cannot Connect to Raspberry Pi
```bash
# Check network connectivity
ping 192.168.1.100

# Check if Samba is running
ssh pi@192.168.1.100 'sudo systemctl status smbd'

# Check firewall (if enabled)
ssh pi@192.168.1.100 'sudo ufw status'
```

### Mount Point Issues
```bash
# Check current mounts
mount | grep pi-nas

# Force unmount and remount
sudo umount /mnt/pi-nas
sudo mount -a

# Check fstab syntax
sudo mount -fav
```

### Performance Issues
```bash
# Check network speed
iperf3 -s  # On Pi
iperf3 -c 192.168.1.100  # On computer

# Check disk I/O
ssh pi@192.168.1.100 'iostat -x 1'

# Check Samba performance
smbclient //192.168.1.100/media -U pi -c 'allinfo .'
```

---

## Access Points

After setup completion:
- **PI-NAS Web Interface**: `http://your-computer-ip:5000`
- **Direct Pi Access**: `http://192.168.1.100` (if using OMV)
- **File Shares**: `\\192.168.1.100\media` (Windows) or `smb://192.168.1.100/media` (Mac/Linux)

This distributed setup gives you the best of both worlds - the power of your computer for the web interface and the reliability of a dedicated Pi for storage!