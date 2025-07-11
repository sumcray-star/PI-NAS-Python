import streamlit as st
import os
from pathlib import Path
from utils.auth import is_authenticated
from utils.media_handler import get_media_files, get_media_info, delete_media_file, search_media, get_media_by_type
from utils.file_manager import format_size

# Check authentication
if not is_authenticated():
    st.switch_page("pages/4_Settings.py")
    st.stop()

st.set_page_config(
    page_title="Media Library - PI-NAS",
    page_icon="📚",
    layout="wide"
)

def main():
    st.title("📚 Media Library")
    st.markdown("Browse and manage your media files stored on Raspberry Pi")
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")
        
        # Media type filter
        media_types = ["All", "Videos", "Images", "Documents", "Audio"]
        selected_type = st.selectbox("Media Type", media_types)
        
        # Search
        search_query = st.text_input("🔍 Search files", placeholder="Enter filename...")
        
        # Sort options
        sort_options = ["Name", "Date Modified", "Size", "Type"]
        sort_by = st.selectbox("Sort by", sort_options)
        sort_order = st.radio("Order", ["Ascending", "Descending"])
        
        st.markdown("---")
        
        # View options
        st.header("👀 View Options")
        view_mode = st.radio("View Mode", ["Grid", "List"])
        show_thumbnails = st.checkbox("Show Thumbnails", value=True)
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Quick actions
        st.markdown("### Quick Actions")
        if st.button("🔄 Refresh Library", use_container_width=True):
            st.rerun()
        
        if st.button("📤 Upload Files", use_container_width=True):
            st.switch_page("pages/2_Upload_Media.py")
        
        if st.button("🌐 Network Settings", use_container_width=True):
            st.switch_page("pages/3_Network_Storage.py")
    
    with col1:
        # Get media files
        if search_query:
            media_files = search_media(search_query)
        elif selected_type != "All":
            media_files = get_media_by_type(selected_type.lower())
        else:
            media_files = get_media_files()
        
        # Sort files
        if sort_by == "Name":
            media_files.sort(key=lambda x: x['name'], reverse=(sort_order == "Descending"))
        elif sort_by == "Date Modified":
            media_files.sort(key=lambda x: x.get('modified', 0), reverse=(sort_order == "Descending"))
        elif sort_by == "Size":
            media_files.sort(key=lambda x: x.get('size_bytes', 0), reverse=(sort_order == "Descending"))
        elif sort_by == "Type":
            media_files.sort(key=lambda x: x.get('type', ''), reverse=(sort_order == "Descending"))
        
        # Display files
        if media_files:
            st.markdown(f"### Found {len(media_files)} files")
            
            if view_mode == "Grid":
                # Grid view
                cols = st.columns(3)
                for i, file in enumerate(media_files):
                    with cols[i % 3]:
                        display_file_card(file, show_thumbnails)
            else:
                # List view
                for file in media_files:
                    display_file_list(file)
        else:
            st.info("No media files found. Upload some files to get started!")

def display_file_card(file, show_thumbnails=True):
    """Display file as a card"""
    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #333; border-radius: 8px; padding: 15px; margin: 10px 0; 
                    background: #1e1e1e; height: 300px;">
            <h4 style="color: #fff; margin: 0 0 10px 0; font-size: 14px;">{file['name'][:30]}...</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # File info
        st.write(f"**Type:** {file.get('type', 'Unknown')}")
        st.write(f"**Size:** {format_size(file.get('size_bytes', 0))}")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👁️ View", key=f"view_{file['name']}"):
                view_file(file)
        with col2:
            if st.button("🗑️ Delete", key=f"delete_{file['name']}"):
                if st.session_state.get(f"confirm_delete_{file['name']}", False):
                    delete_media_file(file['path'])
                    st.success(f"Deleted {file['name']}")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{file['name']}"] = True
                    st.warning("Click again to confirm deletion")

def display_file_list(file):
    """Display file in list format"""
    with st.expander(f"📁 {file['name']}"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**Type:** {file.get('type', 'Unknown')}")
            st.write(f"**Size:** {format_size(file.get('size_bytes', 0))}")
            st.write(f"**Path:** {file['path']}")
            st.write(f"**Modified:** {file.get('modified', 'Unknown')}")
        
        with col2:
            if st.button("👁️ View", key=f"view_list_{file['name']}"):
                view_file(file)
            
            if st.button("🗑️ Delete", key=f"delete_list_{file['name']}"):
                if st.session_state.get(f"confirm_delete_list_{file['name']}", False):
                    delete_media_file(file['path'])
                    st.success(f"Deleted {file['name']}")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_list_{file['name']}"] = True
                    st.warning("Click again to confirm deletion")

def view_file(file):
    """View file content"""
    file_type = file.get('type', '').lower()
    file_path = file['path']
    
    if file_type in ['image', 'images']:
        try:
            st.image(file_path, caption=file['name'], use_column_width=True)
        except Exception as e:
            st.error(f"Cannot display image: {e}")
    
    elif file_type in ['video', 'videos']:
        try:
            st.video(file_path)
        except Exception as e:
            st.error(f"Cannot play video: {e}")
    
    elif file_type in ['audio']:
        try:
            st.audio(file_path)
        except Exception as e:
            st.error(f"Cannot play audio: {e}")
    
    else:
        st.info(f"Preview not available for {file_type} files")
        
        # Show download link
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                st.download_button(
                    label="📥 Download File",
                    data=f.read(),
                    file_name=file['name'],
                    mime=file.get('mime_type', 'application/octet-stream')
                )

if __name__ == "__main__":
    main()