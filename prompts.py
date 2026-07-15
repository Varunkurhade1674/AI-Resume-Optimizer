"""
Prompt templates used to instruct the Groq LLM (Llama 3.3) for each stage
of the resume analysis pipeline. Each function returns a ready-to-send
prompt string built from the resume text and job description.

Every prompt instructs the model to respond with STRICT JSON only, so the
generator module can reliably parse the response.
"""


def ats_analysis_prompt(resume_text: str, job_description: str) -> str:
    """Prompt for the core ATS score, resume summary, and skill matching."""
    return f"""You are an expert ATS (Applicant Tracking System) analyzer and technical recruiter.

Compare the RESUME below against the JOB DESCRIPTION and evaluate how well the resume
matches the role from an ATS keyword-matching and recruiter perspective.

RESUME:
\"\"\"{resume_text}\"\"\"

JOB DESCRIPTION:
\"\"\"{job_description}\"\"\"

Respond with STRICT JSON ONLY (no markdown, no commentary, no code fences) in exactly
this shape:
{{
  "ats_score": <integer 0-100 representing overall match quality>,
  "summary": "<3-4 sentence professional summary of the candidate based on the resume>",
  "matching_skills": ["skill1", "skill2", "..."],
  "missing_skills": ["skill1", "skill2", "..."]
}}

Rules:
- "matching_skills" are skills/keywords present in BOTH the resume and job description.
- "missing_skills" are important skills/keywords in the job description that are absent
  from the resume.
- Keep each skill entry short (1-4 words).
- Return valid JSON only.
"""


def improvement_prompt(resume_text: str, job_description: str) -> str:
    """Prompt for actionable improvement suggestions and an optimized summary."""
    return f"""You are a professional resume writing coach specializing in ATS optimization.

RESUME:
\"\"\"{resume_text}\"\"\"

JOB DESCRIPTION:
\"\"\"{job_description}\"\"\"

Respond with STRICT JSON ONLY (no markdown, no commentary, no code fences) in exactly
this shape:
{{
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3", "..."],
  "optimized_summary": "<a rewritten 3-4 sentence professional summary optimized for this job description, using strong action verbs and relevant keywords>"
}}

Rules:
- Provide 5-7 concrete, specific improvement suggestions (e.g. add quantifiable
  metrics, include missing keywords, restructure experience section).
- The optimized_summary must be ready to paste directly into a resume.
- Return valid JSON only.
"""


def cover_letter_prompt(resume_text: str, job_description: str) -> str:
    """Prompt for a personalized cover letter."""
    return f"""You are an expert career writer. Write a concise, compelling, and personalized
cover letter for the candidate below, tailored specifically to the job description.

RESUME:
\"\"\"{resume_text}\"\"\"

JOB DESCRIPTION:
\"\"\"{job_description}\"\"\"

Respond with STRICT JSON ONLY (no markdown, no commentary, no code fences) in exactly
this shape:
{{
  "cover_letter": "<full cover letter text, 3-4 short paragraphs, plain text with \\n for line breaks>"
}}

Rules:
- Do not invent facts about the candidate that are not supported by the resume.
- Keep the tone professional, confident, and specific to the job description.
- Return valid JSON only.
"""


def interview_questions_prompt(resume_text: str, job_description: str) -> str:
    """Prompt for 5 tailored interview questions."""
    return f"""You are a hiring manager preparing to interview the candidate below for the
role described in the job description.

RESUME:
\"\"\"{resume_text}\"\"\"

JOB DESCRIPTION:
\"\"\"{job_description}\"\"\"

Respond with STRICT JSON ONLY (no markdown, no commentary, no code fences) in exactly
this shape:
{{
  "interview_questions": ["question 1", "question 2", "question 3", "question 4", "question 5"]
}}

Rules:
- Generate exactly 5 questions.
- Mix technical, behavioral, and role-specific questions based on gaps or highlights
  found in the resume versus the job description.
- Return valid JSON only.
"""
