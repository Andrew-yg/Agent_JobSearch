"""Upload router - Resume file upload endpoint."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime

from ..models import ResumeUploadResponse
from ..services.resume_parser import ResumeParser

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF resume for processing.
    
    - Parses PDF text
    - Extracts skills using LLM
    - Generates embeddings
    - Stores in ChromaDB
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    # Read file content
    content = await file.read()
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )
    
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )
    
    try:
        # Process resume
        parser = ResumeParser()
        resume_id, text, skills = parser.process_resume(content, file.filename)
        
        return ResumeUploadResponse(
            resume_id=resume_id,
            filename=file.filename,
            text_length=len(text),
            skills_extracted=skills,
            uploaded_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing resume: {str(e)}"
        )


@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    """Get resume details by ID."""
    parser = ResumeParser()
    resume = parser.get_resume(resume_id)
    
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )
    
    return resume
