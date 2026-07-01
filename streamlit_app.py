import streamlit as st
import sqlite3
import hashlib
import os

# 🚨 RULE 1 OF STREAMLIT: set_page_config MUST ALWAYS RUN FIRST BEFORE ANY OTHER ST ENTRY
st.set_page_config(page_title="KEA System - Command Deck", page_icon="🏫", layout="wide")

# --- DATABASE SETUP & CORRECTION DESK ---
def verify_and_build_database():
    db_needs_init = True
    if os.path.exists("school_data.db"):
        try:
            conn = sqlite3.connect("school_data.db")
            cursor = conn.cursor()
            # Double check if the users core database registry is healthy
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            if cursor.fetchone():
                db_needs_init = False  
            conn.close()
        except Exception:
            db_needs_init = True

    if db_needs_init:
        try:
            from init_db import initialize_database
            initialize_database()
        except Exception:
            pass

# Safe database initialization check execution
verify_and_build_database()

# Initialize session state variables safely upfront
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""

def verify_login(user, pwd):
    try:
        conn = sqlite3.connect("school_data.db")
        cursor = conn.cursor()
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest()
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (user, hashed_pwd))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.OperationalError:
        # Emergency fallback if database tables are still locked or unreadable
        return None

def fetch_teacher_profile(username):
    conn = sqlite3.connect("school_data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name, photo FROM teachers WHERE username = ?", (username,))
        res = cursor.fetchone()
    except Exception:
        res = None
    conn.close()
    return res if res else ("Instructor", None)

# --- APPLICATION AUTHENTICATION DECK LAYOUT ---
if not st.session_state["logged_in"]:
    
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏫 MC ALOYO ANALYSIS SYSTEM</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #475569;'>KEA COMPREHENSIVE SCHOOL Command Center</h4>", unsafe_allow_html=True)
    
    # Restored center frame profile badge logo asset
    col_logo_center, _ = st.columns([1, 3])
    with col_logo_center:
        st.markdown("<div style='text-align: center; font-size: 72px;'>🏫</div>", unsafe_allow_html=True)

    with st.form("login_form"):
        st.subheader("🔒 Authentication Portal")
        input_user = st.text_input("Username / Access ID")
        input_pwd = st.text_input("Security Access Password", type="password")
        submit_btn = st.form_submit_button("Authorize Access Session", type="primary")
        
        if submit_btn:
            user_role = verify_login(input_user, input_pwd)
            if user_role:
                st.session_state["logged_in"] = True
                st.session_state["username"] = input_user
                st.session_state["role"] = user_role
                st.success("Authorization Granted! Provisioning secure environment modules...")
                st.rerun()
            else:
                st.error("Access Denied: Invalid credentials token provided or table structure missing.")
else:
    # --- AUTHENTICATED USER ENVIRONMENT ---
    # Sidebar control panel
    st.sidebar.markdown(f"### 👤 Active Account")
    st.sidebar.write(f"**User:** {st.session_state['username']}")
    st.sidebar.info(f"🛡️ **Role Profile:** {st.session_state['role']}")
    
    if st.sidebar.button("🔒 Terminate Secure Session", type="primary"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = ""
        st.rerun()
        
    current_role = st.session_state["role"]
    
    if current_role == "Admin":
        st.markdown("## ⚙️ Institutional Supreme Administrative Workspace")
        st.write("Welcome, System Administrator. You have comprehensive master read/write clearance across all database entries.")
        
        # --- EXCLUSIVE ADMIN QUICK NAVIGATION HUB ---
        st.markdown("### 📂 Quick Navigation Hub")
        
        col_nav1, col_nav2, col_nav3 = st.columns(3)
        col_nav1.page_link("pages/1_Student_Registration.py", label="Register & Manage Students", icon="👥")
        col_nav2.page_link("pages/4_Teacher_Registration.py", label="Manage Faculty Allocations", icon="💼")
        col_nav3.page_link("pages/5_Fee_Payments.py", label="Institutional Fee Ledgers", icon="💰")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_nav4, col_nav5, col_nav6 = st.columns(3)
        col_nav4.page_link("pages/6_Teacher_Portal.py", label="Global Marks Review Deck", icon="✏️")
        col_nav5.page_link("pages/3_Results_Analysis.py", label="View School Analytics Performance", icon="📊")
        col_nav6.page_link("pages/7_Staff_Attendance.py", label="Teacher Attendance Logs", icon="⏱️")
        
    elif current_role in ["Class Teacher", "Subject Teacher"]:
        official_name, photo_blob = fetch_teacher_profile(st.session_state["username"])
        st.markdown(f"## 🏫 Welcome back, Instructor {official_name}!")
        
        col_profile, col_actions = st.columns([1, 3])
        with col_profile:
            if photo_blob:
                st.image(photo_blob, caption="Official Faculty Profile", width=170)
            else:
                st.markdown("<div style='background-color:#F1F5F9; width:160px; height:160px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2px solid #CBD5E1;'><span style='font-size:64px;'>👨‍🏫</span></div>", unsafe_allow_html=True)
                st.caption("Default Profile Asset")

        with col_actions:
            if current_role == "Class Teacher":
                assigned_class_room = st.session_state.get('assigned_class') or "Assigned Learning Class"
                st.success(f"📋 Managed Learning Environment Active for: **{assigned_class_room}**")
                
                col_a, col_b = st.columns(2)
                col_a.page_link("pages/6_Teacher_Portal.py", label="Access Marks Entry Desk", icon="✏️")
                col_b.page_link("pages/3_Results_Analysis.py", label="Review My Class Performance", icon="📊")
            else:
                st.warning("📖 Subject Instructor Access Scope Loaded. Please use the navigation pages sidebar to proceed with curriculum assessment postings.")
