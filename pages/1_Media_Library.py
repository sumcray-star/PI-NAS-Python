import streamlit as st
import os
from pathlib import Path
import mimetypes
from utils.auth import is_authenticated
from utils.media_handler import get_media_files, get_media_info, delete_media_file
from utils.file_manager import get_file_size, get_file_date

# Check authentication
if not is_authenticated():
    st.error("Please login to access this page")
    st.stop()

st.set_page_config(page_title="Media Library - PI-NAS", page_icon="📁", layout="wide")

st.title("📁 Media Library")

# Sidebar filters
with st.sidebar:
    st.subheader("Filters")
    
    # Media type filter
    media_type = st.selectbox(
        "Media Type",
        ["All", "Videos", "Audio", "Images", "Documents"]
    )
    
    # Sort options
    sort_by = st.selectbox(
        "Sort by",
        ["Name", "Date Added", "Size", "Type"]
    )
    
    sort_order = st.radio("Order", ["Ascending", "Descending"])
    
    # Search
    search_query = st.text_input("Search files", placeholder="Enter filename...")

# Main content
col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("Library Stats")
    media_files = get_media_files()
    
    total_files = len(media_files)
    total_size = sum(get_file_size(f) for f in media_files)
    
    st.metric("Total Files", total_files)
    st.metric("Total Size", f"{total_size / (1024**3):.2f} GB")
    
    # File type breakdown
    file_types = {}
    for file_path in media_files:
        ext = file_path.suffix.lower()
        file_types[ext] = file_types.get(ext, 0) + 1
    
    if file_types:
        st.subheader("File Types")
        for ext, count in sorted(file_types.items()):
            st.text(f"{ext or 'No ext'}: {count}")

with col1:
    # Apply filters
    filtered_files = media_files.copy()
    
    # Filter by media type
    if media_type != "All":
        if media_type == "Videos":
            filtered_files = [f for f in filtered_files if f.suffix.lower() in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']]
        elif media_type == "Audio":
            filtered_files = [f for f in filtered_files if f.suffix.lower() in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma']]
        elif media_type == "Images":
            filtered_files = [f for f in filtered_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']]
        elif media_type == "Documents":
            filtered_files = [f for f in filtered_files if f.suffix.lower() in ['.pdf', '.doc', '.docx', '.txt', '.rtf']]
    
    # Apply search filter
    if search_query:
        filtered_files = [f for f in filtered_files if search_query.lower() in f.name.lower()]
    
    # Sort files
    if sort_by == "Name":
        filtered_files.sort(key=lambda x: x.name.lower())
    elif sort_by == "Date Added":
        filtered_files.sort(key=lambda x: get_file_date(x))
    elif sort_by == "Size":
        filtered_files.sort(key=lambda x: get_file_size(x))
    elif sort_by == "Type":
        filtered_files.sort(key=lambda x: x.suffix.lower())
    
    if sort_order == "Descending":
        filtered_files.reverse()
    
    # Display files
    st.subheader(f"Files ({len(filtered_files)})")
    
    if not filtered_files:
        st.info("No files found matching your criteria.")
    else:
        # Pagination
        items_per_page = 20
        total_pages = (len(filtered_files) + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            page = st.selectbox("Page", range(1, total_pages + 1))
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_files = filtered_files[start_idx:end_idx]
        else:
            page_files = filtered_files
        
        # Display files in a grid
        for i, file_path in enumerate(page_files):
            with st.container():
                file_col1, file_col2, file_col3, file_col4 = st.columns([1, 3, 2, 1])
                
                with file_col1:
                    # File type icon
                    ext = file_path.suffix.lower()
                    if ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']:
                        st.markdown("🎬")
                    elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma']:
                        st.markdown("🎵")
                    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
                        st.markdown("🖼️")
                    elif ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
                        st.markdown("📄")
                    else:
                        st.markdown("📎")
                
                with file_col2:
                    st.write(f"**{file_path.name}**")
                    file_size = get_file_size(file_path)
                    file_date = get_file_date(file_path)
                    st.caption(f"Size: {file_size / (1024**2):.1f} MB • Modified: {file_date}")
                
                with file_col3:
                    # Media player for supported formats
                    if ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm']:
                        try:
                            if os.path.exists(file_path):
                                st.video(str(file_path))
                        except Exception as e:
                            st.error(f"Error loading video: {e}")
                    elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
                        try:
                            if os.path.exists(file_path):
                                st.audio(str(file_path))
                        except Exception as e:
                            st.error(f"Error loading audio: {e}")
                    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                        try:
                            if os.path.exists(file_path):
                                st.image(str(file_path), width=200)
                        except Exception as e:
                            st.error(f"Error loading image: {e}")
                    else:
                        st.text("Preview not available")
                
                with file_col4:
                    if st.button("Delete", key=f"delete_{i}", type="secondary"):
                        if delete_media_file(file_path):
                            st.success(f"Deleted {file_path.name}")
                            st.rerun()
                        else:
                            st.error("Failed to delete file")
                
                st.markdown("---")

# Selected media playback
if 'selected_media' in st.session_state:
    media = st.session_state.selected_media
    st.subheader(f"Now Playing: {media['name']}")
    
    media_path = Path("media/uploads") / media['name']
    if media_path.exists():
        ext = media_path.suffix.lower()
        if ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm']:
            st.video(str(media_path))
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            st.audio(str(media_path))
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            st.image(str(media_path))
        else:
            st.info("File format not supported for preview")
    else:
        st.error("Media file not found")
    
    if st.button("Clear Selection"):
        del st.session_state.selected_media
        st.rerun()
