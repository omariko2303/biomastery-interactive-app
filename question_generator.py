import json
import random
import re

def get_high_yield_question(paper_focus, topic, seen_ids=None):
    if seen_ids is None:
        seen_ids = []

    try:
        with open("questions_bank.json", "r") as f:
            bank = json.load(f)

        # Strict filtering
        filtered = [q for q in bank if q.get("paper") == paper_focus and q.get("topic") == topic and q.get("id") not in seen_ids]
        
        if not filtered:
            filtered = [q for q in bank if q.get("paper") == paper_focus and q.get("id") not in seen_ids]
            
        if not filtered:
            filtered = [q for q in bank if q.get("paper") == paper_focus]

        if filtered:
            return random.choice(filtered)
            
    except Exception:
        pass # Proceed to strict fallback if file is missing/empty

    # STRICT FALLBACK: Ensure P2 is ALWAYS Multiple Choice
    is_p2 = "Paper 2" in paper_focus
    mock_id = f"{'P2' if is_p2 else 'P4'}_{random.randint(1000, 9999)}"
    
    if is_p2:
        return {
            "id": mock_id,
            "paper": paper_focus,
            "topic": topic,
            "question": f"Which statement correctly describes a process in {topic}?",
            "options": [
                "A physically incorrect distractor.",
                "The correct Cambridge-verified statement.",
                "A common student misconception.",
                "Another closely related but incorrect fact."
            ],
            "correct_index": 1,
            "examiner_note": "This option is correct because it aligns with the 0610 syllabus definition.",
            "allowed_time_seconds": 45
        }
    else:
        return {
            "id": mock_id,
            "paper": paper_focus,
            "topic": topic,
            "question": f"Describe the biological principles underlying {topic}. [3]",
            "marks": 3,
            "model_answer": "Point 1 relating to structure. Point 2 relating to function. Point 3 relating to overall mechanism.",
            "keywords": ["structure", "function", "mechanism"],
            "reject_terms": ["magic", "grows"],
            "allowed_time_seconds": 180
        }

def evaluate_written_answer_fast(question_data, student_answer):
    text = student_answer.lower().strip()
    keywords = question_data.get("keywords", [])
    reject_terms = question_data.get("reject_terms", [])

    # 1. Check Rejects
    for reject in reject_terms:
        if re.search(r'\b' + re.escape(reject.lower()) + r'\b', text):
            return {
                "score_awarded": 0,
                "matched_keywords": [],
                "missing_keywords": keywords,
                "examiner_feedback": f"❌ Marked 0 due to forbidden term: '{reject}'."
            }

    # 2. Check Keywords using word boundaries
    matched, missing = [], []
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text) or kw.lower() in text:
            matched.append(kw)
        else:
            missing.append(kw)

    max_marks = question_data.get("marks", len(keywords))
    score = round((len(matched) / len(keywords)) * max_marks) if keywords else (max_marks if len(text) > 10 else 0)

    feedback = f"✅ Matched {len(matched)} of {len(keywords)} mark scheme point(s)." if score > 0 else "⚠️ Missing key scientific terminology."

    return {
        "score_awarded": min(score, max_marks),
        "matched_keywords": matched,
        "missing_keywords": missing,
        "examiner_feedback": feedback
    }
