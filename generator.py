"""
AI generation layer. Wraps calls to the Groq API (Llama 3.3) and parses the
JSON responses produced from the prompt templates in prompts.py.
"""

import os
import json
import re

from dotenv import load_dotenv
from groq import Groq

import prompts

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


class GenerationError(Exception):
    """Raised when the AI provider fails or returns an unparsable response."""


def _call_groq(prompt: str) -> str:
    """Send a single prompt to Groq's chat completion endpoint and return raw text."""
    if _client is None:
        raise GenerationError(
            "GROQ_API_KEY is not set. Please add it to your .env file."
        )

    try:
        response = _client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that always replies with strict, valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=1500,
        )
        return response.choices[0].message.content
    except Exception as exc:
        raise GenerationError(f"Groq API request failed: {exc}") from exc


def _parse_json(raw_text: str) -> dict:
    """Strip any markdown code fences and parse the model output as JSON."""
    cleaned = raw_text.strip()

    # Remove ```json ... ``` or ``` ... ``` fences if the model added them.
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # Some models add stray text before/after the JSON object; extract the
    # outermost braces as a fallback.
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise GenerationError(f"Could not parse AI response as JSON: {exc}") from exc
        raise GenerationError("AI response did not contain valid JSON.")


def analyze_ats(resume_text: str, job_description: str) -> dict:
    """Run the ATS analysis stage: score, summary, matching/missing skills."""
    raw = _call_groq(prompts.ats_analysis_prompt(resume_text, job_description))
    data = _parse_json(raw)

    return {
        "ats_score": int(data.get("ats_score", 0)),
        "summary": data.get("summary", "").strip(),
        "matching_skills": [s.strip() for s in data.get("matching_skills", []) if s.strip()],
        "missing_skills": [s.strip() for s in data.get("missing_skills", []) if s.strip()],
    }


def generate_improvements(resume_text: str, job_description: str) -> dict:
    """Run the resume improvement stage: suggestions + optimized summary."""
    raw = _call_groq(prompts.improvement_prompt(resume_text, job_description))
    data = _parse_json(raw)

    return {
        "suggestions": [s.strip() for s in data.get("suggestions", []) if s.strip()],
        "optimized_summary": data.get("optimized_summary", "").strip(),
    }


def generate_cover_letter(resume_text: str, job_description: str) -> str:
    """Run the cover letter generation stage."""
    raw = _call_groq(prompts.cover_letter_prompt(resume_text, job_description))
    data = _parse_json(raw)
    return data.get("cover_letter", "").strip()


def generate_interview_questions(resume_text: str, job_description: str) -> list:
    """Run the interview question generation stage."""
    raw = _call_groq(prompts.interview_questions_prompt(resume_text, job_description))
    data = _parse_json(raw)
    return [q.strip() for q in data.get("interview_questions", []) if q.strip()]


def run_full_analysis(resume_text: str, job_description: str) -> dict:
    """Run all four generation stages and combine the results into one report."""
    ats_result = analyze_ats(resume_text, job_description)
    improvements = generate_improvements(resume_text, job_description)
    cover_letter = generate_cover_letter(resume_text, job_description)
    interview_questions = generate_interview_questions(resume_text, job_description)

    return {
        **ats_result,
        **improvements,
        "cover_letter": cover_letter,
        "interview_questions": interview_questions,
    }
