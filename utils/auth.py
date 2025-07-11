import json
import hashlib
import streamlit as st
from pathlib import Path
import os
from datetime import datetime

# User data file
USER_DATA_FILE = Path("data/users.json")

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    try:
        if USER_DATA_FILE.exists():
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading users: {e}")
        return []

def save_users(users):
    """Save users to JSON file"""
    try:
        USER_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def register_user(username, password):
    """Register a new user"""
    try:
        users = load_users()
        
        # Check if user already exists
        if any(user['username'] == username for user in users):
            return False
        
        # Create new user
        new_user = {
            'username': username,
            'password': hash_password(password),
            'is_admin': len(users) == 0,  # First user is admin
            'created_at': datetime.now().isoformat()
        }
        
        users.append(new_user)
        return save_users(users)
        
    except Exception as e:
        print(f"Error registering user: {e}")
        return False

def authenticate_user(username, password):
    """Authenticate user login"""
    try:
        users = load_users()
        hashed_password = hash_password(password)
        
        for user in users:
            if user['username'] == username and user['password'] == hashed_password:
                return True
        return False
        
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return False

def login_user(username, password):
    """Login user and set session"""
    if authenticate_user(username, password):
        st.session_state['authenticated'] = True
        st.session_state['username'] = username
        return True
    return False

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def logout_user():
    """Logout current user"""
    st.session_state['authenticated'] = False
    st.session_state['username'] = None

def change_password(username, current_password, new_password):
    """Change user password"""
    try:
        if not authenticate_user(username, current_password):
            return False
        
        users = load_users()
        for user in users:
            if user['username'] == username:
                user['password'] = hash_password(new_password)
                break
        
        return save_users(users)
        
    except Exception as e:
        print(f"Error changing password: {e}")
        return False

def get_all_users():
    """Get list of all users (admin only)"""
    try:
        current_user = st.session_state.get('username')
        if not current_user or not is_admin(current_user):
            return []
        
        users = load_users()
        # Remove password from response for security
        return [{'username': u['username'], 'is_admin': u.get('is_admin', False)} for u in users]
        
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

def delete_user(username):
    """Delete a user (admin only)"""
    try:
        current_user = st.session_state.get('username')
        if not current_user or not is_admin(current_user):
            return False
        
        users = load_users()
        users = [u for u in users if u['username'] != username]
        return save_users(users)
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False

def get_user_info(username):
    """Get user information"""
    try:
        users = load_users()
        for user in users:
            if user['username'] == username:
                return {
                    'username': user['username'],
                    'is_admin': user.get('is_admin', False),
                    'created_at': user.get('created_at', 'Unknown')
                }
        return None
        
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None

def is_admin(username):
    """Check if user is admin"""
    try:
        users = load_users()
        for user in users:
            if user['username'] == username:
                return user.get('is_admin', False)
        return False
        
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

def promote_user(username, is_admin=True):
    """Promote/demote user to/from admin"""
    try:
        current_user = st.session_state.get('username')
        if not current_user or not is_admin(current_user):
            return False
        
        users = load_users()
        for user in users:
            if user['username'] == username:
                user['is_admin'] = is_admin
                break
        
        return save_users(users)
        
    except Exception as e:
        print(f"Error promoting user: {e}")
        return False

def get_user_stats():
    """Get user statistics"""
    try:
        users = load_users()
        return {
            'total_users': len(users),
            'admin_users': sum(1 for u in users if u.get('is_admin', False)),
            'active_sessions': 1 if is_authenticated() else 0
        }
        
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {
            'total_users': 0,
            'admin_users': 0,
            'active_sessions': 0
        }