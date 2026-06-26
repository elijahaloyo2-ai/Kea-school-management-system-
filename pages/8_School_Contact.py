import streamlit as st
import sqlite3
import pandas as pd

# 🔒 GATEKEEPER MODULE: Open to ALL authenticated logged-in system staff roles
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()

st.title("🏫 Campus Geography & Co-curricular Media Assets")
st.markdown("### 📍 Contact Desk Registry\n* **Postal Address:** P.O BOX 557-40404 SUNA MIGORI")

conn = sqlite3.connect("school_data.db")
cursor = conn.cursor()
cursor.execute("SELECT value FROM contact_info WHERE key = 'map_embed'")
map_url = cursor.fetchone()[0]
conn.close()

st.components.v1.iframe(map_url, height=450)

# Static restriction check: Only show modification tools to Admins
if st.session_state["role"] == "Admin":
    st.markdown("### 🛠️ Media Uploads (Admin Control Hub)")
    with st.form("co_curricular_form"):
        caption = st.text_input("Event Description")
        uploaded_media = st.file_uploader("Upload Photo File", type=["png","jpg","jpeg"])
        if st.form_submit_button("Post Media Update"):
            if caption and uploaded_media:
                conn = sqlite3.connect("school_data.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO co_curricular (caption, image_blob) VALUES (?, ?)", (caption, uploaded_media.read()))
                conn.commit()
                conn.close()
                st.success("Activity uploaded.")
