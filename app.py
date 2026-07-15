"""
AI Resume Optimizer & ATS Analyzer - FastAPI application entrypoint.

Handles:
    - Serving the single-page UI
    - Accepting resume uploads + job descriptions
    - Orchestrating text extraction and AI analysis
    - Persisting resumes and analysis reports to SQLite
    - Serving downloadable markdown reports
"""

import os
import shutil
import uuid
from datetime import datetime

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import generator
import parser as resume_parser
from database.database import init_db, get_db
from database import models

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 5

app = FastAPI(title="AI Resume Optimizer & ATS Analyzer")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.on_event("startup")
def on_startup() -> None:
    """Ensure required folders and database tables exist before serving requests."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    init_db()


@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    """Serve the single-page application."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze_resume(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    candidate_name: str = Form("Guest"),
    provider: str = Form("groq"),
    api_key: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Accept a resume file + job description, run the full AI analysis pipeline,
    persist everything to SQLite, and return the report as JSON.
    """
    job_description = job_description.strip()
    if not job_description:
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    file_ext = os.path.splitext(resume_file.filename or "")[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, detail="Only PDF and DOCX resumes are supported."
        )

    # Save the uploaded file to disk with a unique name to avoid collisions.
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    saved_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)

        if os.path.getsize(saved_path) > MAX_FILE_SIZE_MB * 1024 * 1024:
            os.remove(saved_path)
            raise HTTPException(status_code=400, detail="File too large. Max size is 5MB.")

        # Extract text from the resume file.
        resume_text = resume_parser.extract_resume_text(saved_path)

    except resume_parser.ResumeParseError as exc:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=500, detail=f"Failed to process file: {exc}")

    # Get or create the user record (no authentication - simple name lookup).
    user = db.query(models.User).filter(models.User.name == candidate_name).first()
    if not user:
        user = models.User(name=candidate_name or "Guest")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Persist the resume record.
    resume_record = models.Resume(
        user_id=user.id,
        filename=resume_file.filename,
        resume_text=resume_text,
    )
    db.add(resume_record)
    db.commit()
    db.refresh(resume_record)

    # Run the AI analysis pipeline (ATS score, improvements, cover letter, questions).
    try:
        result = generator.run_full_analysis(resume_text, job_description, provider, api_key)
    except generator.GenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Persist the analysis report.
    analysis_record = models.Analysis(
        resume_id=resume_record.id,
        ats_score=result["ats_score"],
        matching_skills=", ".join(result["matching_skills"]),
        missing_skills=", ".join(result["missing_skills"]),
        summary=result["summary"],
        suggestions="\n".join(result["suggestions"]),
        optimized_summary=result["optimized_summary"],
        cover_letter=result["cover_letter"],
        interview_questions="\n".join(result["interview_questions"]),
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    # Write a markdown report to disk for later download.
    report_path = _write_markdown_report(analysis_record, resume_record)

    return JSONResponse(
        {
            "analysis_id": analysis_record.id,
            "ats_score": result["ats_score"],
            "summary": result["summary"],
            "matching_skills": result["matching_skills"],
            "missing_skills": result["missing_skills"],
            "suggestions": result["suggestions"],
            "optimized_summary": result["optimized_summary"],
            "cover_letter": result["cover_letter"],
            "interview_questions": result["interview_questions"],
            "report_url": f"/download/{analysis_record.id}",
        }
    )


def _write_markdown_report(analysis: models.Analysis, resume: models.Resume) -> str:
    """Build a markdown report for a given analysis and save it to /reports."""
    content = f"""# ATS Analysis Report

**Resume File:** {resume.filename}
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

## ATS Score
{analysis.ats_score}/100

## Resume Summary
{analysis.summary}

## Matching Skills
{analysis.matching_skills or "None found"}

## Missing Skills
{analysis.missing_skills or "None found"}

## Improvement Suggestions
{analysis.suggestions}

## Optimized Professional Summary
{analysis.optimized_summary}

## Cover Letter
{analysis.cover_letter}

## Interview Questions
{analysis.interview_questions}
"""
    report_path = os.path.join(REPORTS_DIR, f"report_{analysis.id}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
    return report_path


@app.get("/download/{analysis_id}")
def download_report(analysis_id: int, db: Session = Depends(get_db)):
    """Serve the markdown report file for a given analysis id."""
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    report_path = os.path.join(REPORTS_DIR, f"report_{analysis_id}.md")
    if not os.path.exists(report_path):
        resume = db.query(models.Resume).filter(models.Resume.id == analysis.resume_id).first()
        report_path = _write_markdown_report(analysis, resume)

    return FileResponse(
        report_path,
        media_type="text/markdown",
        filename=f"ATS_Report_{analysis_id}.md",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
