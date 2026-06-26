import streamlit as st
import sqlite3
import pandas as pd

# 🔒 GATEKEEPER MODULE: Restricted to Admins, Class Teachers, and Subject Teachers
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()
if st.session_state["role"] not in ["Admin", "Class Teacher", "Subject Teacher"]:
    st.error("❌ Access Denied. You do not hold academic editing clearance.")
    st.stop()

st.title("✏️ Academic Marks Entry Node")

GRADES = [f"Grade {i}" for i in range(1, 10)]
target_grade = st.selectbox("Target Assessment Grade Level", GRADES)

st.write("### Upload Assessment Spreadsheet")
excel_file = st.file_uploader("Upload Marks Records Sheet", type=["xlsx", "csv"])

if excel_file:
    try:
        df = pd.read_excel(excel_file) if excel_file.name.endswith("xlsx") else pd.read_csv(excel_file)
        st.dataframe(df.head(), use_container_width=True)
        
        if st.button("Execute Core System Submission"):
            conn = sqlite3.connect("school_data.db")
            cursor = conn.cursor()
            
            cols_mapping = {
                'MATHEMATICS': 'mathematics', 'ENGLISH': 'english', 'KISWAHILI': 'kiswahili',
                'INTEGRATED SCIENCE': 'integrated_science', 'AGRICULTURE': 'agriculture',
                'PRETECHNICAL STUDIES': 'pretechnical_studies', 'SOCIAL STUDIES': 'social_studies',
                'RELIGIOUS EDUCATION': 'religious_education', 'CAS': 'cas'
            }
            
            count = 0
            for _, row in df.iterrows():
                adm = str(row['ADM NO']).strip()
                cursor.execute("SELECT grade FROM students WHERE adm_no = ?", (adm,))
                db_grade = cursor.fetchone()
                if not db_grade or db_grade[0] != target_grade:
                    continue
                    
                m_vals = {}
                for k, col_db_name in cols_mapping.items():
                    val = row.get(k, 0)
                    try: m_vals[col_db_name] = float(val)
                    except: m_vals[col_db_name] = 0.0
                
                cursor.execute("""
                    INSERT INTO marks (adm_no, grade, mathematics, english, kiswahili, integrated_science, agriculture, pretechnical_studies, social_studies, religious_education, cas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(adm_no, grade) DO UPDATE SET
                        mathematics=excluded.mathematics, english=excluded.english, kiswahili=excluded.kiswahili,
                        integrated_science=excluded.integrated_science, agriculture=excluded.agriculture,
                        pretechnical_studies=excluded.pretechnical_studies, social_studies=excluded.social_studies,
                        religious_education=excluded.religious_education, cas=excluded.cas
                """, (adm, target_grade, m_vals['mathematics'], m_vals['english'], m_vals['kiswahili'],
                      m_vals['integrated_science'], m_vals['agriculture'], m_vals['pretechnical_studies'],
                      m_vals['social_studies'], m_vals['religious_education'], m_vals['cas']))
                count += 1
                
            conn.commit()
            conn.close()
            st.success(f"Processed and posted academic results for {count} valid students inside {target_grade}.")
    except Exception as e:
        st.error(f"Processing Failure: {e}")
