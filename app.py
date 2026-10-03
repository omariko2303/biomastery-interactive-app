import streamlit as st
import pandas as pd
import plotly.express as px
from database import init_db, save_session_results, get_student_performance
from question_bank import QUESTION_BANK

# Page Config
st.set_page_config(
    page_title="BioMastery IGCSE | Interactive Practice",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
init_db()

# Custom CSS styling for professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0E7490;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .question-box {
        background-color: #FFFFFF;
        border-left: 5px solid #0284C7;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .examiner-box-success {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 5px solid #16A34A;
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
    }
    .examiner-box-error {
        background-color: #FEF2F2;
        border: 1px solid #FECACA;
        border-left: 5px solid #DC2626;
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
    }
    .keyword-pill {
        display: inline-block;
        background-color: #E0F2FE;
        color: #0369A1;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        margin-right: 5px;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "quiz_complete" not in st.session_state:
    st.session_state.quiz_complete = False
if "student_name" not in st.session_state:
    st.session_state.student_name = "Student"

# Sidebar
st.sidebar.title("🧬 BioMastery IGCSE")
st.sidebar.caption("Cambridge O Level / IGCSE Biology Diagnostic Platform")

menu = st.sidebar.radio("Navigation", ["🎯 Interactive Practice", "📊 Student Analytics", "⚙️ Session Config"])

if menu == "⚙️ Session Config":
    st.header("⚙️ Student Configuration")
    student_input = st.text_input("Enter Student Name:", value=st.session_state.student_name)
    if st.button("Save Profile"):
        st.session_state.student_name = student_input
        st.success(f"Active student set to: **{student_input}**")

elif menu == "🎯 Interactive Practice":
    st.markdown(f'<div class="main-header">Cambridge O Level Biology Diagnostic Drill</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Active Candidate: <b>{st.session_state.student_name}</b> | Focused Mode: Examiner Keywords & Command Words</div>', unsafe_allow_html=True)

    total_q = len(QUESTION_BANK)
    curr_i = st.session_state.current_index

    if not st.session_state.quiz_complete:
        q_data = QUESTION_BANK[curr_i]
        
        # Progress Bar Header
        col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
        with col_p1:
            st.progress((curr_i + 1) / total_q)
        with col_p2:
            st.caption(f"Question **{curr_i + 1} of {total_q}**")
        with col_p3:
            st.caption(f"Syllabus: `{q_data['syllabus_code']}`")

        # Question Presentation Box
        st.markdown(f"""
        <div class="question-box">
            <span style="color:#0284C7; font-weight:bold; font-size:0.9rem;">[{q_data['topic']}] — {q_data['command_word']}</span>
            <h4 style="margin-top:8px; color:#1E293B;">{q_data['question']}</h4>
        </div>
        """, unsafe_allow_html=True)

        # Answer Options
        selected_option = st.radio(
            "Select your response:",
            options=q_data["options"],
            key=f"q_opt_{curr_i}",
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
                    <p style="margin-top:8px; color:#166534;"><b>Examiner Breakdown:</b> {q_data['examiner_note']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="examiner-box-error">
                    <h4 style="color:#B91C1C; margin:0;">❌ Incorrect / Mark Loss Trap</h4>
                    <p style="margin-top:8px; color:#991B1B;"><b>Correct Option:</b> {q_data['options'][q_data['correct_index']]}</p>
                    <p style="margin-top:5px; color:#991B1B;"><b>Examiner Report Note:</b> {q_data['examiner_note']}</p>
                </div>
                """, unsafe_allow_html=True)

            # Key Terminology Callout
            st.markdown("##### 🔑 Mandatory Mark Scheme Keywords:")
            kw_html = "".join([f'<span class="keyword-pill">{kw}</span>' for kw in q_data['keywords']])
            st.markdown(kw_html, unsafe_allow_html=True)
            st.write("")

            if st.button("Next Question ➔" if curr_i < total_q - 1 else "Finish Diagnostic Drill 🏁"):
                if curr_i < total_q - 1:
                    st.session_state.current_index += 1
                    st.session_state.show_feedback = False
                    st.rerun()
                else:
                    st.session_state.quiz_complete = True
                    correct_cnt = sum(1 for ans in st.session_state.user_answers.values() if ans["is_correct"])
                    log_details = [
                        {
                            "question_id": QUESTION_BANK[idx]["id"],
                            "syllabus_code": QUESTION_BANK[idx]["syllabus_code"],
                            "selected_option": res["selected"],
                            "is_correct": res["is_correct"]
                        }
                        for idx, res in st.session_state.user_answers.items()
                    ]
                    save_session_results(
                        st.session_state.student_name,
                        "IGCSE 0610 Mixed",
                        total_q,
                        correct_cnt,
                        log_details
                    )
                    st.rerun()

    else:
        # Quiz Summary View
        st.balloons()
        st.header("🎉 Diagnostic Drill Completed!")
        
        correct_cnt = sum(1 for ans in st.session_state.user_answers.values() if ans["is_correct"])
        pct = round((correct_cnt / total_q) * 100, 1)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Score", f"{correct_cnt} / {total_q}")
        c2.metric("Accuracy Percentage", f"{pct}%")
        c3.metric("Candidate", st.session_state.student_name)

        st.subheader("📋 Performance & Misconception Review")
        for idx, q_item in enumerate(QUESTION_BANK):
            ans = st.session_state.user_answers.get(idx, {})
            status = "✅ Correct" if ans.get("is_correct") else "❌ Mark Loss"
            with st.expander(f"Q{idx+1}: {q_item['topic']} ({q_item['syllabus_code']}) — {status}"):
                st.write(f"**Question:** {q_item['question']}")
                st.write(f"**Your Choice:** {ans.get('selected')}")
                st.write(f"**Examiner Guidance:** {q_item['examiner_note']}")

        if st.button("Restart Drill"):
            st.session_state.current_index = 0
            st.session_state.user_answers = {}
            st.session_state.show_feedback = False
            st.session_state.quiz_complete = False
            st.rerun()

elif menu == "📊 Student Analytics":
    st.header(f"📊 Diagnostic History: {st.session_state.student_name}")
    rows = get_student_performance(st.session_state.student_name)
    
    if rows:
        df = pd.DataFrame(rows, columns=["Session ID", "Syllabus Code", "Total Questions", "Correct Answers", "Score %", "Timestamp"])
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.subheader("Historical Score Trend")
            fig = px.line(df, x="Timestamp", y="Score %", markers=True, title="Score Percentage Over Sessions")
            fig.update_yaxes(range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
            
        with col_m2:
            st.subheader("Session Log Summary")
            st.dataframe(df[["Syllabus Code", "Total Questions", "Correct Answers", "Score %", "Timestamp"]], use_container_width=True)
    else:
        st.info("No recorded practice sessions found for this candidate yet. Complete a diagnostic drill to view analytics!")
