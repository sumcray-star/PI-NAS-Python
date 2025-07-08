# YouTube Video Companion Guide for PI-NAS

## Overview
This guide complements popular YouTube Raspberry Pi NAS setup tutorials by providing PI-NAS specific steps and configurations that work alongside common video tutorials.

## Before You Start

### Video Tutorial Compatibility
Our PI-NAS application works with most Raspberry Pi NAS setups that include:
- OpenMediaVault (OMV) - Most common in tutorials
- Samba file sharing setup
- SSH access configuration
- Network storage mounting

### What Makes PI-NAS Different
While video tutorials typically show basic file sharing, PI-NAS adds:
- **Web-based media management interface** (like Plex)
- **User authentication system**
- **File upload and organization**
- **Thumbnail generation for videos**
- **Streaming capabilities**
- **Network storage integration**

---

## Following Along with Video Tutorials

### Step 1: Complete the Basic Setup First
Follow your YouTube video for:
1. ✅ Raspberry Pi OS installation
2. ✅ SSH setup and initial configuration
3. ✅ External drive mounting
4. ✅ OpenMediaVault installation (if covered)
5. ✅ Basic Samba sharing setup

### Step 2: Note Down These Details
While following the video, record:
```
Raspberry Pi IP: ________________
Username: _____________________
SMB Share Name: _______________
Mount Point: __________________
```

### Step 3: Install PI-NAS on Top
After completing the video setup, run these commands:

```bash
# Download PI-NAS
git clone https://github.com/[USERNAME]/pi-nas.git
cd pi-nas

# Install dependencies
pip install streamlit pandas pillow psutil requests opencv-python

# Configure for your setup
cp config/storage_config.json.template config/storage_config.json
nano config/storage_config.json
```

Update the configuration with your video setup details:
```json
{
  "server_ip": "YOUR_PI_IP_FROM_VIDEO",
  "share_name": "YOUR_SHARE_NAME_FROM_VIDEO", 
  "username": "YOUR_USERNAME_FROM_VIDEO",
  "mount_point": "/mnt/pi-nas",
  "protocol": "smb",
  "enabled": true
}
```

---

## Common Video Tutorial Scenarios

### Scenario 1: OMV-Based Tutorial
If your video uses OpenMediaVault:
```bash
# Your video likely covered:
# - OMV web interface at http://PI_IP
# - Creating shared folders
# - Setting up SMB shares
# - User management

# Add PI-NAS integration:
./scripts/mount_network_drive.sh mount
streamlit run app.py --server.port 5000 --server.address 0.0.0.0
```

### Scenario 2: Basic Samba Tutorial  
If your video shows simple Samba setup:
```bash
# Your video likely covered:
# - Installing samba
# - Editing /etc/samba/smb.conf
# - Creating samba users
# - Restarting samba service

# Test the connection:
smbclient -L //YOUR_PI_IP -U YOUR_USERNAME

# Configure PI-NAS to use this setup
```

### Scenario 3: Docker-Based Tutorial
If your video uses Docker containers:
```bash
# Your video likely used docker-compose
# PI-NAS can run alongside in its own container

# Create PI-NAS container
docker run -d \
  --name pi-nas \
  -p 5000:5000 \
  -v /path/to/media:/app/media \
  pi-nas:latest
```

---

## Troubleshooting Video Tutorial Issues

### Issue: Can't Access Shares After Video
```bash
# Check if samba is running
sudo systemctl status smbd

# Check your configuration
sudo testparm

# Verify network connectivity
ping YOUR_PI_IP
```

### Issue: Permission Problems
```bash
# Fix common permission issues
sudo chown -R pi:pi /mnt/YOUR_MOUNT_POINT
sudo chmod -R 755 /mnt/YOUR_MOUNT_POINT

# Add user to required groups
sudo usermod -a -G www-data pi
```

### Issue: Network Mount Fails
```bash
# Install required packages (often missed in videos)
sudo apt install cifs-utils smbclient

# Test manual mount
sudo mount -t cifs //PI_IP/SHARE_NAME /mnt/test \
  -o username=YOUR_USER,password=YOUR_PASS
```

---

## Enhancing Your Video Tutorial Setup

### Add Remote Access (Beyond Video Scope)
Most videos only show local access. Add global access:

```bash
# Install nginx reverse proxy
sudo apt install nginx

# Configure domain (optional)
# Follow our network_configuration.md guide

# Add SSL certificate
sudo certbot --nginx -d yourdomain.com
```

### Add Automatic Mounting
Video tutorials often show manual mounting. Make it automatic:

```bash
# Edit fstab for permanent mounting
sudo nano /etc/fstab

# Add line:
//PI_IP/SHARE_NAME /mnt/pi-nas cifs username=USER,password=PASS,uid=1000,gid=1000,iocharset=utf8 0 0
```

### Add Monitoring (Advanced)
```bash
# Install monitoring tools
sudo apt install htop iotop

# Add PI-NAS health monitoring
./scripts/setup_monitoring.sh
```

---

## Video Tutorial Compatibility Matrix

| Tutorial Type | PI-NAS Compatibility | Additional Steps Needed |
|---------------|---------------------|------------------------|
| Basic Samba | ✅ Full | Configure storage_config.json |
| OpenMediaVault | ✅ Full | Use OMV web interface credentials |
| Nextcloud | ⚠️ Partial | Manual WebDAV configuration |
| Docker-based | ✅ Full | Run PI-NAS in separate container |
| USB Direct | ⚠️ Limited | No network storage features |

---

## Quick Commands Reference

### After Completing Video Tutorial
```bash
# Test your setup works
ping YOUR_PI_IP
smbclient -L //YOUR_PI_IP

# Install PI-NAS
git clone https://github.com/[USERNAME]/pi-nas.git
cd pi-nas
pip install -r requirements.txt

# Configure and start
cp config/storage_config.json.template config/storage_config.json
# Edit config file with your video setup details
streamlit run app.py --server.port 5000
```

### Access Your Enhanced NAS
- **Basic file access**: `\\YOUR_PI_IP\SHARE_NAME` (from video)
- **PI-NAS web interface**: `http://YOUR_PI_IP:5000` (new!)
- **OMV interface**: `http://YOUR_PI_IP` (if using OMV)

---

## Next Steps After Video Tutorial

1. **✅ Complete your video tutorial** - Get basic NAS working
2. **🔧 Install PI-NAS** - Add web interface and media features  
3. **🌐 Add remote access** - Follow our network configuration guide
4. **🔒 Enhance security** - Use our security hardening guide
5. **📱 Access from anywhere** - Set up domain and SSL

## Getting Help

If you run into issues combining your video tutorial with PI-NAS:

1. **Check video tutorial first** - Ensure basic NAS functionality works
2. **Test network connectivity** - Verify you can access shares
3. **Check PI-NAS logs** - Look for connection errors
4. **Review our troubleshooting guide** - Common solutions provided

Most YouTube tutorials get you 70% of the way to a functional NAS. PI-NAS adds the missing 30% for a truly professional media server experience!