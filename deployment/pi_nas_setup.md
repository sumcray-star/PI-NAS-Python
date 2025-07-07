# PI-NAS Setup and Deployment Guide

## Overview
PI-NAS is a Plex-like media server application built with Streamlit that provides media library management, file upload capabilities, streaming functionality, and integration with Raspberry Pi OpenMediaVault (OMV) for network storage.

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Linux/macOS/Windows (Linux recommended for best performance)
- 4GB RAM minimum (8GB recommended)
- 100MB free disk space for application
- Network connectivity for Raspberry Pi integration

### Required Python Packages
The following packages will be installed automatically:
- streamlit
- pandas
- Pillow
- psutil
- requests
- opencv-python (optional, for thumbnail generation)

## Installation

### 1. Download PI-NAS
```bash
# Clone or download PI-NAS files to your desired directory
cd /opt/pi-nas  # or your preferred location
