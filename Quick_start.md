# PI-NAS Quick Start Guide

Get your distributed media server running in 15 minutes!

## Overview
PI-NAS creates a Plex-like system where:
- **Your Computer** = Web interface and streaming
- **Raspberry Pi** = 24/7 storage server
- **Network** = Connects them seamlessly

## Quick Setup (15 Minutes)

### Part 1: Raspberry Pi (5 minutes)

1. **SSH into your Pi:**
   ```bash
   ssh pi@your-pi-ip
   ```

2. **Run the setup script:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/sumcray-star/PI-NAS-Python/main/scripts/pi_setup.sh | bash
   ```

3. **Note your Pi's IP address** (shown at the end)

### Part 2: Your Computer (5 minutes)

1. **Run the setup script:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/sumcray-star/PI-NAS-Python/main/scripts/computer_setup.sh | bash
   ```

2. **Start the server:**
   ```bash
   cd PI-NAS-Python
   ./start_pi_nas.sh
   ```

### Part 3: Connect Them (5 minutes)

1. **Open browser:** http://localhost:8501

2. **Login:**
   - Username: `admin`
   - Password: `password`

3. **Configure Network Storage:**
   - Go to "Network Storage" page
   - Enter your Pi's IP address
   - Share Name: `media`
   - Username: `pi`
   - Password: (your Pi's password)
   - Click "Test Connection" → "Save" → "Mount"

4. **Start using:**
   - Upload Media: Drag files to upload page
   - Browse Library: View and stream your media
   - Stream Videos: Click any video to play

## That's It!

Your distributed media server is now running. Upload files through the web interface and they'll be stored on your Raspberry Pi automatically.

## Default Structure
```
Raspberry Pi (/mnt/media-storage/media/):
├── videos/     # MP4, AVI, MKV files
├── images/     # JPG, PNG, GIF files  
├── audio/      # MP3, WAV, FLAC files
└── documents/  # PDF, DOC files
```

## Troubleshooting

**Can't connect to Pi?**
```bash
ping your-pi-ip
smbclient -L //your-pi-ip -U pi
```

**Server won't start?**
```bash
source venv/bin/activate
pip install --upgrade streamlit
```

**Need help?** Check the complete setup guide: `COMPLETE_SETUP_GUIDE.md`

Enjoy your new media server!