"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ExperienceLevel(str, Enum):
    INTERNSHIP = "internship"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"


class PostedTime(str, Enum):
    LAST_24H = "24h"
    LAST_WEEK = "week"
    LAST_MONTH = "month"


class JobType(str, Enum):
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


class JobSearchRequest(BaseModel):
    """Request model for job search."""
    resume_id: str = Field(..., description="ID of the uploaded resume")
    keywords: str = Field(..., min_length=1, description="Job keywords (required)")
    location: str = Field(..., min_length=1, description="Job location (required)")
    experience: ExperienceLevel = Field(default=ExperienceLevel.ENTRY)
    posted_time: PostedTime = Field(default=PostedTime.LAST_24H)
    job_type: JobType = Field(default=JobType.REMOTE)


class ResumeUploadResponse(BaseModel):
    """Response after resume upload."""
    resume_id: str
    filename: str
    text_length: int
    skills_extracted: List[str]
    uploaded_at: datetime


class Job(BaseModel):
    """LinkedIn job data model."""
    id: str
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    posted_time: str
    description: str
    url: str
    logo_initial: str = ""


class ScoredJob(BaseModel):
    """Job with matching score."""
    job: Job
    overall_score: float = Field(..., ge=0, le=100)
    skill_match: float = Field(..., ge=0, le=10)
    experience_match: float = Field(..., ge=0, le=10)
    education_match: float = Field(..., ge=0, le=10)
    analysis: str


class SearchProgress(BaseModel):
    """Progress update during search."""
    step: int
    total_steps: int
    status: str
    message: str


class SearchResult(BaseModel):
    """Final search results."""
    resume_id: str
    total_jobs_found: int
    top_jobs: List[ScoredJob]
    search_time_seconds: float
