import streamlit as st
import sqlite3
import hashlib
import os  # 💡 Add this import

# --- AUTOMATIC DATABASE INITIALIZER ---
# This checks if the database exists. If it doesn't, it automatically builds it!
if not os.path.exists("school_data.db"):
    try:
        # Import the initialize function from your init_db.py file
        from init_db import initialize_database
        initialize_database()
        st.toast("🎯 Database successfully initialized for the first time!", icon="💾")
    except Exception as init_error:
        st.error(f"Failed to auto-initialize database: {init_error}")

# Initialize session state variables safely upfront
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
# ... (rest of your streamlit_app.py code continues exactly as before)

# Initialize session state variables safely upfront
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "display_role" not in st.session_state:
    st.session_state["display_role"] = ""
if "assigned_class" not in st.session_state:
    st.session_state["assigned_class"] = None

st.set_page_config(page_title="KEA Administration Portal", page_icon="🏫", layout="wide")

# --- CUSTOM CSS FOR THE PROFESSIONAL LIGHT THEME & CARDS ---
st.markdown("""
<style>
    /* Force professional white/light theme background */
    .stApp {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
    }
    
    /* Force high visibility text colors on all Streamlit page links & buttons */
    [data-testid="stPageLink-FormSubmitButton"] span,
    [data-testid="stPageLink-FormSubmitButton"] p,
    .stPageLink p,
    .stPageLink span {
        color: #1E293B !important;
        font-weight: 500 !important;
    }
    
    /* Smooth hover contrast background change for navigation links */
    .stPageLink:hover {
        background-color: #F1F5F9 !important;
        border-radius: 6px;
    }

    /* Custom styling for your Dashboard Cards */
    .kpi-card {
        background-color: #F8FAFC;
        border-left: 5px solid #1E3A8A;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0,0.05);
        margin-bottom: 15px;
    }
    .card-title {
        color: #64748B;
        font-size: 14px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .card-value {
        color: #1E3A8A;
        font-size: 28px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- SECURITY LOGIC ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    # Hardcoded master check for both administrator profiles
    if username == "Admin" and password == "Admin123":
        return True
    # Matches exactly: Username 'Hellen' and Password 'KEA2026'
    if username == "Hellen" and password == "Kea@2026":
        return True
        
    conn = sqlite3.connect("school_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0] == hash_password(password)
    return False

def fetch_live_dashboard_metrics():
    conn = sqlite3.connect("school_data.db")
    cursor = conn.cursor()
    
    # 1. Fetch total students count
    try:
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0] or 0
    except Exception:
        total_students = 0
        
    # 2. DIAGNOSTIC SCANNER: Print all tables to the screen
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        all_tables = [row[0] for row in cursor.fetchall()]
        st.sidebar.warning(f"Found Tables: {all_tables}")
    except Exception as e:
        st.sidebar.error(f"Scanner Error: {e}")
        
    # 3. Default total paid logic to keep code safe while checking
    total_paid = 0.0
    for table_name in ["fees", "fee_ledger", "fee_payments", "payments", "transactions"]:
        try:
            cursor.execute(f"SELECT SUM(amount) FROM {table_name}")
            result = cursor.fetchone()[0]
            if result is not None:
                total_paid = float(result)
                break
        except Exception:
            continue
            
    conn.close()
    
    per_student_fee_rate = 500.0
    expected_gross_fees = total_students * per_student_fee_rate
    pending_deficit_balance = max(0.0, expected_gross_fees - total_paid)
    
    return total_students, total_paid, pending_deficit_balance

def fetch_teacher_profile(username):
    conn = sqlite3.connect("school_data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT full_name, photo FROM teacher_assignments WHERE teacher_username = ?", (username,))
        row = cursor.fetchone()
    except Exception:
        row = None
    conn.close()
    
    # If the teacher exists and has a full name, use it. Otherwise, fall back to their username!
    if row and row[0]:
        return row[0], row[1]
    else:
        return username, row[1] if row else None

# --- DEFINE CLASS TEACHERS MAPPING ROLES ---
CLASS_TEACHERS = {
    "Grace": "Grade 7",
    "Omwanda": "Grade 8",
    "Lucas": "Grade 9"
}

# --- LOGIN SCREEN WORKFLOW ---
if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>KEA Comprehensive School Portal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Please sign in to access your administrative dashboard workspace</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            
            if st.form_submit_button("Access Portal"):
                if check_login(user_input, pass_input):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user_input
                    
                    # DYNAMIC EVALUATION ASSIGNING ACCESS LEVEL
                    if user_input in ["Admin", "Hellen"]:
                        st.session_state["role"] = "Admin"
                        if user_input == "Hellen":
                            st.session_state["display_role"] = "THE HEAD OF INSTITUTION"
                        else:
                            st.session_state["display_role"] = "System Administrator"
                    elif user_input in CLASS_TEACHERS:
                        st.session_state["role"] = "Class Teacher"
                        st.session_state["display_role"] = "Class Teacher"
                        st.session_state["assigned_class"] = CLASS_TEACHERS[user_input]
                    else:
                        st.session_state["role"] = "Subject Teacher"
                        st.session_state["display_role"] = "Subject Instructor"
                        
                    st.success("Access granted successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password configuration.")
else:
    # --- DASHBOARD LOGIC (SHOWN ONLY AFTER SUCCESSFUL LOGIN) ---
    
    # Sidebar Session Details & Logout Button
    st.sidebar.markdown("### 👤 Active Session")
    st.sidebar.write(f"Logged in as: **{st.session_state['username']}**")
    st.sidebar.write(f"Access Level: **{st.session_state['display_role']}**")
    
    if st.sidebar.button("🚪 Log Out"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = ""
        st.session_state["display_role"] = ""
        st.session_state["assigned_class"] = None
        st.rerun()
        
    # Header & Centered Logo Section
    left_spacer, center_content, right_spacer = st.columns([1, 2, 1])
    with center_content:
        try:
            st.image("logo.png", use_container_width=True)
        except Exception:
            pass
            
    st.markdown("---")
    
    # Display Greeting Banner based on Roles
    current_role = st.session_state["role"]
    display_title = st.session_state["display_role"]
    
    # 1. ADMIN DASHBOARD WORKFLOW
    if current_role == "Admin":
        st.markdown(f"### 🛡️ Core Management Command Center — Welcome, {display_title}")
        
        # Pull live metrics directly out of system tables
        active_headcount, dynamic_paid, dynamic_deficit = fetch_live_dashboard_metrics()
        
        # Card-Based Key Performance Indicators (KPIs)
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.markdown(f"""
                <div class='kpi-card'>
                    <div class='card-title'>Student Information System</div>
                    <div class='card-value'>{active_headcount} Active</div>
                </div>
            """, unsafe_allow_html=True)
        with kpi2:
            st.markdown(f"""
                <div class='kpi-card'>
                    <div class='card-title'>Financial Management Panel</div>
                    <div class='card-value'>Ksh {dynamic_paid:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
        with kpi3:
            st.markdown(f"""
                <div class='kpi-card'>
                    <div class='card-title'>Pending Balances Deficit</div>
                    <div class='card-value' style='color:#EF4444;'>Ksh {dynamic_deficit:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        st.markdown("### 📂 Quick Navigation Hub")
        
        col_nav1, col_nav2, col_nav3 = st.columns(3)
        col_nav1.page_link("pages/1_Student_Registration.py", label="Register & Manage Students", icon="👥")
        col_nav2.page_link("pages/4_Teacher_Registration.py", label="Manage Faculty Allocations", icon="💼")
        col_nav3.page_link("pages/5_Fee_Payments.py", label="Institutional Fee Ledgers", icon="💰")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_nav4, col_nav5 = st.columns(2)
        col_nav4.page_link("pages/6_Teacher_Portal.py", label="Global Marks Review Deck", icon="✏️")
        col_nav5.page_link("pages/3_Results_Analysis.py", label="View School Analytics Performance", icon="📊")

    # 2. NEW FACULTY WORKFLOW (CLASS TEACHER & SUBJECT TEACHER UPGRADE)
    elif current_role in ["Class Teacher", "Subject Teacher"]:
        # Fetch the official registration database values
        official_name, photo_blob = fetch_teacher_profile(st.session_state["username"])
        
        st.markdown(f"## 🏫 Welcome back, Instructor {official_name}!")
        
        col_profile, col_actions = st.columns([1, 3])
        
        with col_profile:
            if photo_blob:
                st.image(photo_blob, caption="Official Faculty Profile", width=170)
            else:
                # Elegant fallback profile icon circle container 
                st.markdown("""
                    <div style='background-color:#F1F5F9; width:160px; height:160px; border-radius:50%; 
                         display:flex; align-items:center; justify-content:center; border:2px solid #CBD5E1;'>
                        <span style='font-size:64px;'>👨‍🏫</span>
                    </div>
                """, unsafe_allow_html=True)
                st.caption("Default Profile Asset")

        with col_actions:
            if current_role == "Class Teacher":
                assigned_class_room = st.session_state.get('assigned_class') or "Assigned Learning Class"
                st.success(f"📋 Managed Learning Environment Active for: **{assigned_class_room}**")
                
                col_a, col_b = st.columns(2)
                col_a.page_link("pages/6_Teacher_Portal.py", label="Access Marks Entry Desk", icon="✏️")
                col_b.page_link("pages/3_Results_Analysis.py", label="Review My Class Performance", icon="📊")
            else:
                st.warning("📖 Subject Instructor Profile Dashboard Mode Active.")
                st.page_link("pages/6_Teacher_Portal.py", label="Access Assigned Learning Areas", icon="✏️")
