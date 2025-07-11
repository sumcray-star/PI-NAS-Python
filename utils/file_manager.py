import os
import shutil
import hashlib
import re
from pathlib import Path
from datetime import datetime
import mimetypes

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        "data",
        "logs", 
        "media/uploads",
        "media/uploads/videos",
        "media/uploads/images", 
        "media/uploads/audio",
        "media/uploads/documents",
        "media/thumbnails",
        "temp",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def get_file_date(file_path):
    """Get file modification date"""
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Unknown"

def get_directory_size(directory):
    """Get total size of directory in bytes"""
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    except:
        return 0

def is_supported_format(file_path):
    """Check if file format is supported"""
    supported_extensions = {
        # Videos
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',
        # Audio
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
        # Documents
        '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        # Archives
        '.zip', '.rar', '.7z', '.tar', '.gz'
    }
    
    file_ext = Path(file_path).suffix.lower()
    return file_ext in supported_extensions

def clean_filename(filename):
    """Clean filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    # Ensure filename is not empty
    if not filename:
        filename = f"unnamed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return filename

def move_file(source, destination):
    """Move file from source to destination"""
    try:
        # Ensure destination directory exists
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, destination)
        return True
    except Exception as e:
        print(f"Error moving file: {e}")
        return False

def copy_file(source, destination):
    """Copy file from source to destination"""
    try:
        # Ensure destination directory exists
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"Error copying file: {e}")
        return False

def delete_file(file_path):
    """Delete file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False

def create_directory(directory_path):
    """Create directory"""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory: {e}")
        return False

def delete_directory(directory_path):
    """Delete directory and all its contents"""
    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting directory: {e}")
        return False

def get_file_info(file_path):
    """Get detailed file information"""
    try:
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        file_path_obj = Path(file_path)
        
        return {
            'name': file_path_obj.name,
            'path': str(file_path_obj.absolute()),
            'size': stat.st_size,
            'size_formatted': format_size(stat.st_size),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            'extension': file_path_obj.suffix.lower(),
            'mime_type': mimetypes.guess_type(file_path)[0] or 'unknown',
            'is_supported': is_supported_format(file_path)
        }
    except Exception as e:
        print(f"Error getting file info: {e}")
        return None

def format_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def find_files(directory, pattern="*", recursive=True):
    """Find files matching pattern in directory"""
    try:
        directory_path = Path(directory)
        if not directory_path.exists():
            return []
        
        if recursive:
            return list(directory_path.rglob(pattern))
        else:
            return list(directory_path.glob(pattern))
    except Exception as e:
        print(f"Error finding files: {e}")
        return []

def get_available_space(path="."):
    """Get available disk space"""
    try:
        statvfs = os.statvfs(path)
        free_bytes = statvfs.f_bavail * statvfs.f_frsize
        return free_bytes
    except Exception as e:
        print(f"Error getting available space: {e}")
        return 0

def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        temp_dir = Path("temp")
        if temp_dir.exists():
            for file in temp_dir.iterdir():
                if file.is_file():
                    file.unlink()
        return True
    except Exception as e:
        print(f"Error cleaning temp files: {e}")
        return False

def cleanup_thumbnails():
    """Clean up old thumbnails"""
    try:
        thumb_dir = Path("media/thumbnails")
        if thumb_dir.exists():
            # Clean thumbnails older than 30 days
            import time
            current_time = time.time()
            for file in thumb_dir.iterdir():
                if file.is_file():
                    if current_time - file.stat().st_mtime > 30 * 24 * 60 * 60:  # 30 days
                        file.unlink()
        return True
    except Exception as e:
        print(f"Error cleaning thumbnails: {e}")
        return False

def backup_file(file_path, backup_dir="backups"):
    """Create backup of file"""
    try:
        source_path = Path(file_path)
        if not source_path.exists():
            return False
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file_path = backup_path / f"{source_path.stem}_{timestamp}{source_path.suffix}"
        
        shutil.copy2(source_path, backup_file_path)
        return True
    except Exception as e:
        print(f"Error backing up file: {e}")
        return False

def restore_file(backup_path, restore_path):
    """Restore file from backup"""
    try:
        return copy_file(backup_path, restore_path)
    except Exception as e:
        print(f"Error restoring file: {e}")
        return False

def validate_file_upload(file_path, max_size=None, allowed_types=None):
    """Validate uploaded file"""
    try:
        if not os.path.exists(file_path):
            return {'valid': False, 'error': 'File does not exist'}
        
        # Check file size
        file_size = get_file_size(file_path)
        if max_size and file_size > max_size:
            return {'valid': False, 'error': f'File too large. Max size: {format_size(max_size)}'}
        
        # Check file type
        if allowed_types:
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in allowed_types:
                return {'valid': False, 'error': f'File type not allowed. Allowed: {", ".join(allowed_types)}'}
        
        # Check if file is supported
        if not is_supported_format(file_path):
            return {'valid': False, 'error': 'File format not supported'}
        
        return {'valid': True, 'error': None}
        
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def get_file_hash(file_path, algorithm='sha256'):
    """Get file hash"""
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        print(f"Error getting file hash: {e}")
        return None

def find_duplicate_files(directory):
    """Find duplicate files in directory"""
    try:
        file_hashes = {}
        duplicates = []
        
        for file_path in find_files(directory):
            if file_path.is_file():
                file_hash = get_file_hash(file_path)
                if file_hash:
                    if file_hash in file_hashes:
                        duplicates.append({
                            'original': file_hashes[file_hash],
                            'duplicate': str(file_path)
                        })
                    else:
                        file_hashes[file_hash] = str(file_path)
        
        return duplicates
    except Exception as e:
        print(f"Error finding duplicates: {e}")
        return []