import streamlit as st
import sqlite3
import pandas as pd

# 🔒 GATEKEEPER MODULE: Restricted to System Administrators Only
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()
if st.session_state["role"] != "Admin":
    st.error(f"❌ Access Denied. Financial Ledgers are restricted to System Administration personnel.")
    st.stop()

st.title("💰 Institutional Fee & Treasury Operations Panel")
t1, t2, t3, t4 = st.tabs(["📋 Institutional Fee Structures", "📥 Process New Remittance Payment", "🧾 Receipt Ledger History", "📊 Termly Deficit Status Trackers"])

with t1:
    structure_data = {
        "Category Profile": ["Continuing JSS Student", "Newly Admitted JSS Entry"],
        "Gross Total Per Term Payment": ["Ksh 550.00", "Ksh 750.00"]
    }
    st.table(pd.DataFrame(structure_data))

with t2:
    conn = sqlite3.connect("school_data.db")
    df_students = pd.read_sql_query("SELECT adm_no, name, grade FROM students", conn)
    conn.close()
    
    if not df_students.empty:
        student_mapping = {f"{row['name']} ({row['adm_no']})": row['adm_no'] for _, row in df_students.iterrows()}
        selected_search = st.selectbox("Search Student Record", list(student_mapping.keys()))
        target_adm = student_mapping[selected_search]
        
        with st.form("payment_form"):
            amt = st.number_input("Amount Remitted (Ksh)", min_value=1.0)
            channel = st.selectbox("Payment Channel", ["Cash Payment Desk", "Direct Bank Wire Account", "M-Pesa Corporate Paybill"])
            payer = st.text_input("Depositor Reference")
            allocation = st.selectbox("Allocation Type", ["Full Termly Bill-out", "Tuition Fee Balance", "Assessment Exam Matrix Fee"])
            
            if st.form_submit_button("Post Transaction Record"):
                conn = sqlite3.connect("school_data.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO fee_payments (adm_no, amount, channel, payer, payment_for) VALUES (?, ?, ?, ?, ?)", (target_adm, amt, channel, payer, allocation))
                conn.commit()
                conn.close()
                st.success("Remittance record successfully pushed.")

with t4:
    conn = sqlite3.connect("school_data.db")
    df_st = pd.read_sql_query("SELECT adm_no, name, grade FROM students", conn)
    df_p = pd.read_sql_query("SELECT adm_no, SUM(amount) as paid FROM fee_payments GROUP BY adm_no", conn)
    conn.close()
    
    df_merged = pd.merge(df_st, df_p, on="adm_no", how="left").fillna(0)
    df_merged['Status'] = df_merged['paid'].apply(lambda x: "🟢 NILL BALANCE" if x == 550 else ("🔴 PENDING" if x < 550 else "🔵 OVERPAYMENT"))
    st.dataframe(df_merged, use_container_width=True)
