import os
import json
from pathlib import Path
from datetime import datetime
import mimetypes
from utils.file_manager import get_file_size, get_file_date, format_size, find_files

def get_media_files(directory="media/uploads"):
    """Get all media files from directory"""
    try:
        media_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            return media_files
        
        # Supported media extensions
        media_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',  # Video
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',  # Image
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',  # Audio
            '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'  # Document
        }
        
        # Find all files recursively
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                file_info = {
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': format_size(get_file_size(file_path)),
                    'size_bytes': get_file_size(file_path),
                    'modified': get_file_date(file_path),
                    'type': get_media_type(file_path.suffix.lower()),
                    'mime_type': mimetypes.guess_type(file_path)[0] or 'unknown',
                    'extension': file_path.suffix.lower()
                }
                media_files.append(file_info)
        
        return media_files
        
    except Exception as e:
        print(f"Error getting media files: {e}")
        return []

def get_recent_media(limit=10):
    """Get recently added media files"""
    try:
        media_files = get_media_files()
        
        # Sort by modification time (newest first)
        media_files.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        return media_files[:limit]
        
    except Exception as e:
        print(f"Error getting recent media: {e}")
        return []

def get_media_stats():
    """Get media library statistics"""
    try:
        media_files = get_media_files()
        
        stats = {
            'total_files': len(media_files),
            'videos': 0,
            'images': 0,
            'audio': 0,
            'documents': 0,
            'total_size_bytes': 0,
            'total_size_gb': 0
        }
        
        for file in media_files:
            file_type = file.get('type', '').lower()
            
            if file_type in ['video', 'videos']:
                stats['videos'] += 1
            elif file_type in ['image', 'images']:
                stats['images'] += 1
            elif file_type in ['audio']:
                stats['audio'] += 1
            elif file_type in ['document', 'documents']:
                stats['documents'] += 1
            
            stats['total_size_bytes'] += file.get('size_bytes', 0)
        
        stats['total_size_gb'] = stats['total_size_bytes'] / (1024**3)
        
        return stats
        
    except Exception as e:
        print(f"Error getting media stats: {e}")
        return {
            'total_files': 0,
            'videos': 0,
            'images': 0,
            'audio': 0,
            'documents': 0,
            'total_size_bytes': 0,
            'total_size_gb': 0
        }

