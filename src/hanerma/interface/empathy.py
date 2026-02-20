from typing import Dict, Any

class EmpathyEngine:
    """
    Traps stack traces and outputs conversational, actionable failure messages.
    Ensures the user feels supported rather than frustrated by technical errors.
    """
    def __init__(self):
        self.empathy_responses = {
            "RateLimitError": "It looks like the models are a bit overwhelmed right now. Should I: 1) Wait and retry 2) Switch to a local model?",
            "ContradictionError": "The reasoner got a bit confused because fact X contradicts memory Y. Should I force a re-reason or ask for your input?",
            "ContextOverflow": "We're running out of room to think! I can compress the history for you or we can start a fresh thread."
        }

    def handle_failure(self, error_type: str, context: str) -> str:
        """Returns a friendly, human-like failure message."""
        message = self.empathy_responses.get(error_type, "Something went slightly off-track here.")
        return f"[HANERMA Assistant] {message} (Context: {context})"

def friendly_fail(error_type: str, context: str = ""):
    engine = EmpathyEngine()
    return engine.handle_failure(error_type, context)
