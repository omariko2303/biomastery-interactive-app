import json
import random

def get_high_yield_question(paper_focus, topic, seen_ids=None):
    """Fetches a non-repeating question from the bank."""
    if seen_ids is None:
        seen_ids = []

    try:
        with open("questions_bank.json", "r") as f:
            bank = json.load(f)
            
        # Filter by paper, topic, and unseen IDs
        filtered = [q for q in bank if q.get("paper") == paper_focus 
                    and q.get("topic") == topic 
                    and q.get("id") not in seen_ids]
        
        # Fallback 1: Any unseen question in the same paper
        if not filtered:
            filtered = [q for q in bank if q.get("paper") == paper_focus 
                        and q.get("id") not in seen_ids]
            
        # Fallback 2: Reset pool if all questions in the bank have been seen
        if not filtered:
            filtered = [q for q in bank if q.get("paper") == paper_focus]

        if filtered:
            return random.choice(filtered)
            
        return random.choice(bank)
        
    except Exception:
        # Fallback dynamic mock if file isn't populated yet
        mock_id = f"Q_{random.randint(1000, 9999)}"
        return {
            "id": mock_id,
            "paper": paper_focus,
            "topic": topic,
            "question": f"Explain the function of structure X in {topic} (Sample #{random.randint(1, 100)}).",
            "marks": 3,
            "model_answer": "Standard Cambridge mark scheme answer points.",
            "keywords": ["membrane", "energy", "diffusion"],
            "reject_terms": []
        }
