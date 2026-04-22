# Docker & AWS Quick Reference Card

## Docker Compose Commands

### Basic Operations
```bash
# Start application (foreground)
docker-compose up

# Start in background
docker-compose up -d

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Rebuild image
docker-compose build

# Rebuild without cache
docker-compose build --no-cache

# Show status
docker-compose ps
```

### Logging & Debugging
```bash
# View logs (follow)
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific service
docker-compose logs streamlit

# View logs with timestamps
docker-compose logs -f --timestamps
```

### Container Management
```bash
# Execute command in running container
docker-compose exec streamlit bash

# Access container shell
docker exec -it pi-media-server bash

# Copy file from container
docker cp pi-media-server:/app/data/users.json ./

# Inspect container
docker inspect pi-media-server

# View container stats
docker stats
```

### Data & Volumes
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect volume_name

# Remove unused volumes
docker volume prune

# Remove all data (CAREFUL!)
docker-compose down -v
```

---

## AWS EC2 Commands

### Instance Management
```bash
# List running instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"

# Start instance
aws ec2 start-instances --instance-ids i-1234567890abcdef0

# Stop instance
aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# Reboot instance
aws ec2 reboot-instances --instance-ids i-1234567890abcdef0

# Terminate instance (IRREVERSIBLE)
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0

# Get public IP
aws ec2 describe-instances --filters "Name=tag:Name,Values=pi-media-server" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```

### Security Groups
```bash
# List security groups
aws ec2 describe-security-groups

# Authorize port
aws ec2 authorize-security-group-ingress \
  --group-id sg-1234567890abcdef0 \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0

# Revoke port
aws ec2 revoke-security-group-ingress \
  --group-id sg-1234567890abcdef0 \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0
```

### EBS (Storage)
```bash
# List volumes
aws ec2 describe-volumes

# Create snapshot
aws ec2 create-snapshot --volume-id vol-1234567890abcdef0 --description "Backup"

# List snapshots
aws ec2 describe-snapshots --owner-ids self
```

---

## SSH & File Transfer

### SSH Connection
```bash
# Connect to EC2
ssh -i /path/to/key.pem ubuntu@YOUR_PUBLIC_IP

# Connect with verbose output
ssh -vvv -i /path/to/key.pem ubuntu@YOUR_PUBLIC_IP

# Port forwarding (local)
ssh -i key.pem -L 8501:localhost:8501 ubuntu@YOUR_PUBLIC_IP

# Port forwarding (remote)
ssh -i key.pem -R 8501:localhost:8501 ubuntu@YOUR_PUBLIC_IP
```

### File Transfer (SCP)
```bash
# Upload file
scp -i key.pem ./file.txt ubuntu@YOUR_PUBLIC_IP:/home/ubuntu/

# Download file
scp -i key.pem ubuntu@YOUR_PUBLIC_IP:/home/ubuntu/file.txt ./

# Upload directory
scp -i key.pem -r ./directory ubuntu@YOUR_PUBLIC_IP:/home/ubuntu/

# Download directory
scp -i key.pem -r ubuntu@YOUR_PUBLIC_IP:/home/ubuntu/directory ./
```

---

## System Commands (On EC2)

### System Info
```bash
# OS Information
lsb_release -a
cat /etc/os-release

# Memory usage
free -h

# Disk usage
df -h

# CPU information
nproc
top
htop (if installed)

# Uptime
uptime
```

### Package Management
```bash
# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install package
sudo apt-get install package-name

# Remove package
sudo apt-get remove package-name

# List installed packages
apt list --installed
```

### Process Management
```bash
# List processes
ps aux

# Kill process
kill -9 PID

# Monitor processes
top
htop

# Background process
command &
```

### Network
```bash
# Check IP address
ip addr show
hostname -I

# Ping
ping 8.8.8.8

# DNS lookup
nslookup example.com
dig example.com

# Network stats
netstat -tlnp
ss -tlnp

# Open ports
sudo lsof -i -P -n | grep LISTEN
```

---

## Common Workflows

### Deploy New Version
```bash
# SSH to EC2
ssh -i key.pem ubuntu@YOUR_IP

