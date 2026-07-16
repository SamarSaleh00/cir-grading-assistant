"""
Conversational layer: lets the lecturer talk naturally. Uses Gemini function
calling to route intents to grading/indexing/gradebook actions, plus a new
analytics tool that answers questions about the gradebook data itself
(highest/lowest scores, missing submissions, rankings, comparisons, etc.).
"""

from google.genai import types
from src.grader import client, grade_question, grade_mcq_section, format_mcq_feedback, call_gemini_with_retry, DEFAULT_MODEL
from src.rubric_parser import parse_rubric
from src.gradebook import update_grade, log_feedback, view_gradebook

SYSTEM_INSTRUCTION = """You are a helpful teaching assistant that helps a lecturer grade student work
and analyze grading data. You have tools to: set up assignments, add questions/rubrics, grade students
(written or MCQ), approve or edit pending grades, view the gradebook, record attendance, and answer
analytical questions about the gradebook (e.g. who scored highest, who is missing a submission,
average scores, comparisons across students or assignments).

Use the tools whenever the lecturer's message implies one of these actions — don't ask them to use
special commands, just understand natural phrasing. If information is missing to call a tool
(e.g. no rubric given yet), ask a clarifying question instead of guessing.

If the lecturer asks a question ABOUT the data (rankings, comparisons, who did/didn't do something,
averages, etc.) rather than asking you to perform a new grading action, call analyze_gradebook.

After a tool executes, explain the result to the lecturer conversationally."""


def build_tools_config():
    return types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="set_assignment_context",
            description="Start grading a new assignment type (e.g. Midterm, Final Exam, Assignment 1).",
            parameters={
                "type": "object",
                "properties": {"assignment_type": {"type": "string"}},
                "required": ["assignment_type"]
            }
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
                "properties": {
                    "new_score": {"type": "number"},
                    "new_feedback": {"type": "string"}
                }
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
            description=(
                "Answer analytical questions about the gradebook data, such as: who scored highest/"
                "lowest overall or on a specific assignment, which students are missing a submission "
                "(blank/NaN) for a given assignment, class averages, rankings, or comparisons between "
                "students or assignment types. Call this for ANY question about existing data rather "
                "than a request to grade something new."
            ),
            parameters={
                "type": "object",
                "properties": {"question": {"type": "string", "description": "The lecturer's analytical question, verbatim or paraphrased"}},
                "required": ["question"]
            }
        ),
    ])


ANALYTICS_PROMPT = """You are analyzing a lecturer's gradebook to answer their question.

Gradebook (wide format — one row per student, one column per assignment type; blank/NaN means
that student has no recorded score for that assignment, which usually means it wasn't graded or
submitted yet):

{table}

Lecturer's question: "{question}"

Answer accurately based ONLY on the data above. If the question involves a column that doesn't
exist in the table, say so rather than guessing. If it asks about missing submissions, look for
NaN/blank values. Be concise and specific (name the actual students/numbers involved).
"""


class GradingAssistant:
    """
    Wraps session state + the conversational loop. Instantiate once per grading
    session (e.g. one per uploaded course index), then call .send(message) repeatedly.
    """

    def __init__(self, index, chunks, model=DEFAULT_MODEL):
        self.model = model
        self.tools_config = build_tools_config()
        self.chat_history = []
        self.state = {
            "index": index,
            "chunks": chunks,
            "current_assignment": None,
            "written_questions": {},
            "mcq_questions": {},
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

    # ---- tool implementations ----

    def _set_assignment_context(self, assignment_type):
        self.state["current_assignment"] = assignment_type
        self.state["written_questions"] = {}
        self.state["mcq_questions"] = {}
        return f"Now grading: {assignment_type}. Ready for questions/rubrics."

    def _add_written_question(self, question_id, question_text, rubric_text):
        self.state["written_questions"][question_id] = {"question_text": question_text, "rubric_text": rubric_text}
        return f"Added written question {question_id}: {question_text}"

    def _add_mcq_question(self, question_id, correct_answer, points):
        self.state["mcq_questions"][question_id] = {"correct_answer": correct_answer, "points": points}
        return f"Added MCQ {question_id}, correct answer {correct_answer}, {points} points"

    def _grade_student_written(self, student_id, student_name, question_id, student_answer):
        q = self.state["written_questions"].get(question_id)
        if not q:
            return f"No rubric found for question {question_id}. Please provide the rubric first."

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
        mcq_list = [{"id": qid, "correct": q["correct_answer"], "points": q["points"]}
                    for qid, q in self.state["mcq_questions"].items()]
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
        """
        Answers analytical questions about the gradebook by handing the full
        table + the question to Gemini as a plain (non-tool) call.
        """
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
        """
        Sends one lecturer message, resolves any chain of tool calls, and
        returns the final natural-language reply.
        """
        self.chat_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[self.tools_config]
        )

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

        return "(Reached max tool-call rounds without a final reply — this may indicate a loop; check the conversation.)"