import streamlit as st
import sqlite3
import pandas as pd

# 🔒 GATEKEEPER MODULE: Open to ALL authenticated logged-in system staff roles
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()

st.title("📰 KEA Official Institutional Circulars & Newsletter")

# Static restriction check: Only show the creation tools to Admins
if st.session_state["role"] == "Admin":
    st.markdown("### 🛠️ Dispatch Hub (Admin Clearance Node)")
    with st.form("news_form"):
        title = st.text_input("Circular Notice Title")
        content = st.text_area("Narrative Body Text")
        if st.form_submit_button("Publish Article"):
            if title and content:
                conn = sqlite3.connect("school_data.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO newsletter (title, content) VALUES (?, ?)", (title, content))
                conn.commit()
                conn.close()
                st.success("Circular dispatched live.")
                st.rerun()

st.markdown("---")
conn = sqlite3.connect("school_data.db")
df_news = pd.read_sql_query("SELECT title, content, date_posted FROM newsletter ORDER BY date_posted DESC", conn)
conn.close()

for idx, row in df_news.iterrows():
    st.markdown(f"#### {row['title']}")
    st.caption(f"🗓️ {row['date_posted']}")
    st.write(row['content'])
    st.markdown("---")
