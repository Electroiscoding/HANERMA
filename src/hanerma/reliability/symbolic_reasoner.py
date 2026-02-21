import z3
from typing import List, Dict, Any, Optional
import re

class ContradictionError(Exception):
    """Raised when facts are mathematically contradictory."""
    pass

class ConstraintCompiler:
    """
    Translates natural language claims into Z3 predicates.
    """
    def __init__(self):
        self.variables: Dict[str, z3.ExprRef] = {}
    
    def compile_claim(self, claim: str) -> Optional[z3.ExprRef]:
        """
        Parse a natural language claim into a Z3 expression.
        Supports simple patterns like "X is Y", "X must be > Y", etc.
        """
        claim = claim.lower().strip()
        
        # Pattern: "variable is value"
        match = re.match(r'(\w+)\s+is\s+(\d+)', claim)
        if match:
            var_name, value = match.groups()
            var = self._get_var(var_name, z3.IntSort())
            return var == int(value)
        
        # Pattern: "variable must be >= value"
        match = re.match(r'(\w+)\s+must\s+be\s*>=\s*(\d+)', claim)
        if match:
            var_name, value = match.groups()
            var = self._get_var(var_name, z3.IntSort())
            return var >= int(value)
        
        # Pattern: "variable > value"
        match = re.match(r'(\w+)\s*>\s*(\d+)', claim)
        if match:
            var_name, value = match.groups()
            var = self._get_var(var_name, z3.IntSort())
            return var > int(value)
        
        # Pattern: "variable < value"
        match = re.match(r'(\w+)\s*<\s*(\d+)', claim)
        if match:
            var_name, value = match.groups()
            var = self._get_var(var_name, z3.IntSort())
            return var < int(value)
        
        # Pattern: "variable == value"
        match = re.match(r'(\w+)\s*==\s*(\d+)', claim)
        if match:
            var_name, value = match.groups()
            var = self._get_var(var_name, z3.IntSort())
            return var == int(value)
        
        # Boolean patterns
        if "true" in claim:
            match = re.match(r'(\w+)\s+is\s+true', claim)
            if match:
                var_name = match.group(1)
                var = self._get_var(var_name, z3.BoolSort())
                return var == True
        
        if "false" in claim:
            match = re.match(r'(\w+)\s+is\s+false', claim)
            if match:
                var_name = match.group(1)
                var = self._get_var(var_name, z3.BoolSort())
                return var == False
        
        # Add more patterns as needed
        return None  # Unparseable claim
    
    def _get_var(self, name: str, sort):
        """Get or create a Z3 variable."""
        if name not in self.variables:
            if sort == z3.IntSort():
                self.variables[name] = z3.Int(name)
            elif sort == z3.BoolSort():
                self.variables[name] = z3.Bool(name)
            else:
                self.variables[name] = z3.Const(name, sort)
        return self.variables[name]

class SymbolicReasoner:
    """
    Runs deterministic symbolic cross-checks using Z3 Theorem Prover.
    Checks for logical contradictions in factual claims.
    Includes self-evolving ruleset.
    """
    def __init__(self, bus=None):
        self.bus = bus
        self.rules: List[str] = []
        self.compiler = ConstraintCompiler()
    
    def add_rule(self, rule: str):
        """Adds a new logical axiom to the ruleset."""
        self.rules.append(rule)
        print(f"[SymbolicReasoner] Added new axiom: {rule}")
    
    def check_facts_consistency(self, claims: List[str]) -> None:
        """
        Takes a list of natural language claims, compiles them into Z3 constraints,
        adds rules, and checks for satisfiability. Raises ContradictionError if unsat.
        """
        solver = z3.Solver()
        
        # Compile and add claims
        for claim in claims:
            constraint = self.compiler.compile_claim(claim)
            if constraint is not None:
                solver.add(constraint)
        
        # Add rules as additional constraints
        for rule in self.rules:
            constraint = self.compiler.compile_claim(rule)
            if constraint is not None:
                solver.add(constraint)
        
        result = solver.check()
        if result == z3.unsat:
            if self.bus:
                self.bus.record_step("failure_patterns", 0, "log", {"claims": claims, "rules": self.rules, "type": "contradiction"})
            raise ContradictionError("The provided claims are mathematically contradictory with the current ruleset.")
        
        # If sat, optionally get model for verification
        if result == z3.sat:
            model = solver.model()
            # Could log or return model for debugging 
