import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    DATAGOVSG_API_KEY: str = os.getenv("DATAGOVSG_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Database
    DATABASE_URL: str = "sqlite:///./govdata.db"

    # FastAPI
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # LLM Settings
    TEMPERATURE: float = 0.1

    # Mistral API models (tiered by task)
    MISTRAL_ROUTING_MODEL: str = "mistral-small-latest"     # fast, 50 req/min — routing & parsing
    MISTRAL_NARRATIVE_MODEL: str = "mistral-large-latest"   # quality, 4 req/min  — narratives
    MISTRAL_REASONING_MODEL: str = "magistral-medium-latest" # chain-of-thought, 5 req/min — cross-domain

    # Local Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:14b"                       # unlimited, ~25 tok/s on M4 Pro

    # Gemini fallback
    GEMINI_MODEL: str = "gemini-flash-latest"

    # Legacy aliases (kept so existing code referencing these doesn't break)
    DEFAULT_MODEL: str = "mistral-small-latest"
    FALLBACK_MODEL: str = "gemini-flash-latest"
    TERTIARY_MODEL: str = "open-mistral-nemo"
    
    # Redis Settings (for Celery)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    class Config:
        env_file = ".env"

settings = Settings()
