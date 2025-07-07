#!/bin/bash

# PI-NAS Startup Script
# This script manages the startup, shutdown, and monitoring of PI-NAS

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/pinas.pid"
LOG_FILE="$PROJECT_DIR/logs/pinas.log"
ERROR_LOG="$PROJECT_DIR/logs/pinas_error.log"
CONFIG_FILE="$PROJECT_DIR/.streamlit/config.toml"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_CMD="python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    log "ERROR: $1"
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

# Info message
info_msg() {
    echo -e "${BLUE}$1${NC}"
    log "INFO: $1"
}

# Check if PI-NAS is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Get PI-NAS status
get_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ PI-NAS is running (PID: $pid)${NC}"
        
        # Check if port 5000 is listening
        if netstat -tlnp 2>/dev/null | grep -q ":5000 "; then
            echo -e "${GREEN}✓ Web interface available at http://localhost:5000${NC}"
        else
            echo -e "${YELLOW}⚠ Web interface may not be accessible${NC}"
        fi
        
        return 0
    else
        echo -e "${RED}✗ PI-NAS is not running${NC}"
        return 1
    fi
}

# Setup environment
setup_environment() {
    info_msg "Setting up PI-NAS environment..."
    
    # Create necessary directories
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/media/uploads"
    mkdir -p "$PROJECT_DIR/media/thumbnails"
    mkdir -p "$PROJECT_DIR/data"
    mkdir -p "$PROJECT_DIR/config"
    mkdir -p "$PROJECT_DIR/temp"
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        info_msg "Creating virtual environment..."
        python3 -m venv "$VENV_DIR" || error_exit "Failed to create virtual environment"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate" || error_exit "Failed to activate virtual environment"
    
    # Update pip
    pip install --upgrade pip > /dev/null 2>&1
    
    # Install required packages
    info_msg "Installing/updating required packages..."
    pip install streamlit pandas pillow psutil requests opencv-python > /dev/null 2>&1
    
    # Install optional packages
    pip install smbprotocol pysmb > /dev/null 2>&1
    
    success_msg "Environment setup complete"
}

# Check system requirements
check_requirements() {
    info_msg "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error_exit "Python 3 is required but not installed"
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local required_version="3.8"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        error_exit "Python 3.8 or higher is required (found: $python_version)"
    fi
    
    # Check available memory
    local mem_total=$(free -m | awk 'NR==2{print $2}')
    if [ "$mem_total" -lt 1000 ]; then
        warning_msg "Low memory detected (${mem_total}MB). PI-NAS may run slowly."
    fi
    
    # Check disk space
    local disk_free=$(df -BG "$PROJECT_DIR" | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$disk_free" -lt 1 ]; then
        warning_msg "Low disk space (${disk_free}GB free). Consider cleaning up files."
    fi
    
    success_msg "System requirements check passed"
}

# Backup configuration
backup_config() {
    local backup_dir="$PROJECT_DIR/backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/config_backup_$timestamp.tar.gz"
    
    mkdir -p "$backup_dir"
    
    tar -czf "$backup_file" -C "$PROJECT_DIR" config data .streamlit 2>/dev/null
    
    if [ -f "$backup_file" ]; then
        info_msg "Configuration backed up to $backup_file"
    else
        warning_msg "Failed to create configuration backup"
    fi
}

# Start PI-NAS
start_pinas() {
    if is_running; then
        warning_msg "PI-NAS is already running"
        return 0
    fi
    
    info_msg "Starting PI-NAS..."
    
    # Check configuration
    if [ ! -f "$CONFIG_FILE" ]; then
        error_exit "Configuration file not found: $CONFIG_FILE"
    fi
    
    # Change to project directory
    cd "$PROJECT_DIR" || error_exit "Failed to change to project directory"
    
    # Activate virtual environment if it exists
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Start streamlit
    nohup streamlit run app.py --server.port 5000 --server.address 0.0.0.0 > "$LOG_FILE" 2> "$ERROR_LOG" &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment and check if process is still running
    sleep 3
    
    if ps -p "$pid" > /dev/null 2>&1; then
        success_msg "PI-NAS started successfully (PID: $pid)"
        info_msg "Web interface available at http://localhost:5000"
        
        # Try to mount network storage if configured
        if [ -f "$SCRIPT_DIR/mount_network_drive.sh" ]; then
            info_msg "Attempting to mount network storage..."
            "$SCRIPT_DIR/mount_network_drive.sh" auto 2>/dev/null || true
        fi
        
        return 0
    else
        rm -f "$PID_FILE"
        error_exit "Failed to start PI-NAS. Check logs: $ERROR_LOG"
    fi
}

# Stop PI-NAS
stop_pinas() {
    if ! is_running; then
        warning_msg "PI-NAS is not running"
        return 0
    fi
    
    info_msg "Stopping PI-NAS..."
    
    local pid=$(cat "$PID_FILE")
    
    # Try graceful shutdown first
    kill "$pid" 2>/dev/null
    
    # Wait for process to exit
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        warning_msg "Force killing PI-NAS process"
        kill -9 "$pid" 2>/dev/null
    fi
    
    rm -f "$PID_FILE"
    success_msg "PI-NAS stopped"
}

# Restart PI-NAS
restart_pinas() {
    info_msg "Restarting PI-NAS..."
    stop_pinas
    sleep 2
    start_pinas
}

# Monitor PI-NAS
monitor_pinas() {
    info_msg "Monitoring PI-NAS (press Ctrl+C to stop)..."
    
    while true; do
        if is_running; then
            local pid=$(cat "$PID_FILE")
            local cpu_usage=$(ps -p "$pid" -o %cpu --no-headers 2>/dev/null || echo "N/A")
            local mem_usage=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null || echo "N/A")
            local uptime=$(ps -p "$pid" -o etime --no-headers 2>/dev/null | tr -d ' ' || echo "N/A")
            
            echo -e "${GREEN}$(date '+%H:%M:%S') - PI-NAS running (PID: $pid, CPU: ${cpu_usage}%, MEM: ${mem_usage}%, Uptime: $uptime)${NC}"
            
            # Check if web interface is responding
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200"; then
                echo -e "${GREEN}$(date '+%H:%M:%S') - Web interface responding${NC}"
            else
                echo -e "${YELLOW}$(date '+%H:%M:%S') - Web interface not responding${NC}"
            fi
        else
            echo -e "${RED}$(date '+%H:%M:%S') - PI-NAS is not running${NC}"
        fi
        
        sleep 5
    done
}

