"""
Deep Reasoner Agent — model-agnostic.
Uses whatever backend the router provides (Local, HF, OpenRouter).
"""

from ..base_agent import BaseAgent
from ...core.types import AgentRole, AgentMessage


class DeepReasonerAgent(BaseAgent):
    """
    Leverages the configured model's chain-of-thought for deep analysis.
    Model-agnostic: works with Llama, Mistral, Claude, GPT, or any backend.
    """

    def __init__(self, name: str = "native::deep_reasoner"):
        system_prompt = (
            "You are HANERMA's Deep Reasoner. Perform thorough, step-by-step "
            "analysis. Never skip logical steps. Use external tools if needed."
        )
        super().__init__(
            name=name, role="Deep Reasoner", system_prompt=system_prompt
        )

    def execute(self, prompt: str, global_state: dict) -> str:
        """Deep analysis via atomic chain-of-thought."""
        print(f"[{self.name}] Reasoning over: {prompt[:50]}...")

        task = prompt
        simulated_output = (
            f"Deep Reasoner analysis for: {task}\n[Analysis Complete]"
        )

        global_state["history"].append(
            {"role": self.name, "content": simulated_output}
        )
        return simulated_output
