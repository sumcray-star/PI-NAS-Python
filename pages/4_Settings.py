import streamlit as st
from utils.auth import (
    is_authenticated, login_user, register_user, logout_user,
    change_password, get_all_users, delete_user, promote_user,
    is_admin, get_user_stats
)

st.set_page_config(
    page_title="Settings - PI-NAS",
    page_icon="⚙️",
    layout="wide"
)

def main():
    st.title("⚙️ PI-NAS Settings")
    
    if not is_authenticated():
        show_login_page()
    else:
        show_settings_page()

def show_login_page():
    """Show login/register interface"""
    st.markdown("### 🔐 Authentication Required")
    
    # Login/Register tabs
    tab1, tab2 = st.tabs(["🔑 Login", "👤 Register"])
    
    with tab1:
        login_form()
    
    with tab2:
        register_form()

def login_form():
    """Login form"""
    st.markdown("#### Login to PI-NAS")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("🔑 Login", type="primary"):
            if username and password:
                if login_user(username, password):
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
            else:
                st.warning("Please enter both username and password")

def register_form():
    """Registration form"""
    st.markdown("#### Create New Account")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("👤 Register", type="primary"):
            if username and password and confirm_password:
                if password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    if register_user(username, password):
                        st.success("✅ Registration successful! You can now login.")
                    else:
                        st.error("❌ Username already exists")
            else:
                st.warning("Please fill in all fields")

def show_settings_page():
    """Main settings page for authenticated users"""
    username = st.session_state.get('username', 'User')
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {username}")
        
        if st.button("🚪 Logout", type="secondary"):
            logout_user()
            st.rerun()
        
        st.markdown("---")
        
        # Navigation
        settings_page = st.radio(
            "Settings",
            ["🏠 Overview", "🔐 Account", "👥 Users", "🎨 Appearance", "📊 Statistics"]
        )
    
    # Main content
    if settings_page == "🏠 Overview":
        show_overview()
    elif settings_page == "🔐 Account":
        show_account_settings()
    elif settings_page == "👥 Users":
        show_user_management()
    elif settings_page == "🎨 Appearance":
        show_appearance_settings()
    elif settings_page == "📊 Statistics":
        show_statistics()

def show_overview():
    """System overview"""
    st.header("🏠 System Overview")
    
    # System status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; text-align: center;">
            <h3 style="color: white; margin: 0;">System Status</h3>
            <p style="color: white; margin: 10px 0; font-size: 24px;">✅ Online</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 20px; border-radius: 10px; text-align: center;">
            <h3 style="color: white; margin: 0;">Network Storage</h3>
            <p style="color: white; margin: 10px 0; font-size: 24px;">🔗 Connected</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 20px; border-radius: 10px; text-align: center;">
            <h3 style="color: white; margin: 0;">Media Files</h3>
            <p style="color: white; margin: 10px 0; font-size: 24px;">📁 Ready</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("---")
    st.header("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📚 Media Library", use_container_width=True):
            st.switch_page("pages/1_Media_Library.py")
    
    with col2:
        if st.button("📤 Upload Files", use_container_width=True):
            st.switch_page("pages/2_Upload_Media.py")
    
    with col3:
        if st.button("🌐 Network Storage", use_container_width=True):
            st.switch_page("pages/3_Network_Storage.py")
    
    with col4:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.switch_page("app.py")

