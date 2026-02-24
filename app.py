import streamlit as st
import time
import base64
import random
import os
import re
import pandas as pd
from database import init_db, save_score, get_leaderboard, get_all_scores
from questions import parse_markdown_questions

st.set_page_config(page_title="🏆 3D Printing Challenge", page_icon="3️⃣", layout="centered", initial_sidebar_state="collapsed")

# 🌟 Advanced Custom CSS for Gamified, Cyberpunk Mobile-First Look
# Clean CSS: config.toml handles base theme; this only adds decorative cyberpunk effects
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@400;600;800&display=swap');
    html, body, * {
        font-family: 'Prompt', sans-serif !important;
    }
    .stApp {
        background: radial-gradient(ellipse at top, #1a1a2e 0%, #0d0d1a 100%);
    }
    h1 {
        text-align: center;
        color: #00ffcc !important;
        text-shadow: 0 0 8px #00ffcc, 0 0 20px #00ffcc;
        font-weight: 800 !important;
    }
    h2, h3, h4 {
        color: #00ccff !important;
        font-weight: 700 !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background: linear-gradient(135deg, #ff007f, #6600ff) !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 0.6rem 1.5rem;
        box-shadow: 0 4px 15px rgba(255, 0, 127, 0.4);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 0, 255, 0.6);
        background: linear-gradient(135deg, #6600ff, #00ffcc) !important;
    }
    .timer {
        font-size: 2rem;
        font-weight: 800;
        color: #ff4f4f !important;
        text-align: center;
        padding: 10px;
        border: 2px solid #ff4f4f;
        border-radius: 12px;
        margin-bottom: 16px;
    }
    .score-display {
        font-size: 3.5rem !important;
        font-weight: 800;
        color: #00ffcc !important;
        text-align: center;
        text-shadow: 0 0 10px #00ffcc;
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)

# Add background music
def play_bgm():
    # Retaining the exciting action music
    audio_html = """
    <audio autoplay loop>
        <source src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3" type="audio/mpeg">
    </audio>
    """
    st.components.v1.html(audio_html, height=0)

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

if "questions" not in st.session_state:
    qs = parse_markdown_questions("question-3d.md")
    for q in qs:
        # For multiple choice, assume the first parsed option is correct (index 0)
        # We do this because the provided source file didn't hard-key the correct answer
        if q['type'] == 'multiple_choice' and 'correct_index' not in q:
             q['correct_index'] = 0 
    
    # Shuffle options
    for q in qs:
        if q['type'] == 'multiple_choice':
            original_correct_opt = q['options'][q['correct_index']]
            random.shuffle(q['options'])
            q['correct_index'] = q['options'].index(original_correct_opt)

    # Shuffle the main questions array
    random.shuffle(qs)

    st.session_state.questions = qs

# Session Management Setup
if "page" not in st.session_state:
    st.session_state.page = "register"
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.helpers = {"x2": 1, "5050": 1, "skip": 1}
    st.session_state.active_x2 = False
    st.session_state.removed_options = []
    st.session_state.start_time = 0
    st.session_state.user_info = {}

# Sidebar for Teacher Admin
with st.sidebar:
    st.header("👨‍🏫 โหมดครูผู้สอน")
    admin_pwd = st.text_input("รหัสผ่าน Admin", type="password")
    if st.button("เข้าสู่ Dashboard"):
        if admin_pwd == "1234": # Simple hardcoded password for now
            st.session_state.page = "admin"
            st.rerun()
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")

# --- PAGE REGISTRATION ---
if st.session_state.page == "register":
    st.title("🚀 3D Printing Battle!")
    st.markdown("<p style='text-align:center;'>กรอกข้อมูลนักสู้ของคุณเพื่อเข้าสู่สนามรบ</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("register_form"):
        first_name = st.text_input("ชื่อ (First Name)")
        last_name = st.text_input("นามสกุล (Last Name)")
        student_id = st.text_input("รหัสประจำตัว (ID/Student ID)")
        level = st.selectbox("ระดับชั้น (Level)", ["ปวช. 1", "ปวช. 2", "ปวช. 3", "ปวส. 1", "ปวส. 2", "ปริญญาตรี", "ผู้ท้าชิงทั่วไป (อื่นๆ)"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🔥 START GAME 🔥")
        if submitted:
            if first_name and last_name and student_id:
                st.session_state.user_info = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "student_id": student_id,
                    "level": level
                }
                st.session_state.start_time = time.time()
                st.session_state.page = "exam"
                st.rerun()
            else:
                st.error("⚠️ กรุณากรอกข้อมูลให้ครบก่อนเข้าร่วมเกม!")

# --- PAGE EXAM ---
elif st.session_state.page == "exam":
    play_bgm()
    qs = st.session_state.questions
    q_index = st.session_state.current_q
    
    # Calculate Time Spent
    time_spent = int(time.time() - st.session_state.start_time)
    time_limit = len(qs) * 30 # 30 seconds per question
    time_left = max(0, time_limit - time_spent)
    
    # HUD: Live Timer Display
    st.markdown(f'<div class="timer">⏳ {time_left // 60:02d}:{time_left % 60:02d}</div>', unsafe_allow_html=True)
    
    if time_left == 0:
        st.error("💥 TIME OVER! 💥")
        time.sleep(2)
        st.session_state.page = "result"
        st.rerun()

    question = qs[q_index]
    
    # Progress Bar
    st.progress((q_index) / len(qs), text=f"⚔️ Stage {q_index + 1} / {len(qs)}")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if question['type'] == 'multiple_choice':
         st.markdown(f"### 🎯 ภารกิจ (เลือกตอบ):<br><span style='color:white; font-size:1.4rem;'>{question['text']}</span>", unsafe_allow_html=True)
    else:
         st.markdown(f"### ✍️ ภารกิจ (เติมคำ):<br><span style='color:white; font-size:1.4rem;'>{question['text']}</span>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gamification Helpers UI (Power-ups)
    st.markdown("**⚡ POWER-UPS (ใช้ได้ครั้งเดียว)**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.session_state.helpers["x2"] > 0 and not st.session_state.active_x2:
            if st.button("🌟 x2 SCO", key=f"h_x2_{q_index}"):
                st.session_state.helpers["x2"] = 0
                st.session_state.active_x2 = True
                st.rerun()
        elif st.session_state.active_x2:
            st.success("🔥 โหมด x2 ทำงาน!")
            
    with col2:
        if question['type'] == 'multiple_choice':
            if st.session_state.helpers["5050"] > 0 and not st.session_state.removed_options:
                if st.button("✂️ 50/50", key=f"h_50_{q_index}"):
                    st.session_state.helpers["5050"] = 0
                    correct_idx = question['correct_index']
                    all_idx = list(range(len(question['options'])))
                    all_idx.remove(correct_idx)
                    to_remove = random.sample(all_idx, max(1, len(all_idx)-2))
                    st.session_state.removed_options = to_remove
                    st.rerun()
                    
    with col3:
        if st.session_state.helpers["skip"] > 0:
             if st.button("⏭️ SKIP", key=f"h_skip_{q_index}"):
                 st.session_state.helpers["skip"] = 0
                 st.session_state.current_q += 1
                 if st.session_state.current_q >= len(qs):
                     st.session_state.page = "result"
                 st.rerun()
                 
    # Render Options depending on type
    answer = None
    st.markdown("<br>", unsafe_allow_html=True)
    if question['type'] == 'multiple_choice':
        displayed_options = []
        for i, opt in enumerate(question['options']):
            if i not in st.session_state.removed_options:
                displayed_options.append((i, opt))
                
        option_texts = [opt[1] for opt in displayed_options]
        answer_text = st.radio("👉 เล็งเป้าหมาย:", option_texts, index=None, key=f"ans_{q_index}")
        if answer_text:
             answer = [opt[0] for opt in displayed_options if opt[1] == answer_text][0]
    else:
        answer = st.text_input("💻 พิมพ์โค้ดรหัสกู้ภัย:", key=f"ans_{q_index}")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🎯 โจมตี! (SUBMIT)"):
        if answer is not None and answer != "":
            is_correct = False
            
            if question['type'] == 'multiple_choice':
                if answer == question['correct_index']:
                    is_correct = True
            else:
                 ans_str = str(answer).lower().strip()
                 correct_ans = question.get('answer', '').lower()
                 if ans_str in correct_ans or correct_ans in ans_str:
                     is_correct = True

            pts = 10
            if st.session_state.active_x2:
                pts *= 2
                
            if is_correct:
                st.session_state.score += pts
                st.toast(f"🎉 ตู้ม! เข้าเป้า! +{pts} EXP", icon="🔥")
            else:
                if question['type'] == 'multiple_choice':
                    st.toast(f"❌ พลาดเป้า! คำตอบที่ถูกคือ:\n{question['options'][question['correct_index']]}", icon="☠️")
                else:
                    st.toast(f"❌ พลาดเป้า! รหัสที่ถูกต้องคือ:\n{question.get('answer')}", icon="☠️")
                
            # Reset state for next question
            st.session_state.active_x2 = False
            st.session_state.removed_options = []
            st.session_state.current_q += 1
            time.sleep(1.5)
            
            if st.session_state.current_q >= len(qs):
                st.session_state.page = "result"
            st.rerun()
        else:
            st.error("⚠️ ต้องเลือกหรือพิมพ์เป้าหมายก่อนโจมตี!")

# --- PAGE RESULT ---
elif st.session_state.page == "result":
    st.balloons()
    play_bgm()
    time_spent = int(time.time() - st.session_state.start_time)
    
    st.title("🏆 MISSION COMPLETE")
    ui = st.session_state.user_info
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #00ffcc; font-size: 1.5rem;'>นักรบ: {ui.get('first_name')} {ui.get('last_name')} [{ui.get('student_id')}]</p>", unsafe_allow_html=True)
    
    # Heroic Score Display
    st.markdown(f"<div class='score-display'>{st.session_state.score} EXP</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #ff007f;'>⏱️ เวลาที่ใช้: {time_spent} วินาที</p>", unsafe_allow_html=True)
    
    # Save score to DB
    if "saved" not in st.session_state:
        save_score(ui['first_name'], ui['last_name'], ui['student_id'], ui['level'], st.session_state.score, time_spent)
        st.session_state.saved = True
        
    st.markdown("<br><hr style='border: 1px solid #330066;'><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>🏅 HALL OF FAME (Top 10)</h2>", unsafe_allow_html=True)
    
    lb = get_leaderboard()
    
    for idx, row in enumerate(lb[:10]):
        # first_name, last_name, student_id, level, score, time_spent
        medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"#{idx+1}"
        color = "#00ffcc" if idx < 3 else "#e0e0e0"
        
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 8px; margin-bottom: 5px; border-left: 4px solid {color};">
            <span style="font-size: 1.2rem;">{medal}</span> 
            <b style="color: {color};">{row[0]} {row[1]}</b> 
            <span style="float: right;">{row[4]} EXP | ⏱️ {row[5]}s</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔄 RETURN TO BASE (เล่นอีกครั้ง)"):
        for key in list(st.session_state.keys()):
            # Preserve DB init
            if key != "db_initialized":
                del st.session_state[key]
        st.rerun()

# --- PAGE ADMIN / TEACHER DASHBOARD ---
elif st.session_state.page == "admin":
    st.title("👨‍🏫 Teacher Dashboard (สรุปคะแนน)")
    
    # Simple Back Button
    if st.button("⬅️ กลับไปหน้าลงทะเบียน"):
        st.session_state.page = "register"
        st.rerun()
        
    st.markdown("---")
    
    # Fetch Data
    raw_data = get_all_scores()
    
    if not raw_data:
        st.warning("ยังไม่มีข้อมูลนักเรียนเข้าสอบในระบบ")
    else:
        # Columns: id, first_name, last_name, student_id, level, score, time_spent, created_at
        df = pd.DataFrame(raw_data, columns=[
            "ID", "ชื่อ", "นามสกุล", "รหัสนักศึกษา", "ระดับชั้น", "คะแนน (EXP)", "เวลา(วิ)", "วันที่สอบ"
        ])
        
        # Summary Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("จำนวนนักเรียนที่สอบแล้ว", f"{len(df)} คน")
        with col2:
            st.metric("คะแนนเฉลี่ย", f"{df['คะแนน (EXP)'].mean():.1f} EXP")
        with col3:
            st.metric("เวลาเฉลี่ย", f"{df['เวลา(วิ)'].mean():.1f} วินาที")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📊 ข้อมูลคะแนนทั้งหมด")
        
        # Display Table
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Download as CSV
        csv = df.to_csv(index=False).encode('utf-8-sig') # utf-8-sig for Thai compatibility in Excel
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ CSV",
            data=csv,
            file_name='student_scores.csv',
            mime='text/csv',
        )
