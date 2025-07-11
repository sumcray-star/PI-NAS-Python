import json
import os
import subprocess
from pathlib import Path
import socket
import ipaddress

# Configuration file
CONFIG_FILE = Path("config/storage_config.json")

def get_network_storage_config():
    """Load network storage configuration"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading network storage config: {e}")
        return {}

def save_network_storage_config(config):
    """Save network storage configuration"""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving network storage config: {e}")
        return False

def test_smb_connection(server_ip, share_name, username, password):
    """Test SMB/CIFS connection"""
    try:
        # Test basic connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((server_ip, 445))
        sock.close()
        
        if result != 0:
            return {'success': False, 'error': f'Cannot connect to {server_ip}:445'}
        
        # Test SMB connection with smbclient
        cmd = ['smbclient', '-L', f'//{server_ip}', '-U', username, '-N'] if not password else [
            'smbclient', '-L', f'//{server_ip}', '-U', f'{username}%{password}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return {'success': True, 'shares': result.stdout}
        else:
            return {'success': False, 'error': result.stderr or 'Connection failed'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def mount_smb_share(server_ip, share_name, username, password, mount_point):
    """Mount SMB/CIFS share"""
    try:
        # Create mount point directory
        mount_path = Path(mount_point)
        mount_path.mkdir(parents=True, exist_ok=True)
        
        # Check if already mounted
        if is_mount_point(mount_point):
            return {'success': True, 'message': 'Already mounted'}
        
        # Create credentials file
        creds_file = Path("/tmp/smb_creds")
        with open(creds_file, 'w') as f:
            f.write(f"username={username}\n")
            f.write(f"password={password}\n")
        
        os.chmod(creds_file, 0o600)
        
        # Mount command
        cmd = [
            'sudo', 'mount', '-t', 'cifs',
            f'//{server_ip}/{share_name}',
            str(mount_path),
            '-o', f'credentials={creds_file},uid={os.getuid()},gid={os.getgid()},iocharset=utf8'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Clean up credentials file
        creds_file.unlink(missing_ok=True)
        
        if result.returncode == 0:
            return {'success': True, 'mount_point': str(mount_path)}
        else:
            return {'success': False, 'error': result.stderr or result.stdout}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def unmount_smb_share(mount_point):
    """Unmount SMB/CIFS share"""
    try:
        if not is_mount_point(mount_point):
            return {'success': True, 'message': 'Not mounted'}
        
        cmd = ['sudo', 'umount', mount_point]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return {'success': True, 'message': 'Unmounted successfully'}
        else:
            return {'success': False, 'error': result.stderr or result.stdout}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def is_mount_point(path):
    """Check if path is a mount point"""
    try:
        # Check if path exists and is a directory
        if not os.path.exists(path) or not os.path.isdir(path):
            return False
        
        # Check if it's a mount point using mountpoint command
        result = subprocess.run(['mountpoint', '-q', path], capture_output=True)
        return result.returncode == 0
        
    except Exception:
        return False

def get_mounted_shares():
    """Get list of mounted network shares"""
    try:
        mounted_shares = []
        
        # Get mount information
        result = subprocess.run(['mount'], capture_output=True, text=True)
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'type cifs' in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        device = parts[0]
                        mount_point = parts[2]
                        fs_type = parts[4]
                        options = parts[5].strip('()')
                        
                        share_info = {
                            'device': device,
                            'mount_point': mount_point,
                            'type': fs_type,
                            'options': options
                        }
                        
                        # Get storage statistics
                        try:
                            statvfs = os.statvfs(mount_point)
                            total_bytes = statvfs.f_blocks * statvfs.f_frsize
                            free_bytes = statvfs.f_bavail * statvfs.f_frsize
                            used_bytes = total_bytes - free_bytes
                            
                            share_info['stats'] = {
                                'total_gb': total_bytes / (1024**3),
                                'used_gb': used_bytes / (1024**3),
                                'free_gb': free_bytes / (1024**3),
                                'usage_percent': (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0
                            }
                        except:
                            pass
                        
                        mounted_shares.append(share_info)
    
    except Exception as e:
        print(f"Error getting mounted shares: {e}")
    
    return mounted_shares

def scan_network_devices(network_range="192.168.1.0/24"):
    """Scan network for devices"""
    devices = []
    
    try:
        # Extract network and host parts
        network = ipaddress.ip_network(network_range, strict=False)
        
        for ip in network.hosts():
            try:
                # Quick ping test
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '1', str(ip)],
                    capture_output=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    device = {'ip': str(ip)}
                    
                    # Try to get hostname
                    try:
                        hostname = socket.gethostbyaddr(str(ip))[0]
                        device['hostname'] = hostname
                    except:
                        device['hostname'] = 'Unknown'
                    
                    # Check if SMB service is available
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex((str(ip), 445))
                        sock.close()
                        device['smb_available'] = result == 0
                    except:
                        device['smb_available'] = False
                    
                    devices.append(device)
                    
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
    
    except Exception as e:
        print(f"Error scanning network: {e}")
    
    return devices

def check_network_storage():
    """Check network storage connection status"""
    try:
        config = get_network_storage_config()
        
        if not config.get('enabled', False):
            return {'connected': False, 'error': 'Network storage not enabled'}
        
        mount_point = config.get('mount_point', '/mnt/pi-nas')
        
        if is_mount_point(mount_point):
            
            # Get basic stats
            try:
                statvfs = os.statvfs(mount_point)
                total_bytes = statvfs.f_blocks * statvfs.f_frsize
                free_bytes = statvfs.f_bavail * statvfs.f_frsize
                used_bytes = total_bytes - free_bytes
                
                stats = {
                    'total_gb': total_bytes / (1024**3),
                    'used_gb': used_bytes / (1024**3),
                    'free_gb': free_bytes / (1024**3),
                    'usage_percent': (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0
                }
                
                return {'connected': True, 'stats': stats}
            
            except Exception as e:
                return {'connected': True, 'error': f'Cannot get storage stats: {e}'}
        else:
            return {'connected': False, 'error': 'Storage not mounted'}
    
    except Exception as e:
        return {'connected': False, 'error': f'Cannot access mount point: {e}'}

def get_storage_stats():
    """Get storage statistics for network storage"""
    config = get_network_storage_config()
    mount_point = config.get('mount_point', '/mnt/pi-nas')
    
    if not is_mount_point(mount_point):
        return None
    
    try:
        statvfs = os.statvfs(mount_point)
        total_bytes = statvfs.f_blocks * statvfs.f_frsize
        free_bytes = statvfs.f_bavail * statvfs.f_frsize
        used_bytes = total_bytes - free_bytes
        
        return {
            'total_gb': total_bytes / (1024**3),
            'used_gb': used_bytes / (1024**3),
            'free_gb': free_bytes / (1024**3),
            'usage_percent': (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0
        }
    
    except Exception as e:
        print(f"Error getting storage stats: {e}")
        return None

def auto_mount_network_storage():
    """Auto-mount network storage on startup"""
    config = get_network_storage_config()
    
    if not config.get('auto_mount', False) or not config.get('enabled', False):
        return False
    
    server_ip = config.get('server_ip')
    share_name = config.get('share_name')
    username = config.get('username')
    mount_point = config.get('mount_point')
    
    if not all([server_ip, share_name, username, mount_point]):
        return False
    
    # Check if already mounted
    if is_mount_point(mount_point):
        return True
    
    # Try to mount
    password = os.getenv('SMB_PASSWORD', '')  # Get password from environment
    result = mount_smb_share(server_ip, share_name, username, password, mount_point)
    
    return result.get('success', False)

def sync_media_to_network_storage():
    """Sync local media to network storage"""
    config = get_network_storage_config()
    mount_point = config.get('mount_point')
    
    if not mount_point or not is_mount_point(mount_point):
        return {'success': False, 'error': 'Network storage not mounted'}
    
    try:
        import shutil
        
        local_media = Path("media/uploads")
        network_media = Path(mount_point) / "media"
        
        if local_media.exists():
            # Create network media directory
            network_media.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            for file_path in local_media.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(local_media)
                    target_path = network_media / relative_path
                    
                    # Create parent directories
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file if it doesn't exist or is newer
                    if not target_path.exists() or file_path.stat().st_mtime > target_path.stat().st_mtime:
                        shutil.copy2(file_path, target_path)
            
            return {'success': True}
        else:
            return {'success': False, 'error': 'No local media found'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}