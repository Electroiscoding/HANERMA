import requests
import os
from typing import Optional, List

class LocalModelDetector:
    """
    Auto-detects running local model servers (Ollama, vLLM, LM Studio).
    Ensures 95% of use-cases require no environment variables or tokens.
    """
    def __init__(self):
        self.check_endpoints = {
            "ollama": "http://localhost:11434/api/tags",
            "vllm": "http://localhost:8000/v1/models",
            "lm_studio": "http://localhost:1234/v1/models"
        }

    def detect_best_local_model(self) -> str:
        """
        Scans local ports and returns the first available model string.
        Falls back to a default if nothing is found.
        """
        for provider, url in self.check_endpoints.items():
            try:
                response = requests.get(url, timeout=0.5)
                if response.status_code == 200:
                    models = self._parse_models(provider, response.json())
                    if models:
                        return f"{provider}/{models[0]}"
            except Exception:
                continue
        
        return "local-llama3" # Default fallback

    def _parse_models(self, provider: str, data: dict) -> List[str]:
        """Parses model names from provider-specific JSON responses."""
        if provider == "ollama":
            return [m["name"] for m in data.get("models", [])]
        elif provider in ["vllm", "lm_studio"]:
            return [m["id"] for m in data.get("data", [])]
        return []

    def get_auto_config(self) -> dict:
        """Returns a ready-to-use configuration dictionary for HANERMA."""
        model = self.detect_best_local_model()
        return {
            "model": model,
            "api_base": "http://localhost:11434/v1" if "ollama" in model else "http://localhost:8000/v1",
            "api_key": "not-needed-for-local"
        }
