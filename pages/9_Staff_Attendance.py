import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 🔒 Check Session Authorization (STRICTLY ADMIN ONLY)
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()

if st.session_state.get("role") != "Admin":
    st.error("🛑 Access Denied. This Faculty Log Sheet Console is restricted solely to Institutional Administrators.")
    st.stop()

st.title("⏱️ Employee Log Sheet & Attendance Desk")
st.write("Record and manage the real-time clock-in/clock-out logs for institution faculty members.")

# --- DATABASE SETUP ---
def initialize_attendance_db():
    conn = sqlite3.connect("school_data.db")
    cursor = conn.cursor()
    # Create an attendance table tracking real-time events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            teacher_name TEXT,
            time_in TEXT,
            time_out TEXT,
            total_hours TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

initialize_attendance_db()

# --- HELPER WORKFLOWS ---
def get_all_teachers():
    """Fetches valid teacher first names from users or predefined system list."""
    conn = sqlite3.connect("school_data.db")
    cursor = conn.cursor()
    teachers = set(["Grace", "Omwanda", "Lucas"]) # Fallback defaults
    try:
        cursor.execute("SELECT username FROM users WHERE role IN ('Class Teacher', 'Subject Teacher')")
        for row in cursor.fetchall():
            teachers.add(row[0])
    except Exception:
        pass
    conn.close()
    return sorted(list(teachers))

# --- ATTENDANCE SYSTEM CONTROLS ---
col_btn1, col_btn2, _ = st.columns([1, 1, 2])

with col_btn1:
    if st.button("🟢 Time In", type="primary", use_container_width=True):
        st.session_state["show_time_in_modal"] = True
        st.session_state["show_time_out_modal"] = False

with col_btn2:
    if st.button("🔴 Time Out", type="secondary", use_container_width=True):
        st.session_state["show_time_out_modal"] = True
        st.session_state["show_time_in_modal"] = False

# --- "TIME IN" MODAL POPUP DIALOGUE ---
if st.session_state.get("show_time_in_modal", False):
    st.markdown("---")
    with st.form("time_in_form"):
        st.subheader("📥 Register Faculty Clock-In")
        teacher_list = get_all_teachers()
        selected_teacher = st.selectbox("Select Teacher First Name:", teacher_list)
        
        submitted = st.form_submit_button("Confirm Entry Success")
        if submitted:
            current_date = datetime.now().strftime("%d/%m/%Y")
            current_time = datetime.now().strftime("%I:%M:%S %p")
            
            conn = sqlite3.connect("school_data.db")
            cursor = conn.cursor()
            
            # Check if already timed in today without timing out
            cursor.execute("""
                SELECT id FROM staff_attendance 
                WHERE date = ? AND teacher_name = ? AND time_out IS NULL
            """, (current_date, selected_teacher))
            
            if cursor.fetchone():
                st.warning(f"⚠️ {selected_teacher} is already clocked in for today!")
            else:
                cursor.execute("""
                    INSERT INTO staff_attendance (date, teacher_name, time_in) 
                    VALUES (?, ?, ?)
                """, (current_date, selected_teacher, current_time))
                conn.commit()
                st.success(f"ℹ️ Welcome back! Your second home missed you, {selected_teacher}!")
                st.session_state["show_time_in_modal"] = False
                st.rerun()
            conn.close()

# --- "TIME OUT" MODAL POPUP DIALOGUE ---
if st.session_state.get("show_time_out_modal", False):
    st.markdown("---")
    with st.form("time_out_form"):
        st.subheader("📤 Register Faculty Clock-Out")
        
        # Get list of teachers currently clocked in
        current_date_str = datetime.now().strftime("%d/%m/%Y")
        conn = sqlite3.connect("school_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT teacher_name FROM staff_attendance WHERE date = ? AND time_out IS NULL", (current_date_str,))
        active_teachers = [r[0] for r in cursor.fetchall()]
        conn.close()
        
        if not active_teachers:
            st.info("No active teacher entries are currently clocked in.")
        else:
            selected_out_teacher = st.selectbox("Select Teacher Clocking Out:", active_teachers)
            submitted_out = st.form_submit_button("Confirm Exit Success")
            
            if submitted_out:
                current_time_out = datetime.now().strftime("%I:%M:%S %p")
                
                conn = sqlite3.connect("school_data.db")
                cursor = conn.cursor()
                
                # Fetch time_in string to calculate absolute duration
                cursor.execute("""
                    SELECT id, time_in FROM staff_attendance 
                    WHERE date = ? AND teacher_name = ? AND time_out IS NULL
                    ORDER BY id DESC LIMIT 1
                """, (current_date_str, selected_out_teacher))
                row = cursor.fetchone()
                
                if row:
                    row_id, t_in_str = row
                    try:
                        fmt = "%I:%M:%S %p"
                        tdelta = datetime.strptime(current_time_out, fmt) - datetime.strptime(t_in_str, fmt)
                        hours, remainder = divmod(tdelta.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        duration_str = f"{hours}h {minutes}m"
                    except Exception:
                        duration_str = "--"
                    
                    cursor.execute("""
                        UPDATE staff_attendance 
                        SET time_out = ?, total_hours = ? 
                        WHERE id = ?
                    """, (current_time_out, duration_str, row_id))
                    conn.commit()
                    st.success(f"👋 Goodbye {selected_out_teacher}. Shift log finalized successfully.")
                    st.session_state["show_time_out_modal"] = False
                    st.rerun()
                conn.close()

st.markdown("---")
st.subheader("📋 Institutional Weekly Log Summary Sheet")

# --- FETCH AND DISP_PLAY LEDGER DATA FOR THE WEEK ---
conn = sqlite3.connect("school_data.db")
query = """
    SELECT date AS 'Date', 
           teacher_name AS 'Employee Name', 
           time_in AS 'Time In', 
           time_out AS 'Time Out', 
           total_hours AS 'Total Hours'
    FROM staff_attendance 
    ORDER BY timestamp DESC
"""
try:
    attendance_df = pd.read_sql_query(query, conn)
    if not attendance_df.empty:
        st.dataframe(attendance_df, use_container_width=True, hide_index=True)
    else:
        # Show empty template mirror matching your uploaded layout
        empty_data = {
            "Date": [], "Employee Name": [], "Time In": [], "Time Out": [], "Total Hours": []
        }
        st.dataframe(pd.DataFrame(empty_data), use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Error reading logs: {e}")
finally:
    conn.close()
