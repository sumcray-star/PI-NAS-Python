#!/bin/bash

# PI-NAS Network Drive Mount Script
# This script handles mounting and unmounting of network drives (SMB/CIFS)

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config/storage_config.json"
CREDENTIALS_FILE="/tmp/pi-nas-creds"
LOG_FILE="/var/log/pi-nas-mount.log"
LOCK_FILE="/tmp/pi-nas-mount.lock"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    log "ERROR: $1"
    cleanup
    exit 1
}

# Success message
success_msg() {
    echo -e "${GREEN}$1${NC}"
    log "SUCCESS: $1"
}

# Warning message
warning_msg() {
    echo -e "${YELLOW}Warning: $1${NC}"
    log "WARNING: $1"
}

# Cleanup function
cleanup() {
    # Remove credentials file
    if [ -f "$CREDENTIALS_FILE" ]; then
        rm -f "$CREDENTIALS_FILE"
    fi
    
    # Remove lock file
    if [ -f "$LOCK_FILE" ]; then
        rm -f "$LOCK_FILE"
    fi
}

# Check if script is already running
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            error_exit "Script is already running (PID: $pid)"
        else
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
}

# Load configuration from JSON file
load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        error_exit "Configuration file not found: $CONFIG_FILE"
    fi
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        error_exit "jq is required but not installed. Install with: sudo apt install jq"
    fi
    
    # Parse JSON configuration
    SERVER_IP=$(jq -r '.server_ip // empty' "$CONFIG_FILE")
    SHARE_NAME=$(jq -r '.share_name // empty' "$CONFIG_FILE")
    USERNAME=$(jq -r '.username // empty' "$CONFIG_FILE")
    MOUNT_POINT=$(jq -r '.mount_point // "/mnt/pi-nas"' "$CONFIG_FILE")
    MOUNT_TIMEOUT=$(jq -r '.mount_timeout // 30' "$CONFIG_FILE")
    
    # Validate required fields
    if [ -z "$SERVER_IP" ] || [ -z "$SHARE_NAME" ] || [ -z "$USERNAME" ]; then
        error_exit "Missing required configuration: server_ip, share_name, or username"
    fi
}

# Get password from environment or prompt
get_password() {
    if [ -n "$SMB_PASSWORD" ]; then
        PASSWORD="$SMB_PASSWORD"
    elif [ -n "$1" ]; then
        PASSWORD="$1"
    else
        echo -n "Enter SMB password for $USERNAME: "
        read -s PASSWORD
        echo
    fi
    
    if [ -z "$PASSWORD" ]; then
        error_exit "Password is required"
    fi
}

# Create credentials file
create_credentials() {
    cat > "$CREDENTIALS_FILE" << EOF
username=$USERNAME
password=$PASSWORD
domain=workgroup
EOF
    chmod 600 "$CREDENTIALS_FILE"
}

# Check if mount point exists and create if necessary
prepare_mount_point() {
    if [ ! -d "$MOUNT_POINT" ]; then
        log "Creating mount point: $MOUNT_POINT"
        sudo mkdir -p "$MOUNT_POINT" || error_exit "Failed to create mount point"
    fi
    
    # Check if mount point is already in use
    if mountpoint -q "$MOUNT_POINT"; then
        warning_msg "Mount point $MOUNT_POINT is already mounted"
        return 1
    fi
    
    return 0
}

# Test network connectivity
test_connectivity() {
    log "Testing connectivity to $SERVER_IP..."
    
    # Test ping
    if ! ping -c 1 -W 3 "$SERVER_IP" &>/dev/null; then
        error_exit "Cannot reach server $SERVER_IP"
    fi
    
    # Test SMB port
    if ! timeout 5 bash -c "echo >/dev/tcp/$SERVER_IP/445" 2>/dev/null; then
        error_exit "SMB port 445 is not accessible on $SERVER_IP"
    fi
    
    success_msg "Connectivity test passed"
}

