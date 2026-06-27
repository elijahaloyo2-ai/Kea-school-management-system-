import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io

# 🔒 GATEKEEPER MODULE: Restricted to Admins and Class Teachers Only
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()
if st.session_state["role"] not in ["Admin", "Class Teacher"]:
    st.error("❌ Access Denied. Results Analysis metrics are restricted to Admins or Grade Class Teachers.")
    st.stop()

st.title("📊 CBC Analytical Performance Command Deck")

GRADES = [f"Grade {i}" for i in range(1, 10)]
selected_grade = st.selectbox("Choose Evaluation Target Grade", GRADES)

def evaluate_subject_cbc(score):
    if score <= 10: return "BE2", 1
    elif score <= 20: return "BE1", 2
    elif score <= 30: return "AE2", 3
    elif score <= 40: return "AE1", 4
    elif score <= 56: return "ME2", 5
    elif score <= 73: return "ME1", 6
    elif score <= 88: return "EE2", 7
    else: return "EE1", 8

def evaluate_total_performance(total_score):
    if total_score <= 112: return "BE2 (Below Expectation 2)"
    elif total_score <= 224: return "BE1 (Below Expectation 1)"
    elif total_score <= 336: return "AE2 (Approaching Expectation 2)"
    elif total_score <= 449: return "AE1 (Approaching Expectation 1)"
    elif total_score <= 560: return "ME2 (Meeting Expectation 2)"
    elif total_score <= 672: return "ME1 (Meeting Expectation 1)"
    elif total_score <= 785: return "EE2 (Exceeding Expectation 2)"
    else: return "EE1 (Exceeding Expectation 1)"

def get_creative_comment(total_score):
    if total_score >= 673: return "Outstanding academic capability! Demonstrates exceptional talent across all core execution learning areas. Keep up the high standard."
    elif total_score >= 450: return "A very solid performance achieved. Consistently meets standards. With steady focus on technical items, higher records are certain."
    else: return "Requires supportive guidance. Consistent revision and targeted teacher interventions will help achieve standard proficiency."

conn = sqlite3.connect("school_data.db")
query = "SELECT m.*, s.name, s.assessment_no FROM marks m JOIN students s ON m.adm_no = s.adm_no WHERE m.grade = ?"
df_marks = pd.read_sql_query(query, conn, params=(selected_grade,))

cursor = conn.cursor()
cursor.execute("SELECT value FROM global_settings WHERE key = 'opening_date'")
op_date = cursor.fetchone()[0]
cursor.execute("SELECT value FROM global_settings WHERE key = 'closing_date'")
cl_date = cursor.fetchone()[0]
conn.close()

if df_marks.empty:
    st.warning(f"No records returned for {selected_grade}. Please input assessment grades first.")
    st.stop()

subjects_cols = ['mathematics', 'english', 'kiswahili', 'integrated_science', 'agriculture', 'pretechnical_studies', 'social_studies', 'religious_education', 'cas']
df_marks['Total Marks'] = df_marks[subjects_cols].sum(axis=1)
df_marks['Total Points'] = df_marks[subjects_cols].apply(lambda r: sum([evaluate_subject_cbc(x)[1] for x in r]), axis=1)
df_marks['Rank'] = df_marks['Total Marks'].rank(ascending=False, method='min').astype(int)
df_marks = df_marks.sort_values(by="Rank")

tab1, tab2 = st.tabs(["🏆 Grade Performance Overview Analytics", "📜 Student Assessment Report Generator"])

with tab1:
    st.subheader(f"Performance Metrics Dashboard for {selected_grade}")
    st.markdown("### 🥇 Top 10 Best Performing Candidates")
    st.dataframe(df_marks[['Rank', 'adm_no', 'name', 'Total Marks', 'Total Points']].head(10), use_container_width=True)
    
    st.markdown("### 📈 Subject Master Performers")
    best_sub_data = []
    for sub in subjects_cols:
        idx = df_marks[sub].idxmax()
        leader = df_marks.loc[idx]
        best_sub_data.append({"Learning Area": sub.replace('_', ' ').upper(), "Top Student": leader['name'], "Score Achieved": f"{leader[sub]}%"})
    st.table(pd.DataFrame(best_sub_data))

with tab2:
    st.subheader("Report Form Issuance Console")
    if st.session_state["role"] == "Admin":
        with st.expander("⚙️ Adjust Institutional Session Settings"):
            new_op = st.text_input("Opening Date Alignment", op_date)
            new_cl = st.text_input("Closing Date Alignment", cl_date)
            if st.button("Commit Calendar Timelines"):
                c = sqlite3.connect("school_data.db")
                cu = c.cursor()
                cu.execute("UPDATE global_settings SET value = ? WHERE key = 'opening_date'", (new_op,))
                cu.execute("UPDATE global_settings SET value = ? WHERE key = 'closing_date'", (new_cl,))
                c.commit()
                c.close()
                st.success("Session timelines configured successfully.")
                st.rerun()

    def generate_report_canvas(student_row):
        try: base_img = Image.open("report.png").convert("RGBA")
        except: base_img = Image.new("RGBA", (850, 1100), (255, 255, 255, 255))
        draw = ImageDraw.Draw(base_img)
        
        draw.text((250, 40), "KEA COMPREHENSIVE SCHOOL", fill=(30, 58, 138))
        draw.text((250, 60), "P.O BOX 557-40404 SUNA MIGORI", fill=(100, 116, 139))
        draw.text((60, 130), f"NAME: {student_row['name']}", fill=(0,0,0))
        draw.text((60, 150), f"ADM NO: {student_row['adm_no']}", fill=(0,0,0))
        
        y_pos = 240
        for sub in subjects_cols:
            score = student_row[sub]
            lvl, pts = evaluate_subject_cbc(score)
            draw.text((60, y_pos), f"{sub.replace('_',' ').upper()[:20]:<22} {score:<8} {lvl:<12} {pts}", fill=(0,0,0))
            y_pos += 22
            
        try:
            stamp_img = Image.open("stamp.png").resize((120, 120))
            base_img.alpha_composite(stamp_img, dest=(450, y_pos + 70))
        except: pass
        byte_arr = io.BytesIO()
        base_img.save(byte_arr, format="PNG")
        return byte_arr.getvalue()

    view_mode = st.radio("Display View Management Profiles", ["Single Student Evaluation Card", "Complete Classroom Batch Processing Grid"])
    if view_mode == "Single Student Evaluation Card":
        target_student = st.selectbox("Select Student Profile", df_marks['name'].unique())
        row_match = df_marks[df_marks['name'] == target_student].iloc[0]
        report_bytes = generate_report_canvas(row_match)
        st.image(report_bytes)
        st.download_button(f"📥 Download Report", data=report_bytes, fileName=f"Report_{row_match['adm_no']}.png")
    else:
        for idx, row in df_marks.iterrows():
            r_bytes = generate_report_canvas(row)
            st.download_button(f"Download Report: {row['name']}", data=r_bytes, filename=f"Report_{row['adm_no']}.png", key=f"dl_{row['adm_no']}")
