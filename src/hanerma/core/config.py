import os

class Settings:
    """Centralized configuration loading from environment variables."""
    PROJECT_NAME = "HANERMA Orchestration Engine"
    VERSION = "1.0.0"
    
    # API Keys (Defaults to empty for local-first execution)
    GROK_API_KEY = os.getenv("GROK_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Memory Limits
    MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "128000"))
    HCMS_VECTOR_DIMENSION = int(os.getenv("HCMS_VECTOR_DIMENSION", "1536"))

settings = Settings()
