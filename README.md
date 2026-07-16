# \# CIR Grading Assistant

# 

# A conversational, retrieval-grounded grading assistant built for a Conversational Information

# Retrieval (CIR) course project.

# 

# \## What it does

# A lecturer talks to the assistant naturally to:

# \- Index course material (PDF slides/notes, with OCR fallback for scanned files)

# \- Define assignments (Final Exam, Midterm, Assignment N) with MCQ and/or written questions

# \- Provide free-form grading rubrics for written questions — no fixed key answer required

# \- Have student answers graded automatically:

# &#x20; - MCQs: deterministic exact-match against the answer key

# &#x20; - Written answers: graded via semantic retrieval against indexed course material + LLM judgment

# \- Review, approve, or edit every AI-generated grade before it's saved

# \- Maintain a growing gradebook (CSV) across assignment types and students

# \- \*\*Ask analytical questions about the data\*\* — e.g. "who scored highest on the final?",

# &#x20; "who hasn't submitted Assignment 2?", "what's the class average on the midterm?"

# 

# \## Why retrieval matters

# Written answers are graded against evidence retrieved from the course material, not a fixed key

# answer. Every score is traceable to specific retrieved passages, which makes grading transparent.

# The trade-off: if a topic isn't well-covered in the indexed material, a correct answer on that

# topic may not receive full credit, since the system won't take the LLM's general knowledge as

# ground truth over the retrieved evidence. This is a deliberate design choice.

# 

# \## Architecture

# 

# ```

# Course material (PDF)

# &#x20;  │

# &#x20;  ▼

# indexer.py ─ OCR fallback ─ chunking ─ embeddings ─ FAISS index

# &#x20;  │

# &#x20;  ▼

# retriever.py ─ top-k semantic search per rubric criterion

# &#x20;  │

# &#x20;  ▼

# rubric\_parser.py ─ free-form rubric text → structured JSON criteria

# &#x20;  │

# &#x20;  ▼

# grader.py ─ retrieval + Gemini LLM judgment → score + feedback per criterion

# &#x20;  │

# &#x20;  ▼

# gradebook.py ─ wide-format CSV + feedback log

# &#x20;  │

# &#x20;  ▼

# chat\_agent.py ─ conversational interface (Gemini function calling), incl. analytics tool

# &#x20;  │

# &#x20;  ▼

# streamlit\_app.py ─ web UI  /  main.py ─ CLI

# ```

# 

# \## Setup

# 

# ```bash

# git clone https://github.com/<your-username>/cir-grading-assistant.git

# cd cir-grading-assistant

# pip install -r requirements.txt

# ```

# 

# System dependencies for OCR (Ubuntu/Debian):

# ```bash

# sudo apt-get update

# sudo apt-get install -y poppler-utils tesseract-ocr

# ```

# 

# \## Running locally (CLI)

# 

# ```bash

# export GEMINI\_API\_KEY="your-key-here"

# python main.py

# ```

# 

# \## Running the web UI locally

# 

# ```bash

# export GEMINI\_API\_KEY="your-key-here"

# streamlit run streamlit\_app.py

# ```

# 

# \## Live deployment (Streamlit Community Cloud)

# This app is deployed at: \*\*\[add your live URL here]\*\*

# 

# To deploy your own copy: push this repo to GitHub, go to

# \[share.streamlit.io](https://share.streamlit.io), point it at your repo with main file

# `streamlit\\\_app.py`, and add `GEMINI\\\_API\\\_KEY` under the app's "Secrets" settings.

# 

# \## Known limitations

# \- Written-question grading quality depends on how well the indexed course material covers the

# &#x20; exam's topics.

# \- Free-tier Gemini API quotas (requests/minute, requests/day) may require brief waits during

# &#x20; heavy sessions; retry logic is built in for transient 429/503 errors.

# \- OCR quality depends on scan resolution.

