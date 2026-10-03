import json
import random
import google.generativeai as genai

def get_high_yield_question(paper_focus, topic):
    """
    Retrieves 100% accurate, pre-curated exam questions from local JSON repository.
    """
    try:
        with open("questions_bank.json", "r") as f:
            bank = json.load(f)
            
        # Filter by paper and topic
        filtered = [
            q for q in bank 
            if q.get("paper") == paper_focus and q.get("topic") == topic
        ]
        
        if filtered:
            return random.choice(filtered)
        
        # Fallback to any question matching the paper
        paper_filtered = [q for q in bank if q.get("paper") == paper_focus]
        if paper_filtered:
            return random.choice(paper_filtered)
            
        return random.choice(bank)
    except Exception:
        # Fallback question if file is missing or reading fails
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

def evaluate_written_answer(api_key, question_data, student_answer):
    """
    Evaluates written answers using strict mark scheme criteria.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    You are a Senior Cambridge IGCSE Biology Examiner (0610).
    
    QUESTION: {question_data['question']}
    MODEL ANSWER / MARK SCHEME: {question_data.get('model_answer')}
    REQUIRED KEYWORDS: {question_data.get('keywords', [])}
    REJECT TERMS: {question_data.get('reject_terms', [])}
    
    STUDENT ANSWER: "{student_answer}"
    
    Evaluate strictly according to Cambridge mark schemes:
    1. Check for accurate scientific terminology.
    2. Reject vague terms like "makes energy" (must be "releases energy") or "attracts light".
    
    Return a valid JSON object ONLY:
    {{
        "score_awarded": 1 or 0,
        "matched_keywords": ["kw1", "kw2"],
        "missing_keywords": ["kw3"],
        "examiner_feedback": "Detailed Cambridge examiner comment on mark scheme alignment."
    }}
    """
    
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    return json.loads(response.text)
