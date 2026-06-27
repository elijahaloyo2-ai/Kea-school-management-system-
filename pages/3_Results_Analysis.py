import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io

# 🔒 Check Session Authorization
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please sign in through the Main Command Center page first.")
    st.stop()

st.title("📊 CBC Analytical Performance Command Deck")

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

# --- DYNAMIC CBC REPORT CARD GENERATION ENGINE ---
def generate_student_report_card(row):
    # Create a fresh, pristine high-resolution white canvas (A4 Proportion: 800 width x 1150 height)
    # This guarantees that text from a previous student loop never overlaps onto the next!
    img = Image.new("RGB", (800, 1150), color="#FFFFFF")
    draw = ImageDraw.Draw(img)
    
    # Load fonts cleanly (Falls back safely to default if true-type files aren't found)
    try:
        font_title = ImageFont.load_default() # Use customized font sizing if .ttf available
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
    except Exception:
        font_title = font_bold = font_regular = ImageFont.load_default()

    # 1. INSTITUTIONAL HEADER BLOCK
    draw.text((400, 40), "KEA COMPREHENSIVE SCHOOL", fill="#1E3A8A", anchor="mm")
    draw.text((400, 65), "P.O. BOX 557-40404, SUNA MIGORI", fill="#475569", anchor="mm")
    draw.text((400, 95), "STUDENT ASSESSMENT REPORT FORM", fill="#1E293B", anchor="mm")
    
    # Decorative separation border line
    draw.line([(40, 120), (760, 120)], fill="#CBD5E1", width=2)
    
    # 2. BIO DATA SECTION (Using a strict grid layout to prevent text collision)
    # Left Column Bio
    draw.text((50, 140), "STUDENT NAME:", fill="#64748B")
    draw.text((180, 140), str(row['name']).upper(), fill="#0F172A")
    
    draw.text((50, 175), "ADM NO:", fill="#64748B")
    draw.text((180, 175), str(row['adm_no']), fill="#0F172A")
    
    draw.text((50, 210), "ASSESSMENT NO:", fill="#64748B")
    draw.text((180, 210), str(row['assessment_no']) if row['assessment_no'] else "N/A", fill="#0F172A")

    # Right Column Bio
    draw.text((480, 140), "CLASS / GRADE:", fill="#64748B")
    draw.text((620, 140), str(row['grade']), fill="#0F172A")
    
    draw.text((480, 175), "TERM:", fill="#64748B")
    draw.text((620, 175), "TERM 2", fill="#0F172A")
    
    draw.text((480, 210), "YEAR:", fill="#64748B")
    draw.text((620, 210), "2026", fill="#0F172A")

    # 3. PERFORMANCE EVALUATION TABLE HEADERS (Perfect vertical boundary alignment)
    table_top = 260
    # Header Background Bar
    draw.rectangle([(40, table_top), (760, table_top + 35)], fill="#1E3A8A")
    
    # Header Column Titles (X-anchored precisely)
    draw.text((60, table_top + 10), "S/N", fill="#FFFFFF")
    draw.text((120, table_top + 10), "LEARNING AREA / SUBJECT", fill="#FFFFFF")
    draw.text((480, table_top + 10), "SCORE (%)", fill="#FFFFFF")
    draw.text((620, table_top + 10), "PERFORMANCE LEVEL", fill="#FFFFFF")
    
    # Map out the catalog of subject components to print
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
    
    # Helper to calculate CBC Levels based on actual raw percentages
    def compute_cbc_level(score):
        score = score or 0
        if score >= 80: return "EE (Exceeding Expectation)"
        if score >= 50: return "ME (Meeting Expectation)"
        if score >= 30: return "AE (Approaching Expectation)"
        return "BE (Below Expectation)"

    # 4. ITERATE AND PRINT TABLE LINES WITH COMFORTABLE SEPARATION
    current_y = table_top + 35
    total_score = 0
    valid_subjects_count = 0
    
    for idx, (code, subject_name, mark) in enumerate(subjects_list, start=1):
        mark_val = mark if mark is not None else 0
        total_score += mark_val
        valid_subjects_count += 1
        
        # Zebra-striping background effect for beautiful layout readability
        if idx % 2 == 0:
            draw.rectangle([(40, current_y), (760, current_y + 35)], fill="#F8FAFC")
            
        # Draw text rows aligned cleanly to columns
        draw.text((60, current_y + 10), str(idx), fill="#334155")
        draw.text((120, current_y + 10), f"({code}) {subject_name}", fill="#0F172A")
        draw.text((500, current_y + 10), f"{int(mark_val)}%", fill="#0F172A")
        draw.text((620, current_y + 10), compute_cbc_level(mark_val), fill="#1E3A8A")
        
        # Row outline border lines
        draw.line([(40, current_y + 35), (760, current_y + 35)], fill="#E2E8F0", width=1)
        current_y += 35

    # 5. TOTALS AND GLOBAL REMARKS FOOTER BLOCK
    current_y += 20
    draw.rectangle([(40, current_y), (760, current_y + 40)], fill="#F1F5F9")
    draw.text((60, current_y + 12), f"TOTAL MARKS SCORED: {int(total_score)}", fill="#1E3A8A")
    
    mean_score = total_score / valid_subjects_count if valid_subjects_count > 0 else 0
    draw.text((450, current_y + 12), f"OVERALL ASSESSMENT VALUE: {compute_cbc_level(mean_score)}", fill="#1E3A8A")
    
    # 6. SIGNATURES & INSTITUTIONAL VALIDATION
    current_y += 80
    draw.text((50, current_y), "CLASS TEACHER SIGNATURE: _______________________", fill="#475569")
    current_y += 50
    draw.text((50, current_y), "HOI STAMP & SIGNATURE:     _______________________", fill="#475569")
    
    # Save processed canvas object into clean memory bytes
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
        report_bytes = generate_student_report_card(student_row)
        
    st.image(report_bytes, caption=f"Preview Evaluation Form: {selected_student_name}", use_container_width=True)
    st.download_button(
        label=f"📥 Download Official PDF/Report: {selected_student_name}",
        data=report_bytes,
        file_name=f"Report_{student_row['adm_no']}.png",
        mime="image/png"
    )

elif display_mode == "Complete Classroom Batch Processing Grid":
    st.success(f"Verified {len(students_df)} classroom profiles ready for automatic batch rendering.")
    
    if st.button("🚀 Process & Generate All Classroom Reports", type="primary"):
        for idx, row in students_df.iterrows():
            with st.spinner(f"Rendering: {row['name']}..."):
                r_bytes = generate_student_report_card(row)
                
            st.write(f"✅ **{row['name']}** (ADM NO: {row['adm_no']})")
            st.download_button(
                label=f"Download Report Card: {row['name']}",
                data=r_bytes,
                file_name=f"Report_{row['adm_no']}.png",
                key=f"dl_batch_{row['adm_no']}",
                mime="image/png"
    )
