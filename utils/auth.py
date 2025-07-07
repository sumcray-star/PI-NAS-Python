import streamlit as st
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    users_file = Path("data/users.json")
    if users_file.exists():
        try:
            with open(users_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_users(users):
    """Save users to JSON file"""
    users_file = Path("data/users.json")
    users_file.parent.mkdir(exist_ok=True)
    
    try:
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except IOError:
        return False

def register_user(username, password):
    """Register a new user"""
    users = load_users()
    
    if username in users:
        return False
    
    users[username] = {
        'password': hash_password(password),
        'created_at': datetime.now().isoformat(),
        'is_admin': len(users) == 0  # First user is admin
    }
    
    return save_users(users)

def authenticate_user(username, password):
    """Authenticate user login"""
    users = load_users()
    
    if username not in users:
        return False
    
    if users[username]['password'] == hash_password(password):
        # Set session state
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.is_admin = users[username].get('is_admin', False)
        st.session_state.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Initialize recent activity
        if 'recent_activity' not in st.session_state:
            st.session_state.recent_activity = []
        
        st.session_state.recent_activity.append(f"User {username} logged in at {st.session_state.login_time}")
        
        return True
    
    return False

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def logout_user():
    """Logout current user"""
    if 'username' in st.session_state:
        username = st.session_state.username
        if 'recent_activity' not in st.session_state:
            st.session_state.recent_activity = []
        
        st.session_state.recent_activity.append(f"User {username} logged out at {datetime.now().strftime('%H:%M:%S')}")
    
    # Clear session state
    for key in ['authenticated', 'username', 'is_admin', 'login_time']:
        if key in st.session_state:
            del st.session_state[key]

def change_password(username, current_password, new_password):
    """Change user password"""
    users = load_users()
    
    if username not in users:
        return False
    
    if users[username]['password'] != hash_password(current_password):
        return False
    
    users[username]['password'] = hash_password(new_password)
    users[username]['password_changed_at'] = datetime.now().isoformat()
    
    return save_users(users)

def get_all_users():
    """Get list of all users (admin only)"""
    users = load_users()
    return list(users.keys())

def delete_user(username):
    """Delete a user (admin only)"""
    users = load_users()
    
    if username in users:
        del users[username]
        return save_users(users)
    
    return False

def get_user_info(username):
    """Get user information"""
    users = load_users()
    return users.get(username, {})

def is_admin(username):
    """Check if user is admin"""
    users = load_users()
    return users.get(username, {}).get('is_admin', False)

def promote_user(username, is_admin=True):
    """Promote/demote user to/from admin"""
    users = load_users()
    
    if username in users:
        users[username]['is_admin'] = is_admin
        users[username]['admin_changed_at'] = datetime.now().isoformat()
        return save_users(users)
    
    return False

def get_user_stats():
    """Get user statistics"""
    users = load_users()
    
    stats = {
        'total_users': len(users),
        'admin_users': sum(1 for user in users.values() if user.get('is_admin', False)),
        'recent_users': []
    }
    
    # Get users created in last 7 days
    from datetime import datetime, timedelta
    week_ago = datetime.now() - timedelta(days=7)
    
    for username, user_data in users.items():
        try:
            created_at = datetime.fromisoformat(user_data['created_at'])
            if created_at > week_ago:
                stats['recent_users'].append({
                    'username': username,
                    'created_at': created_at.strftime("%Y-%m-%d")
                })
        except (KeyError, ValueError):
            pass
    
    return stats
