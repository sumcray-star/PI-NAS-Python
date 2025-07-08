# Complete Network Configuration Guide for PI-NAS

## Overview
This comprehensive guide covers all aspects of network configuration for PI-NAS deployment, from local network setup to global internet access, including security, performance optimization, and troubleshooting.

## Table of Contents
1. [Network Architecture](#network-architecture)
2. [Local Network Configuration](#local-network-configuration)
3. [Router and Port Forwarding](#router-and-port-forwarding)
4. [Domain and DNS Setup](#domain-and-dns-setup)
5. [SSL/TLS Configuration](#ssl-tls-configuration)
6. [Firewall and Security](#firewall-and-security)
7. [VPN Access](#vpn-access)
8. [Performance Optimization](#performance-optimization)
9. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)

---

## 1. Network Architecture {#network-architecture}

### Basic Network Topology
```
Internet → Router → [DMZ/Port Forward] → PI-NAS Server
                 → Raspberry Pi OMV (Local Network)
                 → Client Devices
```

### IP Address Planning
```bash
# Recommended IP allocation:
# Router/Gateway:     192.168.1.1
# Raspberry Pi OMV:   192.168.1.100 (Static)
# PI-NAS Server:      192.168.1.101 (Static) 
# DHCP Range:         192.168.1.50-192.168.1.99
# IoT Devices:        192.168.1.200-192.168.1.250
```

### Network Segments (Advanced)
```bash
# VLAN Configuration (if supported by router):
# VLAN 10: Management (192.168.10.0/24)
# VLAN 20: Media Servers (192.168.20.0/24)
# VLAN 30: User Devices (192.168.30.0/24)
# VLAN 40: Guest Network (192.168.40.0/24)
```

---

## 2. Local Network Configuration {#local-network-configuration}

### Static IP Configuration

#### For Ubuntu/Debian (PI-NAS Server)
```bash
# Configure static IP using netplan
sudo nano /etc/netplan/01-netcfg.yaml

# Add configuration:
network:
  version: 2
  ethernets:
    eth0:  # or your interface name
      dhcp4: false
      addresses:
        - 192.168.1.101/24
      gateway4: 192.168.1.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
          - 192.168.1.1

# Apply configuration
sudo netplan apply

# Verify configuration
ip addr show
ping 8.8.8.8
```

#### For Raspberry Pi (OMV)
```bash
# Configure static IP in OMV web interface:
# System → Network → Interfaces → eth0 → Edit
# Method: Static
# Address: 192.168.1.100
# Netmask: 255.255.255.0
# Gateway: 192.168.1.1
# DNS servers: 8.8.8.8, 8.8.4.4

# Or via command line:
sudo nano /etc/dhcpcd.conf

# Add to end of file:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Restart networking
sudo systemctl restart dhcpcd
```

### Network Interface Optimization
```bash
# Optimize network interfaces for better performance
sudo nano /etc/sysctl.conf

# Add network optimizations:
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 30000
net.ipv4.tcp_congestion_control = bbr

# Apply changes
sudo sysctl -p
```

---

## 3. Router and Port Forwarding {#router-and-port-forwarding}

### Port Forwarding Rules
```bash
# Essential ports to forward:
# External Port → Internal IP:Port → Service
80 → 192.168.1.101:80 → HTTP (Nginx)
443 → 192.168.1.101:443 → HTTPS (Nginx)
5000 → 192.168.1.101:5000 → PI-NAS Direct Access

# Optional ports:
2222 → 192.168.1.101:22 → SSH (if remote SSH needed)
51820 → 192.168.1.101:51820 → WireGuard VPN

# SMB access (for direct OMV access):
445 → 192.168.1.100:445 → SMB/CIFS
```

### Router Configuration Examples

#### Linksys/Belkin Routers
```bash
# Access router admin panel (usually 192.168.1.1)
# Navigation: Advanced → Port Forwarding
# Add rules:
# Service Name: PI-NAS-HTTP
# External Port: 80
# Internal Port: 80
# Device IP: 192.168.1.101
# Protocol: TCP
```

#### ASUS Routers
```bash
# Access router admin panel
# Navigation: Advanced Settings → WAN → Virtual Server/Port Forwarding
# Enable Port Forwarding: Yes
# Add rules with same port mappings as above
```

#### Netgear Routers
```bash
# Access router admin panel
# Navigation: Advanced → Advanced Setup → Port Forwarding/Port Triggering
# Select "Port Forwarding"
# Add custom services with port mappings
```

#### pfSense/OPNsense (Advanced)
```bash
# Firewall → NAT → Port Forward
# Add rules with detailed configuration:
# Interface: WAN
# Protocol: TCP
# Destination: WAN Address
# Destination Port Range: 80-80
# Redirect Target IP: 192.168.1.101
# Redirect Target Port: 80
# Description: PI-NAS HTTP
```

### DMZ Configuration (Alternative)
```bash
# If port forwarding is complex, use DMZ:
# Router Admin → Advanced → DMZ
# DMZ Host IP Address: 192.168.1.101
# Enable DMZ: Yes

# WARNING: DMZ exposes all ports - ensure firewall is configured!
```

---

## 4. Domain and DNS Setup {#domain-and-dns-setup}

### Domain Registration and DNS
```bash
# Register domain with provider (Namecheap, GoDaddy, etc.)
# Configure DNS records:

# A Record:
# Name: @ (root domain)
# Value: [Your Public IP]
# TTL: 3600

# A Record:
# Name: nas
# Value: [Your Public IP]
# TTL: 3600

# CNAME Record:
# Name: www
# Value: yourdomain.com
# TTL: 3600
```

### Dynamic DNS Configuration
```bash
# For dynamic IP addresses, use DDNS services:

# Option 1: No-IP
# 1. Register at no-ip.com
# 2. Create hostname: yournas.no-ip.info
# 3. Install client:
sudo apt install ddclient -y

# Configure ddclient
sudo nano /etc/ddclient.conf

# No-IP configuration:
protocol=noip
use=web
server=dynupdate.no-ip.com
login=your-email@example.com
password='your-noip-password'
your-hostname.no-ip.info

# Option 2: DuckDNS
# 1. Register at duckdns.org
# 2. Create subdomain: yournas.duckdns.org
# 3. Create update script:
echo url="https://www.duckdns.org/update?domains=yournas&token=your-token&ip=" | curl -k -o ~/duckdns/duck.log -K -

# Add to crontab:
echo "*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1" | crontab -

# Option 3: Cloudflare (Free)
# 1. Add domain to Cloudflare
# 2. Update nameservers
# 3. Create A record
# 4. Use cloudflare-ddns script:
curl -s https://raw.githubusercontent.com/fire1ce/cloudflare-ddns/main/cloudflare-ddns.py -o cloudflare-ddns.py
# Configure with API key and run via cron
```

### DNS Propagation Testing
```bash
# Test DNS propagation
nslookup yourdomain.com 8.8.8.8
dig +short yourdomain.com @8.8.8.8

# Online tools:
# - whatsmydns.net
# - dnschecker.org
```

---

## 5. SSL/TLS Configuration {#ssl-tls-configuration}

### Let's Encrypt SSL Certificate
```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# Stop PI-NAS temporarily
sudo systemctl stop pi-nas

# Install Nginx if not already installed
sudo apt install nginx -y

# Configure Nginx for PI-NAS
sudo tee /etc/nginx/sites-available/pi-nas << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration (will be added by certbot)
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # PI-NAS proxy
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Increase timeouts for large file uploads
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Static files optimization
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/pi-nas /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test certificate renewal
sudo certbot renew --dry-run

# Set up auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Restart PI-NAS
sudo systemctl start pi-nas
```

### SSL Configuration for OMV (Optional)
```bash
# Generate self-signed certificate for OMV
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/omv-selfsigned.key \
    -out /etc/ssl/certs/omv-selfsigned.crt

# Configure in OMV web interface:
# System → Certificates → SSL → Create
# Upload certificate files
# System → General Settings → Web Administrator Panel
# SSL certificate: Select uploaded certificate
# Force SSL: Yes
# Port: 443
```

---

## 6. Firewall and Security {#firewall-and-security}

### UFW Firewall Configuration
```bash
# Install and configure UFW
sudo apt install ufw -y

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change port if using non-standard)
sudo ufw allow 22/tcp
# sudo ufw allow 2222/tcp  # if using custom SSH port

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PI-NAS direct access (optional)
sudo ufw allow 5000/tcp

# Allow specific IPs only (more secure)
# sudo ufw allow from 192.168.1.0/24 to any port 5000

# Allow SMB for local network only
sudo ufw allow from 192.168.1.0/24 to any port 445

# Allow VPN (if using WireGuard)
sudo ufw allow 51820/udp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose

# Log configuration
sudo ufw logging on
```

### Fail2Ban Configuration
```bash
# Install Fail2Ban
sudo apt install fail2ban -y

# Configure for SSH protection
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 192.168.1.0/24

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 6

[nginx-noscript]
enabled = true
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

# Create custom filter for PI-NAS
sudo tee /etc/fail2ban/filter.d/pi-nas.conf << 'EOF'
[Definition]
failregex = ^<HOST> - - \[.*\] "(GET|POST) .* HTTP/.*" 4(0[1-9]|1[0-9]|2[0-9]) .*$
ignoreregex =
EOF

# Add PI-NAS jail
sudo tee -a /etc/fail2ban/jail.local << 'EOF'

[pi-nas]
enabled = true
filter = pi-nas
logpath = /var/log/nginx/access.log
maxretry = 10
bantime = 3600
EOF

# Start and enable Fail2Ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Check status
sudo fail2ban-client status
```

### Network Security Hardening
```bash
# Disable unnecessary network services
sudo systemctl disable avahi-daemon
sudo systemctl disable cups
sudo systemctl disable bluetooth

# Secure kernel parameters
sudo tee -a /etc/sysctl.conf << 'EOF'

# Network security
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
EOF

# Apply changes
sudo sysctl -p
```

---

## 7. VPN Access {#vpn-access}

### WireGuard VPN Setup
```bash
# Install WireGuard
sudo apt install wireguard -y

# Generate server keys
cd /etc/wireguard
sudo wg genkey | sudo tee privatekey | wg pubkey | sudo tee publickey

# Create server configuration
sudo tee /etc/wireguard/wg0.conf << 'EOF'
[Interface]
PrivateKey = [SERVER_PRIVATE_KEY]
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Client configurations will be added here
[Peer]
PublicKey = [CLIENT_PUBLIC_KEY]
AllowedIPs = 10.0.0.2/32

[Peer]
PublicKey = [CLIENT2_PUBLIC_KEY]
AllowedIPs = 10.0.0.3/32
EOF

# Enable IP forwarding
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Start WireGuard
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# Client configuration template
cat > client1.conf << 'EOF'
[Interface]
PrivateKey = [CLIENT_PRIVATE_KEY]
Address = 10.0.0.2/24
DNS = 8.8.8.8

[Peer]
PublicKey = [SERVER_PUBLIC_KEY]
Endpoint = yourdomain.com:51820
AllowedIPs = 192.168.1.0/24, 10.0.0.0/24
PersistentKeepalive = 25
EOF
```

### OpenVPN Setup (Alternative)
```bash
# Install OpenVPN
sudo apt install openvpn easy-rsa -y

# Set up certificate authority
make-cadir ~/openvpn-ca
cd ~/openvpn-ca

# Configure CA variables
nano vars
# Set KEY_SIZE, KEY_COUNTRY, KEY_PROVINCE, etc.

# Initialize CA
source vars
./clean-all
./build-ca

# Generate server certificate
./build-key-server server

# Generate Diffie-Hellman parameters
./build-dh

# Generate client certificates
./build-key client1

# Configure OpenVPN server
sudo cp keys/{server.crt,server.key,ca.crt,dh2048.pem} /etc/openvpn/

# Create server configuration
sudo tee /etc/openvpn/server.conf << 'EOF'
port 1194
proto udp
dev tun
ca ca.crt
cert server.crt
key server.key
dh dh2048.pem
server 10.8.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt
push "route 192.168.1.0 255.255.255.0"
push "dhcp-option DNS 8.8.8.8"
push "dhcp-option DNS 8.8.4.4"
keepalive 10 120
comp-lzo
user nobody
group nogroup
persist-key
persist-tun
status openvpn-status.log
verb 3
EOF

# Start OpenVPN
sudo systemctl start openvpn@server
sudo systemctl enable openvpn@server
```

---

## 8. Performance Optimization {#performance-optimization}

### Network Performance Tuning
```bash
# TCP congestion control optimization
echo 'net.ipv4.tcp_congestion_control = bbr' | sudo tee -a /etc/sysctl.conf

# Buffer size optimization
echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 87380 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

### Nginx Performance Optimization
```bash
# Update Nginx configuration for better performance
sudo tee /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 30;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate any;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Include sites
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### Bandwidth Management (QoS)
```bash
# Install traffic control tools
sudo apt install iproute2 -y

# Create QoS script
sudo tee /usr/local/bin/setup-qos.sh << 'EOF'
#!/bin/bash

# Interface (change to your interface)
INTERFACE="eth0"
UPLOAD_RATE="50mbit"    # Your upload speed
DOWNLOAD_RATE="100mbit" # Your download speed

# Clear existing rules
tc qdisc del dev $INTERFACE root 2>/dev/null

# Create root qdisc
tc qdisc add dev $INTERFACE root handle 1: htb default 30

# Create classes
tc class add dev $INTERFACE parent 1: classid 1:1 htb rate $UPLOAD_RATE
tc class add dev $INTERFACE parent 1:1 classid 1:10 htb rate 30mbit ceil $UPLOAD_RATE # High priority
tc class add dev $INTERFACE parent 1:1 classid 1:20 htb rate 15mbit ceil $UPLOAD_RATE # Medium priority  
tc class add dev $INTERFACE parent 1:1 classid 1:30 htb rate 5mbit ceil $UPLOAD_RATE  # Low priority

# Create filters
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 1 u32 match ip dport 22 0xffff flowid 1:10    # SSH
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 1 u32 match ip dport 443 0xffff flowid 1:10   # HTTPS
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 2 u32 match ip dport 5000 0xffff flowid 1:20  # PI-NAS
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 3 u32 match ip dport 445 0xffff flowid 1:30   # SMB
EOF

sudo chmod +x /usr/local/bin/setup-qos.sh

# Add to startup
echo '/usr/local/bin/setup-qos.sh' | sudo tee -a /etc/rc.local
```

---

## 9. Monitoring and Troubleshooting {#monitoring-and-troubleshooting}

### Network Monitoring Setup
```bash
# Install monitoring tools
sudo apt install iftop nethogs nload iperf3 mtr-tiny -y

# Create network monitoring script
sudo tee /usr/local/bin/network-monitor.sh << 'EOF'
#!/bin/bash

LOG_FILE="/var/log/network-monitor.log"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Check internet connectivity
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    log_message "Internet connectivity: OK"
else
    log_message "Internet connectivity: FAILED"
fi

# Check PI-NAS service
if curl -s http://localhost:5000 >/dev/null; then
    log_message "PI-NAS service: OK"
else
    log_message "PI-NAS service: FAILED"
fi

# Check OMV connectivity
if ping -c 1 192.168.1.100 >/dev/null 2>&1; then
    log_message "OMV connectivity: OK"
else
    log_message "OMV connectivity: FAILED"
fi

# Check SSL certificate expiry
if command -v openssl >/dev/null; then
    CERT_EXPIRY=$(echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
    log_message "SSL certificate expires: $CERT_EXPIRY"
fi

# Log network statistics
NETWORK_STATS=$(cat /proc/net/dev | grep eth0)
log_message "Network stats: $NETWORK_STATS"
EOF

sudo chmod +x /usr/local/bin/network-monitor.sh

# Schedule monitoring
echo "*/5 * * * * /usr/local/bin/network-monitor.sh" | sudo crontab -
```

### Troubleshooting Common Issues

#### Issue: Cannot access PI-NAS from internet
```bash
# Diagnostic steps:
# 1. Check public IP
curl ifconfig.me

# 2. Test port forwarding
nmap -p 80,443,5000 your-public-ip

# 3. Check local service
netstat -tlnp | grep :5000

# 4. Check firewall
sudo ufw status
sudo iptables -L

# 5. Check router configuration
# Access router admin panel and verify port forwarding rules

# 6. Test from external network
# Use online port checker: canyouseeme.org
```

#### Issue: SSL certificate problems
```bash
# Check certificate status
sudo certbot certificates

# Test SSL configuration
openssl s_client -connect yourdomain.com:443

# Check certificate expiry
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Renew certificate
sudo certbot renew --force-renewal

# Check Nginx SSL configuration
sudo nginx -t
```

#### Issue: Poor network performance
```bash
# Test bandwidth
iperf3 -s  # On server
iperf3 -c server-ip -t 30  # From client

# Check network utilization
sudo nethogs
sudo iftop

# Test DNS resolution
nslookup yourdomain.com
dig yourdomain.com

# Check for packet loss
mtr yourdomain.com

# Optimize network settings
# Implement QoS rules as shown above
```

#### Issue: VPN connection problems
```bash
# WireGuard troubleshooting
sudo wg show
sudo systemctl status wg-quick@wg0

# Check WireGuard logs
sudo journalctl -u wg-quick@wg0

# OpenVPN troubleshooting
sudo systemctl status openvpn@server
sudo tail -f /var/log/openvpn.log

# Check VPN routes
ip route show table all
```

### Performance Monitoring Dashboard
```bash
# Install Netdata for real-time monitoring
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Configure Netdata for PI-NAS
sudo tee -a /etc/netdata/netdata.conf << 'EOF'
[web]
    web files owner = root
    web files group = netdata
    bind to = 127.0.0.1:19999

[plugins]
    python.d = yes
    node.d = yes
    go.d = yes
EOF

# Add Nginx proxy for Netdata
sudo tee /etc/nginx/sites-available/netdata << 'EOF'
server {
    listen 8080;
    server_name yourdomain.com;

    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:19999;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# Create authentication file
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Enable Netdata site
sudo ln -s /etc/nginx/sites-available/netdata /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Access at: http://yourdomain.com:8080
```

This comprehensive network configuration guide covers all aspects of setting up PI-NAS for both local and global access with proper security measures. The setup process typically takes 3-4 hours depending on your network complexity and experience level.
