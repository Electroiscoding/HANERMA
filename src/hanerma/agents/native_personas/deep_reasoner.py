"""
Deep Reasoner Agent — model-agnostic.
Uses whatever backend the router provides (Local, HF, OpenRouter).
"""

from ..base_agent import BaseAgent


class DeepReasonerAgent(BaseAgent):
    """
    Leverages the configured model's chain-of-thought for deep analysis.
    Model-agnostic: works with Llama, Mistral, Claude, GPT, or any backend.
    """

    def __init__(self, name: str = "native::deep_reasoner", model: str = None):
        system_prompt = (
            "You are HANERMA's Deep Reasoner. Perform thorough, step-by-step "
            "analysis. Never skip logical steps. Use external tools if needed."
        )
        super().__init__(
            name=name, role="Deep Reasoner", system_prompt=system_prompt, model=model
        )

    # Inherits execute() from BaseAgent which now supports real LLM calls
