import streamlit as st
import os
from pathlib import Path
from utils.auth import is_authenticated, logout_user
from utils.file_manager import ensure_directories
from utils.network_storage import auto_mount_network_storage

# Configure page
st.set_page_config(
    page_title="PI-NAS Media Server",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize directories
ensure_directories()

# Auto-mount network storage
auto_mount_network_storage()

# Authentication check
if not is_authenticated():
    st.switch_page("pages/4_Settings.py")
    st.stop()

# Main app
def main():
    st.title("🎬 PI-NAS Media Server")
    st.markdown("### Your Personal Media Library")
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/FF6B6B/FFFFFF?text=PI-NAS", width=200)
        st.markdown("---")
        
        # User info
        username = st.session_state.get('username', 'User')
        st.write(f"Welcome, **{username}**")
        
        # Logout button
        if st.button("🚪 Logout"):
            logout_user()
            st.rerun()
    
    # Main content
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">📚 Media Library</h3>
            <p style="color: white; margin: 10px 0;">Browse and stream your media files</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Open Media Library", key="media_lib", use_container_width=True):
            st.switch_page("pages/1_Media_Library.py")
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">📤 Upload Media</h3>
            <p style="color: white; margin: 10px 0;">Upload files to your Raspberry Pi</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Upload Files", key="upload", use_container_width=True):
            st.switch_page("pages/2_Upload_Media.py")
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">🌐 Network Storage</h3>
            <p style="color: white; margin: 10px 0;">Configure Raspberry Pi connection</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Network Settings", key="network", use_container_width=True):
            st.switch_page("pages/3_Network_Storage.py")
    
    # Quick stats
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    
    # Get basic stats
    from utils.media_handler import get_media_stats
    stats = get_media_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Files", stats.get('total_files', 0))
    
    with col2:
        st.metric("Videos", stats.get('videos', 0))
    
    with col3:
        st.metric("Images", stats.get('images', 0))
    
    with col4:
        st.metric("Documents", stats.get('documents', 0))
    
    # Recent files
    st.markdown("### 📋 Recent Files")
    from utils.media_handler import get_recent_media
    recent_files = get_recent_media(5)
    
    if recent_files:
        for file in recent_files:
            with st.expander(f"📁 {file['name']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Type:** {file['type']}")
                    st.write(f"**Size:** {file['size']}")
                    st.write(f"**Modified:** {file['modified']}")
                with col2:
                    if st.button("Open", key=f"open_{file['name']}"):
                        st.switch_page("pages/1_Media_Library.py")
    else:
        st.info("No files found. Upload some media to get started!")

if __name__ == "__main__":
    main()