import google.generativeai as genai
import json
import re

def generate_cambridge_questions(api_key, paper_type, topic, num_questions=3):
    """
    Generates authentic Cambridge IGCSE / O Level Biology (0610 / 0970) questions
    in strict JSON format using Gemini 3.8-Flash.
    """
    if not api_key:
        raise ValueError("Gemini API Key is missing!")

    genai.configure(api_key=api_key.strip().strip('"').strip("'"))
    
    generation_config = {
        "temperature": 0.2, # Low temperature for strict exam factual consistency
        "top_p": 0.95
    }
    
    model = genai.GenerativeModel("gemini-3.8-flash", generation_config=generation_config)

    paper_guidelines = {
        "Paper 2 (Multiple Choice Core/Extended)": "Focus on precise definition traps, distractor choices where 1 word causes mark loss, and core concepts.",
        "Paper 4 (Theory & Data Analysis)": "Focus on Command Words ('Describe' vs 'Explain'), graph trend analysis, and compulsory mark scheme keyword alignment.",
        "Paper 6 (Alternative to Practical)": "Focus on experimental procedures, variables (independent, dependent, controlled), sources of error, drawing rules, and indicator tests (Benedict's, Biuret, Iodine, DCPIP)."
    }

    prompt = f"""You are a Senior Cambridge IGCSE / O Level Biology (0610 / 0970) Chief Examiner.
Generate exactly {num_questions} professional-grade practice questions for:
- Paper Type: {paper_type}
- Syllabus Topic: {topic}
- Specific Focus: {paper_guidelines.get(paper_type, "Cambridge Syllabus Alignment")}

CRITICAL REQUIREMENTS:
1. Return strictly valid JSON array without any markdown formatting wrappers or extra text.
2. Every question MUST highlight exact Cambridge Mark Scheme traps and mandatory keywords.

JSON Output Schema:
[
  {{
    "id": "Q1",
    "syllabus_code": "0610/X.X",
    "topic": "{topic}",
    "command_word": "Command Word (e.g., Describe / Explain / Identify)",
    "question": "Question text here...",
    "options": [
      "A) Option A text",
      "B) Option B text",
      "C) Option C text",
      "D) Option D text"
    ],
    "correct_index": 0,
    "keywords": ["mandatory keyword 1", "mandatory keyword 2", "mandatory keyword 3"],
    "examiner_note": "Detailed Cambridge examiner report breakdown explaining WHY the correct option wins and why distractors lose marks."
  }}
]
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Clean potential markdown wrapping around JSON
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    try:
        data = json.loads(raw_text.strip())
        return data
    except Exception as e:
        # Fallback regex extraction if model adds trailing characters
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        raise ValueError(f"Failed to parse AI generated questions JSON: {e}\nRaw Output: {raw_text}")