def show_account_settings():
    """Account settings"""
    st.header("🔐 Account Settings")
    
    username = st.session_state.get('username', 'User')
    
    # Account info
    st.subheader("👤 Account Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Username:** {username}")
        st.info(f"**Role:** {'Admin' if is_admin(username) else 'User'}")
    
    with col2:
        st.info(f"**Account Status:** Active")
        st.info(f"**Last Login:** Recent")
    
    # Change password
    st.subheader("🔒 Change Password")
    
    with st.form("change_password"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("🔒 Change Password"):
            if current_password and new_password and confirm_new_password:
                if new_password != confirm_new_password:
                    st.error("❌ New passwords do not match")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    if change_password(username, current_password, new_password):
                        st.success("✅ Password changed successfully!")
                    else:
                        st.error("❌ Current password is incorrect")
            else:
                st.warning("Please fill in all fields")

def show_user_management():
    """User management (Admin only)"""
    st.header("👥 User Management")
    
    username = st.session_state.get('username', 'User')
    
    if not is_admin(username):
        st.warning("⚠️ Admin access required for user management")
        return
    
    # User list
    st.subheader("👥 All Users")
    
    users = get_all_users()
    if users:
        for user in users:
            with st.expander(f"👤 {user['username']} {'(Admin)' if user.get('is_admin', False) else ''}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Username:** {user['username']}")
                    st.write(f"**Role:** {'Admin' if user.get('is_admin', False) else 'User'}")
                
                with col2:
                    # Promote/Demote
                    if user['username'] != username:  # Can't modify own account
                        if user.get('is_admin', False):
                            if st.button(f"👤 Demote to User", key=f"demote_{user['username']}"):
                                promote_user(user['username'], False)
                                st.success(f"✅ {user['username']} demoted to user")
                                st.rerun()
                        else:
                            if st.button(f"👑 Promote to Admin", key=f"promote_{user['username']}"):
                                promote_user(user['username'], True)
                                st.success(f"✅ {user['username']} promoted to admin")
                                st.rerun()
                
                with col3:
                    # Delete user
                    if user['username'] != username:  # Can't delete own account
                        if st.button(f"🗑️ Delete User", key=f"delete_{user['username']}"):
                            if st.session_state.get(f"confirm_delete_{user['username']}", False):
                                delete_user(user['username'])
                                st.success(f"✅ User {user['username']} deleted")
                                st.rerun()
                            else:
                                st.session_state[f"confirm_delete_{user['username']}"] = True
                                st.warning("Click again to confirm deletion")
    else:
        st.info("No users found")

def show_appearance_settings():
    """Appearance settings"""
    st.header("🎨 Appearance Settings")
    
    st.markdown("### 🌙 Theme")
    st.info("PI-NAS uses a dark theme optimized for media viewing")
    
    st.markdown("### 🎨 Color Scheme")
    st.info("Current theme: Dark with blue accents")
    
    st.markdown("### 📱 Layout")
    layout_option = st.radio(
        "Layout Style",
        ["Wide", "Centered", "Compact"]
    )
    
    if st.button("💾 Save Appearance Settings"):
        st.success("✅ Appearance settings saved!")

def show_statistics():
    """System statistics"""
    st.header("📊 System Statistics")
    
    # User stats
    user_stats = get_user_stats()
    
    st.subheader("👥 User Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Users", user_stats.get('total_users', 0))
    
    with col2:
        st.metric("Admin Users", user_stats.get('admin_users', 0))
    
    with col3:
        st.metric("Active Sessions", user_stats.get('active_sessions', 0))
    
    # Media stats
    st.subheader("📁 Media Statistics")
    
    from utils.media_handler import get_media_stats
    media_stats = get_media_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Files", media_stats.get('total_files', 0))
    
    with col2:
        st.metric("Videos", media_stats.get('videos', 0))
    
    with col3:
        st.metric("Images", media_stats.get('images', 0))
    
    with col4:
        st.metric("Documents", media_stats.get('documents', 0))
    
    # Storage stats
    st.subheader("💾 Storage Statistics")
    
    from utils.network_storage import get_storage_stats
    storage_stats = get_storage_stats()
    
    if storage_stats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Space", f"{storage_stats.get('total_gb', 0):.1f} GB")
        
        with col2:
            st.metric("Used Space", f"{storage_stats.get('used_gb', 0):.1f} GB")
        
        with col3:
            st.metric("Free Space", f"{storage_stats.get('free_gb', 0):.1f} GB")
    else:
        st.info("Storage statistics not available")

if __name__ == "__main__":
    main()