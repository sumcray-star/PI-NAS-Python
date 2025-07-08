#!/bin/bash

# PI-NAS Service Installation Script
# This script installs PI-NAS as a systemd service for production deployment

set -e

# Configuration
SERVICE_NAME="pi-nas"
SERVICE_USER="pi-nas"
SERVICE_GROUP="pi-nas"
INSTALL_DIR="/opt/pi-nas"
LOG_DIR="/var/log/pi-nas"
DATA_DIR="/var/lib/pi-nas"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

install_dependencies() {
    print_status "Installing system dependencies..."
    
    # Update package list
    apt update
    
    # Install required packages
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        nginx \
        certbot \
        python3-certbot-nginx \
        cifs-utils \
        smbclient \
        fail2ban \
        ufw \
        htop \
        iotop \
        nethogs \
        iftop
    
    print_status "Dependencies installed successfully"
}

create_service_user() {
    print_status "Creating service user and group..."
    
    # Create group if it doesn't exist
    if ! getent group $SERVICE_GROUP >/dev/null; then
        groupadd --system $SERVICE_GROUP
    fi
    
    # Create user if it doesn't exist
    if ! getent passwd $SERVICE_USER >/dev/null; then
        useradd --system --gid $SERVICE_GROUP --create-home \
            --home-dir $DATA_DIR --shell /bin/false $SERVICE_USER
    fi
    
    print_status "Service user created successfully"
}

setup_directories() {
    print_status "Setting up directories..."
    
    # Create necessary directories
    mkdir -p $INSTALL_DIR
    mkdir -p $LOG_DIR
    mkdir -p $DATA_DIR
    mkdir -p $DATA_DIR/data
    mkdir -p $DATA_DIR/config
    mkdir -p $DATA_DIR/media
    mkdir -p $DATA_DIR/temp
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
    chown -R $SERVICE_USER:$SERVICE_GROUP $LOG_DIR
    chown -R $SERVICE_USER:$SERVICE_GROUP $DATA_DIR
    
    # Set proper permissions for directories
    chmod 755 $INSTALL_DIR
    chmod 755 $LOG_DIR
    chmod 755 $DATA_DIR
    
    print_status "Directories created successfully"
}

install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv $INSTALL_DIR/venv
    
    # Activate virtual environment and install packages
    source $INSTALL_DIR/venv/bin/activate
    pip install --upgrade pip
    pip install streamlit pandas pillow psutil requests opencv-python
    
    # Set ownership
    chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR/venv
    
    print_status "Python dependencies installed successfully"
}

create_systemd_service() {
    print_status "Creating systemd service..."
    
    # Create service file
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=PI-NAS Media Server
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR $LOG_DIR $DATA_DIR

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Systemd service created successfully"
}

configure_firewall() {
    print_status "Configuring firewall..."
    
    # Configure UFW
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow PI-NAS direct access
    ufw allow 5000/tcp
    
    # Allow SMB for local network
    ufw allow from 192.168.0.0/16 to any port 445
    
    # Enable firewall
    ufw --force enable
    
    print_status "Firewall configured successfully"
}

configure_fail2ban() {
    print_status "Configuring Fail2Ban..."
    
    # Create local configuration
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 192.168.0.0/16

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
    
    # Restart fail2ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    print_status "Fail2Ban configured successfully"
}

create_nginx_config() {
    print_status "Creating Nginx configuration..."
    
    # Create PI-NAS site configuration
    cat > /etc/nginx/sites-available/pi-nas << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
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
        client_max_body_size 100M;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/pi-nas /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    nginx -t
    
    # Restart nginx
    systemctl restart nginx
    systemctl enable nginx
    
    print_status "Nginx configuration created successfully"
}

