import streamlit as st
import os
import json
import subprocess
from pathlib import Path
from utils.auth import is_authenticated
from utils.network_storage import (
    test_smb_connection, mount_smb_share, unmount_smb_share,
    get_mounted_shares, scan_network_devices, get_network_storage_config,
    save_network_storage_config
)

# Check authentication
if not is_authenticated():
    st.error("Please login to access this page")
    st.stop()

st.set_page_config(page_title="Network Storage - PI-NAS", page_icon="🔗", layout="wide")

st.title("🔗 Network Storage")

# Load configuration
config = get_network_storage_config()

# Main interface
tab1, tab2, tab3, tab4 = st.tabs(["SMB/CIFS", "Network Scan", "Mount Status", "Configuration"])

with tab1:
    st.subheader("SMB/CIFS Connection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("smb_connection"):
            st.markdown("**Connect to SMB/CIFS Share**")
            
            server_ip = st.text_input(
                "Server IP Address",
                value=config.get('server_ip', ''),
                placeholder="192.168.1.100"
            )
            
            share_name = st.text_input(
                "Share Name",
                value=config.get('share_name', ''),
                placeholder="media"
            )
            
            username = st.text_input(
                "Username",
                value=config.get('username', ''),
                placeholder="pi"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password"
            )
            
            mount_point = st.text_input(
                "Mount Point",
                value=config.get('mount_point', '/mnt/pi-nas'),
                placeholder="/mnt/pi-nas"
            )
            
            col_test, col_mount = st.columns(2)
            
            with col_test:
                test_connection = st.form_submit_button("Test Connection")
            
            with col_mount:
                mount_share = st.form_submit_button("Mount Share")
            
            if test_connection:
                if server_ip and share_name and username and password:
                    with st.spinner("Testing connection..."):
                        result = test_smb_connection(server_ip, share_name, username, password)
                        if result['success']:
                            st.success("✅ Connection successful!")
                            st.info(f"Available shares: {', '.join(result.get('shares', []))}")
                        else:
                            st.error(f"❌ Connection failed: {result.get('error', 'Unknown error')}")
                else:
                    st.error("Please fill in all required fields")
            
            if mount_share:
                if server_ip and share_name and username and password and mount_point:
                    with st.spinner("Mounting share..."):
                        result = mount_smb_share(server_ip, share_name, username, password, mount_point)
                        if result['success']:
                            st.success("✅ Share mounted successfully!")
                            # Save configuration
                            config.update({
                                'server_ip': server_ip,
                                'share_name': share_name,
                                'username': username,
                                'mount_point': mount_point
                            })
                            save_network_storage_config(config)
                            st.rerun()
                        else:
                            st.error(f"❌ Mount failed: {result.get('error', 'Unknown error')}")
                else:
                    st.error("Please fill in all required fields")
    
    with col2:
        st.subheader("Quick Actions")
        
        # Raspberry Pi OMV preset
        if st.button("🥧 Raspberry Pi OMV Preset", use_container_width=True):
            st.session_state.preset_values = {
                'server_ip': '192.168.1.100',
                'share_name': 'SharedFolder',
                'username': 'pi',
                'mount_point': '/mnt/pi-omv'
            }
            st.success("OMV preset loaded! Fill in your specific details.")
        
        # Common presets
        st.markdown("**Common Configurations:**")
        st.markdown("• **OMV Default**: SharedFolder")
        st.markdown("• **Samba**: Usually on port 445")
        st.markdown("• **Default user**: pi or admin")
        
        st.markdown("---")
        st.subheader("Connection Help")
        
        with st.expander("Troubleshooting"):
            st.markdown("**Common Issues:**")
            st.markdown("• Check IP address is correct")
            st.markdown("• Verify share name exists")
            st.markdown("• Ensure SMB is enabled on server")
            st.markdown("• Check firewall settings")
            st.markdown("• Try different SMB protocol versions")
        
        with st.expander("Raspberry Pi OMV Setup"):
            st.markdown("**Steps to enable SMB on OMV:**")
            st.markdown("1. Login to OMV web interface")
            st.markdown("2. Go to Services → SMB/CIFS")
            st.markdown("3. Enable SMB service")
            st.markdown("4. Create shared folder")
            st.markdown("5. Set permissions")
            st.markdown("6. Note the IP address")

with tab2:
    st.subheader("Network Device Scanner")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        network_range = st.text_input(
            "Network Range",
            value="192.168.1.0/24",
            placeholder="192.168.1.0/24"
        )
        
        if st.button("Scan Network"):
            with st.spinner("Scanning network for devices..."):
                devices = scan_network_devices(network_range)
                
                if devices:
                    st.success(f"Found {len(devices)} devices:")
                    
                    for device in devices:
                        with st.container():
                            device_col1, device_col2, device_col3 = st.columns([2, 2, 1])
                            
                            with device_col1:
                                st.write(f"**IP:** {device['ip']}")
                                if device.get('hostname'):
                                    st.caption(f"Hostname: {device['hostname']}")
                            
                            with device_col2:
                                if device.get('mac'):
                                    st.caption(f"MAC: {device['mac']}")
                                if device.get('vendor'):
                                    st.caption(f"Vendor: {device['vendor']}")
                            
                            with device_col3:
                                if st.button("Use IP", key=f"use_ip_{device['ip']}"):
                                    st.session_state.selected_ip = device['ip']
                                    st.success(f"Selected IP: {device['ip']}")
                            
                            st.markdown("---")
                else:
                    st.warning("No devices found on the network")
    
    with col2:
        st.subheader("Network Info")
        
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            st.metric("Local IP", local_ip)
            st.metric("Hostname", hostname)
        except Exception as e:
            st.error(f"Error getting network info: {e}")
        
        st.markdown("---")
        st.subheader("Common Ports")
        st.markdown("• SMB/CIFS: 445, 139")
        st.markdown("• FTP: 21")
        st.markdown("• SSH: 22")
        st.markdown("• HTTP: 80")
        st.markdown("• HTTPS: 443")

with tab3:
    st.subheader("Mount Status")
    
    mounted_shares = get_mounted_shares()
    
    if mounted_shares:
        st.success(f"Found {len(mounted_shares)} mounted shares:")
        
        for share in mounted_shares:
            with st.container():
                share_col1, share_col2, share_col3 = st.columns([2, 2, 1])
                
                with share_col1:
                    st.write(f"**Mount Point:** {share['mount_point']}")
                    st.caption(f"Source: {share['source']}")
                
                with share_col2:
                    st.write(f"**Type:** {share['type']}")
                    if share.get('options'):
                        st.caption(f"Options: {share['options']}")
                
                with share_col3:
                    if st.button("Unmount", key=f"unmount_{share['mount_point']}"):
                        result = unmount_smb_share(share['mount_point'])
                        if result['success']:
                            st.success("Share unmounted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to unmount: {result.get('error', 'Unknown error')}")
                
                # Show mount statistics if available
                if share.get('stats'):
                    stats = share['stats']
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    with stat_col1:
                        st.metric("Total", f"{stats.get('total_gb', 0):.1f} GB")
                    with stat_col2:
                        st.metric("Used", f"{stats.get('used_gb', 0):.1f} GB")
                    with stat_col3:
                        st.metric("Free", f"{stats.get('free_gb', 0):.1f} GB")
                
                st.markdown("---")
    else:
        st.info("No mounted network shares found")
    
    # Manual mount/unmount
    st.subheader("Manual Mount/Unmount")
    
    with st.expander("Advanced Operations"):
        manual_mount_point = st.text_input("Mount Point", placeholder="/mnt/manual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create Mount Point"):
                if manual_mount_point:
                    try:
                        os.makedirs(manual_mount_point, exist_ok=True)
                        st.success(f"Created mount point: {manual_mount_point}")
                    except Exception as e:
                        st.error(f"Error creating mount point: {e}")
                else:
                    st.error("Please enter a mount point")
        
        with col2:
            if st.button("Remove Mount Point"):
                if manual_mount_point:
                    try:
                        if os.path.exists(manual_mount_point) and os.path.isdir(manual_mount_point):
                            os.rmdir(manual_mount_point)
                            st.success(f"Removed mount point: {manual_mount_point}")
                        else:
                            st.error("Mount point does not exist or is not empty")
                    except Exception as e:
                        st.error(f"Error removing mount point: {e}")
                else:
                    st.error("Please enter a mount point")

with tab4:
    st.subheader("Configuration")
    
    # Load current configuration
    current_config = get_network_storage_config()
    
    with st.form("config_form"):
        st.markdown("**Default Connection Settings**")
        
        default_server = st.text_input(
            "Default Server IP",
            value=current_config.get('server_ip', ''),
            placeholder="192.168.1.100"
        )
        
        default_share = st.text_input(
            "Default Share Name",
            value=current_config.get('share_name', ''),
            placeholder="SharedFolder"
        )
        
        default_username = st.text_input(
            "Default Username",
            value=current_config.get('username', ''),
            placeholder="pi"
        )
        
        default_mount = st.text_input(
            "Default Mount Point",
            value=current_config.get('mount_point', '/mnt/pi-nas'),
            placeholder="/mnt/pi-nas"
        )
        
        # Advanced settings
        st.markdown("**Advanced Settings**")
        
        smb_version = st.selectbox(
            "SMB Protocol Version",
            ["auto", "1.0", "2.0", "2.1", "3.0"],
            index=0
        )
        
        auto_mount = st.checkbox(
            "Auto-mount on startup",
            value=current_config.get('auto_mount', False)
        )
        
        mount_timeout = st.number_input(
            "Mount Timeout (seconds)",
            min_value=5,
            max_value=120,
            value=current_config.get('mount_timeout', 30)
        )
        
        if st.form_submit_button("Save Configuration"):
            new_config = {
                'server_ip': default_server,
                'share_name': default_share,
                'username': default_username,
                'mount_point': default_mount,
                'smb_version': smb_version,
                'auto_mount': auto_mount,
                'mount_timeout': mount_timeout
            }
            
            if save_network_storage_config(new_config):
                st.success("Configuration saved successfully!")
            else:
                st.error("Failed to save configuration")
    
    # Configuration backup/restore
    st.markdown("---")
    st.subheader("Backup & Restore")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Export Configuration**")
        if st.button("Export Config"):
            config_json = json.dumps(current_config, indent=2)
            st.download_button(
                "Download Config",
                config_json,
                file_name="pinas_network_config.json",
                mime="application/json"
            )
    
    with col2:
        st.markdown("**Import Configuration**")
        uploaded_config = st.file_uploader("Upload Config", type=['json'])
        if uploaded_config:
            try:
                imported_config = json.load(uploaded_config)
                if st.button("Import Config"):
                    if save_network_storage_config(imported_config):
                        st.success("Configuration imported successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to import configuration")
            except Exception as e:
                st.error(f"Error reading config file: {e}")
