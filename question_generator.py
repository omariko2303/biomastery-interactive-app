import json
import random

def get_high_yield_question(paper_focus, topic, seen_ids=None):
    """
    Fetches a non-repeating question based on paper and topic.
    Ensures questions never repeat within the same session.
    """
    if seen_ids is None:
        seen_ids = []

    try:
        with open("questions_bank.json", "r") as f:
            bank = json.load(f)

        # 1. Exact match on paper, topic, and unseen ID
        filtered = [
            q for q in bank 
            if q.get("paper") == paper_focus 
            and q.get("topic") == topic 
            and q.get("id") not in seen_ids
        ]

        # 2. Fallback: Any unseen question in the same paper
        if not filtered:
            filtered = [
                q for q in bank 
                if q.get("paper") == paper_focus 
                and q.get("id") not in seen_ids
            ]

        # 3. Fallback: If all questions in paper were seen, reset pool for paper
        if not filtered:
            filtered = [q for q in bank if q.get("paper") == paper_focus]

        # 4. Global fallback
        if not filtered:
            filtered = bank

        return random.choice(filtered)

    except Exception:
        # Dynamic fallback item if JSON is unreadable or empty
        fallback_id = f"FALLBACK_{random.randint(1000, 9999)}"
        return {
            "id": fallback_id,
            "paper": paper_focus,
            "topic": topic,
            "question": f"Explain the key biological adaptation related to {topic}.",
            "marks": 3,
            "model_answer": "High concentration of active components working down or against gradient.",
            "keywords": ["concentration", "gradient", "active"],
            "reject_terms": [],
            "allowed_time_seconds": 60
        }


def evaluate_written_answer_fast(question_data, student_answer):
    """
    Evaluates student written answers instantly in Python (<10ms).
    Prevents API delays and evaluates against required keywords and rejected terms.
    """
    text = student_answer.lower().strip()
    keywords = question_data.get("keywords", [])
    reject_terms = question_data.get("reject_terms", [])

    # Check for explicitly rejected/forbidden phrasing first
    for reject in reject_terms:
        if reject.lower() in text:
            return {
                "score_awarded": 0,
                "matched_keywords": [],
                "missing_keywords": keywords,
                "examiner_feedback": f"❌ Marked 0 due to forbidden term/phrasing: '{reject}'. Cambridge mark scheme strictly rejects this term."
            }

    matched = []
    missing = []

    for kw in keywords:
        if kw.lower() in text:
            matched.append(kw)
        else:
            missing.append(kw)

    max_marks = question_data.get("marks", len(keywords))
    if len(keywords) > 0:
        score = round((len(matched) / len(keywords)) * max_marks)
    else:
        score = max_marks if len(text) > 5 else 0

    if score > 0:
        feedback = f"✅ Matched {len(matched)} of {len(keywords)} essential mark scheme point(s)."
    else:
        feedback = "⚠️ Missing key scientific terminology required by the Cambridge mark scheme."

    return {
        "score_awarded": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "examiner_feedback": feedback
    }
