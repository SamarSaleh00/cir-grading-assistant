"""
Conversational layer: lets the lecturer talk naturally. Uses Gemini function
calling to route intents to grading/indexing/gradebook actions, plus an
analytics tool. Each assignment type keeps its own persistent question set,
so switching between assignments never loses previously added questions.
"""

from google.genai import types
from src.grader import client, grade_question, grade_mcq_section, format_mcq_feedback, call_gemini_with_retry, DEFAULT_MODEL
from src.rubric_parser import parse_rubric
from src.gradebook import update_grade, log_feedback, view_gradebook

SYSTEM_INSTRUCTION = """You are a helpful teaching assistant that helps a lecturer grade student work
and analyze grading data. You have tools to: set up assignments, add questions/rubrics, grade students
(written or MCQ), approve or edit pending grades, view the gradebook, record attendance, and answer
analytical questions about the gradebook.

Use the tools whenever the lecturer's message implies one of these actions — don't ask them to use
special commands, just understand natural phrasing. Switching to a different assignment type is safe
and never loses previously added questions for any assignment.

If a tool call reports missing information (e.g. no rubric found), relay that tool's message exactly —
do not invent your own explanation or guess what might be wrong. Always call the tool first; never
describe a problem without having actually called the relevant tool to check.

If the lecturer asks a question ABOUT the data (rankings, comparisons, who did/didn't do something,
averages, etc.) rather than asking you to perform a new grading action, call analyze_gradebook.

After a tool executes, explain the result to the lecturer conversationally."""


def build_tools_config():
    return types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="set_assignment_context",
            description="Switch to grading a given assignment type (e.g. Midterm, Final Exam, Assignment 1). Safe to call anytime — never loses that assignment's previously added questions.",
            parameters={"type": "object", "properties": {"assignment_type": {"type": "string"}}, "required": ["assignment_type"]}
        ),
        types.FunctionDeclaration(
            name="add_written_question",
            description="Add a written/essay question with its grading rubric to the current assignment.",
            parameters={
                "type": "object",
                "properties": {
                    "question_id": {"type": "string"},
                    "question_text": {"type": "string"},
                    "rubric_text": {"type": "string"}
                },
                "required": ["question_id", "question_text", "rubric_text"]
            }
        ),
        types.FunctionDeclaration(
            name="add_mcq_question",
            description="Add a multiple-choice question with its correct answer to the current assignment.",
            parameters={
                "type": "object",
                "properties": {
                    "question_id": {"type": "string"},
                    "correct_answer": {"type": "string"},
                    "points": {"type": "number"}
                },
                "required": ["question_id", "correct_answer", "points"]
            }
        ),
        types.FunctionDeclaration(
            name="grade_student_written",
            description="Grade a student's written answer for a specific question in the current assignment.",
            parameters={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "student_name": {"type": "string"},
                    "question_id": {"type": "string"},
                    "student_answer": {"type": "string"}
                },
                "required": ["student_id", "student_name", "question_id", "student_answer"]
            }
        ),
        types.FunctionDeclaration(
            name="grade_student_mcq",
            description="Grade a student's multiple-choice answers for the current assignment.",
            parameters={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "student_name": {"type": "string"},
                    "answers": {"type": "object", "description": "question_id -> chosen letter"}
                },
                "required": ["student_id", "student_name", "answers"]
            }
        ),
        types.FunctionDeclaration(
            name="approve_pending_grade",
            description="Approve the most recently shown grade result exactly as-is, saving it to the gradebook.",
            parameters={"type": "object", "properties": {}}
        ),
        types.FunctionDeclaration(
            name="edit_pending_grade",
            description="Edit the most recently shown grade result before saving.",
            parameters={
                "type": "object",
                "properties": {"new_score": {"type": "number"}, "new_feedback": {"type": "string"}}
            }
        ),
        types.FunctionDeclaration(
            name="view_gradebook_tool",
            description="Show the current gradebook contents to the lecturer.",
            parameters={"type": "object", "properties": {}}
        ),
        types.FunctionDeclaration(
            name="record_attendance",
            description="Directly record an attendance score for a student.",
            parameters={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "student_name": {"type": "string"},
                    "score": {"type": "number"}
                },
                "required": ["student_id", "student_name", "score"]
            }
        ),
        types.FunctionDeclaration(
            name="analyze_gradebook",
            description="Answer analytical questions about the gradebook data (rankings, comparisons, missing submissions, averages).",
            parameters={
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"]
            }
        ),
    ])


