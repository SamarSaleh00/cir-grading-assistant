"""
- Gemini client + retry wrapper (shared across the whole project).
- MCQ grading: deterministic exact-match, no LLM/retrieval.
- Written-question grading: retrieval-grounded LLM judgment per criterion.
"""

import json
import time
import os
from google import genai
from src.retriever import retrieve

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

DEFAULT_MODEL = "gemini-flash-lite-latest"  # higher free-tier quota; swap to
                                             # "gemini-flash-latest" for higher quality if quota allows


def call_gemini_with_retry(model, contents, config=None, max_retries=4, base_delay=5):
    """
    Wraps client.models.generate_content with retry logic for transient
    server errors (503 UNAVAILABLE, 429 rate limit / RESOURCE_EXHAUSTED).
    `config` is optional (used for system_instruction/tools in chat_agent.py).
    """
    for attempt in range(max_retries):
        try:
            if config is not None:
                return client.models.generate_content(model=model, contents=contents, config=config)
            return client.models.generate_content(model=model, contents=contents)
        except Exception as e:
            error_str = str(e)
            transient = any(code in error_str for code in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"])
            if transient and attempt < max_retries - 1:
                delay = base_delay * (attempt + 1)
                print(f"  Transient error, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError(f"Failed after {max_retries} retries due to repeated transient errors.")


def _strip_json_fences(raw_text):
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()
    return raw_text


# ---------------- MCQ grading (no LLM, no retrieval) ----------------

def format_mcq_feedback(mcq_results):
    """Builds a readable per-question feedback string from grade_mcq_section results."""
    lines = []
    for r in mcq_results:
        if r["is_correct"]:
            lines.append(f"{r['id']}: correct")
        else:
            lines.append(f"{r['id']}: incorrect (chose {r['student_choice']}, correct is {r['correct_answer']})")
    return "\n".join(lines)


def grade_mcq_section(mcq_questions, student_answers):
    """
    mcq_questions: list of {"id", "correct", "points"}
    student_answers: dict mapping question id -> chosen letter
    Returns: {"mcq_results": [...], "mcq_total": float, "mcq_max": float}
    """
    results = []
    total_score = 0
    max_total = 0

    for q in mcq_questions:
        qid, correct, points = q["id"], q["correct"], q["points"]
        student_choice = student_answers.get(qid)
        is_correct = (student_choice == correct)
        score = points if is_correct else 0

        results.append({
            "id": qid, "student_choice": student_choice, "correct_answer": correct,
            "is_correct": is_correct, "score": score, "max_points": points
        })
        total_score += score
        max_total += points

    return {"mcq_results": results, "mcq_total": total_score, "mcq_max": max_total}


# ---------------- Written-question grading (retrieval + LLM) ----------------

GRADE_PROMPT = """You are grading a student's exam/assignment answer based on a specific grading criterion, using evidence retrieved from the course material (NOT a fixed key answer).

Grading criterion: {criterion_description}
Maximum points for this criterion: {max_points}

Relevant course material evidence (retrieved by semantic search):
\"\"\"
{evidence_text}
\"\"\"

Student's answer (full submission, judge only the parts relevant to this criterion):
\"\"\"
{student_answer}
\"\"\"

Judge whether the student's answer satisfies this specific criterion, using the course material evidence as your ground truth for what's correct. Partial credit is allowed (e.g., 1.5 out of 2) if the student partially addresses the criterion.

Return ONLY valid JSON, no markdown, no explanation outside the JSON:
{{
  "score": <number, between 0 and {max_points}>,
  "feedback": "<one concise sentence explaining the score>"
}}
"""


def grade_criterion(criterion, student_answer, index, chunks, k=3, model=DEFAULT_MODEL):
    """Grades one rubric criterion against the student's answer using retrieved evidence."""
    query = criterion["description"]
    retrieved = retrieve(query, index, chunks, k=k)

    evidence_text = "\n\n".join(
        f"[{r['chunk']['source_file']}, page(s) {r['chunk']['pages']}]\n{r['chunk']['text']}"
        for r in retrieved
    ) or "(no relevant course material found)"

    prompt = GRADE_PROMPT.format(
        criterion_description=criterion["description"],
        max_points=criterion["max_points"],
        evidence_text=evidence_text,
        student_answer=student_answer
    )

    response = call_gemini_with_retry(model, prompt)
    raw_text = _strip_json_fences(response.text)

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print("Failed to parse grading JSON. Raw output:")
        print(raw_text)
        raise e

    return {
        "id": criterion["id"],
        "description": criterion["description"],
        "max_points": criterion["max_points"],
        "score": result["score"],
        "feedback": result["feedback"],
        "evidence_used": [(r["chunk"]["source_file"], r["chunk"]["pages"]) for r in retrieved]
    }


def grade_question(criteria, student_answer, index, chunks, k=3, model=DEFAULT_MODEL):
    """Grades every criterion for one question, returns per-criterion results + total."""
    results = []
    for criterion in criteria:
        results.append(grade_criterion(criterion, student_answer, index, chunks, k=k, model=model))
        time.sleep(2)  # pacing delay to help stay under per-minute quotas

    total_score = sum(r["score"] for r in results)
    max_total = sum(r["max_points"] for r in results)
    feedback_lines = [f"Criterion {r['id']} ({r['score']}/{r['max_points']}): {r['feedback']}" for r in results]

    return {
        "criteria_results": results,
        "total_score": total_score,
        "max_total": max_total,
        "feedback_summary": "\n".join(feedback_lines)
    }