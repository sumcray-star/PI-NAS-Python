# Complete PI-NAS Media Server Setup Guide

This comprehensive guide will help you set up your PI-NAS media server with Raspberry Pi as network storage, creating a distributed Plex-like system.

## Architecture Overview

**Your Setup Will Work Like This:**
- **Computer**: Runs the web interface (powerful processing for streaming)
- **Raspberry Pi**: Handles file storage (24/7 dedicated NAS server)
- **Network**: Connects both devices for seamless file access

## Part 1: Raspberry Pi NAS Setup

### Step 1: Prepare Your Raspberry Pi

#### 1.1 Install Raspberry Pi OS
```bash
# Flash Raspberry Pi OS to SD card using Raspberry Pi Imager
# Enable SSH and set username/password during setup
```

#### 1.2 Initial Pi Configuration
```bash
# SSH into your Pi
ssh pi@your-pi-ip-address

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install samba samba-common-bin ntfs-3g exfat-fuse -y
```

### Step 2: Set Up Storage

#### 2.1 Connect External Storage (Optional)
```bash
# If using external USB drive, format it
sudo fdisk -l  # Find your drive (e.g., /dev/sda1)

# Create mount point
sudo mkdir /mnt/media-storage

# Mount the drive
sudo mount /dev/sda1 /mnt/media-storage

# Add to fstab for auto-mount
echo '/dev/sda1 /mnt/media-storage ntfs defaults,uid=1000,gid=1000 0 0' | sudo tee -a /etc/fstab
```

#### 2.2 Create Media Directories
```bash
# Create media folders
sudo mkdir -p /mnt/media-storage/media/{videos,images,audio,documents}
sudo chown -R pi:pi /mnt/media-storage/media
sudo chmod -R 755 /mnt/media-storage/media
```

### Step 3: Configure Samba (SMB) Sharing

#### 3.1 Edit Samba Configuration
```bash
# Backup original config
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.backup

# Edit Samba config
sudo nano /etc/samba/smb.conf
```

#### 3.2 Add Media Share Configuration
Add this to the end of `/etc/samba/smb.conf`:
```ini
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
```

#### 3.3 Set Up Samba User
```bash
# Add pi user to Samba
sudo smbpasswd -a pi
# Enter password when prompted (remember this!)

# Restart Samba services
sudo systemctl restart smbd
sudo systemctl restart nmbd

# Enable auto-start
sudo systemctl enable smbd
sudo systemctl enable nmbd
```

### Step 4: Configure Network and Security

#### 4.1 Set Static IP (Recommended)
```bash
# Edit dhcpcd config
sudo nano /etc/dhcpcd.conf

# Add at the end (adjust for your network):
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

#### 4.2 Configure Firewall
```bash
# Install UFW firewall
sudo apt install ufw -y

# Allow SSH
sudo ufw allow ssh

# Allow Samba
sudo ufw allow samba

# Enable firewall
sudo ufw enable
```

## Part 2: Computer Setup (Media Server)

### Step 1: Install PI-NAS Application

#### 1.1 Clone Repository
```bash
git clone https://github.com/sumcray-star/PI-NAS-Python.git
cd PI-NAS-Python
```

#### 1.2 Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install streamlit pandas pillow psutil requests opencv-python
```

#### 1.3 Start the Server
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Step 2: Configure Network Storage Connection

#### 2.1 Access PI-NAS Web Interface
1. Open browser: http://localhost:8501
2. Login with default credentials:
   - Username: `admin`
   - Password: `password`

