"""
LLM Agnostic Adapters.
"""
from .router import LocalModelRouter
from .cloud_llm import OpenRouterAdapter, HuggingFaceAdapter
from .local_llm import LocalLLMAdapter

__all__ = ["LocalModelRouter", "OpenRouterAdapter", "HuggingFaceAdapter", "LocalLLMAdapter"]
