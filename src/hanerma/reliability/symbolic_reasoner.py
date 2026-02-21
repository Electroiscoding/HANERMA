import z3
from typing import Dict, Any

class ContradictionError(Exception):
    """Raised when facts are mathematically contradictory."""
    pass

class SymbolicReasoner:
    """
    Runs deterministic symbolic cross-checks using Z3 Theorem Prover.
    Checks for logical contradictions in factual claims.
    Includes self-evolving ruleset.
    """
    def __init__(self, bus=None):
        self.bus = bus
        self.rules: List[str] = []
    
    def add_rule(self, rule: str):
        """Adds a new logical axiom to the ruleset."""
        self.rules.append(rule)
        print(f"[SymbolicReasoner] Added new axiom: {rule}")
    def check_facts_consistency(self, facts: Dict[str, Any]) -> None:
        """
        Takes a JSON dictionary of facts, dynamically converts them into Z3 variables,
        asserts them into a Z3 solver, and checks for unsatisfiability (contradiction).
        Raises ContradictionError if unsat.
        """
        solver = z3.Solver()
        for key, value in facts.items():
            if isinstance(value, int):
                var = z3.Int(key)
                solver.add(var == value)
            elif isinstance(value, bool):
                var = z3.Bool(key)
                solver.add(var == value)
            elif isinstance(value, str):
                var = z3.String(key)
                solver.add(var == value)
            # Add more types as needed (float, etc.)
            else:
                # For unsupported types, skip or handle
                pass
        
        result = solver.check()
        if result == z3.unsat:
            if self.bus:
                self.bus.record_step("failure_patterns", 0, "log", {"facts": facts, "type": "contradiction"})
            raise ContradictionError("The provided facts are mathematically contradictory.") 
