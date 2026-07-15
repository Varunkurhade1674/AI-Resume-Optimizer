"""
SQLAlchemy ORM models for the AI Resume Optimizer application.

Defines three tables:
    - Users:    basic user record (no authentication, just a display name)
    - Resumes:  uploaded resume metadata and extracted raw text
    - Analysis: AI-generated ATS analysis report linked to a resume
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database.database import Base


class User(Base):
    """Represents a person using the tool (no login required)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, default="Guest")
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    """Represents a single uploaded resume file and its extracted text."""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    resume_text = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    analyses = relationship("Analysis", back_populates="resume", cascade="all, delete-orphan")


class Analysis(Base):
    """Represents one AI-generated ATS analysis report for a resume."""

    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)

    ats_score = Column(Integer, nullable=False, default=0)
    matching_skills = Column(Text, nullable=True)      # stored as comma-separated string
    missing_skills = Column(Text, nullable=True)       # stored as comma-separated string
    summary = Column(Text, nullable=True)
    suggestions = Column(Text, nullable=True)          # newline-separated bullet points
    optimized_summary = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    interview_questions = Column(Text, nullable=True)  # newline-separated questions
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="analyses")
