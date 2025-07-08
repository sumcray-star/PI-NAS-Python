# PI-NAS - Personal Media Server

## Overview

PI-NAS is a Streamlit-based personal media server application that provides Plex-like functionality for managing and streaming media files. The application features user authentication, file upload capabilities, media library management, network storage integration, and system settings management. It's designed to work with Raspberry Pi OpenMediaVault setups but can run on any Python-compatible system.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework
- **Multi-page Structure**: Main app.py with separate pages for different functionalities
- **Authentication**: Session-based authentication with login/logout functionality
- **UI Components**: Wide layout with sidebar navigation and tabbed interfaces

### Backend Architecture
- **Language**: Python 3.8+
- **File Structure**: Modular utility functions organized by domain
- **Storage**: File-based storage using JSON for configuration and user data
- **Media Processing**: PIL for image processing, optional OpenCV for thumbnails

### Data Storage Solutions
- **User Data**: JSON file storage (`data/users.json`)
- **Configuration**: JSON configuration files in `config/` directory
- **Media Files**: Local filesystem storage in `media/` directory
- **Thumbnails**: Generated and stored in `media/thumbnails/`

## Key Components

### Authentication System (`utils/auth.py`)
- **Purpose**: Handles user registration, login, and session management
- **Security**: SHA-256 password hashing
- **Admin System**: First registered user becomes admin
- **Session Management**: Streamlit session state for authentication tracking

### Media Handler (`utils/media_handler.py`)
- **Purpose**: Manages media file operations and metadata
- **Supported Formats**: Videos (MP4, AVI, MKV, etc.), Audio (MP3, WAV, FLAC, etc.), Images (JPG, PNG, GIF, etc.), Documents (PDF, DOC, TXT, etc.)
- **Features**: File organization, thumbnail generation, media statistics
- **Processing**: Automatic file type detection and organization

### Network Storage (`utils/network_storage.py`)
- **Purpose**: Handles SMB/CIFS network share connections
- **Features**: Mount/unmount operations, connection testing, network scanning
- **Integration**: Designed for Raspberry Pi OpenMediaVault integration
- **Configuration**: Persistent storage of network settings

### File Manager (`utils/file_manager.py`)
- **Purpose**: Low-level file operations and directory management
- **Features**: Directory creation, file size calculation, format validation
- **Organization**: Automatic directory structure creation and maintenance

## Data Flow

1. **User Authentication**: Users authenticate through the main app interface
2. **Media Upload**: Authenticated users upload files through the Upload Media page
3. **File Processing**: Files are organized, thumbnails generated, and metadata extracted
4. **Library Management**: Media files are indexed and made available in the Media Library
5. **Network Integration**: Optional SMB/CIFS shares can be mounted for additional storage
6. **Settings Management**: System configuration through the Settings page

## External Dependencies

### Core Dependencies
- **streamlit**: Web framework for the user interface
- **pandas**: Data manipulation and analysis
- **Pillow (PIL)**: Image processing and thumbnail generation
- **psutil**: System and process monitoring
- **requests**: HTTP requests for network operations

### Optional Dependencies
- **opencv-python**: Advanced video processing and thumbnail generation
- **subprocess**: System command execution for network operations

### System Dependencies
- **SMB/CIFS tools**: For network storage mounting (Linux/Unix systems)
- **Network utilities**: For network scanning and connectivity testing

## Deployment Strategy

### Local Deployment
- **Target Platform**: Linux, macOS, or Windows
- **Requirements**: Python 3.8+, 4GB RAM minimum, network connectivity
- **Installation**: Direct file deployment with pip dependency installation

### Raspberry Pi Integration
- **OpenMediaVault**: Comprehensive setup guide for OMV integration
- **Network Configuration**: SMB/CIFS share setup and mounting
- **Hardware Requirements**: Raspberry Pi 4 with 4GB RAM recommended

### File Structure
```
pi-nas/
├── app.py                 # Main application entry point
├── pages/                 # Streamlit pages
├── utils/                 # Utility modules
├── data/                  # User data and logs
├── config/               # Configuration files
├── media/                # Media storage
├── deployment/           # Deployment guides
└── temp/                 # Temporary files
```

## Changelog

```
Changelog:
- July 07, 2025. Initial setup
- July 07, 2025. Added comprehensive deployment documentation covering:
  - Complete Raspberry Pi OMV setup guide with hardware requirements
  - Detailed network configuration with router setup and DNS
  - GitHub deployment with CI/CD pipeline
  - Production server installation with systemd service
  - SSL/TLS configuration with Let's Encrypt
  - Security hardening with firewall and Fail2Ban
  - VPN setup for secure remote access
  - Performance optimization and monitoring
  - Troubleshooting guides for common issues
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```