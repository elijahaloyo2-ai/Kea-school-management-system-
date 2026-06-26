import streamlit as st
import sqlite3
import pandas as pd

# 🔒 GATEKEEPER MODULE: Restricted to System Administrators Only
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()
if st.session_state["role"] != "Admin":
    st.error(f"❌ Access Denied. Your profile tier ({st.session_state.get('display_role')}) does not have admin clearance.")
    st.stop()

st.title("👥 Student Registration & Admission Deck")

GRADES = [f"Grade {i}" for i in range(1, 10)]
tab_manual, tab_batch = st.tabs(["✍️ Manual Data Entry Form", "📊 Bulk Excel Spreadsheet Upload"])

with tab_manual:
    with st.form("manual_admission"):
        adm_no = st.text_input("Admission Number (ADM NO)")
        name = st.text_input("Full Registered Name")
        assess_no = st.text_input("Assessment Number")
        selected_grade = st.selectbox("Assigned Grade Level", GRADES)
        
        if st.form_submit_button("Admit New Student"):
            if adm_no and name and assess_no:
                conn = sqlite3.connect("school_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO students (adm_no, name, assessment_no, grade) VALUES (?, ?, ?, ?)",
                                   (adm_no.strip(), name.strip(), assess_no.strip(), selected_grade))
                    conn.commit()
                    st.success(f"Successfully admitted student: {name} ({adm_no}) into {selected_grade}")
                except sqlite3.IntegrityError:
                    st.error("Admission Number already exists inside records.")
                finally:
                    conn.close()
            else:
                st.error("All data fields must be populated.")

with tab_batch:
    st.info("Ensure files contain exact columns: ADM NO, NAME, ASSESSMENT NO, GRADE")
    uploaded_excel = st.file_uploader("Upload Student Spreadsheet", type=["xlsx", "csv"])
    if uploaded_excel:
        try:
            df = pd.read_excel(uploaded_excel) if uploaded_excel.name.endswith("xlsx") else pd.read_csv(uploaded_excel)
            st.dataframe(df, use_container_width=True)
            
            if st.button("Process Bulk Admission"):
                conn = sqlite3.connect("school_data.db")
                cursor = conn.cursor()
                success_count = 0
                for _, row in df.iterrows():
                    try:
                        cursor.execute("INSERT INTO students (adm_no, name, assessment_no, grade) VALUES (?, ?, ?, ?)",
                                       (str(row['ADM NO']).strip(), str(row['NAME']).strip(), str(row['ASSESSMENT NO']).strip(), str(row['GRADE']).strip()))
                        success_count += 1
                    except Exception:
                        continue
                conn.commit()
                conn.close()
                st.success(f"Successfully loaded {success_count} student records into database system profiles.")
        except Exception as e:
            st.error(f"Spreadsheet Processing Error: {e}")
