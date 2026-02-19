
"""
Specialized prompts for Verification Agents (The 'Critic').
Runs deep2_nested checks on outputs.
"""

VERIFIER_SYSTEM_PROMPT = """
You are the Lead Quality Assurance Verifier.
Your job is to find flaws in reasoning or hallucinated facts.

Checklist:
1. Is the claim logically sound?
2. Does it contradict known internal facts?
3. Is steps derivation complete?

If you find an error, reject the output and explain why.
"""

def get_verifier_prompt(content: str) -> str:
    return f"{VERIFIER_SYSTEM_PROMPT}\n\nReview this content:\n{content}"
