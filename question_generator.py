import google.generativeai as genai
import json
import re

def generate_single_question(api_keys, paper_type, topic):
    """
    Tries multiple Gemini API keys in sequence until one succeeds.
    Automatically fails over if a quota (429) or rate limit is reached.
    """
    if isinstance(api_keys, str):
        api_keys = [k.strip() for k in api_keys.split(",") if k.strip()]

    if not api_keys:
        raise ValueError("No Gemini API keys provided in Secrets!")

    paper_specs = {
        "Paper 2 (Multiple Choice)": "Focus on precise keyword definitions, distractor choice traps, and core biological concepts.",
        "Paper 4 (Theory & Data Analysis)": "Focus on Command Words ('Describe' vs 'Explain'), graph/data interpretation, and compulsory mark scheme keywords.",
        "Paper 6 (Alternative to Practical)": "Focus on experimental procedures, variables, drawing rules, and indicator tests (Benedict's, Biuret, Iodine, DCPIP)."
    }

    prompt = f"""You are a Senior Cambridge IGCSE / O Level Biology (0610 / 0970) Chief Examiner.
Generate 1 professional-grade practice question for:
- Paper Type: {paper_type}
- Syllabus Topic: {topic}
- Focus: {paper_specs.get(paper_type, "Cambridge Syllabus Alignment")}

CRITICAL TIMING & EVALUATION INSTRUCTIONS:
1. Assess the question difficulty and length.
2. Dynamically assign a strict time limit in seconds (`allowed_time_seconds`):
   - Simple Paper 2 questions: 40 to 60 seconds.
   - Medium Paper 4 or Paper 6 conceptual questions: 60 to 90 seconds.
   - Complex data analysis or multi-step reasoning questions: 90 to 120 seconds.
3. Return STRICTLY a valid JSON object without markdown wrappers or extra text.

JSON Schema:
{{
  "id": "Q_GEN",
  "syllabus_code": "0610/X.X",
  "topic": "{topic}",
  "command_word": "Command Word (e.g., Describe / Explain / Identify / Calculate)",
  "question": "Question text here...",
  "options": [
    "A) Option A text",
    "B) Option B text",
    "C) Option C text",
    "D) Option D text"
  ],
  "correct_index": 0,
  "allowed_time_seconds": 60,
  "difficulty_level": "Core / Extended / Challenge",
  "keywords": ["mandatory keyword 1", "mandatory keyword 2", "mandatory keyword 3"],
  "examiner_note": "Detailed Cambridge examiner report breakdown explaining WHY the correct option wins and why distractors lose marks."
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
