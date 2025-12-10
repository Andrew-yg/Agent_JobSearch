"""LLM Scorer - GPT-4 based job matching and scoring."""
import json
from typing import List, Dict
from openai import OpenAI

from ..config import get_settings
from ..models import ScoredJob, Job


class LLMScorer:
    """
    Uses GPT-4 to deeply analyze and score job-resume matches.
    Scores Top 50 candidates → selects Top 10.
    """
    
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def score_jobs(
        self,
        resume_text: str,
        jobs: List[Dict],
        top_n: int = 10
    ) -> List[ScoredJob]:
        """
        Score jobs against resume and return top N matches.
        
        Scoring weights:
        - Skills: 40%
        - Experience: 30%
        - Education: 20%
        - Other: 10%
        """
        scored_jobs = []
        
        # Process in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            batch_results = self._score_batch(resume_text, batch)
            scored_jobs.extend(batch_results)
        
        # Sort by overall score and take top N
        scored_jobs.sort(key=lambda x: x.overall_score, reverse=True)
        return scored_jobs[:top_n]
    
    def _score_batch(
        self,
        resume_text: str,
        jobs: List[Dict]
    ) -> List[ScoredJob]:
        """Score a batch of jobs."""
        results = []
        
        for job in jobs:
            try:
                scored = self._score_single_job(resume_text, job)
                results.append(scored)
            except Exception as e:
                print(f"Error scoring job {job.get('id')}: {e}")
                # Create a default low score
                results.append(ScoredJob(
                    job=Job(
                        id=job.get("id", "unknown"),
                        title=job.get("title", "Unknown"),
                        company=job.get("company", "Unknown"),
                        location=job.get("location", ""),
                        salary=job.get("salary"),
                        posted_time=job.get("posted_time", ""),
                        description=job.get("description", "")[:500],
                        url=job.get("url", ""),
                        logo_initial=job.get("logo_initial", "?")
                    ),
                    overall_score=0,
                    skill_match=0,
                    experience_match=0,
                    education_match=0,
                    analysis="Unable to analyze this job."
                ))
        
        return results
    
    def _score_single_job(self, resume_text: str, job: Dict) -> ScoredJob:
        """Score a single job against resume using GPT-4."""
        
        prompt = f"""Analyze how well this resume matches the job posting.

RESUME:
{resume_text[:3000]}

JOB POSTING:
Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Location: {job.get('location', 'N/A')}
Description: {job.get('description', 'N/A')[:2000]}

Score the match on these dimensions (0-10 scale):
1. skill_match: How well do the candidate's technical skills match?
2. experience_match: How relevant is their work experience?
3. education_match: How suitable is their educational background?

Also provide a brief analysis (2-3 sentences) of why this is/isn't a good match.

Respond in valid JSON format:
{{
    "skill_match": <number 0-10>,
    "experience_match": <number 0-10>,
    "education_match": <number 0-10>,
    "analysis": "<string>"
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert recruiter analyzing job-candidate matches. Be objective and provide accurate scores. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        scores = json.loads(content)
        
        # Calculate overall score with weights
        skill = min(10, max(0, float(scores.get("skill_match", 0))))
        experience = min(10, max(0, float(scores.get("experience_match", 0))))
        education = min(10, max(0, float(scores.get("education_match", 0))))
        
        # Weighted average (40% skill, 30% exp, 20% edu, 10% base)
        overall = (skill * 0.4 + experience * 0.3 + education * 0.2 + 
                   job.get("similarity_score", 50) / 10 * 0.1)
        overall = round(overall * 10, 1)  # Convert to 0-100 scale
        
        return ScoredJob(
            job=Job(
                id=job.get("id", "unknown"),
                title=job.get("title", "Unknown"),
                company=job.get("company", "Unknown"),
                location=job.get("location", ""),
                salary=job.get("salary"),
                posted_time=job.get("posted_time", ""),
                description=job.get("description", "")[:500],
                url=job.get("url", ""),
                logo_initial=job.get("logo_initial", "?")
            ),
            overall_score=overall,
            skill_match=skill,
            experience_match=experience,
            education_match=education,
            analysis=scores.get("analysis", "No analysis provided.")
        )
