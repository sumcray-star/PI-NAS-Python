import streamlit as st
import os
import json
from datetime import datetime
import psutil
from pathlib import Path
from utils.auth import authenticate_user, is_authenticated, logout_user
from utils.media_handler import get_recent_media, get_media_stats
from utils.network_storage import check_network_storage, get_storage_stats
from utils.file_manager import ensure_directories

# Page configuration
st.set_page_config(
    page_title="PI-NAS - Home Media Server",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize directories
ensure_directories()

# Authentication check
if not is_authenticated():
    st.title("🎬 PI-NAS - Personal Media Server")
    st.markdown("---")
    
    # Login form
    with st.form("login_form"):
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if authenticate_user(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    # Registration form
    with st.expander("Don't have an account? Register here"):
        with st.form("register_form"):
            st.subheader("Register")
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif new_username and new_password:
                    from utils.auth import register_user
                    if register_user(new_username, new_password):
                        st.success("Registration successful! You can now login.")
                    else:
                        st.error("Username already exists")
                else:
                    st.error("Please fill in all fields")
    
    st.stop()

# Main application
st.title("🎬 PI-NAS Dashboard")

# Sidebar
with st.sidebar:
    st.markdown(f"Welcome, **{st.session_state.username}**!")
    st.markdown("---")
    
    # Quick stats
    st.subheader("Quick Stats")
    media_stats = get_media_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Files", media_stats.get('total_files', 0))
        st.metric("Videos", media_stats.get('videos', 0))
    with col2:
        st.metric("Audio Files", media_stats.get('audio', 0))
        st.metric("Images", media_stats.get('images', 0))
    
    # Storage info
    st.markdown("---")
    st.subheader("Storage")
    try:
        disk_usage = psutil.disk_usage('.')
        total_gb = disk_usage.total / (1024**3)
        used_gb = disk_usage.used / (1024**3)
        free_gb = disk_usage.free / (1024**3)
        usage_percent = (used_gb / total_gb) * 100
        
        st.metric("Total Storage", f"{total_gb:.1f} GB")
        st.metric("Used", f"{used_gb:.1f} GB")
        st.metric("Free", f"{free_gb:.1f} GB")
        st.progress(usage_percent / 100, f"Usage: {usage_percent:.1f}%")
    except Exception as e:
        st.error(f"Error getting storage info: {e}")
    
    # Network storage status
    st.markdown("---")
    st.subheader("Network Storage")
    network_status = check_network_storage()
    if network_status['connected']:
        st.success("✅ Connected")
        if network_status.get('stats'):
            stats = network_status['stats']
            st.metric("Network Used", f"{stats.get('used_gb', 0):.1f} GB")
            st.metric("Network Free", f"{stats.get('free_gb', 0):.1f} GB")
    else:
        st.error("❌ Disconnected")
    
    st.markdown("---")
    if st.button("Logout"):
        logout_user()
        st.rerun()

# Main dashboard content
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader("Recent Media")
    recent_media = get_recent_media(limit=10)
    
    if recent_media:
        for media in recent_media:
            with st.container():
                media_col1, media_col2, media_col3 = st.columns([1, 3, 1])
                
                with media_col1:
                    # Media type icon
                    file_ext = media['name'].split('.')[-1].lower()
                    if file_ext in ['mp4', 'avi', 'mkv', 'mov', 'wmv']:
                        st.markdown("🎬")
                    elif file_ext in ['mp3', 'wav', 'flac', 'aac']:
                        st.markdown("🎵")
                    elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                        st.markdown("🖼️")
                    else:
                        st.markdown("📄")
                
                with media_col2:
                    st.write(f"**{media['name']}**")
                    st.caption(f"Added: {media['date_added']} • Size: {media['size']}")
                
                with media_col3:
                    if st.button("Play", key=f"play_{media['name']}"):
                        st.session_state.selected_media = media
                        st.switch_page("pages/1_Media_Library.py")
                
                st.markdown("---")
    else:
        st.info("No media files found. Upload some media to get started!")

with col2:
    st.subheader("System Status")
    
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    st.metric("CPU Usage", f"{cpu_percent}%")
    st.progress(cpu_percent / 100)
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    st.metric("Memory Usage", f"{memory_percent}%")
    st.progress(memory_percent / 100)
    
    # Network connectivity
    st.markdown("---")
    st.subheader("Network")
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        st.success("✅ Internet Connected")
    except:
        st.error("❌ No Internet")

with col3:
    st.subheader("Quick Actions")
    
    if st.button("📁 Browse Media", use_container_width=True):
        st.switch_page("pages/1_Media_Library.py")
    
    if st.button("⬆️ Upload Files", use_container_width=True):
        st.switch_page("pages/2_Upload_Media.py")
    
    if st.button("🔗 Network Storage", use_container_width=True):
        st.switch_page("pages/3_Network_Storage.py")
    
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/4_Settings.py")
    
    st.markdown("---")
    st.subheader("Recently Active")
    
    # Show recent activity
    if 'recent_activity' in st.session_state:
        for activity in st.session_state.recent_activity[-5:]:
            st.caption(f"• {activity}")
    else:
        st.caption("No recent activity")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 14px;'>"
    "PI-NAS v1.0 - Personal Media Server"
    "</div>",
    unsafe_allow_html=True
)
