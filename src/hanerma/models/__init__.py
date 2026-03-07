"""
LLM Agnostic Adapters + Grammar Shield (Constrained Decoding).
"""
from .router import LocalModelRouter
from .cloud_llm import OpenRouterAdapter, HuggingFaceAdapter
from .local_llm import LocalLLMAdapter
from .constrained import (
    GrammarShield,
    BackendType,
    AgentOutput,
    ReasoningStep,
    ToolCallRequest,
    MultiToolPlan,
    OutlinesBackend,
    InstructorBackend,
    OllamaConstrainedBackend,
)

__all__ = [
    "LocalModelRouter",
    "OpenRouterAdapter",
    "HuggingFaceAdapter",
    "LocalLLMAdapter",
    "GrammarShield",
    "BackendType",
    "AgentOutput",
    "ReasoningStep",
    "ToolCallRequest",
    "MultiToolPlan",
    "OutlinesBackend",
    "InstructorBackend",
    "OllamaConstrainedBackend",
]
