import math
from collections import Counter
from typing import Dict, Any, List

class FailurePredictor:
    """
    Computes a "risk score" for LLM calls before execution using token entropy and structural analysis.
    """
    def __init__(self):
        pass

    def analyze_prompt_complexity(self, prompt: str) -> float:
        """
        Calculates token entropy and structural ambiguity to generate a Risk Score (0.0 to 1.0).
        """
        if not prompt.strip():
            return 0.0
        
        # Tokenize and compute entropy
        tokens = prompt.split()
        if not tokens:
            return 0.0
        
        freq = Counter(tokens)
        total = len(tokens)
        entropy = -sum((count / total) * math.log2(count / total) for count in freq.values())
        
        # Structural ambiguity: count punctuation and nesting indicators
        ambiguity_score = (
            prompt.count('?') * 2 +  # Questions increase ambiguity
            prompt.count('!') * 1.5 +
            prompt.count('(') + prompt.count(')') +
            prompt.count('[') + prompt.count(']') +
            prompt.count('{') + prompt.count('}') +
            prompt.count('if ') + prompt.count('else ') +  # Control flow
            prompt.count('for ') + prompt.count('while ')
        )
        
        # Normalize and combine
        normalized_entropy = min(entropy / 10.0, 1.0)  # Cap at 1.0
        normalized_ambiguity = min(ambiguity_score / 20.0, 1.0)
        
        risk_score = (normalized_entropy * 0.6) + (normalized_ambiguity * 0.4)
        return min(risk_score, 1.0)

    def compute_risk(self, prompt: str, model: str, context_length: int) -> Dict[str, Any]:
        """
        Returns a risk report with normalized score and action (inject CriticAgent if >0.8).
        """
        base_score = self.analyze_prompt_complexity(prompt)
        reasons = []
        
        # Adjust for context length
        if context_length > 10000:
            base_score += 0.2
            reasons.append("Large context window (cost/latency risk)")
        
        # Adjust for model sensitivity
        if "local" in model.lower() and base_score > 0.3:
            base_score += 0.1
            reasons.append("Potential reasoning bottleneck for local model")
        
        final_score = min(base_score, 1.0)
        
        if final_score > 0.5:
            reasons.append("High entropy/structural complexity")
        
        action = "inject_critic" if final_score > 0.8 else "proceed"
        
        return {
            "risk_score": round(final_score, 2),
            "reasons": reasons,
            "action": action
        }
