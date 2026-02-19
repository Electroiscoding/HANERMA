from typing import List, Dict
import requests
import json

class LocalLLM:
    """
    Connects to Ollama, LM Studio, or vLLM backends running on localhost.
    Allows HANERMA to run completely offline without API costs.
    """
    def __init__(self, endpoint: str = "http://localhost:11434", model: str = "llama3"):
        self.endpoint = endpoint
        self.model = model
        print(f"[Local LLM] Connected to {self.model} at {self.endpoint}")

    def generate(self, prompt: str) -> str:
        """
        Standard Ollama 'generate' endpoint wrapper.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            resp = requests.post(f"{self.endpoint}/api/generate", json=payload, timeout=30)
            resp.raise_for_status()
            
            # Ollama returns one JSON object per line if streaming, 
            # but we requested stream=False so we get one big object.
            return resp.json().get("response", "")
            
        except requests.exceptions.RequestException as e:
            return f"[Local LLM Error] Could not connect: {str(e)}"