# Mount SMB share
mount_smb() {
    log "Mounting SMB share //$SERVER_IP/$SHARE_NAME to $MOUNT_POINT"
    
    # Mount options
    MOUNT_OPTIONS="credentials=$CREDENTIALS_FILE,uid=$(id -u),gid=$(id -g),iocharset=utf8,file_mode=0644,dir_mode=0755"
    
    # Add timeout if specified
    if [ "$MOUNT_TIMEOUT" -gt 0 ]; then
        MOUNT_OPTIONS="$MOUNT_OPTIONS,timeout=$MOUNT_TIMEOUT"
    fi
    
    # Attempt to mount
    if sudo mount -t cifs "//$SERVER_IP/$SHARE_NAME" "$MOUNT_POINT" -o "$MOUNT_OPTIONS"; then
        success_msg "Successfully mounted //$SERVER_IP/$SHARE_NAME to $MOUNT_POINT"
        
        # Verify mount
        if ! mountpoint -q "$MOUNT_POINT"; then
            error_exit "Mount verification failed"
        fi
        
        # Test write access
        if ! sudo -u $(whoami) touch "$MOUNT_POINT/.pi-nas-test" 2>/dev/null; then
            warning_msg "Mount is read-only or write permission denied"
        else
            rm -f "$MOUNT_POINT/.pi-nas-test"
            success_msg "Write access confirmed"
        fi
        
        return 0
    else
        error_exit "Failed to mount SMB share"
    fi
}

# Unmount SMB share
unmount_smb() {
    log "Unmounting $MOUNT_POINT"
    
    if ! mountpoint -q "$MOUNT_POINT"; then
        warning_msg "$MOUNT_POINT is not mounted"
        return 0
    fi
    
    # Try gentle unmount first
    if sudo umount "$MOUNT_POINT" 2>/dev/null; then
        success_msg "Successfully unmounted $MOUNT_POINT"
        return 0
    fi
    
    # Force unmount if gentle fails
    log "Gentle unmount failed, trying force unmount"
    if sudo umount -f "$MOUNT_POINT" 2>/dev/null; then
        success_msg "Force unmount successful"
        return 0
    fi
    
    # Lazy unmount as last resort
    log "Force unmount failed, trying lazy unmount"
    if sudo umount -l "$MOUNT_POINT" 2>/dev/null; then
        warning_msg "Lazy unmount initiated - mount point will be unmounted when not in use"
        return 0
    fi
    
    error_exit "Failed to unmount $MOUNT_POINT"
}

# Check mount status
check_status() {
    echo "=== PI-NAS Mount Status ==="
    
    if mountpoint -q "$MOUNT_POINT"; then
        echo -e "${GREEN}✓ $MOUNT_POINT is mounted${NC}"
        
        # Show mount details
        mount | grep "$MOUNT_POINT"
        
        # Show disk usage
        echo
        echo "Disk Usage:"
        df -h "$MOUNT_POINT"
        
        # Test access
        echo
        if [ -r "$MOUNT_POINT" ]; then
            echo -e "${GREEN}✓ Read access: OK${NC}"
        else
            echo -e "${RED}✗ Read access: FAILED${NC}"
        fi
        
        if [ -w "$MOUNT_POINT" ]; then
            echo -e "${GREEN}✓ Write access: OK${NC}"
        else
            echo -e "${YELLOW}⚠ Write access: LIMITED${NC}"
        fi
    else
        echo -e "${RED}✗ $MOUNT_POINT is not mounted${NC}"
    fi
    
    echo
    echo "Configuration:"
    echo "  Server: $SERVER_IP"
    echo "  Share: $SHARE_NAME"
    echo "  Mount Point: $MOUNT_POINT"
    echo "  User: $USERNAME"
}

# Auto-mount with retry
auto_mount() {
    local max_retries=3
    local retry_delay=5
    local attempt=1
    
    while [ $attempt -le $max_retries ]; do
        log "Mount attempt $attempt of $max_retries"
        
        if prepare_mount_point; then
            test_connectivity
            create_credentials
            
            if mount_smb; then
                return 0
            fi
        fi
        
        if [ $attempt -lt $max_retries ]; then
            log "Retrying in $retry_delay seconds..."
            sleep $retry_delay
        fi
        
        attempt=$((attempt + 1))
    done
    
    error_exit "Failed to mount after $max_retries attempts"
}

