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

# Fill missing scores with 0 upfront
subj_cols = list(SUBJECT_MAP.values())
students_df[subj_cols] = students_df[subj_cols].fillna(0)

# Calculate Subject Performance Levels and Points
def compute_subject_cbc(score):
    score = score or 0
    if 89 <= score <= 100: return "EE1", 8
    if 74 <= score <= 88:  return "EE2", 7
    if 57 <= score <= 73:  return "ME1", 6
    if 41 <= score <= 56:  return "ME2", 5
    if 31 <= score <= 40:  return "AE1", 4
    if 21 <= score <= 30:  return "AE2", 3
    if 11 <= score <= 20:  return "BE1", 2
    return "BE2", 1

# Calculate Global performance levels based on total marks added
def compute_global_cbc(total_score):
    total_score = total_score or 0
    if 786 <= total_score <= 900: return "EE1 (Exceeding Expectation 1)"
    if 673 <= total_score <= 785: return "EE2 (Exceeding Expectation 2)"
    if 561 <= total_score <= 672: return "ME1 (Meeting Expectation 1)"
    if 450 <= total_score <= 560: return "ME2 (Meeting Expectation 2)"
    if 337 <= total_score <= 449: return "AE1 (Approaching Expectation 1)"
    if 225 <= total_score <= 336: return "AE2 (Approaching Expectation 2)"
    if 113 <= total_score <= 224: return "BE1 (Below Expectation 1)"
    return "BE2 (Below Expectation 2)"

# Compute dynamic totals and point summaries
total_marks_list = []
total_points_list = []

for idx, row in students_df.iterrows():
    t_marks = 0
    t_points = 0
    for col in subj_cols:
        score = row[col]
        t_marks += score
        _, pts = compute_subject_cbc(score)
        t_points += pts
    total_marks_list.append(t_marks)
    total_points_list.append(t_points)

students_df["TOTAL MARKS"] = total_marks_list
students_df["TOTAL POINTS"] = total_points_list

