
"""
Prompt Enhancer - Layer 1 Pre-processing.
Bulletproofs user input using a fast, cheap local model.
"""
from hanerma.models.local_llm import LocalLLMAdapter
import os

class AutoPromptEnhancer:
    """
    Upgrades raw user inputs into structured, enterprise-grade prompts.
    Uses a sub-10ms local model when available, falls back to structural templating.
    """
    def __init__(self, model_name: str = "qwen2.5:0.5b"):
        # We use a tiny model for speed (0.5b or 1.5b)
        self.local_model = LocalLLMAdapter(model_name=model_name)
        self.use_model = os.getenv("USE_LOCAL_ENHANCER", "false").lower() == "true"
        
        self.system_instructions = (
            "You are the HANERMA Prompt Optimizer. "
            "Rewrite the user's prompt to be extremely clear, concise, and structured for an AI agent. "
            "Add instructions for zero-error execution and explicit tool usage if applicable. "
            "Output ONLY the optimized prompt. No conversation."
        )

    async def enhance(self, raw_prompt: str) -> str:
        """
        Rewrites the prompt using a local model or applies structural templates.
        """
        if self.use_model:
            try:
                # LocalLLMAdapter.generate is sync for now, but we'll await it in spirit 
                # or wrap it if we had a thread pool. For now, we'll keep it simple.
                print(f"[Enhancer] Bulletproofing prompt with local model ({self.local_model.model_name})...")
                optimized = self.local_model.generate(
                    prompt=f"Optimize this prompt: {raw_prompt}",
                    system_prompt=self.system_instructions
                )
                if optimized.strip():
                    return optimized.strip()
            except Exception as e:
                print(f"[Enhancer Warning] Local model enhancement failed: {e}. Using template fallback.")

        # Template Fallback (Ultra Fast)
        return (
            f"[SYSTEM_INSTRUCTION: APEX_V4_CORE]\n"
            f"1. DECOMPOSE: Break the following task into atomic, verifiable steps.\n"
            f"2. EXECUTE: Use available tools (web_search, calculator, sandbox) for any data retrieval or computation.\n"
            f"3. VERIFY: Cross-check outputs before final delivery.\n\n"
            f"USER_TASK: {raw_prompt}"
        )
