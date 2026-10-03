import json
import random
import re

def get_high_yield_question(paper_focus, topic, seen_ids=None):
    if seen_ids is None:
        seen_ids = []

    try:
        with open("questions_bank.json", "r") as f:
            bank = json.load(f)

        filtered = [q for q in bank if q.get("paper") == paper_focus and q.get("topic") == topic and q.get("id") not in seen_ids]
        if not filtered:
            filtered = [q for q in bank if q.get("paper") == paper_focus and q.get("id") not in seen_ids]
        if not filtered:
            filtered = [q for q in bank if q.get("paper") == paper_focus]

        if filtered:
            return random.choice(filtered)
            
    except Exception:
        pass 

    # --- STRICT FALLBACK GENERATION ---
    is_p2 = "Paper 2" in paper_focus
    is_p6 = "Paper 6" in paper_focus
    
    mock_id = f"FALLBACK_{random.randint(1000, 9999)}"
    
    if is_p2:
        return {
            "id": mock_id,
            "paper": paper_focus,
            "topic": topic,
            "question": f"Which of the following is a fundamental characteristic related to {topic}?",
            "options": [
                "A distractor based on a common student misconception.",
                "The correct statement derived directly from the syllabus.",
                "An incorrect statement describing a different biological process.",
                "A physically impossible biological phenomenon."
            ],
            "correct_index": 1,
            "examiner_note": "This option is correct because it perfectly aligns with the Cambridge definitions for this specific topic.",
            "allowed_time_seconds": 45
        }
    elif is_p6:
        # Paper 6 focuses on Alternative to Practical (variables, sources of error, graphs, tests)
        return {
            "id": mock_id,
            "paper": paper_focus,
            "topic": topic,
            "question": f"A student investigates a biological process related to {topic}. State the independent variable and describe how they should maintain safety during this experiment. [3]",
            "marks": 3,
            "model_answer": "1. Identify the specific variable being changed (e.g., temperature/pH). 2. Wear safety goggles to protect eyes from reagents. 3. Use tongs/water bath when handling hot apparatus.",
            "keywords": ["variable", "goggles", "safety", "temperature", "pH", "water bath"],
            "reject_terms": ["be careful", "don't spill"],
            "allowed_time_seconds": 120
        }
    else:
        # Paper 4 focuses on detailed theory and explanation
        return {
            "id": mock_id,
            "paper": paper_focus,
            "topic": topic,
            "question": f"Describe and explain the biological mechanisms underlying {topic}. [4]",
            "marks": 4,
            "model_answer": "A detailed explanation involving structural adaptations, the movement of substances down a gradient, and the specific enzymes or biological molecules involved.",
            "keywords": ["gradient", "adaptation", "enzymes", "molecules", "structure"],
            "reject_terms": ["magic", "just happens"],
            "allowed_time_seconds": 180
        }

def evaluate_written_answer_fast(question_data, student_answer):
    text = student_answer.lower().strip()
    keywords = question_data.get("keywords", [])
    reject_terms = question_data.get("reject_terms", [])

    for reject in reject_terms:
        if re.search(r'\b' + re.escape(reject.lower()) + r'\b', text):
            return {
                "score_awarded": 0,
                "matched_keywords": [],
                "missing_keywords": keywords,
                "examiner_feedback": f"❌ Marked 0 due to forbidden term: '{reject}'. Cambridge examiners specifically penalize this phrasing."
            }

    matched, missing = [], []
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text) or kw.lower() in text:
            matched.append(kw)
        else:
            missing.append(kw)

    max_marks = question_data.get("marks", len(keywords))
    score = round((len(matched) / len(keywords)) * max_marks) if keywords else (max_marks if len(text) > 10 else 0)

    feedback = f"✅ Matched {len(matched)} of {len(keywords)} essential mark scheme point(s)." if score > 0 else "⚠️ Missing key scientific terminology."

    return {
        "score_awarded": min(score, max_marks),
        "matched_keywords": matched,
        "missing_keywords": missing,
        "examiner_feedback": feedback
    }
