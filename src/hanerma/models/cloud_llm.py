"""
Cloud LLM Adapters — OpenRouter + HuggingFace.
Both use the standard OpenAI SDK with a swapped base_url.
No vendor lock-in. No Grok monopoly.
"""

import os
from openai import OpenAI


class OpenRouterAdapter:
    """Routes HANERMA to 300+ models via OpenRouter's unified gateway."""

    def __init__(self, model_name: str = "anthropic/claude-3.5-sonnet"):
        self.model_name = model_name
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        print(f"[OpenRouter] Executing intent on: {self.model_name}")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content


class HuggingFaceAdapter:
    """Routes HANERMA to Hugging Face Serverless Inference API."""

    def __init__(self, model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct"):
        self.model_name = model_name
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=os.getenv("HF_TOKEN"),
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        print(f"[HuggingFace] Executing intent on: {self.model_name}")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
