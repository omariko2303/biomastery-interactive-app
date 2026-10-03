import streamlit as st
import time
import pandas as pd
from question_generator import generate_single_question, evaluate_written_answer
from database import init_local_db, log_score, get_leaderboard

# Page Configuration
st.set_page_config(
    page_title="BioMastery IGCSE | AI Portal",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_local_db()

# Custom UI Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #0E7490; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #475569; margin-bottom: 1.5rem; }
    .login-card { background-color: #FFFFFF; border-radius: 12px; padding: 30px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-top: 5px solid #0284C7; max-width: 550px; margin: 40px auto; }
    .question-box { background-color: #FFFFFF; border-left: 5px solid #0284C7; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .examiner-box-success { background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .examiner-box-error { background-color: #FEF2F2; border: 1px solid #FECACA; border-left: 5px solid #DC2626; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .keyword-pill-matched { display: inline-block; background-color: #DCFCE7; color: #15803D; font-weight: 600; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem; margin-right: 5px; margin-top: 5px; }
    .keyword-pill-missing { display: inline-block; background-color: #FEE2E2; color: #B91C1C; font-weight: 600; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem; margin-right: 5px; margin-top: 5px; }
    .timer-badge { background-color: #FEF3C7; color: #92400E; font-weight: bold; padding: 8px 15px; border-radius: 20px; font-size: 1.1rem; border: 1px solid #FCD34D; text-align: center; }
    .timer-badge-warning { background-color: #FEE2E2; color: #991B1B; font-weight: bold; padding: 8px 15px; border-radius: 20px; font-size: 1.1rem; border: 2px solid #EF4444; text-align: center; animation: pulse 1s infinite; }
    .ai-badge { background-color: #F3E8FF; color: #6B21A8; font-weight: bold; padding: 4px 10px; border-radius: 10px; font-size: 0.85rem; }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)

COUNTDOWN_AUDIO_HTML = """
<audio autoplay>
  <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
</audio>
"""

CAMBRIDGE_SYLLABUS = [
    "01. Characteristics and Classification of Living Organisms",
    "02. Organisation of the Organism (Cell Structure & Magnification)",
    "03. Movement Into and Out of Cells (Diffusion, Osmosis, Active Transport)",
    "04. Biological Molecules (Carbohydrates, Proteins, Lipids, Water)",
    "05. Enzymes (Enzyme Action, Temperature, pH Effects)",
    "06. Plant Nutrition (Photosynthesis, Leaf Structure, Limiting Factors)",
    "07. Human Nutrition (Diet, Alimentary Canal, Digestion, Absorption)",
    "08. Transport in Plants (Xylem, Phloem, Transpiration, Translocation)",
    "09. Transport in Animals (Circulatory System, Heart, Blood Vessels, Blood)",
    "10. Diseases and Immunity (Pathogens, Defences, Vaccination, Antibodies)",
    "11. Gas Exchange in Humans (Lungs, Alveoli, Ventilation Mechanics)",
    "12. Respiration (Aerobic vs Anaerobic Respiration, ATP)",
    "13. Excretion in Humans (Kidneys, Nephrons, Urea, Excretory Organs)",
    "14. Coordination and Response (Nervous System, Reflexes, Eye, Hormones, Tropisms)",
    "15. Drugs (Medicinal Drugs, Antibiotics, Alcohol, Heroin)",
    "16. Reproduction (Asexual vs Sexual, Flowering Plants, Human Reproductive System)",
    "17. Inheritance (Chromosomes, Mitosis, Meiosis, Monohybrid Crosses, Pedigrees)",
    "18. Variation and Selection (Mutation, Adaptive Features, Natural/Artificial Selection)",
    "19. Organisms and Their Environment (Energy Flow, Food Chains, Nutrient Cycles)",
    "20. Biotechnology and Genetic Modification (Bacterial Culture, Recombinant DNA, Fermenters)",
    "21. Human Influences on Ecosystems (Deforestation, Pollution, Conservation)"
]

# State Management Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "student_email" not in st.session_state:
    st.session_state.student_email = ""
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "drill_active" not in st.session_state:
    st.session_state.drill_active = False
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "correct_count" not in st.session_state:
    st.session_state.correct_count = 0
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "written_eval" not in st.session_state:
    st.session_state.written_eval = None
if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None
if "session_logs" not in st.session_state:
    st.session_state.session_logs = []
if "show_summary" not in st.session_state:
    st.session_state.show_summary = False


# --- 1. OBLIGATORY ENTRY GATE (GMAIL / ICLOUD) ---
if not st.session_state.authenticated:
    st.markdown('<div class="main-header" style="text-align: center;">🧬 BioMastery IGCSE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="text-align: center;">Cambridge AI Engine & Live Performance Tracking</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="login-card">
        <h3 style="color: #0F172A; margin-top: 0;">🔒 Mandatory Student Verification</h3>
        <p style="color: #475569; font-size: 0.95rem;">Please sign in with your official <b>Gmail</b> or <b>iCloud</b> address to unlock practice drills, log leaderboard scores, and receive feedback.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_email_input = st.text_input("Enter your Gmail or iCloud address:", placeholder="e.g., candidate@gmail.com or student@icloud.com")
        
        if st.button("🚀 Sign In & Continue", type="primary", use_container_width=True):
            clean_email = user_email_input.strip().lower()
            
            # Validation rule for Gmail or iCloud
            if not clean_email or not ("@gmail.com" in clean_email or "@icloud.com" in clean_email):
                st.error("⚠️ Access restricted. Please enter a valid Gmail (@gmail.com) or iCloud (@icloud.com) address.")
            else:
                # Extract candidate name automatically from handle
                handle = clean_email.split("@")[0]
                extracted_name = handle.replace(".", " ").replace("_", " ").replace("-", " ").title()
                
                st.session_state.student_email = clean_email
                st.session_state.student_name = extracted_name
                st.session_state.authenticated = True
                st.rerun()
    st.stop()  # Halt execution so non-authenticated users cannot bypass screen


# --- 2. AUTHENTICATED APP CONTENT ---
st.sidebar.title("🧬 BioMastery IGCSE")
st.sidebar.markdown(f"Candidate: **{st.session_state.student_name}**")
st.sidebar.caption(f"📧 `{st.session_state.student_email}`")

if st.sidebar.button("🚪 Sign Out / Switch Account"):
    st.session_state.authenticated = False
    st.session_state.student_email = ""
    st.session_state.student_name = ""
    st.session_state.drill_active = False
    st.rerun()

st.sidebar.divider()
menu = st.sidebar.radio("Navigation", ["🎯 Infinite Practice Mode", "🏆 Leaderboard"])

# LEADERBOARD VIEW
if menu == "🏆 Leaderboard":
    st.header("🏆 Live Cambridge Student Leaderboard")
    st.caption("Rankings update automatically based on total marks scored across all drill sessions.")
    
    leaderboard_data = get_leaderboard()
    if leaderboard_data:
        df_lb = pd.DataFrame(leaderboard_data, columns=["Candidate Name", "Total Marks Scored", "Total Questions Solved", "Accuracy (%)"])
        df_lb.index = df_lb.index + 1
        st.dataframe(df_lb, use_container_width=True)
    else:
        st.info("No leaderboard entries recorded yet. Be the first to launch a session!")

# PRACTICE DRILL VIEW
elif menu == "🎯 Infinite Practice Mode":
    st.markdown('<div class="main-header">Infinite AI Diagnostic Drill</div>', unsafe_allow_html=True)

    keys_pool = st.secrets.get("GEMINI_API_KEYS", st.secrets.get("GEMINI_API_KEY", ""))

    if not st.session_state.drill_active and not st.session_state.show_summary:
        st.subheader("🛠 Configure Exam Session")
        c1, c2 = st.columns(2)
        with c1:
            selected_paper = st.selectbox("Select Paper Focus:", ["Paper 2 (Multiple Choice)", "Paper 4 (Theory & Data Analysis)", "Paper 6 (Alternative to Practical)"])
        with c2:
            selected_topic = st.selectbox("Select Cambridge Chapter:", CAMBRIDGE_SYLLABUS)

        if st.button("🚀 Launch Diagnostic Session", type="primary"):
            if not keys_pool:
                st.error("❌ No API Keys found in Streamlit Secrets!")
            else:
                st.session_state.selected_paper = selected_paper
                st.session_state.selected_topic = selected_topic
                st.session_state.drill_active = True
                st.session_state.question_count = 0
                st.session_state.correct_count = 0
                st.session_state.current_question = None
                st.session_state.show_feedback = False
                st.session_state.written_eval = None
                st.session_state.session_logs = []
                st.session_state.show_summary = False
                st.rerun()

    elif st.session_state.show_summary:
        st.balloons()
        st.header("📊 Diagnostic Performance Report")
        
        total_q = st.session_state.question_count
        corr_q = st.session_state.correct_count
        pct = round((corr_q / total_q) * 100, 1) if total_q > 0 else 0.0

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Candidate Name", st.session_state.student_name)
        col_m2.metric("Final Score", f"{corr_q} / {total_q}")
        col_m3.metric("Accuracy Percentage", f"{pct}%")

        st.divider()

        matched_kw_set = set()
        missing_kw_set = set()
        for log in st.session_state.session_logs:
            matched_kw_set.update(log.get("matched_keywords", []))
            missing_kw_set.update(log.get("missing_keywords", []))

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("🟢 Mastered Keywords")
            if matched_kw_set:
                for kw in matched_kw_set:
                    st.markdown(f"- ✅ `{kw}`")
            else:
                st.info("Keep practicing to build your keyword bank!")

        with col_s2:
            st.subheader("🔴 Areas for Improvement")
            if missing_kw_set:
                for kw in missing_kw_set:
                    st.markdown(f"- ⚠️ `{kw}`")
            else:
                st.success("Perfect accuracy! No missing keywords identified.")

        if st.button("Start New Drill"):
            st.session_state.drill_active = False
            st.session_state.show_summary = False
            st.session_state.current_question = None
            st.rerun()

    else:
        if st.session_state.current_question is None:
            with st.spinner("🤖 Gemini is generating question & setting timer..."):
                try:
                    q_data = generate_single_question(keys_pool, st.session_state.selected_paper, st.session_state.selected_topic)
                    st.session_state.current_question = q_data
                    st.session_state.question_start_time = time.time()
                    st.session_state.show_feedback = False
                    st.session_state.written_eval = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation error: {e}")
                    if st.button("Retry"):
                        st.rerun()
                    st.stop()

        q = st.session_state.current_question
        is_mcq = q.get("question_format") == "MULTIPLE_CHOICE"
        allowed_sec = q.get("allowed_time_seconds", 60)
        elapsed_sec = int(time.time() - st.session_state.question_start_time)
        remaining_sec = max(0, allowed_sec - elapsed_sec)

        if 0 < remaining_sec <= 10 and not st.session_state.show_feedback:
            st.components.v1.html(COUNTDOWN_AUDIO_HTML, height=0)

        s1, s2, s3, s4 = st.columns([1.5, 1, 1, 1])
        s1.markdown(f"**Candidate:** `{st.session_state.student_name}` | **Q#{st.session_state.question_count + 1}**")
        s2.markdown(f"**Score:** `{st.session_state.correct_count}/{st.session_state.question_count}`")
        s3.markdown(f'<span class="ai-badge">AI Timer: {allowed_sec}s</span>', unsafe_allow_html=True)
        
        if remaining_sec > 10:
            s4.markdown(f'<div class="timer-badge">⏱ {remaining_sec}s</div>', unsafe_allow_html=True)
        else:
            s4.markdown(f'<div class="timer-badge-warning">⚠️ {remaining_sec}s</div>', unsafe_allow_html=True)

        st.write("")

        st.markdown(f"""
        <div class="question-box">
            <span style="color:#0284C7; font-weight:bold; font-size:0.9rem;">[{q.get('syllabus_code', '0610')}] — {q.get('command_word', 'Question')}</span>
            <h4 style="margin-top:8px; color:#1E293B;">{q['question']}</h4>
        </div>
        """, unsafe_allow_html=True)

        if is_mcq:
            selected_option = st.radio(
                "Select your option:",
                options=q["options"],
                key=f"mcq_opt_{st.session_state.question_count}",
                disabled=st.session_state.show_feedback
            )

            if not st.session_state.show_feedback:
                c_btn1, c_btn2 = st.columns([2, 1])
                with c_btn1:
                    if st.button("Submit MCQ Answer", type="primary"):
                        st.session_state.show_feedback = True
                        is_corr = q["options"].index(selected_option) == q["correct_index"]
                        st.session_state.question_count += 1
                        if is_corr:
                            st.session_state.correct_count += 1
                        
                        st.session_state.session_logs.append({
                            "question": q['question'],
                            "is_correct": is_corr,
                            "matched_keywords": q.get("keywords", []) if is_corr else [],
                            "missing_keywords": [] if is_corr else q.get("keywords", [])
                        })
                        
                        log_score(
                            st.session_state.student_email, 
                            st.session_state.student_name, 
                            st.session_state.selected_topic, 
                            1 if is_corr else 0, 
                            1
                        )
                        st.rerun()

                with c_btn2:
                    if st.button("🏁 End Session & Save Score"):
                        st.session_state.drill_active = False
                        st.session_state.show_summary = True
                        st.rerun()

            else:
                is_corr = q["options"].index(selected_option) == q["correct_index"]
                if is_corr:
                    st.markdown(f'<div class="examiner-box-success"><h4>✅ Correct (+1 Mark)</h4><p>{q["examiner_note"]}</p></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="examiner-box-error"><h4>❌ Incorrect Option</h4><p><b>Correct Answer:</b> {q["options"][q["correct_index"]]}</p><p>{q["examiner_note"]}</p></div>', unsafe_allow_html=True)

        else:
            user_text_response = st.text_area(
                "Write your answer below (use precise Cambridge scientific terminology):",
                key=f"written_opt_{st.session_state.question_count}",
                disabled=st.session_state.show_feedback,
                height=130
            )

            if not st.session_state.show_feedback:
                c_btn1, c_btn2 = st.columns([2, 1])
                with c_btn1:
                    if st.button("Submit Written Answer for AI Examiner Review", type="primary"):
                        if not user_text_response.strip():
                            st.warning("Please type your response before submitting!")
                        else:
                            with st.spinner("🤖 Senior Examiner evaluating response against Mark Scheme keywords..."):
                                eval_result = evaluate_written_answer(keys_pool, q, user_text_response)
                                st.session_state.written_eval = eval_result
                                st.session_state.show_feedback = True
                                st.session_state.question_count += 1
                                score_awarded = eval_result.get("score_awarded", 0)
                                if score_awarded > 0:
                                    st.session_state.correct_count += 1
                                
                                st.session_state.session_logs.append({
                                    "question": q['question'],
                                    "is_correct": score_awarded > 0,
                                    "matched_keywords": eval_result.get("matched_keywords", []),
                                    "missing_keywords": eval_result.get("missing_keywords", [])
                                })
                                
                                log_score(
                                    st.session_state.student_email, 
                                    st.session_state.student_name, 
                                    st.session_state.selected_topic, 
                                    score_awarded, 
                                    1
                                )
                                st.rerun()

                with c_btn2:
                    if st.button("🏁 End Session & Save Score"):
                        st.session_state.drill_active = False
                        st.session_state.show_summary = True
                        st.rerun()

            else:
                eval_res = st.session_state.written_eval or {}
                score = eval_res.get("score_awarded", 0)
                
                if score > 0:
                    st.markdown(f'<div class="examiner-box-success"><h4>✅ Full Marks Awarded</h4><p>{eval_res.get("examiner_feedback")}</p></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="examiner-box-error"><h4>⚠️ Mark Loss / Incomplete Key Terms</h4><p>{eval_res.get("examiner_feedback")}</p></div>', unsafe_allow_html=True)

                st.markdown(f"**Ideal Cambridge Model Answer:**\n> {q.get('model_answer', 'N/A')}")
                
                matched = eval_res.get("matched_keywords", [])
                missing = eval_res.get("missing_keywords", [])
                
                st.markdown("##### 🔑 Keyword Checklist:")
                html_kw = "".join([f'<span class="keyword-pill-matched">✓ {kw}</span>' for kw in matched])
                html_kw += "".join([f'<span class="keyword-pill-missing">✗ {kw}</span>' for kw in missing])
                st.markdown(html_kw, unsafe_allow_html=True)

        if st.session_state.show_feedback:
            st.write("")
            b1, b2 = st.columns([2, 1])
            with b1:
                if st.button("Next Question ➔", type="primary"):
                    st.session_state.current_question = None
                    st.session_state.show_feedback = False
                    st.session_state.written_eval = None
                    st.rerun()
            with b2:
                if st.button("🏁 End Session & View Report"):
                    st.session_state.drill_active = False
                    st.session_state.show_summary = True
                    st.rerun()
                
