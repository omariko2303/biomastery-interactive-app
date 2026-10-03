import streamlit as st
import pandas as pd
import plotly.express as px
import time
from database import init_db, save_session_results, get_student_performance
from question_generator import generate_cambridge_questions

# Page Config
st.set_page_config(
    page_title="BioMastery IGCSE | AI Cambridge Engine",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
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
    .timer-badge { background-color: #FEF3C7; color: #92400E; font-weight: bold; padding: 8px 15px; border-radius: 20px; font-size: 1.1rem; border: 1px solid #FCD34D; }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "student_name" not in st.session_state:
    st.session_state.student_name = "Omar Mohamed"
if "active_questions" not in st.session_state:
    st.session_state.active_questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "quiz_complete" not in st.session_state:
    st.session_state.quiz_complete = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "time_limit_sec" not in st.session_state:
    st.session_state.time_limit_sec = 180

# Sidebar Setup
st.sidebar.title("🧬 BioMastery IGCSE")
st.sidebar.caption("AI-Powered Cambridge Diagnostic Engine")

menu = st.sidebar.radio("Navigation", ["🎯 AI Practice Drill", "📊 Performance Analytics", "⚙️ API & Settings"])

# 1. API & SETTINGS TAB
if menu == "⚙️ Settings & API":
    st.header("⚙️ Configuration & Gemini API Setup")
    api_input = st.text_input("Gemini API Key:", type="password", value=st.secrets.get("GEMINI_API_KEY", ""))
    student_input = st.text_input("Active Student Name:", value=st.session_state.student_name)
    
    if st.button("Save Settings", type="primary"):
        st.session_state.student_name = student_input
        st.success("✅ Settings updated successfully!")

# 2. PRACTICE DRILL TAB
elif menu == "🎯 AI Practice Drill":
    st.markdown(f'<div class="main-header">Cambridge AI Diagnostic Engine</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Candidate: <b>{st.session_state.student_name}</b> | Target: 0610 / 0970 Syllabus Precision</div>', unsafe_allow_html=True)

    # Question Generator Setup Panel
    if not st.session_state.active_questions:
        st.subheader("🛠️ Configure AI Drill Session")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            selected_paper = st.selectbox(
                "Select Paper Type:",
                ["Paper 2 (Multiple Choice Core/Extended)", "Paper 4 (Theory & Data Analysis)", "Paper 6 (Alternative to Practical)"]
            )
        with c2:
            selected_topic = st.selectbox(
                "Syllabus Topic Focus:",
                [
                    "03. Movement In and Out of Cells (Diffusion, Osmosis, Active Transport)",
                    "05. Enzymes & Biological Catalyst Mechanics",
                    "06. Plant Nutrition & Photosynthesis Experiments",
                    "07. Human Nutrition & Alimentary Canal",
                    "08. Transport in Plants (Xylem, Phloem, Transpiration)",
                    "09. Transport in Animals (Heart, Circulation, Blood)",
                    "12. Respiration & Gas Exchange",
                    "14. Coordination & Response (Nerves, Hormones, Tropisms)",
                    "16. Reproduction in Plants & Humans",
                    "20. Human Influences on Ecosystems"
                ]
            )
        with c3:
            num_q = st.slider("Number of AI Questions:", min_value=3, max_value=10, value=4)
            time_per_q = st.selectbox("Timer per Question:", ["45 seconds", "60 seconds", "90 seconds"])
            sec_per_q = int(time_per_q.split()[0])

        api_key_to_use = st.secrets.get("GEMINI_API_KEY", "")

        if st.button("🚀 Generate Cambridge AI Questions (Gemini 3.8-Flash)", type="primary"):
            if not api_key_to_use:
                st.error("❌ GEMINI_API_KEY is missing! Add it in Streamlit Secrets or under '⚙️ Settings & API'.")
            else:
                with st.spinner("🤖 Gemini 3.8-Flash is drafting Cambridge exam questions and examiner traps..."):
                    try:
                        q_data = generate_cambridge_questions(api_key_to_use, selected_paper, selected_topic, num_questions=num_q)
                        st.session_state.active_questions = q_data
                        st.session_state.current_index = 0
                        st.session_state.user_answers = {}
                        st.session_state.show_feedback = False
                        st.session_state.quiz_complete = False
                        st.session_state.start_time = time.time()
                        st.session_state.time_limit_sec = num_q * sec_per_q
                        st.session_state.selected_paper = selected_paper
                        st.session_state.selected_topic = selected_topic
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Error generating questions: {e}")

    else:
        # Active Drill Session Screen
        if not st.session_state.quiz_complete:
            questions = st.session_state.active_questions
            curr_i = st.session_state.current_index
            total_q = len(questions)
            q_data = questions[curr_i]

            # Countdown Timer Calculations
            elapsed_time = int(time.time() - st.session_state.start_time)
            remaining_time = st.session_state.time_limit_sec - elapsed_time

            if remaining_time <= 0:
                st.warning("⏰ TIME EXPIRED! Auto-submitting diagnostic drill...")
                st.session_state.quiz_complete = True
                st.rerun()

            # Top Status Bar
            col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
            with col_p1:
                st.progress((curr_i + 1) / total_q)
            with col_p2:
                st.caption(f"Question **{curr_i + 1} of {total_q}**")
            with col_p3:
                mins, secs = divmod(remaining_time, 60)
                st.markdown(f'<div class="timer-badge">⏱️ {mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)

            st.write("")

            # Question Presentation Card
            st.markdown(f"""
            <div class="question-box">
                <span style="color:#0284C7; font-weight:bold; font-size:0.9rem;">[{q_data.get('syllabus_code', '0610')}] — {q_data.get('command_word', 'Question')}</span>
                <h4 style="margin-top:8px; color:#1E293B;">{q_data['question']}</h4>
            </div>
            """, unsafe_allow_html=True)

            selected_option = st.radio(
                "Select your answer:",
                options=q_data["options"],
                key=f"ai_q_opt_{curr_i}",
                disabled=st.session_state.show_feedback
            )

            col_b1, col_b2 = st.columns([1, 4])
            with col_b1:
                if not st.session_state.show_feedback:
                    if st.button("Submit Answer", type="primary"):
                        st.session_state.show_feedback = True
                        st.session_state.user_answers[curr_i] = {
                            "selected": selected_option,
                            "selected_index": q_data["options"].index(selected_option),
                            "is_correct": q_data["options"].index(selected_option) == q_data["correct_index"]
                        }
                        st.rerun()

            # Feedback Panel
            if st.session_state.show_feedback:
                user_res = st.session_state.user_answers[curr_i]
                if user_res["is_correct"]:
                    st.markdown(f"""
                    <div class="examiner-box-success">
                        <h4 style="color:#15803D; margin:0;">✅ Correct Answer (+1 Mark)</h4>
                        <p style="margin-top:8px; color:#166534;"><b>Examiner Report Note:</b> {q_data['examiner_note']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="examiner-box-error">
                        <h4 style="color:#B91C1C; margin:0;">❌ Incorrect / Examiner Trap Triggered</h4>
                        <p style="margin-top:8px; color:#991B1B;"><b>Correct Option:</b> {q_data['options'][q_data['correct_index']]}</p>
                        <p style="margin-top:5px; color:#991B1B;"><b>Examiner Report Note:</b> {q_data['examiner_note']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("##### 🔑 Compulsory Mark Scheme Keywords:")
                kw_html = "".join([f'<span class="keyword-pill">{kw}</span>' for kw in q_data.get('keywords', [])])
                st.markdown(kw_html, unsafe_allow_html=True)
                st.write("")

                if st.button("Next Question ➔" if curr_i < total_q - 1 else "Finish & View Detailed Report 🏁"):
                    if curr_i < total_q - 1:
                        st.session_state.current_index += 1
                        st.session_state.show_feedback = False
                        st.rerun()
                    else:
                        st.session_state.quiz_complete = True
                        time_spent = int(time.time() - st.session_state.start_time)
                        correct_cnt = sum(1 for ans in st.session_state.user_answers.values() if ans["is_correct"])
                        
                        log_details = [
                            {
                                "paper_type": st.session_state.selected_paper,
                                "syllabus_code": questions[idx].get("syllabus_code", "0610"),
                                "question_text": questions[idx]["question"],
                                "selected_option": res["selected"],
                                "is_correct": res["is_correct"]
                            }
                            for idx, res in st.session_state.user_answers.items()
                        ]
                        
                        save_session_results(
                            st.session_state.student_name,
                            st.session_state.selected_paper,
                            st.session_state.selected_topic,
                            total_q,
                            correct_cnt,
                            time_spent,
                            log_details
                        )
                        st.rerun()

        else:
            # Final Diagnostic Summary
            st.balloons()
            st.header("🎉 Drill Completed & Analytics Logged!")
            
            questions = st.session_state.active_questions
            total_q = len(questions)
            correct_cnt = sum(1 for ans in st.session_state.user_answers.values() if ans["is_correct"])
            pct = round((correct_cnt / total_q) * 100, 1)

            c1, c2, c3 = st.columns(3)
            c1.metric("Final Score", f"{correct_cnt} / {total_q}")
            c2.metric("Accuracy Percentage", f"{pct}%")
            c3.metric("Candidate", st.session_state.student_name)

            st.divider()
            st.subheader("📋 Question Breakdown & Examiner Guidance")
            for idx, q_item in enumerate(questions):
                ans = st.session_state.user_answers.get(idx, {})
                status = "✅ Correct" if ans.get("is_correct") else "❌ Mark Loss Trap"
                with st.expander(f"Q{idx+1}: [{q_item.get('syllabus_code', '0610')}] {q_item.get('command_word', '')} — {status}"):
                    st.write(f"**Question:** {q_item['question']}")
                    st.write(f"**Your Answer:** {ans.get('selected')}")
                    st.write(f"**Examiner Breakdown:** {q_item['examiner_note']}")

            if st.button("Start New Drill Session"):
                st.session_state.active_questions = []
                st.session_state.current_index = 0
                st.session_state.user_answers = {}
                st.session_state.show_feedback = False
                st.session_state.quiz_complete = False
                st.rerun()

# 3. PERFORMANCE ANALYTICS TAB
elif menu == "📊 Performance Analytics":
    st.header(f"📊 Cambridge Diagnostic History: {st.session_state.student_name}")
    rows = get_student_performance(st.session_state.student_name)
    
    if rows:
        df = pd.DataFrame(rows, columns=["Session ID", "Paper Type", "Syllabus Topic", "Total Questions", "Correct Answers", "Score %", "Time (s)", "Timestamp"])
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.subheader("Score Progress Trend")
            fig = px.line(df, x="Timestamp", y="Score %", color="Paper Type", markers=True, title="Score Percentage Over Sessions")
            fig.update_yaxes(range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
            
        with col_m2:
            st.subheader("Historical Log Table")
            st.dataframe(df[["Paper Type", "Syllabus Topic", "Correct Answers", "Score %", "Time (s)", "Timestamp"]], use_container_width=True)
    else:
        st.info("No recorded practice sessions found yet. Generate an AI drill to log diagnostic metrics!")
