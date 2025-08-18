# Running PI-NAS in VS Code

This guide will help you set up and run your PI-NAS media server in VS Code locally.

## Prerequisites

### 1. Install Required Software
- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **VS Code** - [Download VS Code](https://code.visualstudio.com/)
- **Git** - [Download Git](https://git-scm.com/)

### 2. Install VS Code Extensions
Open VS Code and install these extensions:
- **Python** by Microsoft
- **Python Extension Pack** by Microsoft
- **Git Extension Pack** by Don Jayamanne (optional)

## Setup Steps

### 1. Clone Your Repository
```bash
git clone https://github.com/sumcray-star/PI-NAS-Python.git
cd PI-NAS-Python
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Install required packages
pip install streamlit pandas pillow psutil requests opencv-python

# Or install from requirements file if you create one:
pip install -r requirements.txt
```

### 4. Create Requirements File (Optional)
Create `requirements.txt` with:
```
streamlit==1.28.0
pandas==2.0.3
pillow==10.0.0
psutil==5.9.5
requests==2.31.0
opencv-python==4.8.0.76
```

## Running the Server

### Method 1: Using VS Code Terminal
1. Open VS Code
2. Open your PI-NAS project folder
3. Open terminal in VS Code (`Terminal > New Terminal`)
4. Make sure virtual environment is activated
5. Run the server:
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Method 2: Using VS Code Python Extension
1. Open `app.py` in VS Code
2. Press `F5` or click `Run > Start Debugging`
3. Select "Python File" when prompted
4. The server will start automatically

### Method 3: Create Launch Configuration
Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run PI-NAS Server",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/app.py",
            "console": "integratedTerminal",
            "args": [],
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Run Streamlit Server",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "args": [
                "run",
                "app.py",
                "--server.port",
                "8501",
                "--server.address",
                "0.0.0.0"
            ],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

## Development Tips

### 1. Set Up Python Interpreter
- Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
- Type "Python: Select Interpreter"
- Choose the Python interpreter from your virtual environment

### 2. Enable Auto-Reload
Streamlit automatically reloads when you save files. You'll see changes immediately in your browser.

### 3. Debug Mode
Add this to your Streamlit config (`.streamlit/config.toml`):
```toml
[global]
developmentMode = true

[server]
runOnSave = true
```

## Access Your Application

Once running, open your browser and go to:
- **Local:** http://localhost:8501
- **Network:** http://your-computer-ip:8501

## Default Login
- **Username:** admin
- **Password:** password

## Common Issues & Solutions

### Issue 1: Port Already in Use
```bash
# Kill process using port 8501
# Windows:
netstat -ano | findstr :8501
taskkill /PID <process_id> /F

# macOS/Linux:
lsof -ti:8501 | xargs kill -9
```

### Issue 2: Module Not Found
```bash
# Make sure virtual environment is activated
# Reinstall packages
pip install -r requirements.txt
```

### Issue 3: Permission Errors
```bash
# On Windows, run as administrator
# On macOS/Linux, check file permissions
chmod +x app.py
```

## File Structure
```
PI-NAS-Python/
├── app.py                 # Main application
├── pages/                 # Streamlit pages
│   ├── 1_Media_Library.py
│   ├── 2_Upload_Media.py
│   ├── 3_Network_Storage.py
│   └── 4_Settings.py
├── utils/                 # Utility modules
│   ├── auth.py
│   ├── file_manager.py
│   ├── media_handler.py
│   └── network_storage.py
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── data/                  # User data
├── media/                 # Media files
├── config/               # Configuration files
└── requirements.txt      # Python dependencies
```

## Next Steps

1. **Configure Raspberry Pi Connection**
   - Go to Network Storage page
   - Enter your Pi's IP address and credentials
   - Test the connection

2. **Upload Media Files**
   - Use the Upload Media page
   - Files will be organized automatically
   - Thumbnails generated for videos

3. **Browse Media Library**
   - View all your media files
   - Stream videos and view images
   - Search and filter functionality

## Troubleshooting

If you encounter issues:
1. Check that all dependencies are installed
2. Verify Python version compatibility
3. Ensure virtual environment is activated
4. Check firewall settings for port 8501
5. Review VS Code Python extension settings

For more help, check the project documentation or create an issue on GitHub.