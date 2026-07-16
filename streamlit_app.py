"""
Web UI for the CIR Grading Assistant.
Deployed via Streamlit Community Cloud — reads GEMINI_API_KEY from st.secrets.
"""

import streamlit as st
import os

# IMPORTANT: set the API key in the environment BEFORE importing any src module,
# since src/grader.py builds the Gemini client at import time.
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

import tempfile
from src.indexer import index_course_material
from src.chat_agent import GradingAssistant
from src.gradebook import view_gradebook, GRADEBOOK_PATH

st.set_page_config(page_title="CIR Grading Assistant", page_icon="📝", layout="wide")

st.title("📝 CIR Grading Assistant")
st.caption("A conversational, retrieval-grounded grading assistant for lecturers.")

if "assistant" not in st.session_state:
    st.session_state.assistant = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed" not in st.session_state:
    st.session_state.indexed = False

with st.sidebar:
    st.header("1. Course Material")

    uploaded_files = st.file_uploader(
        "Upload lecture slides/notes (PDF)", type=["pdf"], accept_multiple_files=True
    )

    if st.button("Index course material", disabled=not uploaded_files):
        with st.spinner("Indexing (OCR may run on scanned pages — this can take a minute)..."):
            temp_paths = []
            for f in uploaded_files:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp.write(f.read())
                tmp.close()
                temp_paths.append(tmp.name)

            index, chunks = index_course_material(temp_paths)
            st.session_state.assistant = GradingAssistant(index, chunks)
            st.session_state.indexed = True
            st.session_state.messages = []

        st.success(f"Indexed {len(chunks)} chunks from {len(uploaded_files)} file(s).")

    st.divider()
    st.header("2. Gradebook")

    df = view_gradebook()
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download gradebook.csv", csv_bytes, "gradebook.csv", "text/csv")
    else:
        st.info("Gradebook is empty so far.")

if not st.session_state.indexed:
    st.info("👈 Upload and index course material in the sidebar to get started.")
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input(
        "Talk naturally — grade students, or ask things like 'who scored highest on the midterm?'"
    )

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = st.session_state.assistant.send(user_input)
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()