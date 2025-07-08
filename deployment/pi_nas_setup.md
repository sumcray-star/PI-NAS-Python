# PI-NAS Complete Setup and Deployment Guide

## Overview
PI-NAS is a Plex-like media server application built with Streamlit that provides media library management, file upload capabilities, streaming functionality, and integration with Raspberry Pi OpenMediaVault (OMV) for network storage. This guide covers the complete setup from Raspberry Pi configuration to global deployment.

## Table of Contents
1. [Raspberry Pi Setup with OMV](#raspberry-pi-setup)
2. [PI-NAS Application Installation](#application-installation)
3. [Database Configuration](#database-configuration)
4. [GitHub Deployment](#github-deployment)
5. [Server Configuration](#server-configuration)
6. [Global Access Setup](#global-access-setup)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

---

## 1. Raspberry Pi Setup with OMV {#raspberry-pi-setup}

### Hardware Requirements
- Raspberry Pi 4 Model B (4GB RAM recommended, 8GB for heavy use)
- MicroSD card (64GB minimum, Class 10 or U3)
- External USB 3.0 hard drive or SSD (1TB+ recommended)
- Ethernet cable (for stable connection)
- Official Raspberry Pi 4 power supply

### Step 1.1: Install OpenMediaVault
```bash
# Download Raspberry Pi Imager
# Visit: https://www.raspberrypi.org/software/

# Flash OMV to SD card:
# 1. Download OMV image from: https://www.openmediavault.org/download
# 2. Use Raspberry Pi Imager to flash OMV image to SD card
# 3. Enable SSH in advanced options before flashing
```

### Step 1.2: Initial OMV Configuration
```bash
# First boot - connect via SSH
ssh root@[PI_IP_ADDRESS]
# Default password: openmediavault

# Change default password immediately
passwd

# Update system
apt update && apt upgrade -y

# Configure timezone
timedatectl set-timezone [YOUR_TIMEZONE]
# Example: timedatectl set-timezone America/New_York
```

### Step 1.3: OMV Web Interface Setup
1. Access OMV web interface: `http://[PI_IP_ADDRESS]`
2. Login with: admin / openmediavault
3. Change admin password immediately
4. Go to **System → General Settings** and configure:
   - Web Administrator Password
   - Time Zone
   - NTP Servers

### Step 1.4: Storage Configuration
```bash
# Connect external drive and configure in OMV:
# 1. Go to Storage → File Systems
# 2. Select your external drive
# 3. Create file system (ext4 recommended)
# 4. Mount the file system
```

### Step 1.5: SMB/CIFS Share Setup
1. **Storage → Shared Folders**: Create folder named "Media"
2. **Services → SMB/CIFS → Settings**:
   - Enable SMB/CIFS
   - Workgroup: WORKGROUP
   - Extra options: `min protocol = SMB2`
3. **Services → SMB/CIFS → Shares**: Add Media share
4. **Access Rights Management → User**: Create media user
5. **Services → SMB/CIFS → Shares**: Set permissions for media user

---

## 2. PI-NAS Application Installation {#application-installation}

### Step 2.1: Server Prerequisites
```bash
# On your server machine (can be same Pi or different server)
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8+
sudo apt install python3 python3-pip python3-venv git -y

# Install system dependencies for SMB mounting
sudo apt install cifs-utils smbclient -y

# Install optional dependencies for thumbnails
sudo apt install ffmpeg -y
```

### Step 2.2: Download PI-NAS
```bash
# Clone from your repository
git clone https://github.com/[USERNAME]/pi-nas.git
cd pi-nas

# Or download and extract files
mkdir -p /opt/pi-nas
cd /opt/pi-nas
# Copy PI-NAS files here
```

### Step 2.3: Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install streamlit pandas pillow psutil requests opencv-python

# Make scripts executable
chmod +x scripts/*.sh
```

### Step 2.4: Initial Configuration
```bash
# Run initial setup
./scripts/start_pinas.sh setup

# Start PI-NAS
./scripts/start_pinas.sh start
```

---

## 3. Database Configuration {#database-configuration}

### Step 3.1: User Authentication Setup
The application uses JSON-based user storage by default. For production use:

```bash
# The first registered user automatically becomes admin
# Users are stored in: data/users.json
# Sessions use Streamlit's session state

# For enhanced security, consider migrating to SQLite:
# 1. Install SQLite support
pip install sqlite3

# 2. Create database migration script
cat > migrate_to_sqlite.py << 'EOF'
import json
import sqlite3
from pathlib import Path

def migrate_users():
    # Create SQLite database
    conn = sqlite3.connect('data/users.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            last_login TEXT
        )
    ''')
    
    # Migrate from JSON
    if Path('data/users.json').exists():
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        
        for username, data in users.items():
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (username, password, created_at, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (username, data['password'], data['created_at'], data.get('is_admin', False)))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_users()
    print("Migration completed successfully!")
EOF

# Run migration
python migrate_to_sqlite.py
```

### Step 3.2: Network Storage Database
```bash
# Network storage configuration is stored in: config/storage_config.json
# Configure your OMV connection:
cat > config/storage_config.json << 'EOF'
{
  "server_ip": "192.168.1.100",
  "share_name": "Media",
  "username": "media",
  "mount_point": "/mnt/pi-nas",
  "protocol": "smb",
  "port": 445,
  "auto_mount": true,
  "mount_timeout": 30,
  "enabled": true
}
EOF
```

---

## 4. GitHub Deployment {#github-deployment}

### Step 4.1: Repository Setup
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial PI-NAS commit"

# Create repository on GitHub and push
git remote add origin https://github.com/[USERNAME]/pi-nas.git
git branch -M main
git push -u origin main
```

### Step 4.2: Environment Variables
```bash
# Create .env file for secrets (don't commit this)
cat > .env << 'EOF'
SMB_PASSWORD=your_smb_password
SECRET_KEY=your_secret_key_for_sessions
ADMIN_EMAIL=admin@yourdomain.com
EOF

# Add .env to .gitignore
echo ".env" >> .gitignore
echo "data/users.json" >> .gitignore
echo "*.log" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "venv/" >> .gitignore
```

### Step 4.3: GitHub Actions for CI/CD
```bash
mkdir -p .github/workflows
cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy PI-NAS

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install streamlit pandas pillow psutil requests
    - name: Test application
      run: |
        python -c "import app; print('App imports successfully')"

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to server
      run: |
        echo "Add your deployment script here"
        # ssh deploy@yourserver.com 'cd /opt/pi-nas && git pull && ./scripts/start_pinas.sh restart'
EOF
```

---

## 5. Server Configuration {#server-configuration}

### Step 5.1: Production Server Setup
```bash
# Install as system service
sudo ./scripts/start_pinas.sh install

# Configure firewall
sudo ufw allow 5000/tcp
sudo ufw enable

# Setup reverse proxy with Nginx
sudo apt install nginx -y

# Configure Nginx
sudo tee /etc/nginx/sites-available/pi-nas << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/pi-nas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5.2: SSL Certificate Setup
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Step 5.3: Performance Optimization
```bash
# Configure Streamlit for production
cat >> .streamlit/config.toml << 'EOF'

[server]
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 2000

[browser]
gatherUsageStats = false

[logger]
level = "warning"
EOF
```

---

## 6. Global Access Setup {#global-access-setup}

### Step 6.1: Dynamic DNS Setup
```bash
# Install ddclient for dynamic DNS
sudo apt install ddclient -y

# Configure for your DNS provider
sudo nano /etc/ddclient.conf
# Example for Cloudflare:
# protocol=cloudflare
# use=web
# login=your-email@domain.com
# password=your-api-key
# zone=yourdomain.com
# your-subdomain.yourdomain.com

# Start ddclient
sudo systemctl enable ddclient
sudo systemctl start ddclient
```

### Step 6.2: Router Configuration
```bash
# Port forwarding setup (configure in router admin):
# External Port: 80 → Internal Port: 80 (Nginx)
# External Port: 443 → Internal Port: 443 (Nginx SSL)
# External Port: 5000 → Internal Port: 5000 (Direct access if needed)

# Optional: VPN setup for secure access
# Install WireGuard
sudo apt install wireguard -y

# Generate server keys
wg genkey | tee /etc/wireguard/privatekey | wg pubkey > /etc/wireguard/publickey

# Configure WireGuard server
sudo tee /etc/wireguard/wg0.conf << 'EOF'
[Interface]
PrivateKey = [SERVER_PRIVATE_KEY]
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = [CLIENT_PUBLIC_KEY]
AllowedIPs = 10.0.0.2/32
EOF
```

### Step 6.3: Domain and CDN Setup
```bash
# Cloudflare setup for global CDN:
# 1. Add domain to Cloudflare
# 2. Update nameservers
# 3. Create A record pointing to your server IP
# 4. Enable proxy for CDN benefits

# Monitor setup with Uptime Robot or similar:
# Monitor: http://your-domain.com/
# Alert email: your-email@domain.com
```

---

## 7. Security Considerations {#security-considerations}

### Step 7.1: Security Hardening
```bash
# SSH hardening
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no
# Port 2222

# Fail2ban setup
sudo apt install fail2ban -y
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 2222

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 6
EOF

sudo systemctl restart fail2ban
```

### Step 7.2: Application Security
```bash
# Rate limiting in application
pip install streamlit-authenticator

# Session management
cat >> utils/auth.py << 'EOF'

import streamlit as st
import time

def check_rate_limit():
    if 'last_login_attempt' not in st.session_state:
        st.session_state.last_login_attempt = 0
        st.session_state.login_attempts = 0
    
    current_time = time.time()
    if current_time - st.session_state.last_login_attempt < 60:
        if st.session_state.login_attempts >= 3:
            return False
    else:
        st.session_state.login_attempts = 0
    
    return True
EOF
```

---

## 8. Troubleshooting {#troubleshooting}

### Common Issues and Solutions

#### Issue: Cannot mount SMB share
```bash
# Check connectivity
ping [OMV_IP]
telnet [OMV_IP] 445

# Check credentials
smbclient -L //[OMV_IP] -U [username]

# Check mount permissions
sudo dmesg | grep -i cifs
```

#### Issue: Streamlit not accessible externally
```bash
# Check if service is running
sudo systemctl status pi-nas

# Check port binding
netstat -tlnp | grep 5000

# Check firewall
sudo ufw status
```

#### Issue: SSL certificate problems
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Check Nginx configuration
sudo nginx -t
```

#### Issue: Performance problems
```bash
# Monitor resources
htop
df -h
iostat -x 1

# Check logs
tail -f logs/pinas.log
tail -f logs/pinas_error.log

# Optimize Streamlit
echo "server.maxUploadSize = 1000" >> .streamlit/config.toml
```

### Monitoring and Maintenance
```bash
# Create monitoring script
cat > scripts/monitor.sh << 'EOF'
#!/bin/bash

# Check PI-NAS service
if ! systemctl is-active --quiet pi-nas; then
    echo "PI-NAS service is down, restarting..."
    sudo systemctl restart pi-nas
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "Disk usage critical: ${DISK_USAGE}%"
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    echo "Memory usage high: ${MEM_USAGE}%"
fi
EOF

chmod +x scripts/monitor.sh

# Add to crontab
echo "*/5 * * * * /opt/pi-nas/scripts/monitor.sh" | crontab -
```

---

## Quick Start Summary

1. **Setup OMV on Raspberry Pi** (30 minutes)
2. **Install PI-NAS application** (15 minutes)
3. **Configure network storage connection** (10 minutes)
4. **Deploy to GitHub** (10 minutes)
5. **Setup domain and SSL** (20 minutes)
6. **Configure global access** (15 minutes)

**Total setup time: ~2 hours**

For support and updates, visit: https://github.com/[USERNAME]/pi-nas
