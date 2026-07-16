"""
Entry point for a terminal-based conversational session (alternative to streamlit_app.py).
Run: python main.py
"""

import os
import sys
from src.indexer import index_course_material
from src.chat_agent import GradingAssistant


def main():
    print("=== CIR Grading Assistant (CLI) ===\n")

    if not os.environ.get("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY environment variable not set.")
        print("Set it with: export GEMINI_API_KEY='your-key-here'\n")

    pdf_input = input("Enter path(s) to course material PDF(s), comma-separated: ").strip()
    pdf_paths = [p.strip() for p in pdf_input.split(",") if p.strip()]

    if not pdf_paths:
        print("No course material provided — exiting.")
        sys.exit(1)

    print("\nIndexing course material...")
    index, chunks = index_course_material(pdf_paths)
    print(f"Indexed {len(chunks)} chunks from {len(pdf_paths)} file(s).\n")

    assistant = GradingAssistant(index, chunks)
    print("Ready. Talk to the assistant naturally (type 'quit' to exit).\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        print(f"\nAssistant: {assistant.send(user_input)}\n")


if __name__ == "__main__":
    main()