import streamlit as st
import os
from pathlib import Path
from utils.auth import is_authenticated
from utils.file_manager import clean_filename, move_file, get_file_info, validate_file_upload
from utils.media_handler import organize_media_file, generate_thumbnail
from utils.network_storage import get_network_storage_config, sync_media_to_network_storage

# Check authentication
if not is_authenticated():
    st.switch_page("pages/4_Settings.py")
    st.stop()

st.set_page_config(
    page_title="Upload Media - PI-NAS",
    page_icon="📤",
    layout="wide"
)

def main():
    st.title("📤 Upload Media")
    st.markdown("Upload files to your Raspberry Pi storage")
    
    # Check network storage configuration
    config = get_network_storage_config()
    if not config.get('enabled', False):
        st.warning("⚠️ Network storage is not configured. Please configure it in Network Settings.")
        if st.button("Go to Network Settings"):
            st.switch_page("pages/3_Network_Storage.py")
        return
    
    # Upload interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📁 File Upload")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            accept_multiple_files=True,
            type=['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v',  # Videos
                  'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg',  # Images
                  'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a',  # Audio
                  'pdf', 'txt', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',  # Documents
                  'zip', 'rar', '7z', 'tar', 'gz']  # Archives
        )
        
        # Upload options
        st.markdown("### ⚙️ Upload Options")
        
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            organize_files = st.checkbox("📂 Organize by file type", value=True)
            generate_thumbnails = st.checkbox("🖼️ Generate thumbnails for videos", value=True)
        
        with col_opt2:
            sync_to_network = st.checkbox("🔄 Sync to Raspberry Pi", value=True)
            overwrite_existing = st.checkbox("♻️ Overwrite existing files", value=False)
        
        # Upload button
        if uploaded_files and st.button("🚀 Upload Files", type="primary"):
            upload_files(uploaded_files, organize_files, generate_thumbnails, sync_to_network, overwrite_existing)
    
    with col2:
        # Upload status and info
        st.markdown("### 📊 Upload Status")
        
        # Storage info
        if config.get('enabled', False):
            st.success(f"🔗 Connected to {config.get('server_ip', 'N/A')}")
            st.info(f"📍 Storage: {config.get('mount_point', 'N/A')}")
        else:
            st.error("❌ Not connected to Raspberry Pi")
        
        # Quick stats
        st.markdown("### 📈 Quick Stats")
        from utils.media_handler import get_media_stats
        stats = get_media_stats()
        
        st.metric("Total Files", stats.get('total_files', 0))
        st.metric("Total Size", f"{stats.get('total_size_gb', 0):.1f} GB")
        
        # Recent uploads
        st.markdown("### 📋 Recent Uploads")
        show_recent_uploads()

def upload_files(uploaded_files, organize_files, generate_thumbnails, sync_to_network, overwrite_existing):
    """Handle file upload process"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    uploaded_count = 0
    total_files = len(uploaded_files)
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            # Update progress
            progress = (i + 1) / total_files
            progress_bar.progress(progress)
            status_text.text(f"Uploading {uploaded_file.name}... ({i+1}/{total_files})")
            
            # Clean filename
            filename = clean_filename(uploaded_file.name)
            
            # Determine upload path
            if organize_files:
                upload_path = get_organized_path(filename)
            else:
                upload_path = Path("media/uploads") / filename
            
            # Create directory if needed
            upload_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists
            if upload_path.exists() and not overwrite_existing:
                st.warning(f"⚠️ File {filename} already exists. Skipping.")
                continue
            
            # Save file
            with open(upload_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Validate uploaded file
            validation_result = validate_file_upload(str(upload_path))
            if not validation_result['valid']:
                st.error(f"❌ Invalid file {filename}: {validation_result['error']}")
                os.remove(upload_path)
                continue
            
            # Generate thumbnail for videos
            if generate_thumbnails and is_video_file(filename):
                try:
                    generate_thumbnail(str(upload_path))
                except Exception as e:
                    st.warning(f"⚠️ Could not generate thumbnail for {filename}: {e}")
            
            uploaded_count += 1
            
        except Exception as e:
            st.error(f"❌ Error uploading {uploaded_file.name}: {str(e)}")
    
    # Sync to network storage if enabled
    if sync_to_network and uploaded_count > 0:
        status_text.text("Syncing to Raspberry Pi...")
        sync_result = sync_media_to_network_storage()
        if sync_result.get('success', False):
            st.success(f"✅ Successfully synced {uploaded_count} files to Raspberry Pi")
        else:
            st.warning(f"⚠️ Upload completed but sync failed: {sync_result.get('error', 'Unknown error')}")
    
    # Final status
    progress_bar.progress(1.0)
    status_text.text(f"✅ Upload complete! {uploaded_count}/{total_files} files uploaded successfully.")
    
    if uploaded_count > 0:
        st.balloons()
        st.success(f"🎉 Successfully uploaded {uploaded_count} files!")
        
        # Option to view uploaded files
        if st.button("📚 View in Media Library"):
            st.switch_page("pages/1_Media_Library.py")

def get_organized_path(filename):
    """Get organized path based on file type"""
    file_ext = Path(filename).suffix.lower()
    
    # Video files
    if file_ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
        return Path("media/uploads/videos") / filename
    
    # Image files
    elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']:
        return Path("media/uploads/images") / filename
    
    # Audio files
    elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a']:
        return Path("media/uploads/audio") / filename
    
    # Document files
    elif file_ext in ['.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        return Path("media/uploads/documents") / filename
    
    # Archive files
    elif file_ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        return Path("media/uploads/archives") / filename
    
    # Other files
    else:
        return Path("media/uploads/other") / filename

def is_video_file(filename):
    """Check if file is a video"""
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']
    return Path(filename).suffix.lower() in video_extensions

def show_recent_uploads():
    """Show recent uploads"""
    from utils.media_handler import get_recent_media
    recent_files = get_recent_media(3)
    
    if recent_files:
        for file in recent_files:
            st.write(f"📁 {file['name']}")
            st.write(f"   Size: {file['size']}")
            st.write(f"   Type: {file['type']}")
            st.markdown("---")
    else:
        st.info("No recent uploads")

if __name__ == "__main__":
    main()