import streamlit as st
import sqlite3
import pandas as pd

# 🔒 GATEKEEPER MODULE: Open to Admins, Class Teachers, and Subject Teachers
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()
if st.session_state["role"] not in ["Admin", "Class Teacher", "Subject Teacher"]:
    st.error("❌ Access Denied. Your profile tier does not have clearance for the grading portal.")
    st.stop()

st.title("👨‍🏫 Subject Allocation & Marks Input Deck")
username = st.session_state["username"]

FACULTY_MAPS = {
    "Eliars": [("english", "Grade 7"), ("english", "Grade 8"), ("english", "Grade 9"), ("pretechnical_studies", "Grade 7"), ("cas", "Grade 8")],
    "Lucas": [("integrated_science", "Grade 7"), ("integrated_science", "Grade 8"), ("agriculture", "Grade 8"), ("agriculture", "Grade 9")],
    "Omwanda": [("social_studies", "Grade 7"), ("social_studies", "Grade 8"), ("social_studies", "Grade 9"), ("kiswahili", "Grade 8"), ("kiswahili", "Grade 9")],
    "Grace": [("religious_education", "Grade 7"), ("religious_education", "Grade 8"), ("agriculture", "Grade 7"), ("integrated_science", "Grade 9")],
    "EliasA": [("kiswahili", "Grade 7"), ("religious_education", "Grade 9")],
    "Valentine": [("mathematics", "Grade 7"), ("mathematics", "Grade 9")],
    "Elijah": [("mathematics", "Grade 8"), ("pretechnical_studies", "Grade 8"), ("pretechnical_studies", "Grade 9"), ("cas", "Grade 7"), ("cas", "Grade 9")]
}

if st.session_state["role"] == "Admin":
    all_subjects = ['mathematics', 'english', 'kiswahili', 'integrated_science', 'agriculture', 'pretechnical_studies', 'social_studies', 'religious_education', 'cas']
    selected_sub = st.selectbox("Select Subject (Admin)", all_subjects)
    selected_grd = st.selectbox("Select Grade (Admin)", [f"Grade {i}" for i in range(1, 10)])
else:
    my_tasks = FACULTY_MAPS.get(username, [])
    if not my_tasks:
        st.warning("You currently have no active course assignments allocated.")
        st.stop()
    task_strings = [f"{t[0].upper()} — {t[1]}" for t in my_tasks]
    idx = st.selectbox("Choose Assigned Subject Track", range(len(task_strings)), format_func=lambda x: task_strings[x])
    selected_sub, selected_grd = my_tasks[idx][0], my_tasks[idx][1]

conn = sqlite3.connect("school_data.db")
df_students = pd.read_sql_query("SELECT adm_no, name FROM students WHERE grade = ?", conn, params=(selected_grd,))

if not df_students.empty:
    df_scores = pd.read_sql_query(f"SELECT adm_no, {selected_sub} FROM marks WHERE grade = ?", conn, params=(selected_grd,))
    df_merged = pd.merge(df_students, df_scores, on="adm_no", how="left").fillna(0.0)
    
    updated_scores = {}
    with st.form("marks_grid"):
        for _, row in df_merged.iterrows():
            updated_scores[row['adm_no']] = st.number_input(f"{row['name']} ({row['adm_no']})", min_value=0.0, max_value=100.0, value=float(row[selected_sub]))
        if st.form_submit_button("Post Updates"):
            cursor = conn.cursor()
            for adm_no, score in updated_scores.items():
                cursor.execute(f"INSERT INTO marks (adm_no, grade, {selected_sub}) VALUES (?, ?, ?) ON CONFLICT(adm_no, grade) DO UPDATE SET {selected_sub}=excluded.{selected_sub}", (adm_no, selected_grd, score))
            conn.commit()
            st.success("Marks saved.")
conn.close()
