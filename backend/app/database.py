"""Database setup for SQLite and ChromaDB."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from sqlalchemy import create_engine, Column, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pathlib import Path
from functools import lru_cache

from .config import get_settings

Base = declarative_base()


class ResumeRecord(Base):
    """SQLite table for resume records."""
    __tablename__ = "resumes"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    text_content = Column(Text, nullable=False)
    skills = Column(Text)  # JSON string of skills
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class JobRecord(Base):
    """SQLite table for cached job records."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    salary = Column(String)
    posted_time = Column(String)
    description = Column(Text)
    url = Column(String)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class SearchHistory(Base):
    """SQLite table for search history."""
    __tablename__ = "search_history"
    
    id = Column(String, primary_key=True)
    resume_id = Column(String, nullable=False)
    keywords = Column(String)
    location = Column(String)
    jobs_found = Column(String)  # JSON list of job IDs
    search_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


# SQLite Engine
def get_sqlite_engine():
    """Get SQLite database engine."""
    settings = get_settings()
    db_path = Path(settings.upload_directory).parent / "jobs.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get SQLite session."""
    engine = get_sqlite_engine()
    Session = sessionmaker(bind=engine)
    return Session()


# ChromaDB Client
@lru_cache()
def get_chroma_client() -> chromadb.Client:
    """Get ChromaDB client with persistence."""
    settings = get_settings()
    persist_path = Path(settings.chroma_persist_directory).absolute()
    persist_path.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(persist_path),
        settings=ChromaSettings(
            anonymized_telemetry=False
        )
    )
    return client


def get_resume_collection():
    """Get or create resume embeddings collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="resumes",
        metadata={"description": "Resume embeddings for matching"}
    )


def get_jobs_collection():
    """Get or create jobs embeddings collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="jobs",
        metadata={"description": "Job description embeddings"}
    )
