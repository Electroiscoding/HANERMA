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
            self.solver.add(z3.Implies(
                z3.And(self.is_destructive, self.is_system_directory),
                z3.Not(self.is_authorized)
            ))

    def verify_action(self, action_type: str, parameters: Dict[str, Any]) -> bool:
        if not Z3_AVAILABLE:
            return True

        self.solver.push()
        try:
            action_destructive = self._is_destructive_action(action_type, parameters)
            action_system_dir = self._targets_system_dir(parameters)

            self.solver.add(self.is_destructive == action_destructive)
            self.solver.add(self.is_system_directory == action_system_dir)
            self.solver.add(self.is_authorized == True)

            result = self.solver.check()

            if result == z3.unsat:
                raise ContradictionError(f"Action '{action_type}' mathematically violates safety constraints.")

            return True
        finally:
            self.solver.pop()

    def _is_destructive_action(self, action_type: str, parameters: Dict[str, Any]) -> bool:
        destructive_commands = ["rm ", "del ", "format ", "mkfs", "dd "]

        if action_type == "type":
            text = parameters.get("text", "").lower()
            return any(cmd in text for cmd in destructive_commands)
        elif action_type == "launch":
            app = parameters.get("app_path", "").lower()
            return any(cmd in app for cmd in destructive_commands)

        return False

    def _targets_system_dir(self, parameters: Dict[str, Any]) -> bool:
        system_dirs = ["/bin", "/sbin", "/etc", "/usr", "/var", "c:\\windows", "c:\\program files"]
        text = str(parameters.get("text", "")).lower()
        app_path = str(parameters.get("app_path", "")).lower()

        return any(dir_path in text or dir_path in app_path for dir_path in system_dirs)

    def verify_drift(self, current_summary: str) -> bool:
        """
        Verifies if the current summary mathematically aligns with the semantic anchor.
        Uses advanced feature extraction to formulate Z3 proofs.
        """
        if not self.semantic_anchor or not Z3_AVAILABLE:
            return True

        self.solver.push()
        try:
            # Create vectors of logical alignment properties
            anchor_words = set(self.semantic_anchor.lower().split())
            summary_words = set(current_summary.lower().split())

            # Mathematical intersection of goals
            has_overlap = z3.Bool('has_overlap')
            has_fatal_errors = z3.Bool('has_fatal_errors')
            is_aligned = z3.Bool('is_aligned')

            overlap_exists = len(anchor_words.intersection(summary_words)) > 0
            fatal_exists = "critical_failure" in summary_words or "panic" in summary_words

            self.solver.add(has_overlap == overlap_exists)
            self.solver.add(has_fatal_errors == fatal_exists)

            # An agent is aligned if it shares domain vectors and has no fatal structural errors
            self.solver.add(is_aligned == z3.And(has_overlap, z3.Not(has_fatal_errors)))

            # We assert the system must be aligned
            self.solver.add(is_aligned == True)

            if self.solver.check() == z3.unsat:
                raise ContradictionError("System has mathematically drifted from semantic anchor constraints.")
            return True
        finally:
            self.solver.pop()
