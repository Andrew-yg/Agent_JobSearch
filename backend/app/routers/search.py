"""Search router - Job search with SSE streaming."""
import asyncio
import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models import JobSearchRequest, SearchResult, SearchProgress
from ..services.browser_agent import get_browser_agent
from ..services.rag_engine import RAGEngine
from ..services.llm_scorer import LLMScorer

router = APIRouter(prefix="/search", tags=["Search"])


async def search_stream(request: JobSearchRequest) -> AsyncGenerator[str, None]:
    """
    Stream search progress using Server-Sent Events (SSE).
    
    Flow:
    1. Check LinkedIn login
    2. Search jobs with browser automation
    3. Store jobs in vector DB
    4. RAG matching
    5. LLM scoring
    6. Return top 10
    """
    start_time = time.time()
    jobs_collected = []
    
    try:
        # Step 1: Initialize browser
        yield f"data: {json.dumps({'step': 1, 'total': 4, 'status': 'processing', 'message': 'Initializing browser...'})}\n\n"
        
        agent = await get_browser_agent()
        
        # Check login
        is_logged_in = await agent.check_login_status()
        if not is_logged_in:
            yield f"data: {json.dumps({'step': 1, 'total': 4, 'status': 'waiting', 'message': 'Please log in to LinkedIn in the opened browser window...'})}\n\n"
            
            # Wait for user to login (max 2 minutes)
            for _ in range(24):
                await asyncio.sleep(5)
                is_logged_in = await agent.check_login_status()
                if is_logged_in:
                    break
            
            if not is_logged_in:
                yield f"data: {json.dumps({'step': 1, 'total': 4, 'status': 'error', 'message': 'LinkedIn login timeout'})}\n\n"
                return
        
        yield f"data: {json.dumps({'step': 1, 'total': 4, 'status': 'completed', 'message': 'Browser ready, logged in to LinkedIn'})}\n\n"
        
        # Step 2: Search jobs
        yield f"data: {json.dumps({'step': 2, 'total': 4, 'status': 'processing', 'message': 'Searching LinkedIn jobs...'})}\n\n"
        
        async for update in agent.search_jobs(
            keywords=request.keywords,
            location=request.location,
            experience=request.experience.value,
            posted_time=request.posted_time.value,
            job_type=request.job_type.value,
            max_jobs=50
        ):
            if update["type"] == "progress":
                yield f"data: {json.dumps({'step': 2, 'total': 4, 'status': 'processing', 'message': update['message']})}\n\n"
            elif update["type"] == "job":
                jobs_collected.append(update["data"])
                yield f"data: {json.dumps({'step': 2, 'total': 4, 'status': 'processing', 'message': f'Found {len(jobs_collected)} jobs...'})}\n\n"
            elif update["type"] == "complete":
                total_count = update["total"]
                yield f"data: {json.dumps({'step': 2, 'total': 4, 'status': 'completed', 'message': f'Collected {total_count} jobs'})}\n\n"
        
        if not jobs_collected:
            yield f"data: {json.dumps({'step': 2, 'total': 4, 'status': 'error', 'message': 'No jobs found matching criteria'})}\n\n"
            return
        
        # Step 3: RAG matching
        yield f"data: {json.dumps({'step': 3, 'total': 4, 'status': 'processing', 'message': 'Analyzing job matches with AI...'})}\n\n"
        
        rag = RAGEngine()
        
        # Clear previous jobs and store new ones
        rag.clear_jobs()
        stored = rag.store_jobs(jobs_collected)
        
        yield f"data: {json.dumps({'step': 3, 'total': 4, 'status': 'processing', 'message': f'Stored {stored} jobs, running vector search...'})}\n\n"
        
        # Find top 50 matches
        matched_jobs = rag.search_matching_jobs(request.resume_id, top_k=50)
        
        yield f"data: {json.dumps({'step': 3, 'total': 4, 'status': 'completed', 'message': f'Found {len(matched_jobs)} potential matches'})}\n\n"
        
        # Step 4: LLM scoring
        yield f"data: {json.dumps({'step': 4, 'total': 4, 'status': 'processing', 'message': 'Scoring matches with GPT-4...'})}\n\n"
        
        scorer = LLMScorer()
        resume_text = rag.get_resume_text(request.resume_id)
        
        top_jobs = scorer.score_jobs(resume_text, matched_jobs, top_n=10)
        
        yield f"data: {json.dumps({'step': 4, 'total': 4, 'status': 'completed', 'message': 'Scoring complete!'})}\n\n"
        
        # Final result
        elapsed = time.time() - start_time
        result = SearchResult(
            resume_id=request.resume_id,
            total_jobs_found=len(jobs_collected),
            top_jobs=top_jobs,
            search_time_seconds=round(elapsed, 2)
        )
        
        yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump()})}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'step': 0, 'total': 4, 'status': 'error', 'message': str(e)})}\n\n"


@router.post("")
async def search_jobs(request: JobSearchRequest):
    """
    Start job search with streaming progress.
    
    Returns Server-Sent Events (SSE) stream with:
    - Progress updates for each step
    - Final result with top 10 scored jobs
    """
    # Validate required fields
    if not request.keywords or not request.keywords.strip():
        raise HTTPException(status_code=400, detail="Keywords are required")
    
    if not request.location or not request.location.strip():
        raise HTTPException(status_code=400, detail="Location is required")
    
    return StreamingResponse(
        search_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/test")
async def test_search():
    """Test endpoint for debugging."""
    return {"status": "ok", "message": "Search router is working"}
