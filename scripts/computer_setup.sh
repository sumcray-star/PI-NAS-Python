#!/bin/bash

# PI-NAS Computer Setup Script
# Run this script on your computer to set up the media server

set -e

echo "==================================="
echo "PI-NAS Computer Setup Script"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required."
    exit 1
fi

print_status "Python $PYTHON_VERSION detected - OK"

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

print_status "Git detected - OK"

# Clone repository if not already present
if [ ! -d "PI-NAS-Python" ]; then
    print_status "Cloning PI-NAS repository..."
    git clone https://github.com/sumcray-star/PI-NAS-Python.git
    cd PI-NAS-Python
else
    print_status "PI-NAS repository already exists. Updating..."
    cd PI-NAS-Python
    git pull origin main
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing dependencies..."
pip install streamlit==1.28.0 pandas==2.0.3 pillow==10.0.0 psutil==5.9.5 requests==2.31.0 opencv-python==4.8.0.76

# Create desktop shortcut (Linux/Mac)
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "Creating desktop shortcut..."
    
    # Create start script
    cat > start_pi_nas.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
EOF
    
    chmod +x start_pi_nas.sh
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Create desktop file for Linux
        cat > ~/Desktop/PI-NAS.desktop << EOF
[Desktop Entry]
Name=PI-NAS Media Server
Comment=Launch PI-NAS Media Server
Exec=$(pwd)/start_pi_nas.sh
Icon=applications-multimedia
Terminal=true
Type=Application
Categories=AudioVideo;
EOF
        chmod +x ~/Desktop/PI-NAS.desktop
        print_status "Desktop shortcut created: ~/Desktop/PI-NAS.desktop"
    fi
fi

# Test installation
print_status "Testing installation..."
python -c "import streamlit; print('Streamlit version:', streamlit.__version__)"

print_status "Setup completed successfully!"
echo ""
echo "==================================="
echo "PI-NAS Media Server Setup Complete"
echo "==================================="
echo "Installation Directory: $(pwd)"
echo ""
echo "To start the server:"
echo "1. Navigate to: $(pwd)"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run server: streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
echo ""
echo "Or use the start script: ./start_pi_nas.sh"
echo ""
echo "Once running, open your browser to: http://localhost:8501"
echo ""
echo "Default login credentials:"
echo "Username: admin"
echo "Password: password"
echo ""
echo "==================================="
echo "Next Steps:"
echo "==================================="
echo "1. Start the PI-NAS server"
echo "2. Open web browser to http://localhost:8501"
echo "3. Go to Network Storage settings"
echo "4. Configure your Raspberry Pi connection"
echo "5. Start uploading and streaming media!"
echo ""
print_status "Setup complete! Enjoy your PI-NAS media server."