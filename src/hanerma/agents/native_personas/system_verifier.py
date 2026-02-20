from hanerma.agents.base_agent import BaseAgent
from hanerma.reasoning.deep2_nested import NestedVerifier

class SystemVerifier(BaseAgent):
    """
    A framework-native agent that enforces Deep 2 Nested Reasoning.
    It does not generate code; it aggressively attacks and verifies 
    the outputs of other agents against the HCMS.
    """
    def __init__(self, name: str = "native::system_verifier", memory_store=None, model: str = None):
        system_prompt = (
            "You are the HANERMA System Verifier. Your sole purpose is to cross-check "
            "claims made by other agents. If an agent hallucinated, you must return "
            "a strict correction payload. Do not be polite. Be mathematically precise."
        )
        super().__init__(name=name, role="Fact-Checker", system_prompt=system_prompt, model=model)
        self.verifier_logic = NestedVerifier(memory_store=memory_store)

    def execute(self, prompt: str, global_state: dict) -> str:
        """Overrides standard execution to enforce HCMS cross-checking."""
        # Extract the claim from the prompt
        claim_to_check = prompt.replace("[Verify]:", "").strip()
        
        # Run against the infinite memory store
        is_valid, reason = self.verifier_logic.cross_check(
            session_id=global_state.get("session_id", "default"), 
            atomic_claim=claim_to_check
        )
        
        if not is_valid:
            return f"[REJECTED] {reason}"
            
        return "[APPROVED] Claim aligns with verified memory."
