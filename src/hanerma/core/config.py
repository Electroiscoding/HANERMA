import os


class Settings:
    """Centralized configuration loading from environment variables."""

    PROJECT_NAME = "HANERMA Orchestration Engine"
    VERSION = "1.0.0"

    # Local LLM Routing (primary path — zero API keys required)
    OLLAMA_ENDPOINT = os.getenv(
        "OLLAMA_ENDPOINT", "http://localhost:11434/api/generate"
    )
    DEFAULT_LOCAL_MODEL = os.getenv("DEFAULT_LOCAL_MODEL", "llama3")

    # Optional: Cloud / Aggregator fallback keys (leave blank for 100% local)
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    HF_TOKEN = os.getenv("HF_TOKEN", "")

    # Memory Limits
    MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "128000"))
    HCMS_VECTOR_DIMENSION = int(os.getenv("HCMS_VECTOR_DIMENSION", "1536"))


settings = Settings()
