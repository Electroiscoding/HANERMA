"""
Deep Neuro-Symbolic Verification (The Mathematical Firewall).

Takes the structured JSON assertions guaranteed by the Grammar Shield (Slice 3)
and programmatically compiles them into Z3 constraints.

If the LLM reasoning contains logical contradictions, Z3 will prove it 'unsat'
and raise a ContradictionError, triggering a retry loop in the orchestration layer.
"""

import logging
from typing import Any, Dict, List, Set

import z3

logger = logging.getLogger("hanerma.symbolic_reasoner")


class ContradictionError(Exception):
    """Raised when an agent's reasoning contains mathematical contradictions."""
    pass


class LogicCompiler:
    """
    Programmatic translator from JSON assertions to Z3 logic.
    Zero LLM involvement in this step. Pure math.
    """

    def __init__(self):
        self._solver = z3.Solver()
        self._variables: Dict[str, z3.ExprRef] = {}
        # Keep track of variable types to prevent sort mismatch (e.g., comparing Int to Bool)
        self._sorts: Dict[str, z3.SortRef] = {}

    def _get_or_create_var(self, fact_name: str, python_val: Any) -> z3.ExprRef:
        """Create a Z3 variable matching the type of the Python value."""
        if fact_name in self._variables:
            return self._variables[fact_name]

        if isinstance(python_val, bool):
            var = z3.Bool(fact_name)
            self._sorts[fact_name] = z3.BoolSort()
        elif isinstance(python_val, int):
            var = z3.Int(fact_name)
            self._sorts[fact_name] = z3.IntSort()
        elif isinstance(python_val, float):
            var = z3.Real(fact_name)
            self._sorts[fact_name] = z3.RealSort()
        else:
            # For strings/unsupported types, we hash them into Ints for basic equality checks
            var = z3.Int(fact_name)
            self._sorts[fact_name] = z3.IntSort()
            
        self._variables[fact_name] = var
        return var

    def _get_z3_value(self, python_val: Any) -> Any:
        """Convert a python value to something Z3 can compare against."""
        if isinstance(python_val, (bool, int, float)):
            return python_val
        # Hash strings to integers so we can do == and != checks in Z3
        return hash(str(python_val))

    def _apply_operator(
        self, var: z3.ExprRef, operator: str, val: Any
    ) -> z3.BoolRef:
        """Map string operators to Z3 AST nodes."""
        if operator == "==":
            return var == val
        elif operator == "!=":
            return var != val
        elif operator == ">=":
            return var >= val
        elif operator == "<=":
            return var <= val
        elif operator == ">":
            return var > val
        elif operator == "<":
            return var < val
        else:
            raise ValueError(f"Unsupported mathematical operator: '{operator}'")

    def compile_and_check(self, assertions: List[Dict[str, Any]]) -> None:
        """
        Compile a list of JSON assertions into Z3 and check for consistency.
        
        Args:
            assertions: List of dicts e.g. [{"fact": "age", "operator": ">=", "value": 18}]
            
        Raises:
            ContradictionError: If the assertions contradict each other or prior facts.
            ValueError: If the assertion schema is invalid.
        """
        if not assertions:
            return

        logger.debug("Compiling %d assertions to Z3", len(assertions))

        # Push a new context frame so we can verify this specific batch
        self._solver.push()

        try:
            for ast_dict in assertions:
                fact = ast_dict.get("fact")
                operator = ast_dict.get("operator")
                value = ast_dict.get("value")

                if not fact or not operator or value is None:
                    logger.warning("Skipping malformed assertion: %s", ast_dict)
                    continue

                # 1. Map to Z3 Var Types
                z3_var = self._get_or_create_var(fact, value)
                z3_val = self._get_z3_value(value)

                # Prevent Z3 SortMismatch exceptions (e.g. comparing IntVar == True)
                if isinstance(value, bool) and self._sorts[fact] != z3.BoolSort():
                    raise ContradictionError(f"Type mismatch: '{fact}' was proven as non-boolean, but new assertion implies boolean.")

                # 2. Build mathematical expression
                expr = self._apply_operator(z3_var, operator, z3_val)

                # 3. Add to constraint solver
                self._solver.add(expr)

            # 4. Prove Theorem
            result = self._solver.check()

            if result == z3.unsat:
                # Get the conflicting core if possible, or just raise
                raise ContradictionError(
                    f"Z3 Solver found logical contradiction in agent assertions: {assertions}"
                )
            elif result == z3.unknown:
                logger.warning("Z3 solver returned 'unknown' for assertions: %s", assertions)

        except z3.Z3Exception as e:
            # Pop the failed frame to keep base solver clean
            self._solver.pop()
            raise ValueError(f"Failed to compile logic to Z3: {e}")

        except ContradictionError:
            self._solver.pop()
            raise

        # If SAT, we commit the frame (leave it pushed, remove pop)
        # But for an agent step-by-step firewall, usually we just want to
        # accumulate. To keep global state clean from ephemeral steps, 
        # we might pop. Here, we'll keep them to build a global proof chain.
        # So we do NOT pop on success.


class SymbolicReasoner:
    """
    Main interface for the Mathematical Firewall.
    Connects to the Orchestrator to validate agent traces.
    """
    
    def __init__(self, bus: Any = None):
        self.compiler = LogicCompiler()
        self.bus = bus

    def verify_agent_output(self, assertions: List[Dict[str, Any]]) -> bool:
        """
        Validates the strict JSON assertions from AgentOutput using Z3.
        
        Returns:
            True if mathematically sound.
            
        Raises:
            ContradictionError if unsat.
        """
        if not assertions:
            return True
            
        logger.info("Verifying %d formal assertions via Z3...", len(assertions))
        self.compiler.compile_and_check(assertions)
        logger.info("[Z3] Mathematical firewall passed (SAT).")
        return True
