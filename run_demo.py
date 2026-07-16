"""
Runs a scripted demo using data/sample_data.py — no live conversation needed.
Useful for a guaranteed-to-work fallback during a presentation.
Requires a real course material PDF at the path below.
"""

from src.indexer import index_course_material
from src.grader import grade_question, grade_mcq_section, format_mcq_feedback
from src.rubric_parser import parse_rubric
from src.gradebook import update_grade, log_feedback, view_gradebook
from data.sample_data import (
    FINAL_EXAM_MCQ, FINAL_EXAM_WRITTEN, FINAL_EXAM_STUDENTS, ATTENDANCE
)

COURSE_PDF_PATH = "data/CIR_lecture_notes.pdf"  # put a real course PDF at this path


def main():
    print("Indexing course material...")
    index, chunks = index_course_material([COURSE_PDF_PATH])
    print(f"Indexed {len(chunks)} chunks.\n")

    for entry in ATTENDANCE:
        update_grade(entry["student_id"], entry["name"], "Attendance", entry["score"])

    for student in FINAL_EXAM_STUDENTS:
        mcq_result = grade_mcq_section(FINAL_EXAM_MCQ, student["mcq_answers"])
        update_grade(student["student_id"], student["name"], "Final Exam (MCQ)", mcq_result["mcq_total"])

        total_written = 0
        for wq in FINAL_EXAM_WRITTEN:
            criteria = parse_rubric(wq["rubric"])
            answer = student["written_answers"].get(wq["id"], "")
            result = grade_question(criteria, answer, index, chunks)
            total_written += result["total_score"]
            log_feedback(student["student_id"], student["name"], f"Final Exam - {wq['id']}", result["feedback_summary"])

        update_grade(student["student_id"], student["name"], "Final Exam", total_written)

    print("\nFinal gradebook:")
    print(view_gradebook().to_string(index=False))


if __name__ == "__main__":
    main()