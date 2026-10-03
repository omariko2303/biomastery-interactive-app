import streamlit as st
import pandas as pd
import plotly.express as px
import time
from database import init_db, save_session_results, get_student_performance
from question_generator import generate_single_question

st.set_page_config(
    page_title="BioMastery IGCSE | Infinite AI Practice",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

# Custom UI Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #0E7490; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #475569; margin-bottom: 1.5rem; }
    .question-box { background-color: #FFFFFF; border-left: 5px solid #0284C7; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .examiner-box-success { background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .examiner-box-error { background-color: #FEF2F2; border: 1px solid #FECACA; border-left: 5px solid #DC2626; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .keyword-pill { display: inline-block; background-color: #E0F2FE; color: #0369A1; font-weight: 600; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem; margin-right: 5px; margin-top: 5px; }
    .timer-badge { background-color: #FEF3C7; color: #92400E; font-weight: bold; padding: 8px 15px; border-radius: 20px; font-size: 1.1rem; border: 1px solid #FCD34D; text-align: center; }
    .ai-badge { background-color: #F3E8FF; color: #6B21A8; font-weight: bold; padding: 4px 10px; border-radius: 10px; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# Complete 21-Chapter Cambridge O Level / IGCSE Biology Syllabus Index
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
    "21. Human Influences on Ecosystems (Deforestation, Pollution, Conservation, Endangered Species)"
]

# Session State
if "student_name" not in st.session_state:
    st.session_state.student_name = "Omar Mohamed"
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
if "session_logs" not in st.session_state:
    st.session_state.session_logs = []
if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None

st.sidebar.title("🧬 BioMastery IGCSE")
st.sidebar.caption("AI Cambridge Diagnostic Platform")

menu = st.sidebar.radio("Navigation", ["🎯 Infinite Practice Mode", "📊 Performance Analytics", "⚙️ API Settings"])

if menu == "⚙️ API Settings":
    st.header("⚙️ Configuration")
    student_input = st.text_input("Active Student Name:", value=st.session_state.student_name)
    if st.button("Save Profile"):
        st.session_state.student_name = student_input
        st.success("✅ Profile updated!")

elif menu == "🎯 Infinite Practice Mode":
    st.markdown('<div class="main-header">Infinite AI Diagnostic Drill</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Candidate: <b>{st.session_state.student_name}</b> | AI-Regulated Timing & Endless Question Pool</div>', unsafe_allow_html=True)

    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not st.session_state.drill_active:
        st.subheader("🛠️ Setup Practice Session")
        c1, c2 = st.columns(2)
        with c1:
            selected_paper = st.selectbox(
                "Select Paper Focus:",
                ["Paper 2 (Multiple Choice)", "Paper 4 (Theory & Data Analysis)", "Paper 6 (Alternative to Practical)"]
            )
        with c2:
            selected_topic = st.selectbox("Select Cambridge Chapter:", CAMBRIDGE_SYLLABUS)

        if st.button("🚀 Start Infinite Drill Session", type="primary"):
            if not api_key:
                st.error("❌ GEMINI_API_KEY is missing in Streamlit Secrets!")
            else:
                st.session_state.selected_paper = selected_paper
                st.session_state.selected_topic = selected_topic
                st.session_state.drill_active = True
                st.session_state.question_count = 0
                st.session_state.correct_count = 0
                st.session_state.session_logs = []
                st.session_state.current_question = None
                st.session_state.show_feedback = False
                st.rerun()

    else:
        # Load next question if current is empty
        if st.session_state.current_question is None:
            with st.spinner("🤖 Gemini 3.8-Flash is generating question and assessing difficulty..."):
                try:
                    q_data = generate_single_question(api_key, st.session_state.selected_paper, st.session_state.selected_topic)
                    st.session_state.current_question = q_data
                    st.session_state.question_start_time = time.time()
                    st.session_state.show_feedback = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading question: {e}")
                    if st.button("Retry"):
                        st.rerun()
                    st.stop()

        q = st.session_state.current_question
        
        # Calculate AI-Assigned Timer
        allowed_sec = q.get("allowed_time_seconds", 60)
        elapsed_sec = int(time.time() - st.session_state.question_start_time)
        remaining_sec = allowed_sec - elapsed_sec

        # Status Bar
        s1, s2, s3, s4 = st.columns([1.5, 1, 1, 1])
        s1.markdown(f"**Topic:** `{st.session_state.selected_topic.split('.')[0]}` | **Question #{st.session_state.question_count + 1}**")
        s2.markdown(f"**Score:** `{st.session_state.correct_count}/{st.session_state.question_count}`")
        s3.markdown(f'<span class="ai-badge">AI Time Limit: {allowed_sec}s ({q.get("difficulty_level", "Core")})</span>', unsafe_allow_html=True)
        
        # Timer display
        if remaining_sec > 0:
            s4.markdown(f'<div class="timer-badge">⏱️️ {remaining_sec}s</div>', unsafe_allow_html=True)
        else:
            s4.markdown('<div class="timer-badge" style="background-color:#FEE2E2; color:#991B1B;">⏰ Time Expired</div>', unsafe_allow_html=True)

        st.write("")

        # Question Presentation
        st.markdown(f"""
        <div class="question-box">
            <span style="color:#0284C7; font-weight:bold; font-size:0.9rem;">[{q.get('syllabus_code', '0610')}] — {q.get('command_word', 'Question')}</span>
            <h4 style="margin-top:8px; color:#1E293B;">{q['question']}</h4>
        </div>
        """, unsafe_allow_html=True)

        selected_option = st.radio(
            "Select your answer:",
            options=q["options"],
            key=f"inf_opt_{st.session_state.question_count}",
            disabled=st.session_state.show_feedback
        )

        if not st.session_state.show_feedback:
            col_sub1, col_sub2 = st.columns([1, 4])
            with col_sub1:
                if st.button("Submit Answer", type="primary"):
                    st.session_state.show_feedback = True
                    is_corr = q["options"].index(selected_option) == q["correct_index"]
                    
                    st.session_state.question_count += 1
                    if is_corr:
                        st.session_state.correct_count += 1

                    st.session_state.session_logs.append({
                        "paper_type": st.session_state.selected_paper,
                        "syllabus_code": q.get("syllabus_code", "0610"),
                        "question_text": q["question"],
                        "selected_option": selected_option,
                        "is_correct": is_corr
                    })
                    st.rerun()

        else:
            # Feedback Display
            is_corr = q["options"].index(selected_option) == q["correct_index"]
            if is_corr:
                st.markdown(f"""
                <div class="examiner-box-success">
                    <h4 style="color:#15803D; margin:0;">✅ Correct (+1 Mark)</h4>
                    <p style="margin-top:8px; color:#166534;"><b>Examiner Report Breakdown:</b> {q['examiner_note']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="examiner-box-error">
                    <h4 style="color:#B91C1C; margin:0;">❌ Incorrect / Examiner Trap Triggered</h4>
                    <p style="margin-top:8px; color:#991B1B;"><b>Correct Option:</b> {q['options'][q['correct_index']]}</p>
                    <p style="margin-top:5px; color:#991B1B;"><b>Examiner Report Breakdown:</b> {q['examiner_note']}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("##### 🔑 Mandatory Keywords:")
            kw_html = "".join([f'<span class="keyword-pill">{kw}</span>' for kw in q.get('keywords', [])])
            st.markdown(kw_html, unsafe_allow_html=True)
            st.write("")

            b1, b2 = st.columns([2, 1])
            with b1:
                if st.button("Next Question ➔", type="primary"):
                    st.session_state.current_question = None
                    st.session_state.show_feedback = False
                    st.rerun()
            with b2:
                if st.button("🏁 End Session & Save Progress"):
                    save_session_results(
                        st.session_state.student_name,
                        st.session_state.selected_paper,
                        st.session_state.selected_topic,
                        st.session_state.question_count,
                        st.session_state.correct_count,
                        0,
                        st.session_state.session_logs
                    )
                    st.session_state.drill_active = False
                    st.session_state.current_question = None
                    st.success("Session saved!")
                    st.rerun()

elif menu == "📊 Performance Analytics":
    st.header(f"📊 Diagnostic History: {st.session_state.student_name}")
    rows = get_student_performance(st.session_state.student_name)
    if rows:
        df = pd.DataFrame(rows, columns=["Session ID", "Paper Type", "Syllabus Chapter", "Total Questions", "Correct Answers", "Score %", "Time Spent", "Timestamp"])
        st.dataframe(df[["Paper Type", "Syllabus Chapter", "Total Questions", "Correct Answers", "Score %", "Timestamp"]], use_container_width=True)
    else:
        st.info("No recorded sessions yet.")
