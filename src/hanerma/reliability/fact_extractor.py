import json
import requests
from typing import List, Dict, Any
from hanerma.reliability.symbolic_reasoner import SymbolicReasoner, ContradictionError

class ExtractionAgent:
    """
    Specialized agent that parses agent outputs into JSON claims for SymbolicReasoner.
    Triggers ContradictionError on numeric contradictions.
    """
    
    def __init__(self):
        pass
    
    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """
        Uses local LLM to extract factual claims from text as JSON list.
        """
        prompt = f"""Analyze the following text and extract all factual claims as a JSON list of objects.

Each claim should be in format: {{"variable": "name", "value": value, "type": "int|bool|str"}}

Text: {text}

Output ONLY the JSON list:"""
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen", "prompt": prompt, "stream": False}
        )
        response.raise_for_status()
        json_str = response.json()["response"].strip()
        
        try:
            claims = json.loads(json_str)
            return claims
        except json.JSONDecodeError:
            return []
    
    def verify_and_check(self, claims: List[Dict[str, Any]], symbolic_reasoner: SymbolicReasoner):
        """
        Pipes claims to SymbolicReasoner, raises ContradictionError on numeric contradictions.
        """
        # Convert claims to facts dict
        facts = {}
        for claim in claims:
            var = claim.get("variable")
            val = claim.get("value")
            typ = claim.get("type")
            if typ == "int":
                facts[var] = int(val)
            elif typ == "bool":
                facts[var] = bool(val)
            elif typ == "str":
                facts[var] = str(val)
        
        symbolic_reasoner.check_facts_consistency(facts)
