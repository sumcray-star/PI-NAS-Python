import streamlit as st
import os
import shutil
from pathlib import Path
from datetime import datetime
from utils.auth import is_authenticated
from utils.media_handler import organize_media_file, generate_thumbnail
from utils.file_manager import ensure_directories, is_supported_format

# Check authentication
if not is_authenticated():
    st.error("Please login to access this page")
    st.stop()

st.set_page_config(page_title="Upload Media - PI-NAS", page_icon="⬆️", layout="wide")

st.title("⬆️ Upload Media")

# Ensure upload directory exists
ensure_directories()

# Supported formats
SUPPORTED_VIDEO = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
SUPPORTED_AUDIO = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma']
SUPPORTED_IMAGE = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
SUPPORTED_DOCUMENT = ['.pdf', '.doc', '.docx', '.txt', '.rtf']

ALL_SUPPORTED = SUPPORTED_VIDEO + SUPPORTED_AUDIO + SUPPORTED_IMAGE + SUPPORTED_DOCUMENT

# Upload interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Upload Files")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose media files",
        accept_multiple_files=True,
        type=None,
        help="Supported formats: Video (MP4, AVI, MKV, MOV, WMV, FLV, WebM), Audio (MP3, WAV, FLAC, AAC, OGG, WMA), Images (JPG, PNG, GIF, BMP, SVG, WebP), Documents (PDF, DOC, DOCX, TXT, RTF)"
    )
    
    # Upload options
    with st.expander("Upload Options"):
        organize_files = st.checkbox("Organize files by type", value=True)
        generate_thumbnails = st.checkbox("Generate thumbnails for videos", value=True)
        overwrite_existing = st.checkbox("Overwrite existing files", value=False)
    
    # Process uploads
    if uploaded_files:
        upload_progress = st.progress(0)
        upload_status = st.empty()
        
        successful_uploads = []
        failed_uploads = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # Check if file format is supported
                file_ext = Path(uploaded_file.name).suffix.lower()
                if file_ext not in ALL_SUPPORTED:
                    failed_uploads.append(f"{uploaded_file.name}: Unsupported format")
                    continue
                
                upload_status.text(f"Processing {uploaded_file.name}...")
                
                # Determine target directory
                if organize_files:
                    if file_ext in SUPPORTED_VIDEO:
                        target_dir = Path("media/uploads/videos")
                    elif file_ext in SUPPORTED_AUDIO:
                        target_dir = Path("media/uploads/audio")
                    elif file_ext in SUPPORTED_IMAGE:
                        target_dir = Path("media/uploads/images")
                    elif file_ext in SUPPORTED_DOCUMENT:
                        target_dir = Path("media/uploads/documents")
                    else:
                        target_dir = Path("media/uploads/other")
                else:
                    target_dir = Path("media/uploads")
                
                # Create target directory if it doesn't exist
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Target file path
                target_path = target_dir / uploaded_file.name
                
                # Check if file already exists
                if target_path.exists() and not overwrite_existing:
                    # Generate unique filename
                    base_name = target_path.stem
                    extension = target_path.suffix
                    counter = 1
                    while target_path.exists():
                        target_path = target_dir / f"{base_name}_{counter}{extension}"
                        counter += 1
                
                # Save file
                with open(target_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Generate thumbnail for videos
                if generate_thumbnails and file_ext in SUPPORTED_VIDEO:
                    try:
                        generate_thumbnail(target_path)
                    except Exception as e:
                        st.warning(f"Failed to generate thumbnail for {uploaded_file.name}: {e}")
                
                successful_uploads.append(uploaded_file.name)
                
                # Update recent activity
                if 'recent_activity' not in st.session_state:
                    st.session_state.recent_activity = []
                st.session_state.recent_activity.append(
                    f"Uploaded {uploaded_file.name} at {datetime.now().strftime('%H:%M:%S')}"
                )
                
            except Exception as e:
                failed_uploads.append(f"{uploaded_file.name}: {str(e)}")
            
            # Update progress
            upload_progress.progress((i + 1) / len(uploaded_files))
        
        # Show results
        upload_status.empty()
        upload_progress.empty()
        
        if successful_uploads:
            st.success(f"Successfully uploaded {len(successful_uploads)} files:")
            for file in successful_uploads:
                st.text(f"✅ {file}")
        
        if failed_uploads:
            st.error(f"Failed to upload {len(failed_uploads)} files:")
            for error in failed_uploads:
                st.text(f"❌ {error}")
        
        if st.button("Clear Upload Status"):
            st.rerun()

with col2:
    st.subheader("Upload Guidelines")
    
    st.markdown("**Supported Formats:**")
    
    with st.expander("Video Formats"):
        st.markdown("• MP4 (recommended)")
        st.markdown("• AVI")
        st.markdown("• MKV")
        st.markdown("• MOV")
        st.markdown("• WMV")
        st.markdown("• FLV")
        st.markdown("• WebM")
    
    with st.expander("Audio Formats"):
        st.markdown("• MP3 (recommended)")
        st.markdown("• WAV")
        st.markdown("• FLAC")
        st.markdown("• AAC")
        st.markdown("• OGG")
        st.markdown("• WMA")
    
    with st.expander("Image Formats"):
        st.markdown("• JPG/JPEG")
        st.markdown("• PNG")
        st.markdown("• GIF")
        st.markdown("• BMP")
        st.markdown("• SVG")
        st.markdown("• WebP")
    
    with st.expander("Document Formats"):
        st.markdown("• PDF")
        st.markdown("• DOC/DOCX")
        st.markdown("• TXT")
        st.markdown("• RTF")
    
    st.markdown("---")
    st.subheader("Storage Info")
    
    try:
        import psutil
        disk_usage = psutil.disk_usage('.')
        free_gb = disk_usage.free / (1024**3)
        total_gb = disk_usage.total / (1024**3)
        
        st.metric("Free Space", f"{free_gb:.1f} GB")
        st.metric("Total Space", f"{total_gb:.1f} GB")
        
        # Warning if low on space
        if free_gb < 1.0:
            st.warning("⚠️ Low disk space!")
        elif free_gb < 5.0:
            st.info("ℹ️ Consider freeing up space soon")
    except Exception as e:
        st.error(f"Error getting disk info: {e}")
    
    st.markdown("---")
    st.subheader("Recent Uploads")
    
    # Show recent uploads
    if 'recent_activity' in st.session_state:
        recent_uploads = [activity for activity in st.session_state.recent_activity if "Uploaded" in activity]
        for upload in recent_uploads[-5:]:
            st.caption(upload)
    else:
        st.caption("No recent uploads")

# Drag and drop area simulation
st.markdown("---")
st.subheader("Bulk Upload")
st.info("💡 Tip: You can select multiple files at once using Ctrl+Click (Windows/Linux) or Cmd+Click (Mac)")

# Upload from URL
with st.expander("Upload from URL"):
    st.markdown("**Download media from URL**")
    
    url = st.text_input("Enter media URL", placeholder="https://example.com/video.mp4")
    custom_filename = st.text_input("Custom filename (optional)", placeholder="my_video.mp4")
    
    if st.button("Download from URL"):
        if url:
            try:
                import requests
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    st.info("URL is accessible. Feature coming soon!")
                else:
                    st.error("URL is not accessible")
            except Exception as e:
                st.error(f"Error checking URL: {e}")
        else:
            st.error("Please enter a URL")
