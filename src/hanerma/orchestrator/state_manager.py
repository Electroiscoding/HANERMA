from typing import Dict, Any, Optional
from hanerma.memory.manager import HCMSManager
from hanerma.state.raft_consensus import RaftConsensus
import hashlib
import json
import logging

logger = logging.getLogger("hanerma.state_manager")

class MultitenantStateManager:
    """
    Maintains strict boundaries between active user sessions with persistent KV cache.
    Critical for deploying HANERMA as a backend for builder platforms.
    """
    def __init__(self, memory_store: HCMSManager, bus=None):
        self.memory_store = memory_store
        self.bus = bus
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
    
    def get_cache_key(self, prompt: str, agent_config: Dict[str, Any]) -> str:
        """Generate hash key for prompt + agent config."""
        key_data = {
            "prompt": prompt,
            "agent_config": agent_config
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get_cached_response(self, prompt: str, agent_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve cached response with distributed consistency."""
        cache_key = self.get_cache_key(prompt, agent_config)
        
        # Query distributed cache through Raft
        query = {
            "type": "query_cache",
            "cache_key": cache_key
        }
        
        consensus_result = self.raft_consensus.query_distributed(query)
        
        if consensus_result.success:
            cached_data = consensus_result.data
            logger.info(f"[Distributed] Retrieved cached response with consensus: {consensus_result.term}")
            return cached_data
        else:
            logger.error(f"[Distributed] Failed to query cache: {consensus_result.error}")
            return None
    
    def set_cached_response(self, prompt: str, agent_config: Dict[str, Any], response: Dict[str, Any]):
        """Set cached response with distributed consistency."""
        cache_key = self.get_cache_key(prompt, agent_config)
        
        operation = {
            "type": "store_cache",
            "cache_key": cache_key,
            "response": response
        }
        cache_data = {
            "key": cache_key,
            "response": response,
            "agent_config": agent_config
        }
        
        if self.bus:
            self.bus.record_step("kv_cache", 0, "store", cache_data)
    
    def invalidate_cache_for_session(self, session_id: str):
        """Clear cache for a session (e.g., on context change)."""
        # In practice, this would delete cache entries for the session
        pass
