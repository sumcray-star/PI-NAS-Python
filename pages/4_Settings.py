import streamlit as st
import os
import json
import shutil
from pathlib import Path
from utils.auth import is_authenticated, change_password, get_all_users, delete_user
from utils.file_manager import get_directory_size, cleanup_thumbnails
from utils.network_storage import get_network_storage_config, save_network_storage_config

# Check authentication
if not is_authenticated():
    st.error("Please login to access this page")
    st.stop()

st.set_page_config(page_title="Settings - PI-NAS", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings")

# Settings tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Account", "Media", "Storage", "Network", "System"])

with tab1:
    st.subheader("Account Settings")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Change password
        with st.form("change_password"):
            st.markdown("**Change Password**")
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password"):
                if not current_password or not new_password or not confirm_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("New passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    if change_password(st.session_state.username, current_password, new_password):
                        st.success("Password changed successfully!")
                    else:
                        st.error("Current password is incorrect")
    
    with col2:
        st.subheader("Account Info")
        st.metric("Username", st.session_state.username)
        st.metric("Login Time", st.session_state.get('login_time', 'Unknown'))
        
        # User management (admin only)
        if st.session_state.get('is_admin', False):
            st.markdown("---")
            st.subheader("User Management")
            
            users = get_all_users()
            st.metric("Total Users", len(users))
            
            for user in users:
                if user != st.session_state.username:
                    col_user, col_delete = st.columns([3, 1])
                    with col_user:
                        st.text(user)
                    with col_delete:
                        if st.button("Delete", key=f"delete_user_{user}"):
                            if delete_user(user):
                                st.success(f"User {user} deleted")
                                st.rerun()
                            else:
                                st.error("Failed to delete user")

with tab2:
    st.subheader("Media Settings")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Media organization settings
        st.markdown("**File Organization**")
        
        auto_organize = st.checkbox("Auto-organize uploaded files by type", value=True)
        generate_thumbnails = st.checkbox("Generate thumbnails for videos", value=True)
        auto_cleanup = st.checkbox("Auto-cleanup old thumbnails", value=False)
        
        if auto_cleanup:
            cleanup_days = st.number_input("Delete thumbnails older than (days)", min_value=1, max_value=365, value=30)
        
        # Media quality settings
        st.markdown("**Media Quality**")
        
        video_quality = st.selectbox(
            "Default video quality",
            ["Original", "1080p", "720p", "480p"],
            index=0
        )
        
        audio_quality = st.selectbox(
            "Default audio quality",
            ["Original", "320kbps", "192kbps", "128kbps"],
            index=0
        )
        
        # Thumbnail settings
        st.markdown("**Thumbnail Settings**")
        
        thumbnail_size = st.selectbox(
            "Thumbnail size",
            ["Small (150px)", "Medium (300px)", "Large (500px)"],
            index=1
        )
        
        thumbnail_quality = st.slider("Thumbnail quality", min_value=50, max_value=100, value=80)
        
        if st.button("Save Media Settings"):
            media_config = {
                'auto_organize': auto_organize,
                'generate_thumbnails': generate_thumbnails,
                'auto_cleanup': auto_cleanup,
                'cleanup_days': cleanup_days if auto_cleanup else 30,
                'video_quality': video_quality,
                'audio_quality': audio_quality,
                'thumbnail_size': thumbnail_size,
                'thumbnail_quality': thumbnail_quality
            }
            
            # Save to config file
            config_path = Path("config/media_config.json")
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(media_config, f, indent=2)
            
            st.success("Media settings saved!")
    
    with col2:
        st.subheader("Media Statistics")
        
        # Directory sizes
        try:
            uploads_size = get_directory_size("media/uploads")
            thumbnails_size = get_directory_size("media/thumbnails")
            
            st.metric("Uploads Size", f"{uploads_size / (1024**3):.2f} GB")
            st.metric("Thumbnails Size", f"{thumbnails_size / (1024**2):.1f} MB")
        except Exception as e:
            st.error(f"Error getting directory sizes: {e}")
        
        # File counts by type
        try:
            media_path = Path("media/uploads")
            if media_path.exists():
                video_count = len(list(media_path.glob("**/*.mp4"))) + len(list(media_path.glob("**/*.avi")))
                audio_count = len(list(media_path.glob("**/*.mp3"))) + len(list(media_path.glob("**/*.wav")))
                image_count = len(list(media_path.glob("**/*.jpg"))) + len(list(media_path.glob("**/*.png")))
                
                st.metric("Video Files", video_count)
                st.metric("Audio Files", audio_count)
                st.metric("Image Files", image_count)
        except Exception as e:
            st.error(f"Error counting files: {e}")
        
        # Cleanup actions
        st.markdown("---")
        st.subheader("Cleanup Actions")
        
        if st.button("Clean Thumbnails"):
            try:
                cleanup_thumbnails()
                st.success("Thumbnails cleaned up!")
            except Exception as e:
                st.error(f"Error cleaning thumbnails: {e}")

with tab3:
    st.subheader("Storage Settings")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Storage paths
        st.markdown("**Storage Paths**")
        
        media_path = st.text_input("Media Upload Path", value="media/uploads")
        thumbnail_path = st.text_input("Thumbnail Path", value="media/thumbnails")
        temp_path = st.text_input("Temporary Path", value="temp")
        
        # Storage limits
        st.markdown("**Storage Limits**")
        
        max_file_size = st.number_input("Max file size (MB)", min_value=1, max_value=10000, value=1000)
        max_total_size = st.number_input("Max total storage (GB)", min_value=1, max_value=1000, value=100)
        
        # Auto-cleanup settings
        st.markdown("**Auto-cleanup**")
        
        enable_auto_cleanup = st.checkbox("Enable automatic cleanup", value=False)
        
        if enable_auto_cleanup:
            cleanup_threshold = st.slider("Cleanup when storage exceeds (%)", min_value=70, max_value=95, value=85)
            cleanup_method = st.selectbox("Cleanup method", ["Delete oldest files", "Delete largest files", "Ask user"])
        
        if st.button("Save Storage Settings"):
            storage_config = {
                'media_path': media_path,
                'thumbnail_path': thumbnail_path,
                'temp_path': temp_path,
                'max_file_size': max_file_size,
                'max_total_size': max_total_size,
                'enable_auto_cleanup': enable_auto_cleanup,
                'cleanup_threshold': cleanup_threshold if enable_auto_cleanup else 85,
                'cleanup_method': cleanup_method if enable_auto_cleanup else "Ask user"
            }
            
            # Save to config file
            config_path = Path("config/storage_config.json")
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(storage_config, f, indent=2)
            
            st.success("Storage settings saved!")
    
    with col2:
        st.subheader("Storage Status")
        
        try:
            import psutil
            
            # Local storage
            disk_usage = psutil.disk_usage('.')
            total_gb = disk_usage.total / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            usage_percent = (used_gb / total_gb) * 100
            
            st.metric("Total Storage", f"{total_gb:.1f} GB")
            st.metric("Used Storage", f"{used_gb:.1f} GB")
            st.metric("Free Storage", f"{free_gb:.1f} GB")
            st.progress(usage_percent / 100, f"Usage: {usage_percent:.1f}%")
            
            # Warning indicators
            if usage_percent > 90:
                st.error("⚠️ Storage almost full!")
            elif usage_percent > 80:
                st.warning("⚠️ Storage getting full")
            else:
                st.success("✅ Storage healthy")
            
        except Exception as e:
            st.error(f"Error getting storage info: {e}")

with tab4:
    st.subheader("Network Settings")
    
    # Network storage settings
    st.markdown("**Network Storage**")
    
    network_config = get_network_storage_config()
    
    enable_network_storage = st.checkbox("Enable network storage", value=network_config.get('enabled', False))
    
    if enable_network_storage:
        default_protocol = st.selectbox("Default protocol", ["SMB/CIFS", "NFS", "FTP"], index=0)
        connection_timeout = st.number_input("Connection timeout (seconds)", min_value=5, max_value=60, value=30)
        retry_attempts = st.number_input("Retry attempts", min_value=1, max_value=10, value=3)
        
        # Network discovery
        st.markdown("**Network Discovery**")
        enable_discovery = st.checkbox("Enable automatic network discovery", value=True)
        discovery_interval = st.number_input("Discovery interval (minutes)", min_value=5, max_value=60, value=15)
    
    # Server settings
    st.markdown("**Server Settings**")
    
    server_port = st.number_input("PI-NAS server port", min_value=1000, max_value=65535, value=5000)
    enable_https = st.checkbox("Enable HTTPS", value=False)
    
    if enable_https:
        cert_path = st.text_input("Certificate path", placeholder="/path/to/certificate.pem")
        key_path = st.text_input("Private key path", placeholder="/path/to/private.key")
    
    if st.button("Save Network Settings"):
        network_settings = {
            'enabled': enable_network_storage,
            'default_protocol': default_protocol if enable_network_storage else "SMB/CIFS",
            'connection_timeout': connection_timeout if enable_network_storage else 30,
            'retry_attempts': retry_attempts if enable_network_storage else 3,
            'enable_discovery': enable_discovery if enable_network_storage else True,
            'discovery_interval': discovery_interval if enable_network_storage else 15,
            'server_port': server_port,
            'enable_https': enable_https,
            'cert_path': cert_path if enable_https else "",
            'key_path': key_path if enable_https else ""
        }
        
        # Update network config
        network_config.update(network_settings)
        save_network_storage_config(network_config)
        
        st.success("Network settings saved!")

with tab5:
    st.subheader("System Settings")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Application settings
        st.markdown("**Application Settings**")
        
        app_name = st.text_input("Application name", value="PI-NAS")
        app_theme = st.selectbox("Theme", ["Light", "Dark", "Auto"], index=0)
        language = st.selectbox("Language", ["English", "Spanish", "French", "German"], index=0)
        
        # Logging settings
        st.markdown("**Logging**")
        
        log_level = st.selectbox("Log level", ["DEBUG", "INFO", "WARNING", "ERROR"], index=1)
        max_log_size = st.number_input("Max log file size (MB)", min_value=1, max_value=100, value=10)
        log_retention = st.number_input("Log retention (days)", min_value=1, max_value=365, value=30)
        
        # Backup settings
        st.markdown("**Backup**")
        
        enable_auto_backup = st.checkbox("Enable automatic backups", value=False)
        
        if enable_auto_backup:
            backup_interval = st.selectbox("Backup interval", ["Daily", "Weekly", "Monthly"], index=1)
            backup_location = st.text_input("Backup location", placeholder="/path/to/backup")
            backup_retention = st.number_input("Backup retention (days)", min_value=1, max_value=365, value=30)
        
        if st.button("Save System Settings"):
            system_config = {
                'app_name': app_name,
                'app_theme': app_theme,
                'language': language,
                'log_level': log_level,
                'max_log_size': max_log_size,
                'log_retention': log_retention,
                'enable_auto_backup': enable_auto_backup,
                'backup_interval': backup_interval if enable_auto_backup else "Weekly",
                'backup_location': backup_location if enable_auto_backup else "",
                'backup_retention': backup_retention if enable_auto_backup else 30
            }
            
            # Save to config file
            config_path = Path("config/system_config.json")
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(system_config, f, indent=2)
            
            st.success("System settings saved!")
    
    with col2:
        st.subheader("System Information")
        
        try:
            import platform
            import psutil
            
            # System info
            st.text(f"OS: {platform.system()} {platform.release()}")
            st.text(f"Python: {platform.python_version()}")
            st.text(f"CPU: {psutil.cpu_count()} cores")
            
            # Memory info
            memory = psutil.virtual_memory()
            st.text(f"RAM: {memory.total / (1024**3):.1f} GB")
            st.text(f"RAM Usage: {memory.percent}%")
            
            # Uptime
            import time
            uptime = time.time() - psutil.boot_time()
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            st.text(f"Uptime: {hours}h {minutes}m")
            
        except Exception as e:
            st.error(f"Error getting system info: {e}")
        
        st.markdown("---")
        st.subheader("Maintenance")
        
        if st.button("Clear Cache"):
            try:
                # Clear thumbnail cache
                thumb_path = Path("media/thumbnails")
                if thumb_path.exists():
                    shutil.rmtree(thumb_path)
                    thumb_path.mkdir(exist_ok=True)
                
                # Clear temp files
                temp_path = Path("temp")
                if temp_path.exists():
                    shutil.rmtree(temp_path)
                    temp_path.mkdir(exist_ok=True)
                
                st.success("Cache cleared!")
            except Exception as e:
                st.error(f"Error clearing cache: {e}")
        
        if st.button("Restart Application"):
            st.warning("Application restart requested. Please manually restart the server.")
        
        # Export/Import settings
        st.markdown("---")
        st.subheader("Configuration")
        
        if st.button("Export All Settings"):
            try:
                # Collect all config files
                all_config = {}
                
                config_files = [
                    "config/media_config.json",
                    "config/storage_config.json",
                    "config/system_config.json"
                ]
                
                for config_file in config_files:
                    if os.path.exists(config_file):
                        with open(config_file, 'r') as f:
                            config_name = Path(config_file).stem
                            all_config[config_name] = json.load(f)
                
                config_json = json.dumps(all_config, indent=2)
                st.download_button(
                    "Download All Settings",
                    config_json,
                    file_name="pinas_all_settings.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Error exporting settings: {e}")
