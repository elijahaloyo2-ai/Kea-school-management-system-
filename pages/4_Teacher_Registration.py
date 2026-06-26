import streamlit as st
import sqlite3
import hashlib
import pandas as pd  # 💡 ADD THIS LINE HERE
# 🔒 GATEKEEPER MODULE: Restricted to System Administrators Only
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()
if st.session_state["role"] != "Admin":
    st.error(f"❌ Access Denied. Your profile tier ({st.session_state.get('display_role')}) does not have admin clearance.")
    st.stop()

st.title("💼 Faculty Human Resource Control Board")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

tab_reg, tab_mod = st.tabs(["➕ Add New Teacher Account", "⚙️ Update / Transfer Profile Management"])
DESIGNATIONS = ["Head of Institution (HOI)", "Deputy Head of Institution (DHOI)", "Senior teacher", "Teacher", "Junior Teacher"]

with tab_reg:
    with st.form("teacher_reg"):
        f_name = st.text_input("Teacher's Full Name")
        u_name = st.text_input("Secure Login Username")
        p_word = st.text_input("Temporary Assignment Password", type="password")
        desig = st.selectbox("Designation Rank Role", DESIGNATIONS)
        uploaded_photo = st.file_uploader("Upload Profile Image Asset", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("Register Faculty Profile"):
            if f_name and u_name and p_word:
                img_blob = uploaded_photo.read() if uploaded_photo else None
                conn = sqlite3.connect("school_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users (username, full_name, password_hash, designation, photo) VALUES (?, ?, ?, ?, ?)",
                                   (u_name.strip(), f_name.strip(), hash_password(p_word), desig, img_blob))
                    conn.commit()
                    st.success(f"Successfully configured credentials for {f_name}")
                except sqlite3.IntegrityError:
                    st.error("Username already chosen by another faculty member.")
                finally:
                    conn.close()

with tab_mod:
    conn = sqlite3.connect("school_data.db")
    df_teachers = pd.read_sql_query("SELECT username, full_name, designation FROM users", conn)
    conn.close()
    st.dataframe(df_teachers, use_container_width=True)
    
    selected_user = st.selectbox("Select Account Holder to Modify", df_teachers['username'].tolist())
    action = st.radio("Operational Objective Type", ["Modify Profile Rank Status", "Revoke Account Profile Access (Transfer Out)"])
    
    if action == "Modify Profile Rank Status":
        new_rank = st.selectbox("Select New Designation Level", DESIGNATIONS, key="mod_rank")
        if st.button("Apply Structural Rank Assignment"):
            conn = sqlite3.connect("school_data.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET designation = ? WHERE username = ?", (new_rank, selected_user))
            conn.commit()
            conn.close()
            st.success(f"Updated rank profile for {selected_user}.")
            st.rerun()
