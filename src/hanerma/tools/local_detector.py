"""
Local Model Detector — Auto-discovers running LLM backends.

Uses httpx to probe local endpoints and automatically configure
the default model backend for HANERMA.

Supported backends:
  - Ollama (http://localhost:11434)
  - LM Studio (http://localhost:1234)
  - vLLM / text-generation-inference (http://localhost:8000)
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("hanerma.local_detector")


# ═══════════════════════════════════════════════════════════════════════════
#  Backend Probes
# ═══════════════════════════════════════════════════════════════════════════

PROBES = [
    {
        "name": "ollama",
        "url": "http://localhost:11434/api/tags",
        "type": "ollama",
        "base_url": "http://localhost:11434",
    },
    {
        "name": "lm_studio",
        "url": "http://localhost:1234/v1/models",
        "type": "openai_compatible",
        "base_url": "http://localhost:1234/v1",
    },
    {
        "name": "vllm",
        "url": "http://localhost:8000/v1/models",
        "type": "openai_compatible",
        "base_url": "http://localhost:8000/v1",
    },
]


def detect_local_backends(timeout: float = 2.0) -> List[Dict[str, Any]]:
    """
    Probe all known local LLM endpoints.

    Returns a list of discovered backends:
        [{"name": "ollama", "url": ..., "models": [...], "type": ...}]
    """
    discovered = []

    for probe in PROBES:
        try:
            resp = httpx.get(probe["url"], timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                models = _extract_models(data, probe["type"])
                backend = {
                    "name": probe["name"],
                    "base_url": probe["base_url"],
                    "type": probe["type"],
                    "models": models,
                    "status": "online",
                }
                discovered.append(backend)
                logger.info(
                    "Discovered %s: %d models (%s)",
                    probe["name"],
                    len(models),
                    ", ".join(models[:5]),
                )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
            pass  # Not running
        except Exception as e:
            logger.debug("Probe %s failed: %s", probe["name"], e)

    return discovered


def _extract_models(data: Any, backend_type: str) -> List[str]:
    """Extract model names from backend API response."""
    models = []

    if backend_type == "ollama":
        # Ollama: {"models": [{"name": "llama3:latest", ...}]}
        for m in data.get("models", []):
            name = m.get("name", "")
            if name:
                models.append(name)

    elif backend_type == "openai_compatible":
        # OpenAI-compatible: {"data": [{"id": "model-name", ...}]}
        for m in data.get("data", []):
            mid = m.get("id", "")
            if mid:
                models.append(mid)

    return models


def get_default_model(timeout: float = 2.0) -> Dict[str, Any]:
    """
    Auto-detect and return the best available local model.

    Priority:
      1. Ollama (most common local setup)
      2. LM Studio
      3. vLLM / TGI
      4. Fallback to cloud placeholder

    Returns:
        {
            "model": "llama3:latest",
            "backend": "ollama",
            "base_url": "http://localhost:11434",
            "type": "ollama",
            "source": "auto_detected",
        }
    """
    backends = detect_local_backends(timeout=timeout)

    if not backends:
        logger.info("No local LLM backends detected, using cloud fallback")
        return {
            "model": "openrouter/meta-llama/llama-3-8b-instruct",
            "backend": "cloud",
            "base_url": "https://openrouter.ai/api/v1",
            "type": "openai_compatible",
            "source": "fallback",
        }

    # Pick the first available backend (priority by PROBES order)
    best = backends[0]
    model = best["models"][0] if best["models"] else "llama3"

    result = {
        "model": model,
        "backend": best["name"],
        "base_url": best["base_url"],
        "type": best["type"],
        "source": "auto_detected",
    }

    logger.info(
        "Auto-selected model: %s from %s (%s)",
        result["model"],
        result["backend"],
        result["base_url"],
    )

    return result


def is_ollama_running(timeout: float = 1.5) -> bool:
    """Quick check: is Ollama running on localhost?"""
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False


def list_ollama_models(timeout: float = 2.0) -> List[str]:
    """List available Ollama models."""
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=timeout)
        if resp.status_code == 200:
            return _extract_models(resp.json(), "ollama")
    except Exception:
        pass
    return []
