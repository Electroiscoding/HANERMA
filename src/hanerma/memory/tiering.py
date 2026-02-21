from typing import List, Dict, Any
import time
import faiss
from sentence_transformers import SentenceTransformer
from hanerma.state.transactional_bus import TransactionalEventBus

class MemoryTieringManager:
    """
    Implements "Infinite Context Illusion" via dynamic memory tiering.
    - Hot Tier: Current window context (Fast)
    - Warm Tier: Summarized history / Recent events (Vector/Cache)
    - Cold Tier: Archived archives / Long-term storage (Database/HCMS)
    """
    def __init__(self, hot_threshold: int = 4000):
        self.hot_threshold = hot_threshold
        self.hot_memory = []
        self.warm_memory = [] # Summarized versions
        self.cold_memory = [] # Persistent storage IDs
        
        # Cold tier components
        self.bus = TransactionalEventBus()
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.IndexFlatL2(384)  # 384-dimensional vectors
        self.vector_id = 0
        self.raw_texts = {}  # id to raw text mapping

    def add_event(self, event: Dict[str, Any], token_count: int):
        """Adds an event and automatically tiers it based on context pressure."""
        self.hot_memory.append({"event": event, "tokens": token_count, "time": time.time()})
        self._rebalance_tiers()

    def get_active_context(self) -> List[Dict[str, Any]]:
        """Returns the hot tier context for the current LLM call."""
        return [m["event"] for m in self.hot_memory]

    def _rebalance_tiers(self):
        """Moves oldest items from Hot to Cold when threshold exceeded."""
        total_tokens = sum(m["tokens"] for m in self.hot_memory)
        
        if total_tokens > self.hot_threshold:
            to_archive = []
            archived_tokens = 0
            while self.hot_memory and archived_tokens < 2000:
                item = self.hot_memory.pop(0)
                to_archive.append(item)
                archived_tokens += item["tokens"]
            
            if to_archive:
                self._archive_to_cold(to_archive)

    def _archive_to_warm(self, item: Dict[str, Any]):
        """Compresses/Summarizes item and moves to warm tier."""
        # In production, this would call a fast local model to summarize
        summary = {"type": "summary", "content": f"Summary of {item['event'].get('type', 'event')}"}
        self.warm_memory.append({"event": summary, "original": item, "time": time.time()})
        
        if len(self.warm_memory) > 100:
            self._archive_to_cold(self.warm_memory.pop(0))

    def _archive_to_cold(self, items: List[Dict[str, Any]]):
        """Archives items to cold tier: encodes to vectors, indexes in FAISS, saves raw text to SQLite."""
        raw_text = "\n".join(str(item["event"]) for item in items)
        
        # Encode text to vector (byte-transfer)
        vector = self.encoder.encode(raw_text)
        
        # Add to FAISS index
        self.index.add(vector.reshape(1, -1))
        
        # Assign ID and store mapping
        id = self.vector_id
        self.raw_texts[id] = raw_text
        self.vector_id += 1
        
        # Persist to SQLite transactional bus
        self.bus.record_step("cold_memory", id, "archive", {"text": raw_text})
        
        # Update cold memory list
        self.cold_memory.append({"id": id, "text": raw_text})

    def recall_relevant(self, query: str) -> List[Dict[str, Any]]:
        """Retrieves relevant facts from cold/warm tiers using vector search."""
        # Placeholder for vector search retrieval
        return []
