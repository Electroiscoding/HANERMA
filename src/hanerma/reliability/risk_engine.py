import math
from collections import Counter
from typing import Dict, Any, List
import re

class FailurePredictor:
    """
    Computes risk scores using structural complexity analysis.
    """
    def __init__(self):
        # Common words for undefined variable detection
        self.common_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else', 'for', 'while',
            'with', 'from', 'into', 'by', 'on', 'at', 'to', 'of', 'in', 'out', 'up', 'down'
        ])
    
    def analyze_prompt_complexity(self, prompt: str) -> float:
        """
        Calculates Structural Ambiguity based on nested clauses, punctuation, and undefined variables.
        Returns 0.0-1.0 risk score.
        """
        if not prompt.strip():
            return 0.0
        
        # 1. Nested clause analysis (parentheses, brackets)
        nesting_score = self._calculate_nesting(prompt)
        
        # 2. Punctuation ambiguity (questions, exclamations)
        punctuation_score = self._calculate_punctuation_ambiguity(prompt)
        
        # 3. Undefined variable detection
        undefined_score = self._calculate_undefined_variables(prompt)
        
        # 4. Length-based complexity
        length_score = min(len(prompt.split()) / 100.0, 1.0)
        
        # Combine scores
        total_score = (nesting_score * 0.3) + (punctuation_score * 0.2) + (undefined_score * 0.3) + (length_score * 0.2)
        
        return min(total_score, 1.0)
    
    def _calculate_nesting(self, prompt: str) -> float:
        """Calculate nesting depth of clauses."""
        max_depth = 0
        current_depth = 0
        for char in prompt:
            if char in '({[':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in ')}]':
                current_depth = max(0, current_depth - 1)
        
        # Normalize: depth > 3 is high risk
        return min(max_depth / 3.0, 1.0)
    
    def _calculate_punctuation_ambiguity(self, prompt: str) -> float:
        """Calculate ambiguity from punctuation."""
        questions = prompt.count('?')
        exclamations = prompt.count('!')
        ellipses = prompt.count('...')
        
        # High question/exclamation density indicates uncertainty
        total_punct = questions + exclamations + ellipses
        density = total_punct / max(len(prompt.split()), 1)
        
        return min(density * 10, 1.0)
    
    def _calculate_undefined_variables(self, prompt: str) -> float:
        """Detect potentially undefined variables or concepts."""
        words = re.findall(r'\b\w+\b', prompt.lower())
        unique_words = set(words)
        
        # Count words that might be undefined (not common, not in typical vocab)
        undefined_count = 0
        for word in unique_words:
            if len(word) > 3 and word not in self.common_words and not word.isdigit():
                # Check if it looks like a variable (mixed case, underscores)
                if '_' in word or any(c.isupper() for c in word[1:]):
                    undefined_count += 1
        
        # Normalize: >5 undefined vars is high risk
        return min(undefined_count / 5.0, 1.0)

    def compute_risk(self, prompt: str, model: str, context_length: int) -> Dict[str, Any]:
        """
        Returns risk report with structural analysis.
        """
        base_score = self.analyze_prompt_complexity(prompt)
        reasons = []
        
        # Adjust for context length
        if context_length > 10000:
            base_score += 0.2
            reasons.append("Large context window increases risk")
        
        # Adjust for model capability
        if "local" in model.lower() and base_score > 0.5:
            base_score += 0.1
            reasons.append("Local model may struggle with complex structure")
        
        final_score = min(base_score, 1.0)
        
        if final_score > 0.5:
            reasons.append("High structural complexity detected")
        
        action = "route_frontier" if final_score > 0.7 else "route_local" if final_score < 0.3 else "route_auto"
        
        return {
            "risk_score": round(final_score, 2),
            "reasons": reasons,
            "action": action
        }
