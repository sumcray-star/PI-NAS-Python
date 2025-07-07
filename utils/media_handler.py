import os
import json
from pathlib import Path
from datetime import datetime
import mimetypes
from PIL import Image
import subprocess

def get_media_files(directory="media/uploads"):
    """Get all media files from directory"""
    media_path = Path(directory)
    if not media_path.exists():
        return []
    
    supported_extensions = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',  # Video
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma',          # Audio
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', # Images
        '.pdf', '.doc', '.docx', '.txt', '.rtf'                   # Documents
    }
    
    media_files = []
    for file_path in media_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            media_files.append(file_path)
    
    return media_files

def get_recent_media(limit=10):
    """Get recently added media files"""
    media_files = get_media_files()
    
    # Sort by modification time (most recent first)
    media_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    recent_media = []
    for file_path in media_files[:limit]:
        try:
            stat = file_path.stat()
            recent_media.append({
                'name': file_path.name,
                'path': str(file_path),
                'size': format_file_size(stat.st_size),
                'date_added': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                'type': get_media_type(file_path.suffix)
            })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    return recent_media

def get_media_stats():
    """Get media library statistics"""
    media_files = get_media_files()
    
    stats = {
        'total_files': len(media_files),
        'videos': 0,
        'audio': 0,
        'images': 0,
        'documents': 0,
        'total_size': 0
    }
    
    video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
    audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'}
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'}
    doc_exts = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
    
    for file_path in media_files:
        try:
            ext = file_path.suffix.lower()
            size = file_path.stat().st_size
            stats['total_size'] += size
            
            if ext in video_exts:
                stats['videos'] += 1
            elif ext in audio_exts:
                stats['audio'] += 1
            elif ext in image_exts:
                stats['images'] += 1
            elif ext in doc_exts:
                stats['documents'] += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return stats

def get_media_type(extension):
    """Get media type from file extension"""
    ext = extension.lower()
    
    if ext in {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}:
        return 'video'
    elif ext in {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'}:
        return 'audio'
    elif ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'}:
        return 'image'
    elif ext in {'.pdf', '.doc', '.docx', '.txt', '.rtf'}:
        return 'document'
    else:
        return 'other'

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def organize_media_file(file_path, organize_by_type=True):
    """Organize media file into appropriate directory"""
    if not organize_by_type:
        return file_path
    
    media_type = get_media_type(file_path.suffix)
    
    if media_type == 'video':
        target_dir = Path("media/uploads/videos")
    elif media_type == 'audio':
        target_dir = Path("media/uploads/audio")
    elif media_type == 'image':
        target_dir = Path("media/uploads/images")
    elif media_type == 'document':
        target_dir = Path("media/uploads/documents")
    else:
        target_dir = Path("media/uploads/other")
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Move file to organized directory
    target_path = target_dir / file_path.name
    
    # Handle filename conflicts
    counter = 1
    while target_path.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        target_path = target_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    
    try:
        file_path.rename(target_path)
        return target_path
    except Exception as e:
        print(f"Error organizing file {file_path}: {e}")
        return file_path

def generate_thumbnail(video_path, thumbnail_dir="media/thumbnails"):
    """Generate thumbnail for video file"""
    try:
        import cv2
        
        # Create thumbnail directory
        thumb_dir = Path(thumbnail_dir)
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate thumbnail filename
        video_name = Path(video_path).stem
        thumbnail_path = thumb_dir / f"{video_name}.jpg"
        
        # Skip if thumbnail already exists
        if thumbnail_path.exists():
            return str(thumbnail_path)
        
        # Open video and capture frame
        cap = cv2.VideoCapture(str(video_path))
        
        # Get frame from 10% into the video
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 10)
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Resize frame to thumbnail size
            height, width = frame.shape[:2]
            max_size = 300
            
            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)
            
            frame = cv2.resize(frame, (new_width, new_height))
            
            # Save thumbnail
            cv2.imwrite(str(thumbnail_path), frame)
            return str(thumbnail_path)
        
    except ImportError:
        # Fallback: use ffmpeg if available
        try:
            thumbnail_path = Path(thumbnail_dir) / f"{Path(video_path).stem}.jpg"
            subprocess.run([
                'ffmpeg', '-i', str(video_path), '-vframes', '1',
                '-q:v', '2', '-vf', 'scale=300:-1',
                str(thumbnail_path)
            ], check=True, capture_output=True)
            return str(thumbnail_path)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    except Exception as e:
        print(f"Error generating thumbnail for {video_path}: {e}")
    
    return None

def get_media_info(file_path):
    """Get detailed information about media file"""
    try:
        stat = file_path.stat()
        
        info = {
            'name': file_path.name,
            'path': str(file_path),
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'created': datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            'type': get_media_type(file_path.suffix),
            'extension': file_path.suffix.lower()
        }
        
        # Get additional info for images
        if info['type'] == 'image' and file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
            try:
                with Image.open(file_path) as img:
                    info['width'] = img.width
                    info['height'] = img.height
                    info['format'] = img.format
                    info['mode'] = img.mode
            except Exception as e:
                print(f"Error getting image info for {file_path}: {e}")
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        info['mime_type'] = mime_type
        
        return info
        
    except Exception as e:
        print(f"Error getting media info for {file_path}: {e}")
        return None

def delete_media_file(file_path):
    """Delete media file and its thumbnail"""
    try:
        # Delete main file
        if file_path.exists():
            file_path.unlink()
        
        # Delete thumbnail if exists
        thumbnail_path = Path("media/thumbnails") / f"{file_path.stem}.jpg"
        if thumbnail_path.exists():
            thumbnail_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
        return False

def search_media(query, directory="media/uploads"):
    """Search media files by name"""
    media_files = get_media_files(directory)
    
    if not query:
        return media_files
    
    query_lower = query.lower()
    matching_files = []
    
    for file_path in media_files:
        if query_lower in file_path.name.lower():
            matching_files.append(file_path)
    
    return matching_files

def get_media_by_type(media_type, directory="media/uploads"):
    """Get media files filtered by type"""
    media_files = get_media_files(directory)
    
    if media_type == 'all':
        return media_files
    
    filtered_files = []
    for file_path in media_files:
        if get_media_type(file_path.suffix) == media_type:
            filtered_files.append(file_path)
    
    return filtered_files

def create_media_playlist(files, name="My Playlist"):
    """Create a playlist from media files"""
    playlist = {
        'name': name,
        'created_at': datetime.now().isoformat(),
        'files': [str(f) for f in files]
    }
    
    playlist_dir = Path("data/playlists")
    playlist_dir.mkdir(parents=True, exist_ok=True)
    
    playlist_file = playlist_dir / f"{name.replace(' ', '_')}.json"
    
    try:
        with open(playlist_file, 'w') as f:
            json.dump(playlist, f, indent=2)
        return True
    except Exception as e:
        print(f"Error creating playlist: {e}")
        return False

def get_playlists():
    """Get all playlists"""
    playlist_dir = Path("data/playlists")
    if not playlist_dir.exists():
        return []
    
    playlists = []
    for playlist_file in playlist_dir.glob("*.json"):
        try:
            with open(playlist_file, 'r') as f:
                playlist = json.load(f)
                playlists.append(playlist)
        except Exception as e:
            print(f"Error loading playlist {playlist_file}: {e}")
    
    return playlists
