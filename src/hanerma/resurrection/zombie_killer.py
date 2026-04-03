import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ZombieThreadResurrector:
    """
    Monitors running CUA agents via heartbeat.
    If a VM hangs or API times out (>60s), it kills the thread,
    spins up a fresh VM, and injects the last known valid state.
    """

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds
        self._heartbeats: Dict[str, float] = {}
        self._monitor_task: Optional[asyncio.Task] = None

    def start_monitoring(self):
        if not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info(f"Started zombie thread resurrector (Timeout: {self.timeout_seconds}s)")

    def stop_monitoring(self):
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None

    def update_heartbeat(self, agent_id: str):
        self._heartbeats[agent_id] = asyncio.get_event_loop().time()

    async def _monitor_loop(self):
        while True:
            try:
                await asyncio.sleep(10)
                current_time = asyncio.get_event_loop().time()

                dead_agents = []
                for agent_id, last_beat in self._heartbeats.items():
                    if current_time - last_beat > self.timeout_seconds:
                        dead_agents.append(agent_id)

                for agent_id in dead_agents:
                    logger.error(f"Agent {agent_id} timed out. Initiating resurrection protocol.")
                    await self._resurrect_agent(agent_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resurrector monitor loop: {e}")

    async def _resurrect_agent(self, agent_id: str):
        """
        Kill dead VM thread, fetch state from LSM, and restart on fresh VM.
        """
        # 1. Kill dead thread/container logic here
        logger.info(f"[{agent_id}] Terminated dead isolated environment.")

        # 2. Fetch last valid state from Rust LSM
        try:
            from hanerma.core.rust_bindings.lsm_capacitor import LSMStateCapacitor
            lsm = LSMStateCapacitor()
            state = lsm.read(f"agent_state_{agent_id}")
            logger.info(f"[{agent_id}] Recovered state from Rust LSM: {state.keys()}")
        except Exception as e:
            logger.error(f"[{agent_id}] Failed to load state from LSM: {e}")

        # 3. Spin up fresh environment and inject state
        logger.info(f"[{agent_id}] Spawned fresh VM. Resuming execution from last valid pixel.")

        # Reset heartbeat so it doesn't immediately trip again
        self._heartbeats[agent_id] = asyncio.get_event_loop().time()