# Navigate to app
cd PiMediaServer

# Pull latest code
git pull

# Rebuild and restart
sudo docker-compose up -d --build

# Check status
sudo docker-compose ps
```

### Backup Data
```bash
# On EC2
tar -czf backup-$(date +%Y%m%d).tar.gz data/ config/

# Download backup
scp -i key.pem ubuntu@YOUR_IP:~/backup-*.tar.gz ./
```

### Monitor Application
```bash
# SSH to EC2
ssh -i key.pem ubuntu@YOUR_IP

# View logs
cd PiMediaServer
docker-compose logs -f

# Monitor resources
docker stats

# Check disk
df -h
```

### Restart Application
```bash
# SSH to EC2
ssh -i key.pem ubuntu@YOUR_IP

# Quick restart
cd PiMediaServer
sudo docker-compose restart

# Full rebuild restart
sudo docker-compose up -d --build
```

---

## Troubleshooting Commands

### Check Docker Status
```bash
# Service status
sudo systemctl status docker

# Restart Docker service
sudo systemctl restart docker

# Docker logs
sudo journalctl -u docker -f
```

### View Application Logs
```bash
# Full logs
sudo docker-compose logs

# Last 50 lines
sudo docker-compose logs --tail=50

# Logs with timestamps
sudo docker-compose logs --timestamps

# Specific service
sudo docker-compose logs streamlit
```

### Check Port Usage
```bash
# List listening ports
sudo lsof -i -P -n | grep LISTEN

# Check specific port
sudo lsof -i :8501

# Check with netstat
sudo netstat -tlnp | grep 8501
```

### Network Diagnostics
```bash
# Test connectivity to Pi
ping 192.168.1.100

# Test port connectivity
telnet 192.168.1.100 445

# DNS test
nslookup google.com

# Trace route
traceroute example.com
```

### Disk Space Issues
```bash
# Check disk usage
du -sh *
du -sh /app

# Find large files
find . -type f -size +100M

# Clean Docker
docker system prune -a

# Remove old logs
sudo journalctl --vacuum=50M
```

---

## Performance Tuning

### Monitor Resource Usage
```bash
# Real-time stats
docker stats --no-stream

# Memory
free -h
vmstat 1 5

# CPU
top
mpstat 1 5

# Disk I/O
iostat 1 5
```

### Optimize Container
```bash
# Check current limits in docker-compose.yml
# Update as needed:
# deploy:
#   resources:
#     limits:
#       memory: 800M
#       cpus: '0.8'

# Restart with limits
sudo docker-compose up -d
```

---

## Emergency Commands

### Reset Everything
```bash
# CAREFUL - This deletes all data!
sudo docker-compose down -v
sudo docker system prune -a
sudo rm -rf data/ config/ media/

# Restart
sudo docker-compose up -d
```

### Check Health
```bash
# Container health
docker inspect --format='{{.State.Health.Status}}' pi-media-server

# Curl health endpoint
curl http://localhost:8501/_stcore/health

# Container logs for errors
docker-compose logs | grep -i error
```

### Recovery
```bash
# Rebuild from scratch
sudo docker-compose build --no-cache
sudo docker-compose down
sudo docker-compose up -d

# Check if running
sudo docker-compose ps
```

---

## Cost Monitoring

### AWS Billing
```bash
# View costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE

# Set budget alert
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json \
  --notifications-with-subscribers ...
```

---

## Keyboard Shortcuts

```bash
# Exit docker logs (Ctrl+C)
# Ctrl+C

# Detach from container (Ctrl+P, Ctrl+Q)
# Ctrl+P Ctrl+Q

# Clear screen
# Ctrl+L or clear

# Cancel command
# Ctrl+C
```

---

## Useful Links

- **Docker Docs:** https://docs.docker.com
- **AWS EC2 Docs:** https://docs.aws.amazon.com/ec2
- **Streamlit Docs:** https://docs.streamlit.io
- **AWS Pricing:** https://aws.amazon.com/pricing
- **Ubuntu Server:** https://ubuntu.com/server

---

**Print this card and keep it handy! 📋**
