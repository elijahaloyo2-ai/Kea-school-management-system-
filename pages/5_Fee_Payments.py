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

# --- TABS NAVIGATION DESIGN (Now with individual statements) ---
tab_process, tab_ledger, tab_summary, tab_structure, tab_individual = st.tabs([
    "📥 Process New Remittance Payment", 
    "🧾 Receipt Ledger History", 
    "📊 Termly Balance Sheets",
    "📋 Institutional Fee Structure",
    "📄 Individual Student Fee Statements"
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
        
        selected_option = st.selectbox("Search Student Record", student_options, key="process_select")
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
            display_df = ledger_df.copy()
            display_df['Amount (Ksh)'] = display_df['Amount (Kshexport_df)'].map(lambda x: f"Ksh {x:,.2f}") if 'Amount (Kshexport_df)' in display_df else display_df['Amount (Ksh)'].map(lambda x: f"Ksh {x:,.2f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No transaction postings found in the historical logs.")
    except Exception as e:
        st.error(f"Failed to load ledger: {e}")
    finally:
        conn.close()

# =========================================================
# TAB 3: TERMLY BALANCE SHEETS (Download All)
# =========================================================
with tab_summary:
    st.subheader("📊 Institutional Fee Performance Metrics")
    if students_df.empty:
        st.info("Register student profiles to initialize fee statement balances.")
    else:
        conn = sqlite3.connect("school_data.db")
        try:
            pay_query = "SELECT adm_no, SUM(amount) as total_paid FROM fee_payments GROUP BY adm_no"
            pay_df = pd.read_sql_query(pay_query, conn)
            
            admission_paid_query = "SELECT DISTINCT adm_no FROM fee_payments WHERE allocation = 'Admission Fee Clearance'"
            adm_paid_df = pd.read_sql_query(admission_paid_query, conn)
            new_admissions_list = adm_paid_df["adm_no"].tolist()
            
            summary_df = students_df.copy()
            summary_df = summary_df.merge(pay_df, on="adm_no", how="left")
            summary_df["total_paid"] = summary_df["total_paid"].fillna(0.0)
            
            expected_fees = []
            for idx, row in summary_df.iterrows():
                base_rate = 550.0
                if str(row["adm_no"]) in new_admissions_list:
                    base_rate += 200.0
                expected_fees.append(base_rate)
                
            summary_df["Expected Fee (Ksh)"] = expected_fees
            summary_df["Paid (Ksh)"] = summary_df["total_paid"]
            summary_df["Balance Due (Ksh)"] = summary_df["Expected Fee (Ksh)"] - summary_df["Paid (Ksh)"]
            
            view_df = summary_df[["adm_no", "name", "grade", "Expected Fee (Ksh)", "Paid (Ksh)", "Balance Due (Ksh)"]]
            view_df.columns = ["ADM NO", "STUDENT NAME", "GRADE", "EXPECTED (Ksh)", "PAID (Ksh)", "BALANCE DUE (Ksh)"]
            
            st.dataframe(view_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("#### 📥 Export Operational Financial Logs")
            csv_data = view_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="🖨️ Download / Print Complete Classroom Balance Sheets",
                data=csv_data,
                file_name="KEA_School_Termly_Balance_Sheets.csv",
                mime="text/csv",
                type="primary"
            )
        except Exception as e:
            st.error(f"Error compiling financial cards: {e}")
        finally:
            conn.close()

# =========================================================
# TAB 4: INSTITUTIONAL FEE STRUCTURE
# =========================================================
with tab_structure:
    st.subheader("📋 Approved Termly Base Fee Requirements")
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
    st.info("ℹ️ **New Student Admission Policy:** Newly admitted students incur a one-time admission fee of **Ksh 200.00**, bringing their initial term total baseline to **Ksh 750.00**.")

# =========================================================
# TAB 5: INDIVIDUAL STUDENT FEE STATEMENTS (Take Home Feature)
# =========================================================
with tab_individual:
    st.subheader("📄 Student Report Statement Generator")
    st.write("Generate a printable fee statement invoice to send home with an individual student.")
    
    if students_df.empty:
        st.warning("No registered student data found.")
    else:
        students_df["dropdown_label"] = students_df["name"] + " (" + students_df["grade"].astype(str) + ")"
        indiv_options = students_df["dropdown_label"].tolist()
        
        selected_indiv = st.selectbox("Choose Target Student Profile", indiv_options, key="individual_select")
        indiv_index = indiv_options.index(selected_indiv)
        student_row = students_df.iloc[indiv_index]
        
        # Pull transactional history from database for this specific student
        conn = sqlite3.connect("school_data.db")
        stmt_query = """
            SELECT date_timestamp AS 'Date Posted', channel AS 'Channel', 
                   reference AS 'Reference ID', allocation AS 'Allocation Type', amount AS 'Paid (Ksh)'
            FROM fee_payments
            WHERE adm_no = ?
            ORDER BY id ASC
        """
        student_history_df = pd.read_sql_query(stmt_query, conn, params=(str(student_row["adm_no"]),))
        
        # Calculate dynamic totals for statement sheet
        admission_check_query = "SELECT 1 FROM fee_payments WHERE adm_no = ? AND allocation = 'Admission Fee Clearance' LIMIT 1"
        has_admission_fee = conn.execute(admission_check_query, (str(student_row["adm_no"]),)).fetchone()
        conn.close()
        
        expected_total = 750.0 if has_admission_fee else 550.0
        total_paid = student_history_df['Paid (Ksh)'].sum() if not student_history_df.empty else 0.0
        current_balance = expected_total - total_paid
        
        # Visual Summary Block
        st.markdown(f"### **KEA COMPREHENSIVE SCHOOL FEE STATEMENT**")
        col_bio1, col_bio2 = st.columns(2)
        with col_bio1:
            st.markdown(f"**Student Name:** {student_row['name'].upper()}")
            st.markdown(f"**Admission Number:** {student_row['adm_no']}")
        with col_bio2:
            st.markdown(f"**Class/Grade:** {student_row['grade']}")
            st.markdown(f"**Term/Academic Year:** Term 2 / 2026")
            
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Invoiced", f"Ksh {expected_total:,.2f}")
        col_m2.metric("Total Paid", f"Ksh {total_paid:,.2f}")
        col_m3.metric("Outstanding Balance", f"Ksh {current_balance:,.2f}")
        
        st.markdown("#### 🧾 Payment History Records")
        if student_history_df.empty:
            st.info("No posted payment records found for this student profile.")
            # Create a blank row representation to keep the table structure clean
            display_hist = pd.DataFrame(columns=['Date Posted', 'Channel', 'Reference ID', 'Allocation Type', 'Paid (Ksh)'])
        else:
            display_hist = student_history_df.copy()
            display_hist['Paid (Ksh)'] = display_hist['Paid (Ksh)'].map(lambda x: f"Ksh {x:,.2f}")
            st.dataframe(display_hist, use_container_width=True, hide_index=True)
            
        # --- BUILD CLEAN TAKE-HOME PRINT STRING TEXT FILE ---
        statement_text = f"""==================================================
              KEA COMPREHENSIVE SCHOOL
         P.O. BOX 557-40404, SUNA MIGORI, KENYA
               OFFICIAL STUDENT FEE STATEMENT
==================================================
DATE GENERATED: 2026
STUDENT NAME  : {student_row['name'].upper()}
ADMISSION NO  : {student_row['adm_no']}
CLASS / GRADE : {student_row['grade']}
TERM/YEAR     : TERM 2 / 2026
--------------------------------------------------
SUMMARY SUMMARY BALANCE SHEET:
  TOTAL EXPECTED FEES: Ksh {expected_total:,.2f}
  TOTAL AMOUNT PAID  : Ksh {total_paid:,.2f}
  OUTSTANDING BALANCE: Ksh {current_balance:,.2f}
--------------------------------------------------
TRANSACTION PAYMENT LEDGER HISTORY:\n"""

        if student_history_df.empty:
            statement_text += "  No payment entries posted to date.\n"
        else:
            for idx, r in student_history_df.iterrows():
                statement_text += f"  - {r['Date Posted']} | {r['Channel']} | Ref: {r['Reference ID'] or 'N/A'} | {r['Allocation Type']} | Paid: Ksh {r['Paid (Ksh)']:,.2f}\n"

        statement_text += f"""--------------------------------------------------
Current status: {"ACCOUNT CLEARED - THANK YOU" if current_balance <= 0 else "PLEASE REMIT OUTSTANDING BALANCE AS SOON AS POSSIBLE"}

Prepared by: School Treasury Accounts Desk
Authorized Stamp: KEA COMPREHENSIVE SCHOOL OFFICE
=================================================="""

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label=f"📥 Download Official Fee Statement: {student_row['name']}",
            data=statement_text.encode('utf-8'),
            file_name=f"Fee_Statement_{student_row['adm_no']}.txt",
            mime="text/plain",
            type="primary"
        )
