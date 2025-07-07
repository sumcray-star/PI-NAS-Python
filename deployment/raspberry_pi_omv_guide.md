# Raspberry Pi OpenMediaVault (OMV) Setup Guide for PI-NAS

## Overview
This guide will help you set up a Raspberry Pi with OpenMediaVault (OMV) as a network storage server that integrates with PI-NAS for media management and streaming.

## Prerequisites

### Hardware Requirements
- Raspberry Pi 4 Model B (4GB RAM recommended)
- MicroSD card (32GB minimum, Class 10 or better)
- External USB hard drive or SSD
- Ethernet cable (Wi-Fi supported but ethernet recommended)
- Power supply (official Pi 4 power supply recommended)

### Software Requirements
- Raspberry Pi Imager
- OpenMediaVault 6.x
- SSH client (PuTTY for Windows, Terminal for macOS/Linux)

## Step 1: Install OpenMediaVault on Raspberry Pi

### 1.1 Download and Flash OMV
```bash
# Download OMV image for Raspberry Pi
wget https://www.openmediavault.org/download

# Or use Raspberry Pi Imager with OMV image
# Select "Use custom image" and choose the OMV image
