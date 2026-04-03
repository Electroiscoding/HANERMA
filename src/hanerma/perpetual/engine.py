import asyncio
import time
import hashlib
import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from hanerma.reliability.constraint_compiler import ConstraintCompiler, ContradictionError

logger = logging.getLogger(__name__)

class DriftError(Exception):
    """Raised when an agent drifts from its semantic anchor."""
    pass

class PerpetualMode(Enum):
    CONTINUOUS = "continuous"
    POLLING = "polling"
    EVENT_DRIVEN = "event_driven"

class SemanticAnchor:
    """Mathematical anchor for an agent's core goal."""
    def __init__(self, goal: str, constraints: List[str]):
        self.goal = goal
        self.constraints = constraints
        self.anchor_hash = self._generate_anchor_hash(goal, constraints)
        
    def _generate_anchor_hash(self, goal: str, constraints: List[str]) -> str:
        content = f"{goal}_{'_'.join(constraints)}"
        return hashlib.sha256(content.encode()).hexdigest()

class DriftMonitor:
    """Monitors agents for goal drift using Z3 mathematical proofs."""
    
    def __init__(self, semantic_anchor: SemanticAnchor):
        self.semantic_anchor = semantic_anchor
        self.compiler = ConstraintCompiler(semantic_anchor=semantic_anchor.goal)
        self.correction_count = 0
        
    def check_drift(self, current_state: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        try:
            # We use the ConstraintCompiler's verify_drift which uses Z3
            # Extract summary from state
            summary = str(current_state)
            self.compiler.verify_drift(summary)
            return {
                "DriftDetected": False,
                "DriftScore": 0.0,
                "CorrectionRequired": False
            }
        except ContradictionError as e:
            logger.warning(f"Drift detected for agent {agent_id}: {e}")
            self.correction_count += 1
            return {
                "DriftDetected": True,
                "DriftScore": 1.0,
                "CorrectionRequired": True,
                "Anchor": self.semantic_anchor.goal,
                "Timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"[PERPETUAL] Drift check error: {e}")
            return {"DriftDetected": False, "Error": str(e)}

class PerpetualEngine:
    """24/7/365 perpetual execution engine for HANERMA."""
    
    def __init__(self, semantic_goal: str, mode: PerpetualMode = PerpetualMode.CONTINUOUS):
        self.semantic_goal = semantic_goal
        self.mode = mode
        
        self.semantic_anchor = SemanticAnchor(
            goal=semantic_goal,
            constraints=["prevent_hallucination", "continuous_operation"]
        )
        self.drift_monitor = DriftMonitor(self.semantic_anchor)
        self.compiler = ConstraintCompiler(semantic_anchor=semantic_goal)
        
        self.is_running = False
        self.start_time = None
        self.execution_count = 0
        self.last_state = {}
        
    async def start_perpetual_execution(self, user_goal: str) -> Dict[str, Any]:
        if self.is_running:
            return {"success": False, "error": "Already running"}
        
        self.is_running = True
        self.start_time = time.time()
        self.execution_count = 0
        
        try:
            while self.is_running:
                await self._execution_cycle(user_goal)
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            self.is_running = False
            return {"success": True, "execution_count": self.execution_count}
        except Exception as e:
            self.is_running = False
            return {"success": False, "error": str(e)}
            
    async def _execution_cycle(self, user_goal: str) -> None:
        task = {
            "task_id": f"perpetual_task_{self.execution_count + 1}",
            "goal": user_goal,
            "type": "perpetual_maintenance"
        }

        try:
            # 1. Verification Step via ConstraintCompiler
            # For perpetual loops, verify it's not destructive
            self.compiler.verify_action("perpetual_loop", {"text": user_goal})
            
            # 2. Execute via OS or agents (in actual execution, this dispatches to agents)
            execution_result = {"status": "ok", "task": task["task_id"]}
            
            # 3. Drift Check
            state = {"last_execution": execution_result, "execution_count": self.execution_count}
            drift_check = self.drift_monitor.check_drift(state, "engine")
            
            if drift_check.get("DriftDetected", False):
                await self._handle_drift_correction(drift_check, task)
            else:
                self.execution_count += 1
                
        except ContradictionError as e:
            logger.error(f"[PERPETUAL] Verification failed: {e}")
            await self._handle_drift_correction({"DriftScore": 1.0}, task)

    async def _handle_drift_correction(self, drift_result: Dict[str, Any], task: Dict[str, Any]) -> None:
        logger.warning(f"[PERPETUAL] Applying drift correction. Resetting state.")
        self.last_state = {}
        # Execute correction
        self.execution_count += 1

    def get_engine_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "execution_count": self.execution_count,
            "drift_corrections": self.drift_monitor.correction_count
        }

    async def emergency_stop(self) -> Dict[str, Any]:
        self.is_running = False
        return {"success": True, "message": "Stopped"}
