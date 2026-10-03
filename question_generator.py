import google.generativeai as genai
import json
import re

def generate_single_question(api_keys, paper_type, topic):
    """
    Generates paper-appropriate questions:
    - Paper 2: Multiple Choice Options
    - Paper 4 & Paper 6: Open-ended Written Questions evaluated against mark scheme keywords.
    """
    if isinstance(api_keys, str):
        api_keys = [k.strip() for k in api_keys.split(",") if k.strip()]

    if not api_keys:
        raise ValueError("No Gemini API keys provided in Secrets!")

    is_mcq = "Paper 2" in paper_type

    prompt = f"""You are a Senior Cambridge IGCSE / O Level Biology (0610 / 0970) Chief Examiner.
Generate 1 professional-grade practice question for:
- Paper Type: {paper_type}
- Syllabus Topic: {topic}

CRITICAL FORMATTING INSTRUCTIONS:
1. Format Type: {"MULTIPLE_CHOICE" if is_mcq else "WRITTEN_RESPONSE"}
2. For Paper 2 (Multiple Choice): Provide 4 distinct options (A, B, C, D) with 1 correct index.
3. For Paper 4 & Paper 6 (Written Response): Set options to empty list `[]` and correct_index to -1. Create a structured theory/practical question requiring student text input.
4. Dynamically assign `allowed_time_seconds` based on length and paper complexity (40-60s for Paper 2, 70-120s for Paper 4/6).

Return STRICTLY a valid JSON object matching this schema:
{{
  "id": "Q_GEN",
  "paper_type": "{paper_type}",
  "question_format": "{"MULTIPLE_CHOICE" if is_mcq else "WRITTEN_RESPONSE"}",
  "syllabus_code": "0610/X.X",
  "topic": "{topic}",
  "command_word": "Command Word (e.g., Describe / Explain / Suggest / State)",
  "question": "Question text here...",
  "options": {"[\"A) option 1\", \"B) option 2\", \"C) option 3\", \"D) option 4\"]" if is_mcq else "[]"},
  "correct_index": {0 if is_mcq else -1},
  "allowed_time_seconds": 60,
  "difficulty_level": "Core / Extended / Challenge",
  "keywords": ["mandatory keyword 1", "mandatory keyword 2", "mandatory keyword 3"],
  "model_answer": "Complete 100% mark-scheme ideal answer",
  "examiner_note": "Cambridge examiner report breakdown highlighting key trigger terms and common candidate mistakes."
}}
"""

    last_exception = None

    for index, raw_key in enumerate(api_keys):
        key = raw_key.strip().strip('"').strip("'")
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                "gemini-3.8-flash", 
                generation_config={"temperature": 0.1, "top_p": 0.95}
            )
            response = model.generate_content(prompt)
            raw_text = response.text.strip()

            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            try:
                return json.loads(raw_text.strip())
            except Exception:
                json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))

        except Exception as e:
            last_exception = e
            print(f"[API Rotation] Key #{index + 1} failed: {e}. Switching to next key...")
            continue

    raise RuntimeError(f"All API keys exhausted. Last error: {last_exception}")


def evaluate_written_answer(api_keys, question_data, student_answer):
    """
    Uses Gemini to mark written answers for Paper 4 and Paper 6 against the Cambridge Mark Scheme.
    """
    if isinstance(api_keys, str):
        api_keys = [k.strip() for k in api_keys.split(",") if k.strip()]

    prompt = f"""You are a Cambridge IGCSE Biology Chief Examiner marking a Paper 4 / Paper 6 written response.

QUESTION: {question_data['question']}
MANDATORY KEYWORDS: {question_data['keywords']}
MODEL MARK SCHEME: {question_data['model_answer']}

STUDENT WRITTEN RESPONSE: "{student_answer}"

Evaluate the student's answer strictly according to Cambridge mark scheme criteria.
Return STRICTLY a JSON object matching this schema:
{{
  "score_awarded": 1, // 1 for full marks/pass, 0 for mark loss
  "matched_keywords": ["keyword found 1", "keyword found 2"],
  "missing_keywords": ["keyword missed 1"],
  "examiner_feedback": "Detailed 2-3 sentence constructive feedback explaining what was correct, missing trigger words, or invalid phrasing."
}}
"""

    for key in api_keys:
        try:
            genai.configure(api_key=key.strip().strip('"').strip("'"))
            model = genai.GenerativeModel("gemini-3.8-flash", generation_config={"temperature": 0.1})
            response = model.generate_content(prompt)
            raw_text = response.text.strip()

            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            return json.loads(raw_text.strip())
        except Exception:
            continue

    return {
        "score_awarded": 0,
        "matched_keywords": [],
        "missing_keywords": question_data['keywords'],
        "examiner_feedback": "Evaluation complete. Ensure all mandatory keywords are explicitly stated."
    }
