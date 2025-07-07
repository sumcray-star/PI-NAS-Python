import os
import json
import subprocess
import socket
from pathlib import Path
import psutil
import time

def get_network_storage_config():
    """Load network storage configuration"""
    config_path = Path("config/storage_config.json")
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Default configuration
    return {
        'server_ip': '',
        'share_name': '',
        'username': '',
        'mount_point': '/mnt/pi-nas',
        'protocol': 'smb',
        'port': 445,
        'auto_mount': False,
        'mount_timeout': 30,
        'enabled': False
    }

def save_network_storage_config(config):
    """Save network storage configuration"""
    config_path = Path("config/storage_config.json")
    config_path.parent.mkdir(exist_ok=True)
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
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
            return {'success': False, 'error': 'Unable to connect to SMB port 445'}
        
        # Try to list shares using smbclient if available
        try:
            cmd = ['smbclient', '-L', f'//{server_ip}', '-U', f'{username}%{password}', '-N']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Parse shares from output
                shares = []
                for line in result.stdout.split('\n'):
                    if 'Disk' in line and not line.strip().startswith('IPC'):
                        parts = line.split()
                        if len(parts) > 0:
                            shares.append(parts[0])
                
                return {'success': True, 'shares': shares}
            else:
                return {'success': False, 'error': result.stderr or 'Authentication failed'}
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # smbclient not available, just return basic connectivity success
            return {'success': True, 'shares': []}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def mount_smb_share(server_ip, share_name, username, password, mount_point):
    """Mount SMB/CIFS share"""
    try:
        # Create mount point if it doesn't exist
        mount_path = Path(mount_point)
        mount_path.mkdir(parents=True, exist_ok=True)
        
        # Check if already mounted
        if is_mount_point(mount_point):
            return {'success': False, 'error': 'Already mounted'}
        
        # Try different mount methods
        
        # Method 1: Using mount.cifs
        try:
            cmd = [
                'sudo', 'mount', '-t', 'cifs',
                f'//{server_ip}/{share_name}',
                mount_point,
                '-o', f'username={username},password={password},uid={os.getuid()},gid={os.getgid()},iocharset=utf8'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {'success': True, 'mount_point': mount_point}
            else:
                error_msg = result.stderr or result.stdout
        
        except subprocess.TimeoutExpired:
            error_msg = "Mount operation timed out"
        
        except FileNotFoundError:
            error_msg = "mount.cifs not found"
        
        # Method 2: Using smbclient + mount (fallback)
        try:
            # Create credentials file temporarily
            creds_file = Path("/tmp/smb_creds")
            with open(creds_file, 'w') as f:
                f.write(f"username={username}\n")
                f.write(f"password={password}\n")
            
            os.chmod(creds_file, 0o600)
            
            cmd = [
                'sudo', 'mount', '-t', 'cifs',
                f'//{server_ip}/{share_name}',
                mount_point,
                '-o', f'credentials={creds_file},uid={os.getuid()},gid={os.getgid()}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Clean up credentials file
            creds_file.unlink(missing_ok=True)
            
            if result.returncode == 0:
                return {'success': True, 'mount_point': mount_point}
            else:
                error_msg = result.stderr or result.stdout
        
        except Exception as e:
            error_msg = str(e)
        
        return {'success': False, 'error': error_msg}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def unmount_smb_share(mount_point):
    """Unmount SMB/CIFS share"""
    try:
        if not is_mount_point(mount_point):
            return {'success': False, 'error': 'Not mounted'}
        
        cmd = ['sudo', 'umount', mount_point]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return {'success': True}
        else:
            # Try force unmount
            cmd = ['sudo', 'umount', '-f', mount_point]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return {'success': True}
            else:
                return {'success': False, 'error': result.stderr or result.stdout}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def is_mount_point(path):
    """Check if path is a mount point"""
    try:
        return os.path.ismount(path)
    except:
        return False

def get_mounted_shares():
    """Get list of mounted network shares"""
    mounted_shares = []
    
    try:
        # Parse /proc/mounts for network mounts
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4:
                    device, mount_point, fs_type, options = parts[0], parts[1], parts[2], parts[3]
                    
                    # Check for network file systems
                    if fs_type in ['cifs', 'nfs', 'smbfs']:
                        share_info = {
                            'source': device,
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
        import ipaddress
        
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
                        pass
                    
                    # Try to get MAC address (Linux only)
                    try:
                        arp_result = subprocess.run(
                            ['arp', '-n', str(ip)],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        
                        if arp_result.returncode == 0:
                            for line in arp_result.stdout.split('\n'):
                                if str(ip) in line:
                                    parts = line.split()
                                    if len(parts) >= 3:
                                        mac = parts[2]
                                        if ':' in mac:
                                            device['mac'] = mac
                                            break
                    except:
                        pass
                    
                    devices.append(device)
            
            except:
                continue
    
    except Exception as e:
        print(f"Error scanning network: {e}")
    
    return devices

def check_network_storage():
    """Check network storage connection status"""
    config = get_network_storage_config()
    
    if not config.get('enabled', False):
        return {'connected': False, 'error': 'Network storage disabled'}
    
    mount_point = config.get('mount_point', '/mnt/pi-nas')
    
    # Check if mount point exists and is mounted
    if not Path(mount_point).exists():
        return {'connected': False, 'error': 'Mount point does not exist'}
    
    if not is_mount_point(mount_point):
        return {'connected': False, 'error': 'Not mounted'}
    
    # Test connectivity by trying to list directory
    try:
        list(Path(mount_point).iterdir())
        
        # Get storage stats
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