def get_media_type(extension):
    """Get media type from file extension"""
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
    audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
    document_extensions = {'.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
    
    ext = extension.lower()
    
    if ext in video_extensions:
        return 'video'
    elif ext in image_extensions:
        return 'image'
    elif ext in audio_extensions:
        return 'audio'
    elif ext in document_extensions:
        return 'document'
    else:
        return 'unknown'

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    return format_size(size_bytes)

def organize_media_file(file_path, organize_by_type=True):
    """Organize media file into appropriate directory"""
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return False
        
        if not organize_by_type:
            return True
        
        # Determine target directory based on file type
        media_type = get_media_type(file_path_obj.suffix)
        
        if media_type == 'video':
            target_dir = Path("media/uploads/videos")
        elif media_type == 'image':
            target_dir = Path("media/uploads/images")
        elif media_type == 'audio':
            target_dir = Path("media/uploads/audio")
        elif media_type == 'document':
            target_dir = Path("media/uploads/documents")
        else:
            target_dir = Path("media/uploads/other")
        
        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Move file to organized location
        target_path = target_dir / file_path_obj.name
        file_path_obj.rename(target_path)
        
        return True
        
    except Exception as e:
        print(f"Error organizing media file: {e}")
        return False

def generate_thumbnail(video_path, thumbnail_dir="media/thumbnails"):
    """Generate thumbnail for video file"""
    try:
        import cv2
        
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            return False
        
        # Create thumbnail directory
        thumbnail_dir_path = Path(thumbnail_dir)
        thumbnail_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Generate thumbnail filename
        thumbnail_name = f"{video_path_obj.stem}.jpg"
        thumbnail_path = thumbnail_dir_path / thumbnail_name
        
        # Extract frame from video
        cap = cv2.VideoCapture(str(video_path))
        
        # Get video length and seek to middle
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        middle_frame = frame_count // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        
        ret, frame = cap.read()
        if ret:
            # Resize frame to thumbnail size
            height, width = frame.shape[:2]
            if width > 320:
                new_width = 320
                new_height = int(height * (320 / width))
                frame = cv2.resize(frame, (new_width, new_height))
            
            # Save thumbnail
            cv2.imwrite(str(thumbnail_path), frame)
            
        cap.release()
        return True
        
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return False

def get_media_info(file_path):
    """Get detailed information about media file"""
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return None
        
        info = {
            'name': file_path_obj.name,
            'path': str(file_path_obj.absolute()),
            'size': format_size(get_file_size(file_path)),
            'size_bytes': get_file_size(file_path),
            'modified': get_file_date(file_path),
            'type': get_media_type(file_path_obj.suffix),
            'mime_type': mimetypes.guess_type(file_path)[0] or 'unknown',
            'extension': file_path_obj.suffix.lower()
        }
        
        # Additional info for videos
        if info['type'] == 'video':
            try:
                import cv2
                cap = cv2.VideoCapture(str(file_path))
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration = frame_count / fps if fps > 0 else 0
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    info['duration'] = f"{int(duration // 60)}:{int(duration % 60):02d}"
                    info['resolution'] = f"{width}x{height}"
                    info['fps'] = fps
                    
                cap.release()
            except:
                pass
        
        return info
        
    except Exception as e:
        print(f"Error getting media info: {e}")
        return None

def delete_media_file(file_path):
    """Delete media file and its thumbnail"""
    try:
        file_path_obj = Path(file_path)
        
        # Delete main file
        if file_path_obj.exists():
            file_path_obj.unlink()
        
        # Delete thumbnail if it exists
        if get_media_type(file_path_obj.suffix) == 'video':
            thumbnail_path = Path("media/thumbnails") / f"{file_path_obj.stem}.jpg"
            if thumbnail_path.exists():
                thumbnail_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"Error deleting media file: {e}")
        return False

def search_media(query, directory="media/uploads"):
    """Search media files by name"""
    try:
        media_files = get_media_files(directory)
        
        query_lower = query.lower()
        matching_files = []
        
        for file in media_files:
            if query_lower in file['name'].lower():
                matching_files.append(file)
        
        return matching_files
        
    except Exception as e:
        print(f"Error searching media: {e}")
        return []

def get_media_by_type(media_type, directory="media/uploads"):
    """Get media files filtered by type"""
    try:
        media_files = get_media_files(directory)
        
        filtered_files = []
        for file in media_files:
            if file.get('type', '').lower() == media_type.lower():
                filtered_files.append(file)
        
        return filtered_files
        
    except Exception as e:
        print(f"Error getting media by type: {e}")
        return []

def create_media_playlist(files, name="My Playlist"):
    """Create a playlist from media files"""
    try:
        playlist = {
            'name': name,
            'created': datetime.now().isoformat(),
            'files': files
        }
        
        # Save playlist to file
        playlist_dir = Path("data/playlists")
        playlist_dir.mkdir(parents=True, exist_ok=True)
        
        playlist_file = playlist_dir / f"{name.replace(' ', '_')}.json"
        with open(playlist_file, 'w') as f:
            json.dump(playlist, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error creating playlist: {e}")
        return False

def get_playlists():
    """Get all playlists"""
    try:
        playlist_dir = Path("data/playlists")
        if not playlist_dir.exists():
            return []
        
        playlists = []
        for playlist_file in playlist_dir.glob("*.json"):
            try:
                with open(playlist_file, 'r') as f:
                    playlist = json.load(f)
                    playlists.append(playlist)
            except:
                continue
        
        return playlists
        
    except Exception as e:
        print(f"Error getting playlists: {e}")
        return []