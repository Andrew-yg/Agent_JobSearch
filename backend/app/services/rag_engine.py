"""RAG Engine for job-resume matching using ChromaDB."""
import json
from typing import List, Dict
from openai import OpenAI

from ..config import get_settings
from ..database import get_jobs_collection, get_resume_collection


class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) engine for matching
    resumes to job descriptions using vector similarity.
    """
    
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]  # Limit input length
        )
        return response.data[0].embedding
    
    def store_jobs(self, jobs: List[Dict]) -> int:
        """
        Store job descriptions in ChromaDB.
        Returns number of jobs stored.
        """
        if not jobs:
            return 0
        
        collection = get_jobs_collection()
        
        # Prepare data for batch insert
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for job in jobs:
            job_id = job.get("id", str(hash(job.get("title", ""))))
            
            # Create searchable text from job
            search_text = f"{job.get('title', '')} at {job.get('company', '')}. {job.get('description', '')}"
            
            # Generate embedding
            try:
                embedding = self.generate_embedding(search_text)
            except Exception as e:
                print(f"Error generating embedding for job {job_id}: {e}")
                continue
            
            ids.append(job_id)
            embeddings.append(embedding)
            documents.append(search_text[:5000])  # Limit document size
            metadatas.append({
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "salary": job.get("salary", ""),
                "posted_time": job.get("posted_time", ""),
                "url": job.get("url", ""),
                "logo_initial": job.get("logo_initial", "?")
            })
        
        if ids:
            # Upsert to handle duplicates
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        
        return len(ids)
    
    def search_matching_jobs(
        self,
        resume_id: str,
        top_k: int = 50
    ) -> List[Dict]:
        """
        Find top K jobs matching the resume using vector similarity.
        """
        # Get resume from collection
        resume_collection = get_resume_collection()
        resume_result = resume_collection.get(
            ids=[resume_id],
            include=["embeddings", "documents", "metadatas"]
        )
        
        if not resume_result["ids"]:
            raise ValueError(f"Resume {resume_id} not found")
        
        resume_embedding = resume_result["embeddings"][0]
        
        # Query jobs collection
        jobs_collection = get_jobs_collection()
        results = jobs_collection.query(
            query_embeddings=[resume_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        matched_jobs = []
        if results["ids"] and results["ids"][0]:
            for i, job_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                
                # Convert distance to similarity score (0-100)
                # ChromaDB uses L2 distance by default, lower is better
                similarity_score = max(0, 100 - (distance * 50))
                
                matched_jobs.append({
                    "id": job_id,
                    "title": metadata.get("title", ""),
                    "company": metadata.get("company", ""),
                    "location": metadata.get("location", ""),
                    "salary": metadata.get("salary"),
                    "posted_time": metadata.get("posted_time", ""),
                    "description": results["documents"][0][i] if results["documents"] else "",
                    "url": metadata.get("url", ""),
                    "logo_initial": metadata.get("logo_initial", "?"),
                    "similarity_score": round(similarity_score, 2)
                })
        
        # Sort by similarity score
        matched_jobs.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return matched_jobs
    
    def get_resume_text(self, resume_id: str) -> str:
        """Get resume text by ID."""
        resume_collection = get_resume_collection()
        result = resume_collection.get(
            ids=[resume_id],
            include=["documents"]
        )
        
        if result["documents"]:
            return result["documents"][0]
        return ""
    
    def clear_jobs(self):
        """Clear all jobs from collection (for fresh search)."""
        collection = get_jobs_collection()
        # Get all IDs and delete
        all_ids = collection.get()["ids"]
        if all_ids:
            collection.delete(ids=all_ids)
