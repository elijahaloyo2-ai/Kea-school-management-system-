import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import os

# 🔒 Check Session Authorization
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()

st.title("📊 CBC Analytical Performance Command Deck")

# --- GLOBAL SESSION SETTINGS FOR TERM DATES ---
st.sidebar.markdown("### ⚙️ Institutional Settings")
with st.sidebar.expander("📅 Edit Term Dates", expanded=False):
    closing_date = st.text_input("Term Closing Date", value="22/08/2026")
    opening_date = st.text_input("Next Term Opening Date", value="29/09/2026")

# Target Grade Selection
selected_grade = st.selectbox("Choose Evaluation Target Grade", ["Grade 7", "Grade 8", "Grade 9"])

# 🔄 Database Data Fetcher
def fetch_academic_performance(grade):
    conn = sqlite3.connect("school_data.db")
    query = """
        SELECT s.adm_no, s.name, s.assessment_no, s.grade,
               m.mathematics, m.english, m.kiswahili, m.integrated_science,
               m.agriculture, m.pretechnical_studies, m.social_studies,
               m.religious_education, m.cas
        FROM students s
        LEFT JOIN marks m ON s.adm_no = m.adm_no AND s.grade = m.grade
        WHERE s.grade = ?
    """
    df = pd.read_sql_query(query, conn, params=(grade,))
    conn.close()
    return df

students_df = fetch_academic_performance(selected_grade)

if students_df.empty:
    st.warning(f"No student records or marks found registered under {selected_grade}.")
    st.stop()

# List of tracking subjects mapping codes to columns
SUBJECT_MAP = {
    "ENGLISH": "english",
    "KISWAHILI": "kiswahili",
    "MATHEMATICS": "mathematics",
    "INTEGRATED SCIENCE": "integrated_science",
    "SOCIAL STUDIES": "social_studies",
    "RELIGIOUS EDUCATION (C.R.E)": "religious_education",
    "AGRICULTURE": "agriculture",
    "PRE-TECHNICAL STUDIES": "pretechnical_studies",
    "CREATIVE ARTS & SPORTS (C.A.S)": "cas"
}

# Pre-calculate totals for analytics processing
subj_cols = list(SUBJECT_MAP.values())
students_df[subj_cols] = students_df[subj_cols].fillna(0)
students_df["TOTAL MARKS"] = students_df[subj_cols].sum(axis=1)
students_df["MEAN SCORE"] = students_df[subj_cols].mean(axis=1)

# Create Navigation Tabs
tab_overview, tab_reports = st.tabs(["📊 Grade Performance Overview Analytics", "📜 Student Assessment Report Generator"])

# =========================================================
# TAB 1: GRADE PERFORMANCE OVERVIEW ANALYTICS
# =========================================================
with tab_overview:
    st.subheader(f"Performance Analysis Dashboard — {selected_grade}")
    
    # 1. Best Students Per Learning Area
    st.markdown("#### 🏆 Top Performers Per Learning Area")
    best_per_subject = []
    for subj_name, col in SUBJECT_MAP.items():
        if not students_df[col].empty and students_df[col].max() > 0:
            top_student_row = students_df.loc[students_df[col].idxmax()]
            best_per_subject.append({
                "Learning Area": subj_name,
                "Top Student": top_student_row["name"],
                "ADM NO": top_student_row["adm_no"],
                "Highest Score": f"{int(top_student_row[col])}%"
            })
    if best_per_subject:
        st.dataframe(pd.DataFrame(best_per_subject), use_container_width=True, hide_index=True)
    else:
        st.info("No assessment marks have been submitted yet to calculate top subject metrics.")

    col_rank1, col_rank2 = st.columns([1, 1])
    
    # 2. Top 10 Students Overall Ranking
    with col_rank1:
        st.markdown("#### 🏅 Top 10 Overall Students")
        top_10 = students_df.sort_values(by="TOTAL MARKS", ascending=False).head(10)[["adm_no", "name", "TOTAL MARKS", "MEAN SCORE"]]
        top_10.columns = ["ADM NO", "STUDENT NAME", "TOTAL MARKS", "MEAN %"]
        top_10["MEAN %"] = top_10["MEAN %"].map(lambda x: f"{x:.1f}%")
        st.dataframe(top_10, use_container_width=True, hide_index=True)

    # 3. Best Performed Learning Areas (Subject Rankings)
    with col_rank2:
        st.markdown("#### 📈 Subject Performance Ranking")
        subject_means = []
        for subj_name, col in SUBJECT_MAP.items():
            avg_score = students_df[col].mean() or 0
            subject_means.append({"Learning Area": subj_name, "Class Average": avg_score})
        
        subj_rank_df = pd.DataFrame(subject_means).sort_values(by="Class Average", ascending=False)
        subj_rank_df["Class Average"] = subj_rank_df["Class Average"].map(lambda x: f"{x:.1f}%")
        st.dataframe(subj_rank_df, use_container_width=True, hide_index=True)

