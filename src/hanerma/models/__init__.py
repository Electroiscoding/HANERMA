
"""
LLM Agnostic Adapters.
"""
from .router import ModelRouter
from .cloud.openai_adapter import OpenAIAdapter
from .local.vllm_adapter import VLLMAdapter

__all__ = ["ModelRouter", "OpenAIAdapter", "VLLMAdapter"]
