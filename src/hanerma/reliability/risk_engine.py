import re
from typing import Dict, Any, List

class FailurePredictor:
    """
    Computes a "risk score" for LLM calls before execution.
    Analyzes prompt complexity, domain, and historical failure patterns.
    """
    def __init__(self):
        self.risk_patterns = {
            "hallucination": [r"fact", r"statistic", r"date", r"citation"],
            "complexity": [r"nested", r"recursion", r"mathematical", r"logic"],
            "cost": [r"summarize", r"analyze all", r"entire codebase"]
        }

    def compute_risk(self, prompt: str, model: str, context_length: int) -> Dict[str, Any]:
        """
        Returns a risk report with a normalized score (0.0 to 1.0).
        """
        score = 0.0
        reasons = []

        # 1. Complexity heuristic
        complexity_hits = sum(1 for p in self.risk_patterns["complexity"] if re.search(p, prompt, re.I))
        if complexity_hits > 2:
            score += 0.3
            reasons.append("High logical complexity detected")

        # 2. Hallucination risk
        fact_hits = sum(1 for p in self.risk_patterns["hallucination"] if re.search(p, prompt, re.I))
        if fact_hits > 2:
            score += 0.4
            reasons.append("High probability of factual extraction (hallucination risk)")

        # 3. Context/Cost risk
        if context_length > 10000:
            score += 0.2
            reasons.append("Large context window usage (cost/latency risk)")

        # 4. Model sensitivity
        if "local" in model.lower() and complexity_hits > 1:
            score += 0.1
            reasons.append("Potential reasoning bottleneck for local model")

        normalized_score = min(score, 1.0)
        
        return {
            "risk_score": round(normalized_score, 2),
            "reasons": reasons,
            "action": "block" if normalized_score > 0.8 else "rewrite" if normalized_score > 0.5 else "proceed"
        }

    def propose_mitigation(self, risk_report: Dict[str, Any]) -> str:
        """Suggests a prompt rewrite or verifier insertion."""
        if risk_report["action"] == "rewrite":
            return "Insert verifier: [Cross-check facts against HCMS]"
        elif risk_report["action"] == "block":
            return "Decompose task into smaller sub-problems"
        return "None required"