create_monitoring_scripts() {
    print_status "Creating monitoring scripts..."
    
    # Create log rotation configuration
    cat > /etc/logrotate.d/pi-nas << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $SERVICE_USER $SERVICE_GROUP
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF
    
    # Create monitoring script
    cat > /usr/local/bin/pi-nas-monitor.sh << 'EOF'
#!/bin/bash

LOG_FILE="/var/log/pi-nas/monitor.log"
SERVICE_NAME="pi-nas"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Check if service is running
if ! systemctl is-active --quiet $SERVICE_NAME; then
    log_message "ERROR: $SERVICE_NAME service is not running"
    systemctl start $SERVICE_NAME
    log_message "INFO: Attempted to restart $SERVICE_NAME service"
else
    log_message "INFO: $SERVICE_NAME service is running normally"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    log_message "WARNING: Disk usage is at ${DISK_USAGE}%"
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    log_message "WARNING: Memory usage is at ${MEM_USAGE}%"
fi

# Check if PI-NAS is responding
if ! curl -s --connect-timeout 5 http://localhost:5000 >/dev/null; then
    log_message "ERROR: PI-NAS is not responding"
    systemctl restart $SERVICE_NAME
    log_message "INFO: Restarted $SERVICE_NAME due to non-response"
fi
EOF
    
    chmod +x /usr/local/bin/pi-nas-monitor.sh
    
    # Add to crontab
    echo "*/5 * * * * /usr/local/bin/pi-nas-monitor.sh" >> /etc/crontab
    
    print_status "Monitoring scripts created successfully"
}

copy_application_files() {
    print_status "Copying application files..."
    
    # Copy application files from current directory
    cp -r . $INSTALL_DIR/
    
    # Remove unnecessary files
    rm -rf $INSTALL_DIR/.git
    rm -rf $INSTALL_DIR/__pycache__
    rm -rf $INSTALL_DIR/venv
    
    # Create symbolic links for data directories
    ln -sf $DATA_DIR/data $INSTALL_DIR/data
    ln -sf $DATA_DIR/config $INSTALL_DIR/config
    ln -sf $DATA_DIR/media $INSTALL_DIR/media
    ln -sf $DATA_DIR/temp $INSTALL_DIR/temp
    
    # Set ownership
    chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
    
    print_status "Application files copied successfully"
}

create_backup_script() {
    print_status "Creating backup script..."
    
    cat > /usr/local/bin/pi-nas-backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/var/backups/pi-nas"
DATE=$(date +%Y%m%d_%H%M%S)
SERVICE_NAME="pi-nas"
DATA_DIR="/var/lib/pi-nas"

# Create backup directory
mkdir -p $BACKUP_DIR

# Stop service
systemctl stop $SERVICE_NAME

# Create backup
tar -czf "$BACKUP_DIR/pi-nas-backup-$DATE.tar.gz" \
    -C $DATA_DIR . \
    --exclude='./temp/*' \
    --exclude='./media/thumbnails/*'

# Start service
systemctl start $SERVICE_NAME

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/pi-nas-backup-$DATE.tar.gz"
EOF
    
    chmod +x /usr/local/bin/pi-nas-backup.sh
    
    # Schedule daily backups
    echo "0 2 * * * /usr/local/bin/pi-nas-backup.sh" >> /etc/crontab
    
    print_status "Backup script created successfully"
}

main() {
    print_status "Starting PI-NAS service installation..."
    
    check_root
    install_dependencies
    create_service_user
    setup_directories
    copy_application_files
    install_python_dependencies
    create_systemd_service
    configure_firewall
    configure_fail2ban
    create_nginx_config
    create_monitoring_scripts
    create_backup_script
    
    print_status "Installation completed successfully!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Start the service: systemctl start $SERVICE_NAME"
    print_status "2. Enable auto-start: systemctl enable $SERVICE_NAME"
    print_status "3. Check status: systemctl status $SERVICE_NAME"
    print_status "4. View logs: journalctl -u $SERVICE_NAME -f"
    print_status "5. Configure domain and SSL certificate"
    print_status ""
    print_status "PI-NAS will be available at: http://your-server-ip"
    print_status "Service files location: $INSTALL_DIR"
    print_status "Data directory: $DATA_DIR"
    print_status "Log directory: $LOG_DIR"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi