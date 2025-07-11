import streamlit as st
import os
from utils.network_storage import (
    get_network_storage_config, save_network_storage_config,
    test_smb_connection, mount_smb_share, unmount_smb_share,
    is_mount_point, get_mounted_shares, scan_network_devices,
    check_network_storage, get_storage_stats
)
from utils.auth import is_authenticated

# Check authentication
if not is_authenticated():
    st.switch_page("pages/4_Settings.py")
    st.stop()

st.set_page_config(
    page_title="Network Storage - PI-NAS",
    page_icon="🌐",
    layout="wide"
)

def main():
    st.title("🌐 Network Storage")
    st.markdown("Configure connection to your Raspberry Pi storage")
    
    # Sidebar - Connection Status
    with st.sidebar:
        st.header("🔗 Connection Status")
        show_connection_status()
        
        st.markdown("---")
        
        # Quick actions
        st.header("⚡ Quick Actions")
        
        if st.button("🔄 Refresh Connection", use_container_width=True):
            st.rerun()
        
        if st.button("🔍 Scan Network", use_container_width=True):
            scan_network()
        
        if st.button("📊 Storage Stats", use_container_width=True):
            show_storage_stats()
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📡 Configuration", "🔍 Network Scan", "📊 Status"])
    
    with tab1:
        configure_network_storage()
    
    with tab2:
        network_scan_tab()
    
    with tab3:
        storage_status_tab()

def show_connection_status():
    """Show current connection status"""
    config = get_network_storage_config()
    
    if config.get('enabled', False):
        server_ip = config.get('server_ip', 'N/A')
        mount_point = config.get('mount_point', 'N/A')
        
        # Check if mounted
        if is_mount_point(mount_point):
            st.success(f"✅ Connected to {server_ip}")
            st.info(f"📍 Mounted at: {mount_point}")
        else:
            st.warning(f"⚠️ Configured but not mounted")
            st.info(f"📍 Server: {server_ip}")
            
            # Mount button
            if st.button("🔗 Mount Storage", use_container_width=True):
                mount_network_storage()
    else:
        st.error("❌ Not configured")

def configure_network_storage():
    """Network storage configuration interface"""
    st.header("📡 Raspberry Pi Configuration")
    
    # Load current config
    config = get_network_storage_config()
    
    with st.form("network_config"):
        st.markdown("### Connection Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            server_ip = st.text_input(
                "Raspberry Pi IP Address",
                value=config.get('server_ip', '192.168.1.100'),
                help="IP address of your Raspberry Pi"
            )
            
            share_name = st.text_input(
                "Share Name",
                value=config.get('share_name', 'media'),
                help="Name of the shared folder on Pi"
            )
            
            username = st.text_input(
                "Username",
                value=config.get('username', 'pi'),
                help="Username for accessing the share"
            )
        
        with col2:
            password = st.text_input(
                "Password",
                type="password",
                value=config.get('password', ''),
                help="Password for the username"
            )
            
            mount_point = st.text_input(
                "Mount Point",
                value=config.get('mount_point', '/mnt/pi-nas'),
                help="Local directory where Pi storage will be mounted"
            )
            
            protocol = st.selectbox(
                "Protocol",
                ["smb", "nfs"],
                index=0 if config.get('protocol', 'smb') == 'smb' else 1
            )
        
        st.markdown("### Advanced Settings")
        
        col3, col4 = st.columns(2)
        
        with col3:
            auto_mount = st.checkbox(
                "Auto-mount on startup",
                value=config.get('auto_mount', True)
            )
            
            enabled = st.checkbox(
                "Enable network storage",
                value=config.get('enabled', False)
            )
        
        with col4:
            port = st.number_input(
                "Port",
                value=config.get('port', 445),
                min_value=1,
                max_value=65535
            )
            
            mount_timeout = st.number_input(
                "Mount Timeout (seconds)",
                value=config.get('mount_timeout', 30),
                min_value=5,
                max_value=120
            )
        
        # Form buttons
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            test_connection = st.form_submit_button("🧪 Test Connection", type="secondary")
        
        with col_btn2:
            save_config = st.form_submit_button("💾 Save Configuration", type="primary")
        
        with col_btn3:
            mount_storage = st.form_submit_button("🔗 Mount Storage", type="secondary")
    
    # Handle form actions
    if test_connection:
        test_network_connection(server_ip, share_name, username, password)
    
    if save_config:
        new_config = {
            'server_ip': server_ip,
            'share_name': share_name,
            'username': username,
            'password': password,
            'mount_point': mount_point,
            'protocol': protocol,
            'port': port,
            'auto_mount': auto_mount,
            'mount_timeout': mount_timeout,
            'enabled': enabled
        }
        
        save_network_storage_config(new_config)
        st.success("✅ Configuration saved successfully!")
        st.rerun()
    
    if mount_storage:
        mount_network_storage(server_ip, share_name, username, password, mount_point)

def test_network_connection(server_ip, share_name, username, password):
    """Test network connection to Raspberry Pi"""
    with st.spinner("Testing connection..."):
        result = test_smb_connection(server_ip, share_name, username, password)
        
        if result.get('success', False):
            st.success(f"✅ Connection successful! Found share: {share_name}")
        else:
            st.error(f"❌ Connection failed: {result.get('error', 'Unknown error')}")

