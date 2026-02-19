from typing import Dict, Any

class PromptTemplates:
    """
    Standardized Zero-Shot and Few-Shot templates for Deep 1 (Atomic) agents.
    Forcing structured JSON output is critical for 100% downstream parsing reliability.
    """
    
    ATOMIC_REASONER = """You are an atomic reasoner. 
Step 1: Break down the user's request into independent claims.
Step 2: For each claim, assign a confidence score (0.0 - 1.0).
Step 3: If confidence < 0.9, mark it for Deep 2 Verification.

Output Format (JSON Only):
{
  "claims": [
    {"text": "...", "confidence": 0.95, "needs_verification": false},
    {"text": "...", "confidence": 0.40, "needs_verification": true}
  ]
}
"""

    FULL_SYSTEM_PROMPT = """You are HANERMA, a zero-error orchestrator.
Do not generate code unless you have reasoned through the edge cases.
Do not state facts unless you have verified them against the HCMS context.
"""
