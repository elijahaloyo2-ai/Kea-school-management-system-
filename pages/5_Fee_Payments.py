import streamlit as st
import sqlite3
import pandas as pd

# 🔒 Check Session Authorization
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()

st.title("💰 Institutional Fee & Treasury Operations Panel")

# --- DATABASE SETUP & AUTO-REPAIR ---
def initialize_and_sync_tables():
    conn = sqlite3.connect("school_data.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM fee_payments LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS fee_payments")
        
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adm_no TEXT,
            name TEXT,
            grade TEXT,
            amount REAL,
            channel TEXT,
            reference TEXT,
            allocation TEXT,
            date_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

initialize_and_sync_tables()

# --- HELPER FUNCTIONS ---
def fetch_student_registry():
    conn = sqlite3.connect("school_data.db")
    query = "SELECT adm_no, name, grade FROM students ORDER BY name ASC"
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        df = pd.DataFrame(columns=["adm_no", "name", "grade"])
    conn.close()
    return df

students_df = fetch_student_registry()

# --- TABS NAVIGATION DESIGN ---
tab_process, tab_ledger, tab_summary, tab_structure = st.tabs([
    "📥 Process New Remittance Payment", 
    "🧾 Receipt Ledger History", 
    "📊 Termly Balance Sheets",
    "📋 Institutional Fee Structure"
])

# =========================================================
# TAB 1: PROCESS NEW REMITTANCE PAYMENT
# =========================================================
with tab_process:
    if students_df.empty:
        st.warning("No students currently registered in the database system registry.")
    else:
        students_df["dropdown_label"] = students_df["name"] + " (" + students_df["grade"].astype(str) + ")"
        student_options = students_df["dropdown_label"].tolist()
        
        selected_option = st.selectbox("Search Student Record", student_options)
        target_index = student_options.index(selected_option)
        selected_student = students_df.iloc[target_index]
        
        with st.form("payment_form", clear_on_submit=True):
            amount_remitted = st.number_input("Amount Remitted (Ksh)", min_value=0.0, value=550.0, step=50.0)
            payment_channel = st.selectbox("Payment Channel", ["Cash Payment Desk", "M-PESA Paybill", "Bank Deposit Agent"])
            depositor_ref = st.text_input("Depositor Reference (Optional)")
            allocation_type = st.selectbox("Allocation Type", ["Full Termly Bill-out", "Partial Installation", "Admission Fee Clearance", "Arrears Clearance"])
            
            if st.form_submit_button("Post Transaction Record"):
                conn = sqlite3.connect("school_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO fee_payments (adm_no, name, grade, amount, channel, reference, allocation)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(selected_student["adm_no"]), 
                        selected_student["name"], 
                        str(selected_student["grade"]), 
                        amount_remitted, 
                        payment_channel, 
                        depositor_ref, 
                        allocation_type
                    ))
                    conn.commit()
                    st.success(f"Remittance record successfully pushed for {selected_student['name']}!")
                except Exception as e:
                    st.error(f"Error posting transaction: {e}")
                finally:
                    conn.close()

# =========================================================
# TAB 2: RECEIPT LEDGER HISTORY
# =========================================================
with tab_ledger:
    st.subheader("📜 Comprehensive Financial Ledger Logs")
    
    conn = sqlite3.connect("school_data.db")
    query = """
        SELECT id AS 'Receipt No', adm_no AS 'ADM NO', name AS 'Student Name', 
               grade AS 'Grade', amount AS 'Amount (Ksh)', channel AS 'Channel', 
               reference AS 'Reference', allocation AS 'Allocation', date_timestamp AS 'Date/Time'
        FROM fee_payments 
        ORDER BY id DESC
    """
    
    try:
        ledger_df = pd.read_sql_query(query, conn)
        if not ledger_df.empty:
            # Keep a formatted version for UI and clean copy for printing if needed
            display_df = ledger_df.copy()
            display_df['Amount (Ksh)'] = display_df['Amount (Ksh)'].map(lambda x: f"Ksh {x:,.2f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No transaction postings found in the historical logs.")
    except Exception as e:
        st.error(f"Failed to load ledger: {e}")
    finally:
        conn.close()