# Setup auto-mount on boot
setup_auto_mount() {
    local service_file="/etc/systemd/system/pi-nas-mount.service"
    
    log "Setting up auto-mount service"
    
    # Create systemd service file
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=PI-NAS Network Mount
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=$SCRIPT_DIR/mount_network_drive.sh mount
ExecStop=$SCRIPT_DIR/mount_network_drive.sh unmount
RemainAfterExit=yes
Environment=SMB_PASSWORD=$PASSWORD

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable pi-nas-mount.service
    
    success_msg "Auto-mount service configured"
}

# Remove auto-mount service
remove_auto_mount() {
    local service_file="/etc/systemd/system/pi-nas-mount.service"
    
    if [ -f "$service_file" ]; then
        sudo systemctl stop pi-nas-mount.service
        sudo systemctl disable pi-nas-mount.service
        sudo rm "$service_file"
        sudo systemctl daemon-reload
        success_msg "Auto-mount service removed"
    else
        warning_msg "Auto-mount service not found"
    fi
}

# Show help
show_help() {
    cat << EOF
PI-NAS Network Drive Mount Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    mount       Mount the network drive
    unmount     Unmount the network drive  
    status      Show mount status
    test        Test network connectivity
    auto        Mount with retry logic
    setup       Setup auto-mount on boot
    remove      Remove auto-mount service
    help        Show this help message

Options:
    -p PASSWORD    Specify SMB password
    -v             Verbose output
    -f             Force operation

Environment Variables:
    SMB_PASSWORD   SMB password (alternative to -p)

Examples:
    $0 mount -p mypassword
    $0 status
    $0 auto
    SMB_PASSWORD=mypass $0 mount

Configuration:
    Edit $CONFIG_FILE to change settings
EOF
}

# Main execution
main() {
    # Set up signal handlers
    trap cleanup EXIT
    trap 'error_exit "Script interrupted"' INT TERM
    
    # Check for root privileges when needed
    if [[ "$1" == "mount" ]] || [[ "$1" == "unmount" ]] || [[ "$1" == "setup" ]] || [[ "$1" == "remove" ]]; then
        if [ "$EUID" -eq 0 ]; then
            error_exit "This script should not be run as root"
        fi
        
        # Check if sudo is available
        if ! sudo -n true 2>/dev/null; then
            echo "This script requires sudo privileges"
            sudo -v || error_exit "Failed to obtain sudo privileges"
        fi
    fi
    
    # Parse command line arguments
    VERBOSE=false
    FORCE=false
    PASSWORD=""
    
    while getopts "p:vfh" opt; do
        case $opt in
            p)
                PASSWORD="$OPTARG"
                ;;
            v)
                VERBOSE=true
                ;;
            f)
                FORCE=true
                ;;
            h)
                show_help
                exit 0
                ;;
            \?)
                error_exit "Invalid option: -$OPTARG"
                ;;
        esac
    done
    shift $((OPTIND-1))
    
    # Check lock
    check_lock
    
    # Load configuration
    load_config
    
    # Execute command
    case "$1" in
        mount)
            get_password "$PASSWORD"
            prepare_mount_point
            test_connectivity
            create_credentials
            mount_smb
            ;;
        unmount)
            unmount_smb
            ;;
        status)
            check_status
            ;;
        test)
            test_connectivity
            ;;
        auto)
            get_password "$PASSWORD"
            auto_mount
            ;;
        setup)
            get_password "$PASSWORD"
            setup_auto_mount
            ;;
        remove)
            remove_auto_mount
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            if [ -z "$1" ]; then
                show_help
            else
                error_exit "Unknown command: $1"
            fi
            ;;
    esac
}

# Run main function
main "$@"