ANALYTICS_PROMPT = """You are analyzing a lecturer's gradebook to answer their question.

Gradebook (wide format — one row per student, one column per assignment type; blank/NaN means
that student has no recorded score for that assignment):

{table}

Lecturer's question: "{question}"

Answer accurately based ONLY on the data above. If a referenced column doesn't exist, say so.
Be concise and specific (name actual students/numbers).
"""


class GradingAssistant:
    def __init__(self, index, chunks, model=DEFAULT_MODEL):
        self.model = model
        self.tools_config = build_tools_config()
        self.chat_history = []
        self.state = {
            "index": index,
            "chunks": chunks,
            "current_assignment": None,
            "assignments": {},   # assignment_type -> {"written_questions": {}, "mcq_questions": {}}
            "pending_grade": None
        }
        self.dispatch = {
            "set_assignment_context": self._set_assignment_context,
            "add_written_question": self._add_written_question,
            "add_mcq_question": self._add_mcq_question,
            "grade_student_written": self._grade_student_written,
            "grade_student_mcq": self._grade_student_mcq,
            "approve_pending_grade": self._approve_pending_grade,
            "edit_pending_grade": self._edit_pending_grade,
            "view_gradebook_tool": self._view_gradebook_tool,
            "record_attendance": self._record_attendance,
            "analyze_gradebook": self._analyze_gradebook,
        }

    def _get_assignment_bucket(self, assignment_type):
        """Returns (creating if needed) the persistent question store for an assignment type."""
        if assignment_type not in self.state["assignments"]:
            self.state["assignments"][assignment_type] = {"written_questions": {}, "mcq_questions": {}}
        return self.state["assignments"][assignment_type]

    def _current_bucket(self):
        at = self.state["current_assignment"]
        if at is None:
            return None
        return self._get_assignment_bucket(at)

    # ---- tool implementations ----

    def _set_assignment_context(self, assignment_type):
        self.state["current_assignment"] = assignment_type
        self._get_assignment_bucket(assignment_type)  # ensure it exists, doesn't wipe if already there
        bucket = self._current_bucket()
        n_written = len(bucket["written_questions"])
        n_mcq = len(bucket["mcq_questions"])
        if n_written or n_mcq:
            return f"Switched to {assignment_type}. It already has {n_mcq} MCQ(s) and {n_written} written question(s) set up."
        return f"Switched to {assignment_type}. No questions added yet."

    def _add_written_question(self, question_id, question_text, rubric_text):
        bucket = self._current_bucket()
        if bucket is None:
            return "No assignment is currently selected. Please specify an assignment type first."
        bucket["written_questions"][question_id] = {"question_text": question_text, "rubric_text": rubric_text}
        return f"Added written question {question_id} to {self.state['current_assignment']}: {question_text}"

    def _add_mcq_question(self, question_id, correct_answer, points):
        bucket = self._current_bucket()
        if bucket is None:
            return "No assignment is currently selected. Please specify an assignment type first."
        bucket["mcq_questions"][question_id] = {"correct_answer": correct_answer, "points": points}
        return f"Added MCQ {question_id} to {self.state['current_assignment']}, correct answer {correct_answer}, {points} points"

    def _grade_student_written(self, student_id, student_name, question_id, student_answer):
        bucket = self._current_bucket()
        if bucket is None or question_id not in bucket["written_questions"]:
            available = list(bucket["written_questions"].keys()) if bucket else []
            return (f"No rubric found for question '{question_id}' under {self.state['current_assignment']}. "
                    f"Available written questions here: {available}. Please add the rubric first.")

        q = bucket["written_questions"][question_id]
        criteria = parse_rubric(q["rubric_text"])
        result = grade_question(criteria, student_answer, self.state["index"], self.state["chunks"])

        self.state["pending_grade"] = {
            "student_id": student_id, "student_name": student_name,
            "assignment_type": f"{self.state['current_assignment']} - {question_id}",
            "score": result["total_score"], "max_score": result["max_total"],
            "feedback": result["feedback_summary"]
        }

        return (f"Graded {student_name}'s answer to {question_id}: "
                f"{result['total_score']}/{result['max_total']}.\n{result['feedback_summary']}\n"
                f"Awaiting your approval — say 'approve' or give me a correction.")

    def _grade_student_mcq(self, student_id, student_name, answers):
        bucket = self._current_bucket()
        if bucket is None or not bucket["mcq_questions"]:
            return f"No MCQ questions found under {self.state['current_assignment']}. Please add them first."

        mcq_list = [{"id": qid, "correct": q["correct_answer"], "points": q["points"]}
                    for qid, q in bucket["mcq_questions"].items()]
        result = grade_mcq_section(mcq_list, answers)
        feedback = format_mcq_feedback(result["mcq_results"])

        self.state["pending_grade"] = {
            "student_id": student_id, "student_name": student_name,
            "assignment_type": f"{self.state['current_assignment']} (MCQ)",
            "score": result["mcq_total"], "max_score": result["mcq_max"],
            "feedback": feedback
        }

        return f"MCQ score for {student_name}: {result['mcq_total']}/{result['mcq_max']}.\n{feedback}\nAwaiting your approval."

    def _approve_pending_grade(self):
        pg = self.state["pending_grade"]
        if not pg:
            return "There's no pending grade to approve."
        update_grade(pg["student_id"], pg["student_name"], pg["assignment_type"], pg["score"])
        log_feedback(pg["student_id"], pg["student_name"], pg["assignment_type"], pg["feedback"])
        self.state["pending_grade"] = None
        return f"Saved: {pg['student_name']} — {pg['assignment_type']}: {pg['score']}/{pg['max_score']}"

    def _edit_pending_grade(self, new_score=None, new_feedback=None):
        pg = self.state["pending_grade"]
        if not pg:
            return "There's no pending grade to edit."
        if new_score is not None:
            pg["score"] = new_score
        if new_feedback:
            pg["feedback"] = new_feedback
        update_grade(pg["student_id"], pg["student_name"], pg["assignment_type"], pg["score"])
        log_feedback(pg["student_id"], pg["student_name"], pg["assignment_type"], pg["feedback"])
        self.state["pending_grade"] = None
        return f"Saved edited grade: {pg['student_name']} — {pg['assignment_type']}: {pg['score']}/{pg['max_score']}"

    def _view_gradebook_tool(self):
        df = view_gradebook()
        return df.to_string(index=False) if df is not None and not df.empty else "Gradebook is empty."

    def _record_attendance(self, student_id, student_name, score):
        update_grade(student_id, student_name, "Attendance", score)
        return f"Recorded attendance for {student_name}: {score}"

    def _analyze_gradebook(self, question):
        df = view_gradebook()
        if df is None or df.empty:
            return "The gradebook is currently empty — nothing to analyze yet."
        table_str = df.to_string(index=False)
        prompt = ANALYTICS_PROMPT.format(table=table_str, question=question)
        response = call_gemini_with_retry(self.model, prompt)
        return response.text.strip()

    # ---- conversational loop ----

    def _extract_text(self, content):
        return "".join(p.text for p in content.parts if getattr(p, "text", None))

    def send(self, user_message, max_tool_rounds=5):
        self.chat_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
        config = types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, tools=[self.tools_config])

        for _ in range(max_tool_rounds):
            response = call_gemini_with_retry(self.model, self.chat_history, config=config)
            candidate = response.candidates[0]
            self.chat_history.append(candidate.content)

            function_calls = [p.function_call for p in candidate.content.parts if p.function_call]
            if not function_calls:
                text = self._extract_text(candidate.content)
                return text if text else "(no response)"

            tool_results = []
            for fc in function_calls:
                func = self.dispatch.get(fc.name)
                result = func(**fc.args) if func else f"Unknown tool: {fc.name}"
                tool_results.append(types.Part.from_function_response(name=fc.name, response={"result": result}))

            self.chat_history.append(types.Content(role="user", parts=tool_results))

        return "(Reached max tool-call rounds without a final reply.)"