# =========================================================
# TAB 2: STUDENT ASSESSMENT REPORT GENERATOR
# =========================================================
with tab_reports:
    
    # Helper to calculate CBC Levels based on actual raw percentages
    def compute_cbc_level(score):
        score = score or 0
        if score >= 80: return "EE (Exceeding Expectation)"
        if score >= 50: return "ME (Meeting Expectation)"
        if score >= 30: return "AE (Approaching Expectation)"
        return "BE (Below Expectation)"

    # Intelligent Auto-Comment Generator Engine
    def generate_teacher_comment(mean_score):
        if mean_score >= 80:
            return "An excellent performance! Demonstrates outstanding mastery of all learning areas."
        elif mean_score >= 65:
            return "A very good performance. Consistently meets expectations. Keep up the steady effort."
        elif mean_score >= 50:
            return "Good progress made. Possesses room for improvement with targeted revision in weak areas."
        elif mean_score >= 35:
            return "Approaching expectations. Requires close monitoring and more remedial support next term."
        else:
            return "Below expectations. Immediate academic intervention and intensive practice are highly advised."

    # --- DYNAMIC CBC REPORT CARD GENERATION ENGINE ---
    def generate_student_report_card(row, close_dt, open_dt):
        img = Image.new("RGB", (800, 1150), color="#FFFFFF")
        draw = ImageDraw.Draw(img)
        
        # Safe structural fallback typography system
        font = ImageFont.load_default()

        # 1. INSTITUTIONAL HEADER BLOCK
        draw.text((400, 40), "KEA COMPREHENSIVE SCHOOL", fill="#1E3A8A", anchor="mm")
        draw.text((400, 65), "P.O. BOX 557-40404, SUNA MIGORI", fill="#475569", anchor="mm")
        draw.text((400, 95), "STUDENT ASSESSMENT REPORT FORM", fill="#1E293B", anchor="mm")
        draw.line([(40, 120), (760, 120)], fill="#CBD5E1", width=2)
        
        # 2. BIO DATA SECTION
        draw.text((50, 140), "STUDENT NAME:", fill="#64748B")
        draw.text((180, 140), str(row['name']).upper(), fill="#0F172A")
        draw.text((50, 175), "ADM NO:", fill="#64748B")
        draw.text((180, 175), str(row['adm_no']), fill="#0F172A")
        draw.text((50, 210), "ASSESSMENT NO:", fill="#64748B")
        draw.text((180, 210), str(row['assessment_no']) if row['assessment_no'] else "N/A", fill="#0F172A")

        draw.text((480, 140), "CLASS / GRADE:", fill="#64748B")
        draw.text((620, 140), str(row['grade']), fill="#0F172A")
        draw.text((480, 175), "TERM:", fill="#64748B")
        draw.text((620, 175), "TERM 2", fill="#0F172A")
        draw.text((480, 210), "YEAR:", fill="#64748B")
        draw.text((620, 210), "2026", fill="#0F172A")

        # 3. TABLE HEADERS
        table_top = 260
        draw.rectangle([(40, table_top), (760, table_top + 35)], fill="#1E3A8A")
        draw.text((60, table_top + 10), "S/N", fill="#FFFFFF")
        draw.text((120, table_top + 10), "LEARNING AREA / SUBJECT", fill="#FFFFFF")
        draw.text((480, table_top + 10), "SCORE (%)", fill="#FFFFFF")
        draw.text((620, table_top + 10), "PERFORMANCE LEVEL", fill="#FFFFFF")
        
        subjects_list = [
            ("901", "ENGLISH", row.get('english', 0)),
            ("902", "KISWAHILI", row.get('kiswahili', 0)),
            ("903", "MATHEMATICS", row.get('mathematics', 0)),
            ("905", "INTEGRATED SCIENCE", row.get('integrated_science', 0)),
            ("907", "SOCIAL STUDIES", row.get('social_studies', 0)),
            ("908", "RELIGIOUS EDUCATION (C.R.E)", row.get('religious_education', 0)),
            ("911", "AGRICULTURE", row.get('agriculture', 0)),
            ("912", "PRE-TECHNICAL STUDIES", row.get('pretechnical_studies', 0)),
            ("915", "CREATIVE ARTS & SPORTS (C.A.S)", row.get('cas', 0))
        ]
        
        current_y = table_top + 35
        total_score = 0
        valid_subjects_count = 0
        
        for idx, (code, subject_name, mark) in enumerate(subjects_list, start=1):
            mark_val = mark if mark is not None else 0
            total_score += mark_val
            valid_subjects_count += 1
            
            if idx % 2 == 0:
                draw.rectangle([(40, current_y), (760, current_y + 35)], fill="#F8FAFC")
                
            draw.text((60, current_y + 10), str(idx), fill="#334155")
            draw.text((120, current_y + 10), f"({code}) {subject_name}", fill="#0F172A")
            draw.text((500, current_y + 10), f"{int(mark_val)}%", fill="#0F172A")
            draw.text((620, current_y + 10), compute_cbc_level(mark_val), fill="#1E3A8A")
            
            draw.line([(40, current_y + 35), (760, current_y + 35)], fill="#E2E8F0", width=1)
            current_y += 35

        # 4. TOTALS BAR
        current_y += 15
        draw.rectangle([(40, current_y), (760, current_y + 40)], fill="#F1F5F9")
        draw.text((60, current_y + 12), f"TOTAL MARKS SCORED: {int(total_score)}", fill="#1E3A8A")
        
        mean_score = total_score / valid_subjects_count if valid_subjects_count > 0 else 0
        draw.text((420, current_y + 12), f"OVERALL ASSESSMENT: {compute_cbc_level(mean_score)}", fill="#1E3A8A")
        current_y += 40

        # 5. DYNAMIC TEACHER COMMENTS SECTION
        current_y += 25
        draw.text((50, current_y), "CLASS TEACHER GENERAL COMMENT:", fill="#1E3A8A")
        current_y += 25
        comment_text = generate_teacher_comment(mean_score)
        draw.text((50, current_y), f'"{comment_text}"', fill="#0F172A")
        
        # 6. DYNAMIC TERM CALENDAR DATES
        current_y += 45
        draw.text((50, current_y), f"TERM CLOSING DATE:  {close_dt}", fill="#475569")
        draw.text((450, current_y), f"NEXT TERM OPENING DATE:  {open_dt}", fill="#475569")
        
        # 7. SIGNATURES & STAMP INJECTION OVERLAY
        current_y += 75
        draw.text((50, current_y), "CLASS TEACHER SIGNATURE: _______________________", fill="#475569")
        
        current_y += 40
        hoi_line_y = current_y
        draw.text((50, hoi_line_y + 25), "HOI STAMP & SIGNATURE:     _______________________", fill="#475569")
        
        # Stamp Overlay Injection Engine logic
        # Looks for files matching 'stamp' extension formats safely
        stamp_path = None
        for file_ext in ["stamp.png", "stamp.jpg", "stamp.jpeg", "stamp.photo"]:
            if os.path.exists(file_ext):
                stamp_path = file_ext
                break
                
        if stamp_path:
            try:
                stamp_img = Image.open(stamp_path).convert("RGBA")
                # Resize stamp proportionally to fit neatly over the line
                stamp_img.thumbnail((120, 120))
                # Paste stamp right above the HOI line safely
                img.paste(stamp_img, (270, hoi_line_y - 30), stamp_img)
            except Exception:
                pass # Skip overlay smoothly if image asset file format is unreadable
        
        byte_arr = io.BytesIO()
        img.save(byte_arr, format="PNG")
        return byte_arr.getvalue()

    # =========================================================
    # UI CONSOLE DISPLAY INTERFACE
    # =========================================================
    st.subheader("Report Form Issuance Console")
    display_mode = st.radio("Display View Management Profiles", ["Single Student Evaluation Card", "Complete Classroom Batch Processing Grid"])

    if display_mode == "Single Student Evaluation Card":
        student_names = students_df["name"].tolist()
        selected_student_name = st.selectbox("Select Student Profile", student_names)
        
        student_row = students_df[students_df["name"] == selected_student_name].iloc[0]
        
        with st.spinner("Generating crisp dynamic report form layout..."):
            report_bytes = generate_student_report_card(student_row, closing_date, opening_date)
            
        st.image(report_bytes, caption=f"Preview Evaluation Form: {selected_student_name}", use_container_width=True)
        st.download_button(
            label=f"📥 Download Official Report: {selected_student_name}",
            data=report_bytes,
            file_name=f"Report_{student_row['adm_no']}.png",
            mime="image/png"
        )

    elif display_mode == "Complete Classroom Batch Processing Grid":
        st.success(f"Verified {len(students_df)} classroom profiles ready for automatic batch rendering.")
        
        if st.button("🚀 Process & Generate All Classroom Reports", type="primary"):
            for idx, row in students_df.iterrows():
                with st.spinner(f"Rendering: {row['name']}..."):
                    r_bytes = generate_student_report_card(row, closing_date, opening_date)
                    
                st.write(f"✅ **{row['name']}** (ADM NO: {row['adm_no']})")
                st.download_button(
                    label=f"Download Report Card: {row['name']}",
                    data=r_bytes,
                    file_name=f"Report_{row['adm_no']}.png",
                    key=f"dl_batch_{row['adm_no']}",
                    mime="image/png"
    )
