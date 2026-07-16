"""
Converts free-form rubric text (any phrasing style) into structured JSON criteria.
"""

import json
from src.grader import call_gemini_with_retry, DEFAULT_MODEL

RUBRIC_PARSE_PROMPT = """You are a grading assistant. A lecturer has provided rubric text describing how to grade a student's answer to a question. This text may be written in any format — a list, a paragraph, shorthand notation, etc.

Your task: extract the grading criteria as a structured JSON list. Each criterion should have:
- "id": a short identifier (e.g., "c1", "c2", ...)
- "description": a clear restatement of what the student must demonstrate to earn these points
- "max_points": the numeric point value for this criterion

Rules:
- If the rubric doesn't explicitly state points for a criterion, infer a reasonable point value so that the total adds up sensibly, but prefer explicit points when given.
- Do not invent criteria that aren't implied by the text.
- Return ONLY valid JSON — no markdown formatting, no explanation, no code fences. Just the raw JSON array.

Rubric text:
\"\"\"
{rubric_text}
\"\"\"

Return the JSON array now.
"""


def _strip_json_fences(raw_text):
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()
    return raw_text


def parse_rubric(rubric_text, model=DEFAULT_MODEL):
    """Returns a list of {"id", "description", "max_points"} dicts."""
    prompt = RUBRIC_PARSE_PROMPT.format(rubric_text=rubric_text)
    response = call_gemini_with_retry(model, prompt)
    raw_text = _strip_json_fences(response.text)

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print("Failed to parse rubric JSON. Raw output:")
        print(raw_text)
        raise e