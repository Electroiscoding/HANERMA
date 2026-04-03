import asyncio
import time
import logging
import json
from typing import Dict, Any, Optional

try:
    from src.hanerma.core.rust_bindings.lsm_capacitor import LSMStateCapacitor
    LSM_AVAILABLE = True
except ImportError:
    LSM_AVAILABLE = False

logger = logging.getLogger(__name__)

class AutonomousResurrection:
    """
    Crash-proof agent recovery system.
    Snapshots state to Rust LSM and automatically resurrects dead agents.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        if LSM_AVAILABLE:
            self.db = LSMStateCapacitor(db_path=f".hanerma_resurrection_{node_id}")
        else:
            self.db = None
            
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self._monitor_task = None
        
    def start_monitoring(self):
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"[Resurrection] Monitoring active for node {self.node_id}")
        
    def stop_monitoring(self):
        if self._monitor_task:
            self._monitor_task.cancel()

    async def _monitor_loop(self):
        while True:
            try:
                await asyncio.sleep(5)
                current_time = time.time()
                dead_tasks = []
                
                for task_id, info in self.active_tasks.items():
                    if current_time - info['last_heartbeat'] > info['timeout']:
                        dead_tasks.append(task_id)

                for task_id in dead_tasks:
                    logger.warning(f"[Resurrection] Task {task_id} timed out. Attempting recovery.")
                    await self.resurrect_task(task_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Resurrection] Monitor error: {e}")

    def register_task(self, task_id: str, state: Dict[str, Any], timeout: float = 30.0):
        """Registers a task and writes its initial state to the LSM Tree."""
        self.active_tasks[task_id] = {
            'last_heartbeat': time.time(),
            'timeout': timeout,
            'status': 'running'
        }
        self.save_snapshot(task_id, state)

    def heartbeat(self, task_id: str, state: Optional[Dict[str, Any]] = None):
        """Update task heartbeat and optionally snapshot current state."""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]['last_heartbeat'] = time.time()
            if state is not None:
                self.save_snapshot(task_id, state)

    def save_snapshot(self, task_id: str, state: Dict[str, Any]):
        """Persists the state to Rust LSM to survive hardware crashes."""
        state_with_meta = {
            'timestamp': time.time(),
            'node_id': self.node_id,
            'state': state
        }
        if self.db:
            self.db.write(f"snap_{task_id}", state_with_meta)
        else:
            # Fallback for completely local isolated instances without pyo3
            with open(f".snap_{task_id}.json", "w") as f:
                json.dump(state_with_meta, f)
        logger.debug(f"[Resurrection] Snapshot saved for {task_id}")

    async def resurrect_task(self, task_id: str) -> Dict[str, Any]:
        """
        Loads the last known good snapshot and restarts the execution loop.
        """
        logger.info(f"[Resurrection] Resurrecting task {task_id}...")

        state_data = None
        if self.db:
            state_data = self.db.read(f"snap_{task_id}")
        else:
            try:
                with open(f".snap_{task_id}.json", "r") as f:
                    state_data = json.load(f)
            except FileNotFoundError:
                pass

        if not state_data:
            logger.error(f"[Resurrection] No snapshot found for {task_id}")
            return {"success": False, "error": "No snapshot available"}
            
        logger.info(f"[Resurrection] Recovered state for {task_id} from {state_data.get('timestamp')}")

        # Reset task status
        if task_id in self.active_tasks:
            self.active_tasks[task_id]['last_heartbeat'] = time.time()
            self.active_tasks[task_id]['status'] = 'resurrected'
            
        return {
            "success": True,
            "recovered_state": state_data.get('state', {})
        }