#### 2.2 Configure Raspberry Pi Connection
1. Go to **Network Storage** page
2. Enter your Raspberry Pi details:
   - **Server IP**: `192.168.1.100` (your Pi's IP)
   - **Share Name**: `media`
   - **Username**: `pi`
   - **Password**: (your Samba password)
   - **Mount Point**: `/mnt/pi-nas` (Linux/Mac) or `Z:\` (Windows)

#### 2.3 Test Connection
1. Click **Test Connection**
2. If successful, click **Save Configuration**
3. Click **Mount Storage**

## Part 3: Using Your Media Server

### Step 1: Upload Media Files

#### 1.1 Using Web Interface
1. Go to **Upload Media** page
2. Drag and drop files or click to browse
3. Configure upload options:
   - ✅ Organize by file type
   - ✅ Generate thumbnails for videos
   - ✅ Sync to Raspberry Pi
4. Click **Upload Files**

#### 1.2 Direct Copy to Pi (Alternative)
```bash
# Copy files directly to Pi via network
scp /path/to/your/video.mp4 pi@192.168.1.100:/mnt/media-storage/media/videos/
```

### Step 2: Browse and Stream Media

#### 2.1 Media Library Features
- **Browse Files**: View all media organized by type
- **Search**: Find files by name
- **Filter**: Show only videos, images, or documents
- **Stream**: Play videos directly in browser
- **View Images**: Display photos with zoom
- **Download**: Save files to your computer

#### 2.2 Streaming Capabilities
- **Video Streaming**: Direct playback of MP4, AVI, MKV files
- **Image Viewing**: JPEG, PNG, GIF display with thumbnails
- **Audio Playback**: MP3, WAV, FLAC support
- **Document Preview**: PDF viewing capability

## Part 4: Advanced Configuration

### Step 1: Performance Optimization

#### 1.1 Raspberry Pi Optimization
```bash
# Increase GPU memory for better video handling
sudo nano /boot/config.txt
# Add: gpu_mem=128

# Optimize network performance
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
```

#### 1.2 Network Optimization
```bash
# On your computer, optimize SMB client settings
# Linux/Mac - Add to ~/.bashrc:
export SMB_CONF_PATH=/etc/samba/smb.conf

# Windows - Run as administrator:
# Set-SmbClientConfiguration -RequireSecuritySignature $false
```

### Step 2: Backup and Maintenance

#### 2.1 Automated Backup Script (Raspberry Pi)
```bash
# Create backup script
sudo nano /home/pi/backup-media.sh

#!/bin/bash
rsync -av /mnt/media-storage/media/ /mnt/backup-drive/media-backup/
echo "Backup completed: $(date)" >> /var/log/media-backup.log

# Make executable
sudo chmod +x /home/pi/backup-media.sh

# Add to crontab for daily backup
(crontab -l 2>/dev/null; echo "0 2 * * * /home/pi/backup-media.sh") | crontab -
```

#### 2.2 Health Monitoring
```bash
# Monitor disk space
df -h /mnt/media-storage

# Check Samba status
sudo systemctl status smbd

# View connection logs
sudo tail -f /var/log/samba/log.smbd
```

## Part 5: Troubleshooting Common Issues

### Issue 1: Cannot Connect to Raspberry Pi

**Solutions:**
```bash
# Check Pi is accessible
ping 192.168.1.100

# Test Samba service
smbclient -L //192.168.1.100 -U pi

# Check firewall
sudo ufw status

# Restart Samba
sudo systemctl restart smbd nmbd
```

### Issue 2: Slow File Transfer

**Solutions:**
```bash
# On Raspberry Pi - increase SMB buffer sizes
sudo nano /etc/samba/smb.conf
# Add under [global]:
socket options = TCP_NODELAY IPTOS_LOWDELAY SO_RCVBUF=65536 SO_SNDBUF=65536

# Restart Samba
sudo systemctl restart smbd
```

### Issue 3: Permission Errors

**Solutions:**
```bash
# Fix ownership on Pi
sudo chown -R pi:pi /mnt/media-storage/media
sudo chmod -R 755 /mnt/media-storage/media

# Reset Samba password
sudo smbpasswd -a pi
```

### Issue 4: Mount Point Issues

**Solutions:**
```bash
# Unmount and remount
sudo umount /mnt/pi-nas
sudo mount -t cifs //192.168.1.100/media /mnt/pi-nas -o username=pi,password=your-password

# Check mount status
mount | grep cifs
```

## Part 6: Security Best Practices

### Step 1: Secure Your Setup

#### 1.1 Change Default Passwords
```bash
# Change Pi user password
sudo passwd pi

# Update Samba password
sudo smbpasswd -a pi

# Change PI-NAS admin password (in web interface)
# Go to Settings > Account > Change Password
```

#### 1.2 Network Security
```bash
# Configure UFW firewall rules
sudo ufw allow from 192.168.1.0/24 to any port 445
sudo ufw deny 445

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
```

### Step 2: Access Control

#### 2.1 Create Additional Users
```bash
# Add new system user
sudo adduser mediauser

# Add to Samba
sudo smbpasswd -a mediauser

# Create restricted share for specific user
# Edit /etc/samba/smb.conf and add user-specific shares
```

## Part 7: Maintenance and Updates

### Regular Maintenance Tasks

#### Weekly Tasks
- Check disk space: `df -h`
- Review logs: `sudo tail /var/log/samba/log.smbd`
- Test backup: verify backup files exist

#### Monthly Tasks
- Update Pi: `sudo apt update && sudo apt upgrade`
- Update PI-NAS: `git pull origin main`
- Check network performance: `iperf3 -c 192.168.1.100`

#### Quarterly Tasks
- Replace SD card if showing wear
- Review and rotate backup media
- Update passwords and security settings

## Success Indicators

Your setup is working correctly when:
- ✅ You can access PI-NAS web interface at http://localhost:8501
- ✅ Network Storage shows "Connected" status
- ✅ You can upload files through the web interface
- ✅ Files appear in Raspberry Pi storage directories
- ✅ Media Library displays your uploaded content
- ✅ Videos stream smoothly without buffering
- ✅ Images load quickly with thumbnails

## Support and Resources

- **GitHub Repository**: https://github.com/sumcray-star/PI-NAS-Python
- **Raspberry Pi Documentation**: https://www.raspberrypi.org/documentation/
- **Samba Configuration**: https://www.samba.org/samba/docs/
- **Streamlit Documentation**: https://docs.streamlit.io/

Your PI-NAS media server is now ready for use as a distributed Plex-like system!