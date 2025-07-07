import os
import shutil
from pathlib import Path
from datetime import datetime
import mimetypes

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        "media/uploads",
        "media/thumbnails",
        "data",
        "config",
        "temp",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return Path(file_path).stat().st_size
    except:
        return 0

def get_file_date(file_path):
    """Get file modification date"""
    try:
        return datetime.fromtimestamp(Path(file_path).stat().st_mtime)
    except:
        return datetime.now()

def get_directory_size(directory):
    """Get total size of directory in bytes"""
    total_size = 0
    
    try:
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except:
        pass
    
    return total_size

def is_supported_format(file_path):
    """Check if file format is supported"""
    supported_extensions = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',  # Video
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma',          # Audio
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', # Images
        '.pdf', '.doc', '.docx', '.txt', '.rtf'                   # Documents
    }
    
    return Path(file_path).suffix.lower() in supported_extensions

def clean_filename(filename):
    """Clean filename for safe storage"""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def move_file(source, destination):
    """Move file from source to destination"""
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(source_path), str(dest_path))
        return True
    except Exception as e:
        print(f"Error moving file: {e}")
        return False

def copy_file(source, destination):
    """Copy file from source to destination"""
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(str(source_path), str(dest_path))
        return True
    except Exception as e:
        print(f"Error copying file: {e}")
        return False

def delete_file(file_path):
    """Delete file"""
    try:
        Path(file_path).unlink()
        return True
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
        shutil.rmtree(directory_path)
        return True
    except Exception as e:
        print(f"Error deleting directory: {e}")
        return False

def get_file_info(file_path):
    """Get detailed file information"""
    try:
        path = Path(file_path)
        stat = path.stat()
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        
        return {
            'name': path.name,
            'size': stat.st_size,
            'size_formatted': format_size(stat.st_size),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'accessed': datetime.fromtimestamp(stat.st_atime),
            'extension': path.suffix.lower(),
            'mime_type': mime_type,
            'is_file': path.is_file(),
            'is_directory': path.is_dir()
        }
    except Exception as e:
        print(f"Error getting file info: {e}")
        return None

def format_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def find_files(directory, pattern="*", recursive=True):
    """Find files matching pattern in directory"""
    try:
        directory_path = Path(directory)
        
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
        import psutil
        usage = psutil.disk_usage(path)
        return {
            'total': usage.total,
            'used': usage.used,
            'free': usage.free,
            'percent': (usage.used / usage.total) * 100
        }
    except Exception as e:
        print(f"Error getting disk usage: {e}")
        return None

def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        temp_dir = Path("temp")
        if temp_dir.exists():
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    # Delete files older than 1 hour
                    if (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).seconds > 3600:
                        file_path.unlink()
        return True
    except Exception as e:
        print(f"Error cleaning temp files: {e}")
        return False

def cleanup_thumbnails():
    """Clean up old thumbnails"""
    try:
        thumb_dir = Path("media/thumbnails")
        if thumb_dir.exists():
            media_dir = Path("media/uploads")
            
            # Get list of media files
            media_files = set()
            for file_path in media_dir.rglob('*'):
                if file_path.is_file():
                    media_files.add(file_path.stem)
            
            # Delete orphaned thumbnails
            for thumb_path in thumb_dir.iterdir():
                if thumb_path.is_file():
                    thumb_name = thumb_path.stem
                    if thumb_name not in media_files:
                        thumb_path.unlink()
        
        return True
    except Exception as e:
        print(f"Error cleaning thumbnails: {e}")
        return False

def backup_file(file_path, backup_dir="backups"):
    """Create backup of file"""
    try:
        source_path = Path(file_path)
        backup_path = Path(backup_dir) / source_path.name
        
        # Create backup directory
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
        backup_path = backup_path.parent / backup_name
        
        # Copy file
        shutil.copy2(str(source_path), str(backup_path))
        return str(backup_path)
    except Exception as e:
        print(f"Error backing up file: {e}")
        return None

def restore_file(backup_path, restore_path):
    """Restore file from backup"""
    try:
        backup_file_path = Path(backup_path)
        restore_file_path = Path(restore_path)
        
        # Create restore directory if needed
        restore_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy backup to restore location
        shutil.copy2(str(backup_file_path), str(restore_file_path))
        return True
    except Exception as e:
        print(f"Error restoring file: {e}")
        return False

def validate_file_upload(file_path, max_size=None, allowed_types=None):
    """Validate uploaded file"""
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return False, "File does not exist"
        
        # Check file size
        if max_size and path.stat().st_size > max_size:
            return False, f"File too large (max: {format_size(max_size)})"
        
        # Check file type
        if allowed_types:
            if path.suffix.lower() not in allowed_types:
                return False, f"File type not allowed: {path.suffix}"
        
        # Check if file is not empty
        if path.stat().st_size == 0:
            return False, "File is empty"
        
        return True, "Valid file"
    
    except Exception as e:
        return False, f"Error validating file: {e}"

def get_file_hash(file_path, algorithm='sha256'):
    """Get file hash"""
    try:
        import hashlib
        
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    except Exception as e:
        print(f"Error getting file hash: {e}")
        return None

def find_duplicate_files(directory):
    """Find duplicate files in directory"""
    try:
        file_hashes = {}
        duplicates = []
        
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file():
                file_hash = get_file_hash(str(file_path))
                if file_hash:
                    if file_hash in file_hashes:
                        duplicates.append({
                            'original': file_hashes[file_hash],
                            'duplicate': str(file_path),
                            'hash': file_hash
                        })
                    else:
                        file_hashes[file_hash] = str(file_path)
        
        return duplicates
    
    except Exception as e:
        print(f"Error finding duplicates: {e}")
        return []
