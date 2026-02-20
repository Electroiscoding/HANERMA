"""
100% Local LLM Adapter.
Talks to Ollama, vLLM, LM Studio, or llama-server — whatever is
running on the developer's machine.  Zero internet required.
"""

import httpx


class LocalLLMAdapter:
    """100% Local Execution via Ollama / vLLM.  Zero internet required."""

    def __init__(
        self,
        model_name: str = "llama3",
        endpoint: str = "http://localhost:11434/api/generate",
    ):
        self.model_name = model_name
        self.endpoint = endpoint

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        print(f"[Local] Executing intent on offline model: {self.model_name}")
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
        }
        response = httpx.post(self.endpoint, json=payload, timeout=120.0)
        response.raise_for_status()
        return response.json().get("response", "")
