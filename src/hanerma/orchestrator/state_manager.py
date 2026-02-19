from typing import Dict, Any
from hanerma.memory.manager import HCMSManager

class MultitenantStateManager:
    """
    Maintains strict boundaries between active user sessions.
    Critical for deploying HANERMA as a backend for builder platforms.
    """
    def __init__(self, memory_store: HCMSManager):
        self.memory_store = memory_store
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def initialize_session(self, session_id: str, user_id: str):
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "short_term_buffer": [],
                "active_agent": None
            }
            print(f"[State] Initialized secure sandbox for Session: {session_id}")

    def push_to_infinite_memory(self, session_id: str, content: str):
        """Moves data from the short-term buffer into the HCMS."""
        if session_id in self.active_sessions:
            self.memory_store.store_atomic_memory(session_id, content)
            
    def get_agent_context(self, session_id: str, current_prompt: str) -> str:
        """Retrieves exactly what the agent needs to know right now, skipping the bloat."""
        relevant_history = self.memory_store.retrieve_relevant_context(current_prompt)
        return "\n".join(relevant_history)