def mount_network_storage(server_ip=None, share_name=None, username=None, password=None, mount_point=None):
    """Mount network storage"""
    if not all([server_ip, share_name, username, mount_point]):
        config = get_network_storage_config()
        server_ip = server_ip or config.get('server_ip')
        share_name = share_name or config.get('share_name')
        username = username or config.get('username')
        password = password or config.get('password', '')
        mount_point = mount_point or config.get('mount_point')
    
    with st.spinner("Mounting storage..."):
        result = mount_smb_share(server_ip, share_name, username, password, mount_point)
        
        if result.get('success', False):
            st.success(f"✅ Storage mounted successfully at {mount_point}")
            st.rerun()
        else:
            st.error(f"❌ Mount failed: {result.get('error', 'Unknown error')}")

def network_scan_tab():
    """Network scanning interface"""
    st.header("🔍 Network Device Scanner")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Scan for Raspberry Pi devices")
        
        # Network range input
        network_range = st.text_input(
            "Network Range",
            value="192.168.1.0/24",
            help="CIDR notation for network range to scan"
        )
        
        if st.button("🔍 Start Scan", type="primary"):
            scan_network(network_range)
    
    with col2:
        st.markdown("### Tips")
        st.info("""
        **Common network ranges:**
        - 192.168.1.0/24
        - 192.168.0.0/24
        - 10.0.0.0/24
        
        **Look for:**
        - Devices with open port 445 (SMB)
        - Raspberry Pi hostnames
        - Known Pi IP addresses
        """)

def scan_network(network_range="192.168.1.0/24"):
    """Scan network for devices"""
    with st.spinner(f"Scanning network {network_range}..."):
        devices = scan_network_devices(network_range)
        
        if devices:
            st.success(f"Found {len(devices)} devices:")
            
            for device in devices:
                with st.expander(f"📱 {device.get('ip', 'Unknown')} - {device.get('hostname', 'Unknown Host')}"):
                    st.write(f"**IP:** {device.get('ip', 'N/A')}")
                    st.write(f"**Hostname:** {device.get('hostname', 'N/A')}")
                    st.write(f"**MAC:** {device.get('mac', 'N/A')}")
                    
                    if device.get('smb_available', False):
                        st.success("✅ SMB service available")
                        
                        # Quick connect button
                        if st.button(f"🔗 Use This Device", key=f"connect_{device['ip']}"):
                            st.session_state['suggested_ip'] = device['ip']
                            st.info(f"Device IP {device['ip']} ready to use in configuration")
                    else:
                        st.info("ℹ️ SMB service not detected")
        else:
            st.warning("No devices found in the specified range")

def storage_status_tab():
    """Storage status and statistics"""
    st.header("📊 Storage Status")
    
    config = get_network_storage_config()
    
    if not config.get('enabled', False):
        st.warning("Network storage is not enabled")
        return
    
    # Connection status
    st.subheader("🔗 Connection Status")
    
    mount_point = config.get('mount_point', '/mnt/pi-nas')
    
    if is_mount_point(mount_point):
        st.success("✅ Storage is mounted and accessible")
        
        # Storage statistics
        stats = get_storage_stats()
        if stats:
            st.subheader("💾 Storage Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Space", f"{stats.get('total_gb', 0):.1f} GB")
            
            with col2:
                st.metric("Used Space", f"{stats.get('used_gb', 0):.1f} GB")
            
            with col3:
                st.metric("Free Space", f"{stats.get('free_gb', 0):.1f} GB")
            
            with col4:
                st.metric("Usage", f"{stats.get('usage_percent', 0):.1f}%")
            
            # Usage chart
            if stats.get('usage_percent', 0) > 0:
                st.subheader("📈 Disk Usage")
                
                usage_data = {
                    'Used': stats.get('used_gb', 0),
                    'Free': stats.get('free_gb', 0)
                }
                
                st.bar_chart(usage_data)
    else:
        st.error("❌ Storage is not mounted")
        
        # Mount button
        if st.button("🔗 Mount Storage", type="primary"):
            mount_network_storage()
    
    # Show mounted shares
    st.subheader("📁 Mounted Shares")
    mounted_shares = get_mounted_shares()
    
    if mounted_shares:
        for share in mounted_shares:
            with st.expander(f"📂 {share.get('mount_point', 'Unknown')}"):
                st.write(f"**Device:** {share.get('device', 'N/A')}")
                st.write(f"**Type:** {share.get('type', 'N/A')}")
                st.write(f"**Options:** {share.get('options', 'N/A')}")
                
                # Unmount button
                if st.button(f"🔗 Unmount", key=f"unmount_{share.get('mount_point', '')}"):
                    unmount_result = unmount_smb_share(share.get('mount_point', ''))
                    if unmount_result.get('success', False):
                        st.success("✅ Storage unmounted successfully")
                        st.rerun()
                    else:
                        st.error(f"❌ Unmount failed: {unmount_result.get('error', 'Unknown error')}")
    else:
        st.info("No network shares currently mounted")

def show_storage_stats():
    """Show storage statistics in sidebar"""
    stats = get_storage_stats()
    
    if stats:
        st.sidebar.markdown("### 💾 Storage")
        st.sidebar.metric("Total", f"{stats.get('total_gb', 0):.1f} GB")
        st.sidebar.metric("Used", f"{stats.get('used_gb', 0):.1f} GB")
        st.sidebar.metric("Free", f"{stats.get('free_gb', 0):.1f} GB")
        
        # Usage progress
        usage_percent = stats.get('usage_percent', 0)
        st.sidebar.progress(usage_percent / 100)
        st.sidebar.caption(f"Usage: {usage_percent:.1f}%")
    else:
        st.sidebar.info("Storage stats unavailable")

if __name__ == "__main__":
    main()