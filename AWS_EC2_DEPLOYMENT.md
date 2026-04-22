# AWS EC2 Docker Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS EC2 Setup](#aws-ec2-setup)
3. [Docker Deployment](#docker-deployment)
4. [Raspberry Pi Connection](#raspberry-pi-connection)
5. [Maintenance](#maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### AWS Account
- ✅ Free Tier eligible AWS account
- ✅ AWS Management Console access
- ✅ EC2 key pair created

### Local Tools
- Git
- SSH client
- Docker (for testing locally)

---

## AWS EC2 Setup

### Step 1: Launch EC2 Instance

#### Via AWS Console:

1. **Go to EC2 Dashboard:**
   - Log in to AWS Console
   - Search for "EC2"
   - Click "Instances" → "Launch Instances"

2. **Configure Instance:**
   - **Name:** `pi-media-server`
   - **AMI:** Ubuntu 22.04 LTS (Free Tier eligible)
   - **Instance Type:** `t2.micro` (Free Tier)
   - **Key Pair:** Create or select existing
   - **Storage:** 30 GB (Free Tier limit)

3. **Security Group Settings:**
   - Create new security group: `streamlit-sg`
   - **Inbound Rules:**
     ```
     Rule 1: HTTP   | Port 80   | 0.0.0.0/0  (for domain redirect)
     Rule 2: HTTPS  | Port 443  | 0.0.0.0/0  (optional, for SSL)
     Rule 3: Custom | Port 8501 | 0.0.0.0/0  (Streamlit)
     Rule 4: SSH    | Port 22   | YOUR_IP    (your home IP)
     ```

4. **Launch Instance**
   - Review and click "Launch Instance"
   - Wait 1-2 minutes for startup

#### Or Via AWS CLI:
```bash
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t2.micro \
  --key-name your-key-pair \
  --security-groups streamlit-sg \
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=30}" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=pi-media-server}]"
```

### Step 2: Connect to Instance

#### Get Public IP:
```bash
aws ec2 describe-instances --filters "Name=tag:Name,Values=pi-media-server" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```

#### SSH Connection:
```bash
# Linux/Mac
ssh -i /path/to/your-key.pem ubuntu@YOUR_PUBLIC_IP

# Windows (PowerShell)
ssh -i C:\path\to\your-key.pem ubuntu@YOUR_PUBLIC_IP
```

---

## Docker Deployment

### Step 1: Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### Step 2: Install Docker & Docker Compose
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (no sudo needed)
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 3: Clone Repository
```bash
# Clone your GitHub repo
git clone https://github.com/YOUR_USERNAME/PiMediaServer.git
cd PiMediaServer
```

### Step 4: Create Directories for Persistent Storage
```bash
mkdir -p data config media/uploads media/thumbnails logs temp
chmod 777 data config media logs temp
```

### Step 5: Build & Run Docker Container
```bash
# Build image
sudo docker-compose build

# Run container
sudo docker-compose up -d

# Check logs
sudo docker-compose logs -f

# Stop container
sudo docker-compose down
```

### Step 6: Access Your Application
```
Open browser: http://YOUR_PUBLIC_IP:8501
```

---

## Raspberry Pi Connection

### Option A: Same Local Network (EASIEST)

If your Raspberry Pi is on the **same LAN** as the EC2 instance:

#### 1. Set up Samba on Raspberry Pi
```bash
# SSH into Pi
ssh pi@raspberry-pi-ip

# Install Samba
sudo apt-get install samba samba-common-bin

# Create shared folder
mkdir -p /home/pi/shared_media
chmod 777 /home/pi/shared_media

# Edit Samba config
sudo nano /etc/samba/smb.conf

# Add at the end:
[media]
   path = /home/pi/shared_media
   writeable = yes
   browseable = yes
   read only = no
   guest ok = no
```

#### 2. Set Samba password
```bash
sudo smbpasswd -a pi
```

#### 3. Update Docker Compose Environment
Edit `docker-compose.yml`:
```yaml
environment:
  PI_SERVER_IP: "192.168.1.100"      # Your Pi's IP
  PI_SHARE_NAME: "media"
  PI_USERNAME: "pi"
  PI_MOUNT_POINT: "/mnt/pi-nas"
```

#### 4. Modify `utils/network_storage.py` for EC2
```python
# Change from: subprocess.run(['sudo', 'mount', ...])
# To: Non-sudo mount on EC2

# Add to docker-compose.yml caps section:
cap_add:
  - SYS_ADMIN
privileged: true
```

---

### Option B: Over Internet (VPN - ADVANCED)

If Pi is on different network (home WiFi):

#### 1. Install WireGuard on Pi
```bash
sudo apt-get install wireguard wireguard-tools
```

#### 2. Install WireGuard on EC2
```bash
sudo apt-get install wireguard wireguard-tools
```

#### 3. Generate Keys & Configure
```bash
# On Pi
wg genkey | tee privatekey | wg pubkey > publickey

# On EC2
wg genkey | tee privatekey | wg pubkey > publickey
```

#### 4. Share Keys & Configure Tunnel
(Detailed WireGuard setup beyond scope - see [WireGuard docs](https://www.wireguard.com/quickstart/))

---

## Maintenance

### View Logs
```bash
# Real-time logs
sudo docker-compose logs -f

# Last 100 lines
sudo docker-compose logs --tail=100
```

### Restart Application
```bash
sudo docker-compose restart
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
sudo docker-compose up -d --build
```

### Monitor Resources
```bash
# Check container stats
docker stats

# Check disk usage
df -h

# Check memory
free -h
```

### Backup Data
```bash
# Backup user data
tar -czf backup-data.tar.gz data/ config/

# Download to local
scp -i key.pem ubuntu@YOUR_IP:backup-data.tar.gz .
```

### Enable Auto-start on Reboot
```bash
# Create systemd service
sudo nano /etc/systemd/system/docker-compose-app.service
```

```ini
[Unit]
Description=PI-NAS Media Server
Requires=docker.service
After=docker.service

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/PiMediaServer
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable service
sudo systemctl daemon-reload
sudo systemctl enable docker-compose-app.service
sudo systemctl start docker-compose-app.service
```

---

## Troubleshooting

### Issue: Port 8501 Not Accessible
```bash
# Check if container is running
docker ps

# Check security group
aws ec2 describe-security-groups --group-names streamlit-sg

# Test port locally
curl http://localhost:8501
```

### Issue: Out of Memory
```bash
# EC2 t2.micro only has 1GB RAM
# Solutions:
# 1. Reduce container memory limit in docker-compose.yml
# 2. Disable thumbnail generation
# 3. Upgrade to t3.small (paid)
```

### Issue: Cannot Connect to Raspberry Pi
```bash
# Check network connectivity
ping 192.168.1.100

# Test SMB port
telnet 192.168.1.100 445

# Check Pi's Samba status
ssh pi@192.168.1.100 'systemctl status smbd'
```

### Issue: Disk Space Full (30GB limit)
```bash
# Check disk usage
df -h

# Clean old logs
rm logs/*.log

# Remove old thumbnails
rm -rf media/thumbnails/*

# Restart container
sudo docker-compose restart
```

### Issue: High CPU Usage
```bash
# Monitor processes
docker stats

# Reduce concurrent uploads in Settings
# Disable thumbnail generation for temporary relief
```

---

## Cost Monitoring

### AWS Free Tier Calculator:
```
t2.micro EC2:
- Monthly hours: 750 (free)
- 24/7 usage: ~730 hours = FREE

Data Transfer:
- Outbound: 1 GB/month free
- Each GB over: $0.09

Estimated costs:
Light use (<1GB data): $0/month
Medium use (5GB data): $0.36/month + potential t2 burst fee
Heavy use (20GB data): $1.71/month + usage fees
```

### Setup AWS Billing Alerts:
1. Go to AWS Billing
2. Set budget alert at $5/month
3. Receive email if exceeded

---

## Optimization Tips

### For t2.micro Performance:
1. **Disable unnecessary features:**
   ```python
   # In app.py
   generate_thumbnails = False  # Disable during off-peak
   ```

2. **Limit concurrent uploads:**
   - Restrict to 1 file at a time
   - Set max file size to 50MB

3. **Cache frequently accessed data:**
   - Use Streamlit @st.cache
   - Add Redis caching layer

4. **Monitor burst credits:**
   ```bash
   aws ec2 describe-spot-price-history --instance-types t2.micro
   ```

---

## Next Steps

1. ✅ Launch EC2 instance
2. ✅ Deploy Docker container
3. ✅ Configure Raspberry Pi connection
4. ✅ Set up monitoring & backups
5. ✅ Monitor costs

**Estimated setup time:** 20-30 minutes

---

## Useful Commands Reference

```bash
# Container management
docker-compose up -d                 # Start in background
docker-compose down                  # Stop container
docker-compose restart               # Restart
docker-compose ps                    # Show status
docker-compose logs -f               # View logs

# System info
docker ps -a                         # List containers
docker images                        # List images
docker stats                         # Monitor resources
df -h                               # Disk space
free -h                             # Memory usage

# Git operations
git pull                            # Update code
git add .                           # Stage changes
git commit -m "message"             # Commit
git push                            # Push to GitHub

# SSH connection
ssh -i key.pem ubuntu@IP            # Connect to EC2
scp -i key.pem file ubuntu@IP:.     # Upload file
scp -i key.pem ubuntu@IP:file .     # Download file
```

---

## Support & Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Docker Docs:** https://docs.docker.com
- **AWS Free Tier:** https://aws.amazon.com/free
- **Ubuntu Server Guide:** https://ubuntu.com/server/docs

---

**Happy Hosting! 🚀**
