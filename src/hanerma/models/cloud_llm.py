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
    """Routes HANERMA to Hugging Face Serverless Inference API via native client.
    
    Supports provider-suffixed model names like:
        'Qwen/Qwen3-Coder-Next-FP8:together'
        'meta-llama/Meta-Llama-3-8B-Instruct'  (default HF provider)
    """

    def __init__(self, model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct"):
        # Parse provider suffix: "org/model:provider" → model="org/model", provider="provider"
        if ":" in model_name:
            self.model_name, self.provider = model_name.rsplit(":", 1)
        else:
            self.model_name = model_name
            self.provider = None  # Use default HF inference

        from huggingface_hub import InferenceClient
        api_key = os.getenv("HF_TOKEN")
        if not api_key:
            print("[WARNING] HF_TOKEN is missing. Hugging Face calls may fail.")

        # Initialize with provider if specified
        if self.provider:
            self.client = InferenceClient(api_key=api_key, provider=self.provider)
            print(f"[HuggingFace] Using routed provider: {self.provider}")
        else:
            self.client = InferenceClient(api_key=api_key)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        print(f"[HuggingFace] Executing intent on: {self.model_name}" +
              (f" (via {self.provider})" if self.provider else ""))

        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                max_tokens=2048
            )

            full_response = ""
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    full_response += content

            return full_response

        except Exception as e:
            print(f"[HuggingFace Error] {e}")
            return f"Error generating response from {self.model_name}: {str(e)}"