# =========================================================
# TAB 3: TERMLY BALANCE SHEETS (With Print/Download Feature)
# =========================================================
with tab_summary:
    st.subheader("📊 Institutional Fee Performance Metrics")
    if students_df.empty:
        st.info("Register student profiles to initialize fee statement balances.")
    else:
        conn = sqlite3.connect("school_data.db")
        try:
            # Aggregate total payments per student profile
            pay_query = "SELECT adm_no, SUM(amount) as total_paid FROM fee_payments GROUP BY adm_no"
            pay_df = pd.read_sql_query(pay_query, conn)
            
            # Check for students who cleared an Admission Fee to dynamically alter their expected base rate
            admission_paid_query = "SELECT DISTINCT adm_no FROM fee_payments WHERE allocation = 'Admission Fee Clearance'"
            adm_paid_df = pd.read_sql_query(admission_paid_query, conn)
            new_admissions_list = adm_paid_df["adm_no"].tolist()
            
            summary_df = students_df.copy()
            summary_df = summary_df.merge(pay_df, on="adm_no", how="left")
            summary_df["total_paid"] = summary_df["total_paid"].fillna(0.0)
            
            # Dynamic computation based on your layout structure rules
            expected_fees = []
            for idx, row in summary_df.iterrows():
                # Base fee: 150 (Tuition) + 200 (Mid-term) + 200 (End-term) = 550
                base_rate = 550.0
                # If they are noted with an admission payment entry, add the extra 200 Ksh
                if str(row["adm_no"]) in new_admissions_list:
                    base_rate += 200.0
                expected_fees.append(base_rate)
                
            summary_df["Expected Fee (Ksh)"] = expected_fees
            summary_df["Paid (Ksh)"] = summary_df["total_paid"]
            summary_df["Balance Due (Ksh)"] = summary_df["Expected Fee (Ksh)"] - summary_df["Paid (Ksh)"]
            
            view_df = summary_df[["adm_no", "name", "grade", "Expected Fee (Ksh)", "Paid (Ksh)", "Balance Due (Ksh)"]]
            view_df.columns = ["ADM NO", "STUDENT NAME", "GRADE", "EXPECTED (Ksh)", "PAID (Ksh)", "BALANCE DUE (Ksh)"]
            
            # Filter layout to active paid participants or pending accounts 
            st.dataframe(view_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("#### 📥 Export Operational Financial Logs")
            
            # Convert DataFrame records to standardized CSV dataset block for local local download/printing spreadsheet tools
            csv_data = view_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="🖨️ Download / Print Complete Classroom Balance Sheets",
                data=csv_data,
                file_name="KEA_School_Termly_Balance_Sheets.csv",
                mime="text/csv",
                type="primary"
            )
            
        except Exception as e:
            st.error(f"Error compiling financial overview cards: {e}")
        finally:
            conn.close()

# =========================================================
# TAB 4: INSTITUTIONAL FEE STRUCTURE (Updated Breakdown)
# =========================================================
with tab_structure:
    st.subheader("📋 Approved Termly Base Fee Requirements")
    st.write("Below is your official breakdown of the termly fee assignment configuration per student profile:")
    
    structure_data = {
        "Fee Component Item Area": [
            "Tuition Fees (Ksh 50 per month × 3 months)", 
            "Mid-Term Examination Papers Assessment", 
            "End-Term Examination Papers Evaluation"
        ],
        "Amount (Ksh)": [150.00, 200.00, 200.00]
    }
    
    struct_df = pd.DataFrame(structure_data)
    st.table(struct_df)
    
    st.metric(label="Regular Student Base Total Term Rate", value="Ksh 550.00")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("ℹ️ **New Student Admission Policy:** Newly admitted students incur a one-time admission processing fee surcharge of **Ksh 200.00**, bringing their initial term total baseline requirement to **Ksh 750.00**.")
