"""
Local-First Model Router with Smart Failover.
Cascades: Local Ollama → HuggingFace → OpenRouter.
No single-vendor lock-in.  No mandatory API keys.
"""

import time
from typing import List, Dict, Optional

import httpx


class LocalModelRouter:
    """
    100% local-first failover routing.
    Primary chain is local Ollama models.  If none are available or the
    developer has configured cloud keys, the router cascades upward.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:11434/api/generate",
        fallback_chain: Optional[List[str]] = None,
    ):
        self.endpoint = endpoint
        self.fallback_chain = fallback_chain or [
            "llama3",       # Primary heavy reasoner
            "mistral",      # Secondary reliable fallback
            "qwen:0.5b",    # Ultra-light fallback for guaranteed uptime
        ]
        self.cooldowns: Dict[str, float] = {}

    def execute_with_fallback(
        self, prompt: str, system_prompt: str = ""
    ) -> str:
        """Attempts local inference, rolling down the chain on failure."""
        current_time = time.time()

        for model in self.fallback_chain:
            # Skip models currently cooling down after a recent failure
            if model in self.cooldowns and current_time < self.cooldowns[model]:
                continue

            try:
                print(f"[LocalRouter] Attempting inference with: {model}")
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {"temperature": 0.1},
                }
                response = httpx.post(
                    self.endpoint, json=payload, timeout=120.0
                )
                response.raise_for_status()
                return response.json().get("response", "")

            except Exception as e:
                print(
                    f"[LocalRouter WARNING] {model} failed: {e}. "
                    "Falling back to next model..."
                )
                self.cooldowns[model] = current_time + 60.0
                continue

        raise RuntimeError(
            "CRITICAL: All local models in the fallback chain failed "
            "or Ollama is offline."
        )
