"""FastAPI Main Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings, init_directories
from app.routers import upload, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_directories()
    print("🚀 Agent_JobSearch Backend Started")
    print(f"📁 Upload directory: {get_settings().upload_directory}")
    print(f"🗄️  ChromaDB directory: {get_settings().chroma_persist_directory}")
    yield
    # Shutdown
    print("👋 Agent_JobSearch Backend Shutting Down")


app = FastAPI(
    title="Agent_JobSearch API",
    description="LinkedIn Job Search Agent with RAG matching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api")
app.include_router(search.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Agent_JobSearch API",
        "docs": "/docs",
        "endpoints": {
            "upload": "/api/upload",
            "search": "/api/search"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "openai_configured": bool(settings.openai_api_key),
        "playwright_mcp": settings.use_playwright_mcp
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
