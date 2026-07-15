# AI Resume Optimizer & ATS Analyzer

A production-ready generative AI web application that analyzes a resume against
a job description and produces a complete ATS optimization report — powered
by Groq's Llama 3.3 model, FastAPI, and SQLite.

## Overview

Upload a resume (PDF or DOCX), paste a job description, and click **Analyze
Resume**. The app extracts the resume text, sends it to Llama 3.3 through the
Groq API, and returns a full report: an ATS match score, a resume summary,
matching/missing skills, improvement suggestions, an optimized professional
summary, a tailored cover letter, and five likely interview questions. Every
report is stored in a local SQLite database and can be downloaded as a
Markdown file.

## Features

- 📄 Upload resumes in **PDF** or **DOCX** format
- 📋 Paste any job description for comparison
- 🤖 AI-generated **ATS Score** (0–100)
- 🧠 AI-generated **resume summary**
- ✅ **Matching skills** and ⚠️ **missing skills** detection
- 💡 Actionable **improvement suggestions**
- ✨ **Optimized professional summary** ready to paste into your resume
- 📝 Personalized **cover letter** generation
- ❓ **5 tailored interview questions** based on the resume + job description
- 🗄️ Full **SQLite** persistence of users, resumes, and analysis reports
- 📋 One-click **copy results** to clipboard
- ⬇️ **Download report** as a Markdown file
- 💻 Clean, responsive, framework-free **blue & white UI** with a loading spinner

## Folder Structure

```
AI-Resume-Optimizer/
├── database/
│   ├── database.py       # SQLAlchemy engine, session, init_db()
│   └── models.py         # User, Resume, Analysis ORM models
├── templates/
│   └── index.html        # Single-page UI (Jinja2)
├── static/
│   ├── style.css          # Blue & white theme, responsive layout
│   └── script.js          # Upload handling, fetch calls, rendering
├── uploads/                # Uploaded resume files (created at runtime)
├── reports/                 # Generated markdown reports (created at runtime)
├── app.py                  # FastAPI app, routes, orchestration
├── parser.py                # PDF/DOCX text extraction
├── generator.py              # Groq API calls + JSON response parsing
├── prompts.py                 # All LLM prompt templates
├── requirements.txt
├── .env.example
└── README.md
```

## Tech Stack

| Layer      | Technology                                   |
|------------|-----------------------------------------------|
| Backend    | Python, FastAPI, SQLAlchemy                   |
| Database   | SQLite                                        |
| Frontend   | HTML, CSS, JavaScript, Jinja2 Templates       |
| AI Model   | Groq API — Llama 3.3 (70B Versatile)          |
| Parsing    | pdfplumber, python-docx                       |
| Config     | python-dotenv                                 |

No React, no build tooling, no authentication, no Docker — just a
straightforward Python web app.

## Installation

1. **Clone / copy the project** and move into the folder:
   ```bash
   cd AI-Resume-Optimizer
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your environment variables**:
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and add your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
   Get a free key at https://console.groq.com/keys

## Database Setup

No manual setup required. On startup, the app automatically:

- Creates `resume_optimizer.db` (SQLite) in the project root if it doesn't exist
- Creates the `users`, `resumes`, and `analysis` tables via SQLAlchemy's
  `Base.metadata.create_all()`

If you ever want to reset the database, simply delete `resume_optimizer.db`
and restart the app — it will be recreated automatically.

## Running the Project

Start the FastAPI server with Uvicorn:

```bash
python app.py
```

or

```bash
uvicorn app:app --reload
```

Then open your browser at:

```
http://127.0.0.1:8000
```

Upload a resume, paste a job description, and click **Analyze Resume** to
generate your report.

## How It Works

1. `parser.py` extracts raw text from the uploaded PDF/DOCX resume.
2. `generator.py` sends four separate prompts (built in `prompts.py`) to the
   Groq API: ATS analysis, improvement suggestions, cover letter, and
   interview questions.
3. `app.py` orchestrates the pipeline, saves the resume and generated report
   to SQLite via SQLAlchemy models in `database/`, and writes a Markdown
   report to `/reports`.
4. The frontend (`templates/index.html`, `static/script.js`) renders the
   report as cards, and lets you copy the results or download the Markdown
   file.

## Future Improvements

- Support batch analysis of multiple resumes against one job description
- Add resume version history and side-by-side comparison of past reports
- Export the report as a formatted PDF in addition to Markdown
- Add keyword-density highlighting directly on the resume text
- Support additional file formats (e.g. `.txt`, `.rtf`)
