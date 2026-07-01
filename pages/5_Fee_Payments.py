import streamlit as st
import sqlite3
import pandas as pd

# 🔒 Check Session Authorization
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()

st.title("💰 Institutional Fee & Treasury Operations Panel")

# Ensure the database tables exist correctly
def verify_fee_tables():
    conn = sqlite3.connect("school_data.db")
    cursor = conn.cursor()
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

verify_fee_tables()

# Fetch active students list for the dropdown registry
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

# Create Navigation Tabs matching your screenshots
tab_process, tab_ledger, tab_summary = st.tabs([
    "📥 Process New Remittance Payment", 
    "🧾 Receipt Ledger History", 
    "📊 Termly Balance Sheets"
])

# =========================================================
# TAB 1: PROCESS NEW REMITTANCE PAYMENT
# =========================================================
with tab_process:
    if students_df.empty:
        st.warning("No students currently registered in the database system registry.")
    else:
        # Create a clean presentation option label
        students_df["dropdown_label"] = students_df["name"] + " (" + students_df["grade"].astype(str) + ")"
        student_options = students_df["dropdown_label"].tolist()
        
        selected_option = st.selectbox("Search Student Record", student_options)
        target_index = student_options.index(selected_option)
        selected_student = students_df.iloc[target_index]
        
        with st.form("payment_form", clear_on_submit=True):
            amount_remitted = st.number_input("Amount Remitted (Ksh)", min_value=0.0, value=550.0, step=50.0)
            payment_channel = st.selectbox("Payment Channel", ["Cash Payment Desk", "M-PESA Paybill", "Bank Deposit Agent"])
            depositor_ref = st.text_input("Depositor Reference (Optional)")
            allocation_type = st.selectbox("Allocation Type", ["Full Termly Bill-out", "Partial Installation", "Arrears Clearance"])
            
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
# TAB 2: RECEIPT LEDGER HISTORY (Fixes your blank screen)
# =========================================================
with tab_ledger:
    st.subheader("📜 Comprehensive Financial Ledger Logs")
    
    conn = sqlite3.connect("school_data.db")
    # Fetch all records sorted by most recent first
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
            # Format the amount values nicely for visual scanning
            ledger_df['Amount (Ksh)'] = ledger_df['Amount (Ksh)'].map(lambda x: f"Ksh {x:,.2f}")
            st.dataframe(ledger_df, use_container_width=True, hide_index=True)
        else:
            st.info("No transaction postings or payment ledgers found in the historical log balances.")
    except Exception as e:
        st.error(f"Failed to load ledger: {e}")
    finally:
        conn.close()

# =========================================================
# TAB 3: TERMLY BALANCE SHEETS
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
            
            # Merge with student registry
            summary_df = students_df.copy()
            summary_df = summary_df.merge(pay_df, on="adm_no", how="left")
            summary_df["total_paid"] = summary_df["total_paid"].fillna(0.0)
            
            # Termly billing rate constant matching main dashboard baseline
            term_rate = 550.0 
            summary_df["Expected Fee (Ksh)"] = term_rate
            summary_df["Paid (Ksh)"] = summary_df["total_paid"]
            summary_df["Balance Due (Ksh)"] = summary_df["Expected Fee (Ksh)"] - summary_df["Paid (Ksh)"]
            
            # Clean view output
            view_df = summary_df[["adm_no", "name", "grade", "Expected Fee (Ksh)", "Paid (Ksh)", "Balance Due (Ksh)"]]
            view_df.columns = ["ADM NO", "STUDENT NAME", "GRADE", "EXPECTED (Ksh)", "PAID (Ksh)", "BALANCE DUE (Ksh)"]
            
            st.dataframe(view_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error compiling financial overview cards: {e}")
        finally:
            conn.close()
