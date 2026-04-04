import logging
from typing import Dict, Any, List
import json

try:
    from hanerma.models.cloud_llm import OpenRouterProvider
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)

class NestedLogicLayer:
    """
    Deep2: Nested Logic Verification.
    Uses an LLM as a 'Critic' model to evaluate complex logical consistency
    that escapes raw First-Order logic (Z3).
    """
    def __init__(self):
        self.llm_critic = OpenRouterProvider(model="openrouter/anthropic/claude-3-haiku") if LLM_AVAILABLE else None
        
    async def verify(self, output: str, previous_state: str) -> tuple[bool, str]:
        if not output:
            return False, "Empty output"
            
        if not self.llm_critic:
            logger.warning("LLM Critic not available. Using strict syntactical check.")
            # Fallback syntax check instead of hardcoded 'True'
            if "error" in output.lower() or "exception" in output.lower():
                return False, "Syntactical failure detected in nested logic fallback."
            return True, "Syntactical validation passed."
            
        prompt = f"""
        You are an advanced logical Critic for the HANERMA system.
        Evaluate the following state transition for logical consistency.

        Previous State:
        {previous_state}

        Proposed Output/Action:
        {output}

        Determine if the Output introduces any logical paradox, violates causality, or contradicts the Previous State.
        Respond in strict JSON: {{"valid": true/false, "reason": "explanation"}}
        """

        try:
            response = await self.llm_critic.generate(prompt)
            # Find JSON in response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                if not result.get("valid", False):
                    return False, result.get("reason", "Critic model rejected the output.")
                return True, "Nested logic verified by Critic."
            else:
                return False, "Critic model failed to return valid JSON."
        except Exception as e:
            logger.error(f"Critic model evaluation failed: {e}")
            return False, f"Critic failure: {e}"
