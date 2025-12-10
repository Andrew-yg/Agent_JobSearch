"""Resume parsing service - PDF extraction and embeddings."""
import uuid
import json
import re
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

from PyPDF2 import PdfReader
from openai import OpenAI

from ..config import get_settings
from ..database import get_resume_collection, get_session, ResumeRecord


class ResumeParser:
    """Service for parsing resumes and generating embeddings."""
    
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.upload_dir = Path(settings.upload_directory)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text using LLM."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a resume analyzer. Extract technical skills, programming languages, frameworks, and tools from the resume. Return ONLY a JSON array of skill strings, nothing else."
                    },
                    {
                        "role": "user",
                        "content": f"Extract skills from this resume:\n\n{text[:4000]}"
                    }
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up response
            if content.startswith("```"):
                content = re.sub(r"```\w*\n?", "", content)
            
            skills = json.loads(content)
            return skills if isinstance(skills, list) else []
        except Exception as e:
            print(f"Error extracting skills: {e}")
            return []
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]  # Limit input length
        )
        return response.data[0].embedding
    
    def process_resume(self, file_content: bytes, filename: str) -> Tuple[str, str, List[str]]:
        """
        Process uploaded resume file.
        Returns: (resume_id, text_content, skills)
        """
        # Generate unique ID
        resume_id = str(uuid.uuid4())
        
        # Save file
        file_path = self.upload_dir / f"{resume_id}.pdf"
        file_path.write_bytes(file_content)
        
        # Extract text
        text = self.parse_pdf(file_path)
        
        # Extract skills
        skills = self.extract_skills(text)
        
        # Generate embedding
        embedding = self.generate_embedding(text)
        
        # Store in ChromaDB
        collection = get_resume_collection()
        collection.add(
            ids=[resume_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "filename": filename,
                "skills": json.dumps(skills),
                "uploaded_at": datetime.utcnow().isoformat()
            }]
        )
        
        # Store in SQLite
        session = get_session()
        record = ResumeRecord(
            id=resume_id,
            filename=filename,
            text_content=text,
            skills=json.dumps(skills),
            uploaded_at=datetime.utcnow()
        )
        session.add(record)
        session.commit()
        session.close()
        
        return resume_id, text, skills
    
    def get_resume(self, resume_id: str) -> dict:
        """Retrieve resume by ID."""
        session = get_session()
        record = session.query(ResumeRecord).filter_by(id=resume_id).first()
        session.close()
        
        if not record:
            return None
        
        return {
            "id": record.id,
            "filename": record.filename,
            "text": record.text_content,
            "skills": json.loads(record.skills) if record.skills else [],
            "uploaded_at": record.uploaded_at
        }
