import streamlit as st
import time
import pandas as pd
from question_generator import get_high_yield_question, evaluate_written_answer_fast
from database import init_local_db, log_score, get_leaderboard

st.set_page_config(page_title="BioMastery IGCSE | AI Portal", page_icon="🧬", layout="wide")
init_local_db()

# FIXED CSS: Explicitly setting 'color' for text to prevent the Dark Mode white-on-white bug
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #0E7490; }
    .question-box { background-color: #F8FAFC; color: #0F172A; border-left: 5px solid #0284C7; padding: 25px; border-radius: 8px; font-size: 1.2rem; margin-bottom: 20px;}
    .examiner-box-success { background-color: #F0FDF4; color: #064E3B; border-left: 5px solid #16A34A; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .examiner-box-error { background-color: #FEF2F2; color: #7F1D1D; border-left: 5px solid #DC2626; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .keyword-pill-matched { background-color: #DCFCE7; color: #15803D; padding: 4px 12px; border-radius: 12px; font-weight: 600; margin: 4px; display: inline-block; }
    .keyword-pill-missing { background-color: #FEE2E2; color: #B91C1C; padding: 4px 12px; border-radius: 12px; font-weight: 600; margin: 4px; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# Full 21 Chapters for O Level Biology
CAMBRIDGE_SYLLABUS = [
    "01. Characteristics and Classification of Living Organisms",
    "02. Organisation of the Organism (Cell Structure)",
    "03. Movement In and Out of Cells",
    "04. Biological Molecules",
    "05. Enzymes",
    "06. Plant Nutrition",
    "07. Human Nutrition",
    "08. Transport in Plants",
    "09. Transport in Animals",
    "10. Diseases and Immunity",
    "11. Gas Exchange in Humans",
    "12. Respiration",
    "13. Excretion in Humans",
    "14. Coordination and Response",
    "15. Drugs",
    "16. Reproduction",
    "17. Inheritance",
    "18. Variation and Selection",
    "19. Organisms and Their Environment",
    "20. Biotechnology and Genetic Modification",
    "21. Human Influences on Ecosystems"
]

# State initialization
for key in ["authenticated", "drill_active", "show_feedback", "show_summary"]:
    if key not in st.session_state: st.session_state[key] = False
for key in ["seen_question_ids"]:
    if key not in st.session_state: st.session_state[key] = []
for key in ["question_count", "correct_count"]:
    if key not in st.session_state: st.session_state[key] = 0
if "current_question" not in st.session_state: st.session_state.current_question = None

if not st.session_state.authenticated:
    st.markdown('<div class="main-header" style="text-align: center;">🧬 BioMastery IGCSE Portal</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        email_in = st.text_input("Candidate Email:")
        name_in = st.text_input("Candidate Name:")
        if st.button("Launch Portal", type="primary", use_container_width=True):
            if email_in and name_in:
                st.session_state.student_email = email_in.strip().lower()
                st.session_state.student_name = name_in.strip()
                st.session_state.authenticated = True
                st.rerun()
    st.stop()

st.sidebar.title("🧬 BioMastery IGCSE")
st.sidebar.caption(f"👤 **{st.session_state.student_name}**")
if st.sidebar.button("🚪 Sign Out"):
    st.session_state.clear()
    st.rerun()

menu = st.sidebar.radio("Navigation", ["🎯 Exam Drill", "🏆 Leaderboard"])

if menu == "🏆 Leaderboard":
    st.header("🏆 Student Leaderboard")
    lb_data = get_leaderboard()
    if lb_data:
        st.dataframe(pd.DataFrame(lb_data, columns=["Name", "Marks", "Attempted", "Accuracy %"]), use_container_width=True)

elif menu == "🎯 Exam Drill":
    if not st.session_state.drill_active and not st.session_state.show_summary:
        st.subheader("Configure Session")
        sel_paper = st.selectbox("Paper Focus:", [
            "Paper 2 (Multiple Choice)", 
            "Paper 4 (Theory & Data Analysis)",
            "Paper 6 (Alternative to Practical)"
        ])
        sel_topic = st.selectbox("Chapter:", CAMBRIDGE_SYLLABUS)
        if st.button("Start Drill", type="primary"):
            st.session_state.selected_paper = sel_paper
            st.session_state.selected_topic = sel_topic
            st.session_state.drill_active = True
            st.session_state.question_count = 0
            st.session_state.correct_count = 0
            st.session_state.seen_question_ids = []
            st.session_state.current_question = None
            st.rerun()

    elif st.session_state.show_summary:
        st.header("📊 Performance Summary")
        st.metric("Total Score", f"{st.session_state.correct_count} / {st.session_state.question_count}")
        if st.button("New Drill"):
            st.session_state.drill_active = False
            st.session_state.show_summary = False
            st.rerun()

    else:
        if st.session_state.current_question is None:
            q = get_high_yield_question(st.session_state.selected_paper, st.session_state.selected_topic, st.session_state.seen_question_ids)
            st.session_state.current_question = q
            st.session_state.seen_question_ids.append(q["id"])
            st.session_state.start_time = time.time()
            st.session_state.show_feedback = False
            st.rerun()

        q = st.session_state.current_question
        is_mcq = "options" in q

        st.markdown(f"**Q{st.session_state.question_count + 1}** | Score: {st.session_state.correct_count}")
        st.markdown(f'<div class="question-box">{q["question"]}</div>', unsafe_allow_html=True)

        if is_mcq:
            sel_opt = st.radio("Select Option:", q["options"], disabled=st.session_state.show_feedback)
            if not st.session_state.show_feedback:
                if st.button("Submit Answer", type="primary"):
                    st.session_state.time_taken = time.time() - st.session_state.start_time
                    st.session_state.is_correct = (q["options"].index(sel_opt) == q["correct_index"])
                    st.session_state.show_feedback = True
                    st.rerun()
            else:
                if st.session_state.is_correct:
                    st.markdown(f'<div class="examiner-box-success">✅ Correct. Time taken: {int(st.session_state.time_taken)}s<br><br><b>Examiner Note:</b> {q.get("examiner_note", "")}</div>', unsafe_allow_html=True)
                    if st.session_state.time_taken <= q.get("allowed_time_seconds", 60):
                        st.session_state.correct_count += 1
                else:
                    st.markdown(f'<div class="examiner-box-error">❌ Incorrect.<br><br><b>Correct Answer:</b> {q["options"][q["correct_index"]]}<br><br><b>Examiner Note:</b> {q.get("examiner_note", "")}</div>', unsafe_allow_html=True)

        else:
            written_ans = st.text_area("Your Answer:", disabled=st.session_state.show_feedback, height=150)
            if not st.session_state.show_feedback:
                if st.button("Submit to AI Examiner", type="primary"):
                    if written_ans.strip():
                        st.session_state.time_taken = time.time() - st.session_state.start_time
                        st.session_state.eval_result = evaluate_written_answer_fast(q, written_ans)
                        st.session_state.show_feedback = True
                        st.rerun()
                    else:
                        st.warning("Please enter an answer.")
            else:
                res = st.session_state.eval_result
                sc = res["score_awarded"]
                box_class = "examiner-box-success" if sc > 0 else "examiner-box-error"
                
                st.markdown(f'<div class="{box_class}"><b>Marks Awarded: {sc}/{q.get("marks", 3)}</b><br><br>{res["examiner_feedback"]}</div>', unsafe_allow_html=True)
                
                st.markdown("### Cambridge Model Answer")
                st.info(q.get("model_answer", ""))
                
                st.markdown("### Keyword Checklist")
                pills = "".join([f'<span class="keyword-pill-matched">✓ {k}</span>' for k in res["matched_keywords"]])
                pills += "".join([f'<span class="keyword-pill-missing">✗ {k}</span>' for k in res["missing_keywords"]])
                st.markdown(pills, unsafe_allow_html=True)
                
                if st.session_state.time_taken <= q.get("allowed_time_seconds", 180):
                     st.session_state.correct_count += sc

        if st.session_state.show_feedback:
            st.write("")
            st.session_state.question_count += 1
            log_score(st.session_state.student_email, st.session_state.student_name, st.session_state.selected_topic, st.session_state.is_correct if is_mcq else sc)
            
            c1, c2 = st.columns(2)
            if c1.button("Next Question ➔", type="primary"):
                st.session_state.current_question = None
                st.session_state.show_feedback = False
                st.rerun()
            if c2.button("End Session"):
                st.session_state.drill_active = False
                st.session_state.show_summary = True
                st.rerun()
