"""Application configuration settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI
    openai_api_key: str = ""
    
    # Paths
    chroma_persist_directory: str = "./data/chroma"
    upload_directory: str = "./data/uploads"
    
    # Browser Automation
    use_playwright_mcp: bool = True
    chrome_user_data_dir: str = ""
    
    # API Settings
    api_prefix: str = "/api"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Ensure directories exist
def init_directories():
    """Create necessary directories if they don't exist."""
    settings = get_settings()
    Path(settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
    Path(settings.upload_directory).mkdir(parents=True, exist_ok=True)