# Show logs
show_logs() {
    local log_type="$1"
    
    case "$log_type" in
        error)
            if [ -f "$ERROR_LOG" ]; then
                tail -f "$ERROR_LOG"
            else
                error_exit "Error log file not found: $ERROR_LOG"
            fi
            ;;
        access)
            if [ -f "$LOG_FILE" ]; then
                tail -f "$LOG_FILE"
            else
                error_exit "Access log file not found: $LOG_FILE"
            fi
            ;;
        *)
            echo "Available logs:"
            echo "  access - Application access log"
            echo "  error  - Error log"
            echo
            echo "Usage: $0 logs [access|error]"
            ;;
    esac
}

# Install as system service
install_service() {
    local service_file="/etc/systemd/system/pi-nas.service"
    
    info_msg "Installing PI-NAS as system service..."
    
    # Create service file
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=PI-NAS Media Server
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=$PROJECT_DIR
ExecStart=$SCRIPT_DIR/start_pinas.sh start
ExecStop=$SCRIPT_DIR/start_pinas.sh stop
ExecReload=$SCRIPT_DIR/start_pinas.sh restart
Restart=always
RestartSec=5
PIDFile=$PID_FILE

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable pi-nas.service
    
    success_msg "PI-NAS service installed and enabled"
    info_msg "Use 'sudo systemctl start pi-nas' to start the service"
}

# Uninstall system service
uninstall_service() {
    local service_file="/etc/systemd/system/pi-nas.service"
    
    if [ -f "$service_file" ]; then
        info_msg "Uninstalling PI-NAS system service..."
        
        sudo systemctl stop pi-nas.service 2>/dev/null || true
        sudo systemctl disable pi-nas.service 2>/dev/null || true
        sudo rm "$service_file"
        sudo systemctl daemon-reload
        
        success_msg "PI-NAS service uninstalled"
    else
        warning_msg "PI-NAS service not found"
    fi
}

# Update PI-NAS
update_pinas() {
    info_msg "Updating PI-NAS..."
    
    # Backup current configuration
    backup_config
    
    # Stop service if running
    local was_running=false
    if is_running; then
        was_running=true
        stop_pinas
    fi
    
    # Update virtual environment
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        pip install --upgrade streamlit pandas pillow psutil requests opencv-python
    fi
    
    # Restart if it was running
    if [ "$was_running" = true ]; then
        start_pinas
    fi
    
    success_msg "PI-NAS updated successfully"
}

# Show help
show_help() {
    cat << EOF
PI-NAS Startup Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start       Start PI-NAS server
    stop        Stop PI-NAS server
    restart     Restart PI-NAS server
    status      Show PI-NAS status
    monitor     Monitor PI-NAS in real-time
    logs        Show logs [access|error]
    setup       Setup environment and dependencies
    check       Check system requirements
    backup      Backup configuration
    install     Install as system service
    uninstall   Uninstall system service
    update      Update PI-NAS dependencies
    help        Show this help message

Options:
    -v          Verbose output
    -f          Force operation

Examples:
    $0 start
    $0 status
    $0 logs error
    $0 monitor

Service Management:
    sudo systemctl start pi-nas      # Start service
    sudo systemctl stop pi-nas       # Stop service
    sudo systemctl restart pi-nas    # Restart service
    sudo systemctl status pi-nas     # Check service status

Log Files:
    $LOG_FILE
    $ERROR_LOG

Configuration:
    $CONFIG_FILE
EOF
}

# Main execution
main() {
    # Parse command line arguments
    VERBOSE=false
    FORCE=false
    
    while getopts "vfh" opt; do
        case $opt in
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
    
    # Execute command
    case "$1" in
        start)
            start_pinas
            ;;
        stop)
            stop_pinas
            ;;
        restart)
            restart_pinas
            ;;
        status)
            get_status
            ;;
        monitor)
            monitor_pinas
            ;;
        logs)
            show_logs "$2"
            ;;
        setup)
            setup_environment
            ;;
        check)
            check_requirements
            ;;
        backup)
            backup_config
            ;;
        install)
            install_service
            ;;
        uninstall)
            uninstall_service
            ;;
        update)
            update_pinas
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

# Set script permissions
chmod +x "$0" 2>/dev/null || true

# Run main function
main "$@"
