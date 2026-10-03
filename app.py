import streamlit as st
import time
import pandas as pd
from question_generator import get_high_yield_question, evaluate_written_answer_fast
from database import init_local_db, log_score, get_leaderboard

st.set_page_config(
    page_title="BioMastery IGCSE | AI Portal",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_local_db()

# Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #0E7490; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #475569; margin-bottom: 1.5rem; }
    .question-box { background-color: #FFFFFF; border-left: 5px solid #0284C7; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .examiner-box-success { background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .examiner-box-error { background-color: #FEF2F2; border: 1px solid #FECACA; border-left: 5px solid #DC2626; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .keyword-pill-matched { display: inline-block; background-color: #DCFCE7; color: #15803D; font-weight: 600; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem; margin-right: 5px; margin-top: 5px; }
    .keyword-pill-missing { display: inline-block; background-color: #FEE2E2; color: #B91C1C; font-weight: 600; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem; margin-right: 5px; margin-top: 5px; }
    .timer-badge { background-color: #FEF3C7; color: #92400E; font-weight: bold; padding: 8px 15px; border-radius: 20px; font-size: 1.1rem; border: 1px solid #FCD34D; text-align: center; }
    .timer-badge-warning { background-color: #FEE2E2; color: #991B1B; font-weight: bold; padding: 8px 15px; border-radius: 20px; font-size: 1.1rem; border: 2px solid #EF4444; text-align: center; }
</style>
""", unsafe_allow_html=True)

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

# Session State Initialization
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
if "seen_question_ids" not in st.session_state:
    st.session_state.seen_question_ids = []
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
if "show_summary" not in st.session_state:
    st.session_state.show_summary = False


# VERIFICATION GATE
if not st.session_state.authenticated:
    st.markdown('<div class="main-header" style="text-align: center;">🧬 BioMastery IGCSE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="text-align: center;">Cambridge High-Yield Diagnostic Engine</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("### 🔒 Student Sign-In")
        email_in = st.text_input("Email:", placeholder="e.g. candidate@gmail.com")
        
        suggested_name = ""
        if email_in and "@" in email_in:
            suggested_name = email_in.split("@")[0].replace(".", " ").replace("_", " ").title()

        name_in = st.text_input("Candidate Name:", value=suggested_name)

        if st.button("🚀 Launch Portal", type="primary", use_container_width=True):
            clean_email = email_in.strip().lower()
            if not clean_email or "@" not in clean_email:
                st.error("Please enter a valid email address.")
            else:
                st.session_state.student_email = clean_email
                st.session_state.student_name = name_in.strip() if name_in.strip() else "Candidate"
                st.session_state.authenticated = True
                st.rerun()
    st.stop()


# SIDEBAR
st.sidebar.title("🧬 BioMastery IGCSE")
st.sidebar.caption(f"👤 **{st.session_state.student_name}** (`{st.session_state.student_email}`)")

if st.sidebar.button("🚪 Sign Out"):
    st.session_state.authenticated = False
    st.session_state.drill_active = False
    st.rerun()

st.sidebar.divider()
menu = st.sidebar.radio("Navigation", ["🎯 High-Yield Exam Drill", "🏆 Leaderboard"])

if menu == "🏆 Leaderboard":
    st.header("🏆 Live Cambridge Student Leaderboard")
    lb_data = get_leaderboard()
    if lb_data:
        df = pd.DataFrame(lb_data, columns=["Candidate Name", "Total Marks", "Questions Attempted", "Accuracy (%)"])
        df.index = df.index + 1
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No leaderboard records found.")

elif menu == "🎯 High-Yield Exam Drill":
    st.markdown('<div class="main-header">High-Yield Exam Diagnostic Drill</div>', unsafe_allow_html=True)

    if not st.session_state.drill_active and not st.session_state.show_summary:
        st.subheader("🛠 Session Configuration")
        col1, col2 = st.columns(2)
        with col1:
            sel_paper = st.selectbox("Select Paper Focus:", [
                "Paper 2 (Multiple Choice)", 
                "Paper 4 (Theory & Data Analysis)", 
                "Paper 6 (Alternative to Practical)"
            ])
        with col2:
            sel_topic = st.selectbox("Select Chapter:", CAMBRIDGE_SYLLABUS)

        if st.button("🚀 Start Drill", type="primary"):
            st.session_state.selected_paper = sel_paper
            st.session_state.selected_topic = sel_topic
            st.session_state.drill_active = True
            st.session_state.question_count = 0
            st.session_state.correct_count = 0
            st.session_state.seen_question_ids = []
            st.session_state.current_question = None
            st.session_state.show_feedback = False
            st.session_state.show_summary = False
            st.rerun()

    elif st.session_state.show_summary:
        st.balloons()
        st.header("📊 Diagnostic Performance Summary")
        t_q = st.session_state.question_count
        c_q = st.session_state.correct_count
        acc = round((c_q / t_q) * 100, 1) if t_q > 0 else 0.0

        m1, m2, m3 = st.columns(3)
        m1.metric("Candidate", st.session_state.student_name)
        m2.metric("Score", f"{c_q} / {t_q}")
        m3.metric("Accuracy", f"{acc}%")

        if st.button("Configure New Drill"):
            st.session_state.drill_active = False
            st.session_state.show_summary = False
            st.session_state.current_question = None
            st.session_state.seen_question_ids = []
            st.rerun()

    else:
        # Load next question if none is active
        if st.session_state.current_question is None:
            q_obj = get_high_yield_question(
                st.session_state.selected_paper,
                st.session_state.selected_topic,
                seen_ids=st.session_state.seen_question_ids
            )
            st.session_state.current_question = q_obj
            if q_obj.get("id"):
                st.session_state.seen_question_ids.append(q_obj["id"])
            st.session_state.question_start_time = time.time()
            st.session_state.show_feedback = False
            st.session_state.written_eval = None
            st.rerun()

        q = st.session_state.current_question
        is_mcq = "options" in q
        allowed_sec = q.get("allowed_time_seconds", 60)

        # Calculate time remaining
        if not st.session_state.show_feedback:
            elapsed_sec = int(time.time() - st.session_state.question_start_time)
            remaining_sec = max(0, allowed_sec - elapsed_sec)

            # Timer expired: Auto-advance to next question immediately
            if remaining_sec == 0:
                st.session_state.question_count += 1
                log_score(
                    st.session_state.student_email,
                    st.session_state.student_name,
                    st.session_state.selected_topic,
                    0, 1
                )
                st.session_state.current_question = None
                st.warning("⏱ Time expired! Moving to next question automatically...")
                time.sleep(1)
                st.rerun()
        else:
            remaining_sec = 0

        # Status row
        r1, r2, r3 = st.columns([2, 1, 1])
        r1.markdown(f"**Candidate:** `{st.session_state.student_name}` | **Q#{st.session_state.question_count + 1}**")
        r2.markdown(f"**Score:** `{st.session_state.correct_count}/{st.session_state.question_count}`")

        if not st.session_state.show_feedback:
            badge = "timer-badge" if remaining_sec > 10 else "timer-badge-warning"
            r3.markdown(f'<div class="{badge}">⏱ {remaining_sec}s</div>', unsafe_allow_html=True)
        else:
            r3.markdown('<div class="timer-badge">✔ Submitted</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown(f"""
        <div class="question-box">
            <span style="color:#0284C7; font-weight:bold; font-size:0.9rem;">[0610 Cambridge IGCSE] — {st.session_state.selected_paper}</span>
            <h4 style="margin-top:8px; color:#1E293B;">{q['question']}</h4>
        </div>
        """, unsafe_allow_html=True)

        if is_mcq:
            sel_opt = st.radio(
                "Select your option:",
                options=q["options"],
                key=f"mcq_{q.get('id', st.session_state.question_count)}",
                disabled=st.session_state.show_feedback
            )

            if not st.session_state.show_feedback:
                b_col1, b_col2 = st.columns([2, 1])
                with b_col1:
                    if st.button("Submit Answer", type="primary"):
                        st.session_state.show_feedback = True
                        correct = (q["options"].index(sel_opt) == q["correct_index"])
                        st.session_state.question_count += 1
                        if correct:
                            st.session_state.correct_count += 1

                        log_score(
                            st.session_state.student_email,
                            st.session_state.student_name,
                            st.session_state.selected_topic,
                            1 if correct else 0, 1
                        )
                        st.rerun()
                with b_col2:
                    if st.button("🏁 End Session"):
                        st.session_state.drill_active = False
                        st.session_state.show_summary = True
                        st.rerun()

            else:
                correct = (q["options"].index(sel_opt) == q["correct_index"])
                if correct:
                    st.markdown(f'<div class="examiner-box-success"><h4>✅ Correct (+1 Mark)</h4><p>{q.get("examiner_note", "")}</p></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="examiner-box-error"><h4>❌ Incorrect</h4><p><b>Correct Answer:</b> {q["options"][q["correct_index"]]}</p></div>', unsafe_allow_html=True)

        else:
            written_input = st.text_area(
                "Write your answer below (use precise Cambridge scientific terminology):",
                key=f"written_{q.get('id', st.session_state.question_count)}",
                disabled=st.session_state.show_feedback,
                height=130
            )

            if not st.session_state.show_feedback:
                b_col1, b_col2 = st.columns([2, 1])
                with b_col1:
                    if st.button("Submit Written Answer for AI Examiner Review", type="primary"):
                        if not written_input.strip():
                            st.warning("Please type an answer before submitting.")
                        else:
                            # Instant evaluation
                            res = evaluate_written_answer_fast(q, written_input)
                            st.session_state.written_eval = res
                            st.session_state.show_feedback = True
                            st.session_state.question_count += 1
                            awarded = res.get("score_awarded", 0)
                            if awarded > 0:
                                st.session_state.correct_count += 1

                            log_score(
                                st.session_state.student_email,
                                st.session_state.student_name,
                                st.session_state.selected_topic,
                                awarded, 1
                            )
                            st.rerun()
                with b_col2:
                    if st.button("🏁 End Session"):
                        st.session_state.drill_active = False
                        st.session_state.show_summary = True
                        st.rerun()

            else:
                eval_res = st.session_state.written_eval or {}
                sc = eval_res.get("score_awarded", 0)

                if sc > 0:
                    st.markdown(f'<div class="examiner-box-success"><h4>✅ {sc} Mark(s) Awarded</h4><p>{eval_res.get("examiner_feedback")}</p></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="examiner-box-error"><h4>⚠️ 0 Marks Awarded</h4><p>{eval_res.get("examiner_feedback")}</p></div>', unsafe_allow_html=True)

                st.markdown(f"**Ideal Model Answer:**\n> {q.get('model_answer', 'N/A')}")

                matched = eval_res.get("matched_keywords", [])
                missing = eval_res.get("missing_keywords", [])

                st.markdown("##### 🔑 Keyword Checklist:")
                pills = "".join([f'<span class="keyword-pill-matched">✓ {k}</span>' for k in matched])
                pills += "".join([f'<span class="keyword-pill-missing">✗ {k}</span>' for k in missing])
                st.markdown(pills, unsafe_allow_html=True)

        if st.session_state.show_feedback:
            st.write("")
            nb1, nb2 = st.columns([2, 1])
            with nb1:
                if st.button("Next Question ➔", type="primary"):
                    st.session_state.current_question = None
                    st.session_state.show_feedback = False
                    st.session_state.written_eval = None
                    st.rerun()
            with nb2:
                if st.button("🏁 End Session"):
                    st.session_state.drill_active = False
                    st.session_state.show_summary = True
                    st.rerun()

        # Refresh page every second while answering to update the timer
        if not st.session_state.show_feedback:
            time.sleep(1)
            st.rerun()
