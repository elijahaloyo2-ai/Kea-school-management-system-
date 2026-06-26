import streamlit as st
import sqlite3
import pandas as pd

# 🔒 Check Session Authorization
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()

st.title("👥 Student Registration & Admission Deck")

tab_manual, tab_batch = st.tabs(["✍️ Manual Data Entry Form", "📊 Bulk Excel Spreadsheet Upload"])

# =========================================================
# TAB 1: MANUAL REGISTRATION
# =========================================================
with tab_manual:
    with st.form("manual_reg_form"):
        st.subheader("Single Student Admission Registration")
        adm_no = st.text_input("Admission Number (ADM NO)")
        name = st.text_input("Full Student Name")
        assess_no = st.text_input("Assessment Number")
        grade = st.selectbox("Assigned Grade", ["Grade 7", "Grade 8", "Grade 9"])
        
        if st.form_submit_button("Register Student"):
            if not adm_no or not name:
                st.error("Admission Number and Full Name are strictly required.")
            else:
                try:
                    conn = sqlite3.connect("school_data.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO students (adm_no, name, assessment_no, grade)
                        VALUES (?, ?, ?, ?)
                    """, (adm_no.strip(), name.strip().upper(), assess_no.strip().upper(), grade))
                    conn.commit()
                    conn.close()
                    st.success(f"🚀 Successfully registered {name.upper()} under ADM NO: {adm_no}")
                except Exception as e:
                    st.error(f"Database Save Error: {e}")

# =========================================================
# TAB 2: BULK EXCEL SPREADSHEET UPLOAD (FIXED)
# =========================================================
with tab_batch:
    st.info("Ensure files contain headers: ADM NO, NAME, ASSESSMENT NO, GRADE")
    uploaded_excel = st.file_uploader("Upload Student Spreadsheet", type=["xlsx", "csv"])
    
    if uploaded_excel:
        try:
            # Read the uploaded file safely
            if uploaded_excel.name.endswith("xlsx"):
                df = pd.read_excel(uploaded_excel)
            else:
                df = pd.read_csv(uploaded_excel)
                
            # --- HEADER NORMALIZER ---
            # This strips extra spaces, converts headers to uppercase, and removes underscores 
            # so that 'ADM NO', 'adm no', and 'ADM_NO' all match up perfectly.
            df.columns = df.columns.str.strip().str.upper().str.replace('_', ' ')
            
            st.write("### Previewing Upload Data:")
            st.dataframe(df, use_container_width=True)
            
            # Verify required columns exist after normalization
            required_cols = ['ADM NO', 'NAME', 'ASSESSMENT NO', 'GRADE']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"❌ Missing required columns in spreadsheet: {', '.join(missing_cols)}")
                st.info(f"Your sheet headers are currently read as: {list(df.columns)}")
            else:
                if st.button("Process Bulk Admission", type="primary"):
                    conn = sqlite3.connect("school_data.db")
                    cursor = conn.cursor()
                    success_count = 0
                    error_logs = []
                    
                    for index, row in df.iterrows():
                        try:
                            # Extract using the safely normalized header mapping names
                            adm = str(row['ADM NO']).strip()
                            student_name = str(row['NAME']).strip().upper()
                            assess = str(row['ASSESSMENT NO']).strip().upper()
                            
                            # Standardize grade string formatting safely
                            raw_grade = str(row['GRADE']).strip()
                            student_grade = raw_grade if "Grade" in raw_grade else f"Grade {raw_grade}"
                            
                            if adm and student_name:
                                cursor.execute("""
                                    INSERT OR REPLACE INTO students (adm_no, name, assessment_no, grade) 
                                    VALUES (?, ?, ?, ?)
                                """, (adm, student_name, assess, student_grade))
                                success_count += 1
                        except Exception as row_error:
                            error_logs.append(f"Row {index + 2} (ADM: {row.get('ADM NO')}): {str(row_error)}")
                            continue
                            
                    conn.commit()
                    conn.close()
                    
                    if success_count > 0:
                        st.success(f"🚀 Successfully loaded {success_count} student records into database system profiles.")
                    else:
                        st.warning("⚠️ 0 records were processed. Check below for detailed line errors.")
                        
                    if error_logs:
                        with st.expander("❌ View Skipped Rows Error Log Details"):
                            for log in error_logs:
                                st.error(log)
                                
        except Exception as e:
            st.error(f"Could not parse spreadsheet structure layout: {e}")
