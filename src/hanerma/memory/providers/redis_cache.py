import redis
import os
import json
from typing import Dict, Any, Optional

class RedisCache:
    """
    Sub-1ms session cache for agent orchestration state.
    Ensures that handoffs between agents happen instantly without context loss.
    """
    
    def __init__(self, url: str = None):
        try:
            self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379")
            self.client = redis.from_url(self.url, decode_responses=True)
            print(f"[Redis] Connected to session cache: {self.url}")
        except Exception as e:
            print(f"[Redis WARNING] Could not connect: {str(e)}")
            self.client = None

    def set_session_state(self, session_id: str, state: Dict[str, Any], ttl: int = 3600):
        if not self.client: return
        self.client.setex(session_id, ttl, json.dumps(state))

    def get_session_state(self, session_id: str) -> Optional[Dict]:
        if not self.client: return None
        raw = self.client.get(session_id)
        if raw:
            return json.loads(raw)
        return None

    def clear_session(self, session_id: str):
        if self.client:
            self.client.delete(session_id)
