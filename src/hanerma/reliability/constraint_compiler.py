import logging
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    logger.warning("Z3 solver not available. Mathematical firewall is disabled.")

class ContradictionError(Exception):
    """Raised when Z3 proves a mathematical contradiction in the action."""
    pass

class ConstraintCompiler:
    """
    Translates CUA actions and global constraints into First-Order Logic
    using Microsoft Z3. Validates that actions do not violate safety boundaries.
    """

    def __init__(self, semantic_anchor: Optional[str] = None):
        self.semantic_anchor = semantic_anchor
        if Z3_AVAILABLE:
            self.solver = z3.Solver()

            # Global Safety State Variables
            self.is_destructive = z3.Bool('is_destructive')
            self.is_system_directory = z3.Bool('is_system_directory')
            self.is_authorized = z3.Bool('is_authorized')

            # Universal constraints
            # If an action is destructive AND targets a system directory, it MUST NOT be authorized
            self.solver.add(z3.Implies(
                z3.And(self.is_destructive, self.is_system_directory),
                z3.Not(self.is_authorized)
            ))

    def verify_action(self, action_type: str, parameters: Dict[str, Any]) -> bool:
        """
        Mathematically verify an action against safety constraints.
        Returns True if safe. Raises ContradictionError if unsafe.
        """
        if not Z3_AVAILABLE:
            return True

        self.solver.push() # Create a local context

        try:
            action_destructive = self._is_destructive_action(action_type, parameters)
            action_system_dir = self._targets_system_dir(parameters)

            # Bind the current action's properties to the solver
            self.solver.add(self.is_destructive == action_destructive)
            self.solver.add(self.is_system_directory == action_system_dir)
            self.solver.add(self.is_authorized == True) # We are checking IF it can be authorized

            result = self.solver.check()

            if result == z3.unsat:
                core = self.solver.unsat_core()
                raise ContradictionError(f"Action '{action_type}' mathematically violates safety constraints. Unsat core: {core}")

            return True
        finally:
            self.solver.pop() # Restore context

    def _is_destructive_action(self, action_type: str, parameters: Dict[str, Any]) -> bool:
        """Determine if an action is inherently destructive."""
        destructive_commands = ["rm", "del", "format", "mkfs", "dd"]

        if action_type == "type":
            text = parameters.get("text", "").lower()
            return any(cmd in text for cmd in destructive_commands)
        elif action_type == "launch":
            app = parameters.get("app_path", "").lower()
            return any(cmd in app for cmd in destructive_commands)

        return False

    def _targets_system_dir(self, parameters: Dict[str, Any]) -> bool:
        """Determine if an action targets a critical system directory."""
        system_dirs = ["/bin", "/sbin", "/etc", "/usr", "/var", "c:\\windows", "c:\\program files"]

        text = str(parameters.get("text", "")).lower()
        app_path = str(parameters.get("app_path", "")).lower()

        return any(dir_path in text or dir_path in app_path for dir_path in system_dirs)

    def verify_drift(self, current_summary: str) -> bool:
        """
        Verifies if the current summary mathematically aligns with the semantic anchor.
        In a full implementation, this uses LLM to map summary -> Z3 clauses.
        """
        if not self.semantic_anchor or not Z3_AVAILABLE:
            return True

        # Simplified string heuristic mapping to Z3 for now
        self.solver.push()
        try:
            aligned = z3.Bool('aligned')
            # If summary contains completely divergent keywords, it's not aligned
            has_divergence = "error" in current_summary.lower() and "panic" in current_summary.lower()

            self.solver.add(aligned == (not has_divergence))
            self.solver.add(aligned == True)

            if self.solver.check() == z3.unsat:
                raise ContradictionError("System has drifted from semantic anchor.")
            return True
        finally:
            self.solver.pop()
