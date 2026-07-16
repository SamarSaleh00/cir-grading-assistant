"""
Wide-format gradebook (one row per student, one column per assignment type)
plus a long-format feedback log for detailed per-assignment feedback.
"""

import pandas as pd
import os
from datetime import datetime

GRADEBOOK_PATH = "gradebook.csv"
FEEDBACK_LOG_PATH = "feedback_log.csv"


def init_gradebook(path=GRADEBOOK_PATH):
    if not os.path.exists(path):
        pd.DataFrame(columns=["student_id", "student_name"]).to_csv(path, index=False)
        print(f"Created new gradebook at {path}")
    else:
        print(f"Using existing gradebook at {path}")


def update_grade(student_id, student_name, assignment_type, score, path=GRADEBOOK_PATH):
    """
    New student -> new row. New assignment_type -> new column.
    Existing entry -> overwritten.
    """
    init_gradebook(path)
    df = pd.read_csv(path, dtype={"student_id": str})

    if assignment_type not in df.columns:
        df[assignment_type] = pd.NA

    student_id = str(student_id)
    existing_row = df[df["student_id"] == student_id]

    if existing_row.empty:
        new_row = {col: pd.NA for col in df.columns}
        new_row["student_id"] = student_id
        new_row["student_name"] = student_name
        new_row[assignment_type] = score
        new_row_df = pd.DataFrame([new_row]).astype(df.dtypes.to_dict(), errors="ignore")
        df = pd.concat([df, new_row_df], ignore_index=True)
    else:
        df.loc[df["student_id"] == student_id, assignment_type] = score
        df.loc[df["student_id"] == student_id, "student_name"] = student_name

    df.to_csv(path, index=False)
    print(f"Updated {student_name} ({student_id}) — {assignment_type}: {score}")


def view_gradebook(path=GRADEBOOK_PATH):
    """Returns the gradebook as a DataFrame (or None if it doesn't exist yet)."""
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, dtype={"student_id": str})


def log_feedback(student_id, student_name, assignment_type, feedback, path=FEEDBACK_LOG_PATH):
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "student_id": str(student_id),
        "student_name": student_name,
        "assignment_type": assignment_type,
        "feedback": feedback.replace("\n", " | ")
    }

    if not os.path.exists(path):
        pd.DataFrame([row]).to_csv(path, index=False)
    else:
        df = pd.read_csv(path, dtype={"student_id": str})
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(path, index=False)

    print(f"Logged feedback for {student_name} ({student_id}) — {assignment_type}")