# Dynamic Position/Rank Generator Logic (Ties share same position rank)
students_df["POSITION"] = students_df["TOTAL MARKS"].rank(method="min", ascending=False).astype(int)
total_students_count = len(students_df)

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
                "Top Performer": top_student_row["name"],
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
        st.markdown("#### 🏅 Top 10 Overall Students (Ranked by Marks)")
        top_10 = students_df.sort_values(by="TOTAL MARKS", ascending=False).head(10)[["POSITION", "adm_no", "name", "TOTAL MARKS", "TOTAL POINTS"]]
        top_10.columns = ["RANK/POS", "ADM NO", "STUDENT NAME", "TOTAL MARKS (900)", "TOTAL POINTS (72)"]
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
    
    # Intelligent Auto-Comment Generator Engine
    def generate_teacher_comment(total_score):
        if total_score >= 786:
            return "Exceptional academic performance! Exhibits exemplary mastery and concept application."
        elif total_score >= 673:
            return "Excellent work! Maintains highly commendable performance. Keep striving for the peak."
        elif total_score >= 561:
            return "Very good progress made. Consistently meets standards. Aim for higher grades next term."
        elif total_score >= 450:
            return "Good performance, but has potential to do much better. Focus on targets for improvement."
        elif total_score >= 337:
            return "Fair performance. Approaching targeted levels but requires more intensive practice."
        else:
            return "Below expectations. Needs focused remedial support and close academic monitoring."

    # --- DYNAMIC CBC REPORT CARD GENERATION ENGINE ---
    def generate_student_report_card(row, close_dt, open_dt, total_students):
        img = Image.new("RGB", (800, 1150), color="#FFFFFF")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        # 1. INSTITUTIONAL HEADER BLOCK
        draw.text((400, 40), "KEA COMPREHENSIVE SCHOOL", fill="#1E3A8A", anchor="mm")
        draw.text((400, 65), "P.O. BOX 557-40404, SUNA MIGORI", fill="#475569", anchor="mm")
        draw.text((400, 95), "STUDENT ASSESSMENT REPORT FORM", fill="#1E293B", anchor="mm")
        draw.line([(40, 120), (760, 120)], fill="#CBD5E1", width=2)
        
        # 2. BIO DATA SECTION WITH RANK POSITION FIELD INCLUDED
        draw.text((50, 140), "STUDENT NAME:", fill="#64748B")
        draw.text((180, 140), str(row['name']).upper(), fill="#0F172A")
        draw.text((50, 175), "ADM NO:", fill="#64748B")
        draw.text((180, 175), str(row['adm_no']), fill="#0F172A")
        draw.text((50, 210), "ASSESSMENT NO:", fill="#64748B")
        draw.text((180, 210), str(row['assessment_no']) if row['assessment_no'] else "N/A", fill="#0F172A")

        draw.text((480, 140), "CLASS / GRADE:", fill="#64748B")
        draw.text((620, 140), str(row['grade']), fill="#0F172A")
        draw.text((480, 175), "CLASS POSITION:", fill="#1E3A8A")
        draw.text((620, 175), f"POS {row['POSITION']} OUT OF {total_students}", fill="#0F172A")
        draw.text((480, 210), "TERM / YEAR:", fill="#64748B")
        draw.text((620, 210), "TERM 2 / 2026", fill="#0F172A")

        # 3. TABLE HEADERS
        table_top = 260
        draw.rectangle([(40, table_top), (760, table_top + 35)], fill="#1E3A8A")
        draw.text((60, table_top + 10), "S/N", fill="#FFFFFF")
        draw.text((120, table_top + 10), "LEARNING AREA / SUBJECT", fill="#FFFFFF")
        draw.text((440, table_top + 10), "SCORE", fill="#FFFFFF")
        draw.text((530, table_top + 10), "LEVEL", fill="#FFFFFF")
        draw.text((660, table_top + 10), "POINTS", fill="#FFFFFF")
        
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
        
        for idx, (code, subject_name, mark) in enumerate(subjects_list, start=1):
            mark_val = mark if mark is not None else 0
            lvl, pts = compute_subject_cbc(mark_val)
            
            if idx % 2 == 0:
                draw.rectangle([(40, current_y), (760, current_y + 35)], fill="#F8FAFC")
                
            draw.text((60, current_y + 10), str(idx), fill="#334155")
            draw.text((120, current_y + 10), f"({code}) {subject_name}", fill="#0F172A")
            draw.text((440, current_y + 10), f"{int(mark_val)}%", fill="#0F172A")
            draw.text((530, current_y + 10), lvl, fill="#1E3A8A")
            draw.text((670, current_y + 10), f"{pts} Pts", fill="#475569")
            
            draw.line([(40, current_y + 35), (760, current_y + 35)], fill="#E2E8F0", width=1)
            current_y += 35

        # 4. TOTALS SUMMARY METRIC DECK
        current_y += 15
        draw.rectangle([(40, current_y), (760, current_y + 40)], fill="#F1F5F9")
        draw.text((60, current_y + 12), f"TOTAL MARKS: {int(row['TOTAL MARKS'])} / 900", fill="#1E3A8A")
        draw.text((320, current_y + 12), f"TOTAL POINTS: {int(row['TOTAL POINTS'])} / 72", fill="#1E3A8A")
        
        global_lvl = compute_global_cbc(row['TOTAL MARKS'])
        draw.text((540, current_y + 12), f"GRADE: {global_lvl.split(' ')[0]}", fill="#1E3A8A")
        current_y += 40

        # Global Grade Full Text Callout
        current_y += 15
        draw.text((50, current_y), f"OVERALL PERFORMANCE LEVEL VALUE:  {global_lvl}", fill="#0F172A")

        # 5. DYNAMIC TEACHER COMMENTS SECTION
        current_y += 35
        draw.text((50, current_y), "CLASS TEACHER GENERAL COMMENT:", fill="#1E3A8A")
        current_y += 25
        comment_text = generate_teacher_comment(row['TOTAL MARKS'])
        draw.text((50, current_y), f'"{comment_text}"', fill="#0F172A")
        
        # 6. DYNAMIC TERM CALENDAR DATES
        current_y += 45
        draw.text((50, current_y), f"TERM CLOSING DATE:  {close_dt}", fill="#475569")
        draw.text((450, current_y), f"NEXT TERM OPENING DATE:  {open_dt}", fill="#475569")
        
        # 7. SIGNATURES & STAMP BACKGROUND REMOVER INJECTION
        current_y += 75
        draw.text((50, current_y), "CLASS TEACHER SIGNATURE: _______________________", fill="#475569")
        
        current_y += 40
        hoi_line_y = current_y
        draw.text((50, hoi_line_y + 25), "HOI STAMP & SIGNATURE:     _______________________", fill="#475569")
        
        # Look for the physical stamp file across extension formats safely
        stamp_path = None
        for file_ext in ["stamp.png", "stamp.jpg", "stamp.jpeg", "stamp.photo"]:
            if os.path.exists(file_ext):
                stamp_path = file_ext
                break
                
        if stamp_path:
            try:
                stamp_img = Image.open(stamp_path).convert("RGBA")
                
                # --- BACKGROUND REMOVAL LOGIC ---
                # Converts nearly white pixels (like scanner sheet background artifacts) 
                # into 100% see-through alpha channel pixels automatically
                datas = stamp_img.getdata()
                newData = []
                for item in datas:
                    # If pixel is bright white/near-white, swap it for transparency
                    if item[0] > 220 and item[1] > 220 and item[2] > 220:
                        newData.append((255, 255, 255, 0))
                    else:
                        newData.append(item)
                stamp_img.putdata(newData)
                
                # Resize stamp proportionally
                stamp_img.thumbnail((120, 120))
                
                # Paste the transparent stamp *next* to the HOI line instead of in front
                img.paste(stamp_img, (240, hoi_line_y - 45), stamp_img)
            except Exception:
                pass
        
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
        
        with st.spinner("Generating dynamic report card with stamp background removal..."):
            report_bytes = generate_student_report_card(student_row, closing_date, opening_date, total_students_count)
            
        st.image(report_bytes, caption=f"Preview Evaluation Form: {selected_student_name}", use_container_width=True)
        st.download_button(
            label=f"📥 Download Official Report: {selected_student_name}",
            data=report_bytes,
            file_name=f"Report_{student_row['adm_no']}.png",
            mime="image/png"
        )

    elif display_mode == "Complete Classroom Batch Processing Grid":
        st.success(f"Verified {total_students_count} classroom profiles ready for automatic batch rendering.")
        
        if st.button("🚀 Process & Generate All Classroom Reports", type="primary"):
            for idx, row in students_df.iterrows():
                with st.spinner(f"Rendering: {row['name']}..."):
                    r_bytes = generate_student_report_card(row, closing_date, opening_date, total_students_count)
                    
                st.write(f"✅ **{row['name']}** (ADM NO: {row['adm_no']} — POSITION: {row['POSITION']})")
                st.download_button(
                    label=f"Download Report Card: {row['name']}",
                    data=r_bytes,
                    file_name=f"Report_{row['adm_no']}.png",
                    key=f"dl_batch_{row['adm_no']}",
                    mime="image/png"
)
