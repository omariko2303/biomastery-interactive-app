import json
import random

def get_high_yield_question(paper_focus, topic):
    """Retrieves pre-curated exam questions from local JSON repository."""
    try:
        with open("questions_bank.json", "r") as f:
            bank = json.load(f)
            
        filtered = [q for q in bank if q.get("paper") == paper_focus and q.get("topic") == topic]
        if filtered:
            return random.choice(filtered)
            
        paper_filtered = [q for q in bank if q.get("paper") == paper_focus]
        if paper_filtered:
            return random.choice(paper_filtered)
            
        return random.choice(bank)
    except Exception:
        return {
            "id": "P4_FALLBACK",
            "paper": paper_focus,
            "topic": topic,
            "question": "Define active transport and state one example in human digestion.",
            "marks": 3,
            "model_answer": "Movement of particles through a cell membrane from lower concentration to higher concentration against a concentration gradient using energy from respiration.",
            "keywords": ["against concentration gradient", "cell membrane", "energy", "respiration"],
            "reject_terms": []
        }

def evaluate_written_answer_fast(question_data, student_answer):
    """
    Instantly evaluates student written answers locally against mark scheme keywords.
    Completes in under 10ms without API latency.
    """
    text = student_answer.lower().strip()
    keywords = question_data.get("keywords", [])
    reject_terms = question_data.get("reject_terms", [])
    
    matched = []
    missing = []
    
    # Check for forbidden/rejected phrasing
    for reject in reject_terms:
        if reject.lower() in text:
            return {
                "score_awarded": 0,
                "matched_keywords": [],
                "missing_keywords": keywords,
                "examiner_feedback": f"❌ Rejected term used ('{reject}'). Cambridge mark scheme explicitly forbids this phrasing."
            }
            
    # Check for required keywords
    for kw in keywords:
        if kw.lower() in text:
            matched.append(kw)
        else:
            missing.append(kw)
            
    # Calculate mark allocation
    max_marks = question_data.get("marks", len(keywords))
    if len(keywords) > 0:
        score = round((len(matched) / len(keywords)) * max_marks)
    else:
        score = max_marks if len(text) > 5 else 0

    if score > 0:
        feedback = f"✅ Matched {len(matched)} of {len(keywords)} required mark scheme point(s)."
    else:
        feedback = "⚠️ Missing key scientific terms required by the Cambridge mark scheme."

    return {
        "score_awarded": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "examiner_feedback": feedback
    }
