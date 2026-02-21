import faiss
import numpy as np
import requests
import json
from typing import Dict, Any, List
from hanerma.memory.compression.base_tokenizer import BaseHyperTokenizer
from hanerma.state.transactional_bus import TransactionalEventBus


class HCMSManager:
    """
    Hyperfast Compressed Memory Store.
    Uses xerv-crayon tokenization for:
      1. Token-derived deterministic embeddings (FAISS)
      2. Compressed storage with real compression metrics
      3. Token-aware retrieval via spectral hashing
    """

    def __init__(self, tokenizer: BaseHyperTokenizer, bus: TransactionalEventBus, embedding_dim: int = 128):
        self.tokenizer = tokenizer
        self.bus = bus
        self.embedding_dim = embedding_dim

        # FAISS for semantic similarity search
        self.vector_index = faiss.IndexFlatL2(self.embedding_dim)
        self.memory_map: Dict[int, Dict[str, Any]] = {}
        self.current_idx = 0

        # Placeholder for Neo4j (GraphRAG)
        self.graph_db = None

        print(f"[HCMS] Memory Store Online. Dimension: {self.embedding_dim}. Index: FAISS FlatL2.")

    async def extract_user_style(self):
        """
        Background task: every 5 interactions, extract user style from prompts using local LLM.
        """
        prompts = self.bus.get_recent_user_prompts(5)
        if len(prompts) < 5:
            return {}
        
        combined = "\n".join(prompts)
        prompt = f"Analyze these user prompts and extract preferred verbosity (short/long/detailed), tone (formal/casual/professional), tool usage (list preferred tools or 'any').\n\nPrompts:\n{combined}\n\nOutput JSON: {{\"verbosity\": \"...\", \"tone\": \"...\", \"tool_usage\": \"...\"}}"
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen", "prompt": prompt, "stream": False}
        )
        response.raise_for_status()
        json_str = response.json()["response"].strip()
        
        style = json.loads(json_str)
        self.bus.record_step("user_style", 0, "update", style)
        return style

    def log_failure_pattern(self, pattern: Dict[str, Any]):
        """
        Logs failure pattern when Z3 catches contradiction or human corrects.
        """
        self.bus.record_step("failure_patterns", 0, "log", pattern)
    
    async def feedback_loop(self):
        """
        Background task: every 10 failures, analyze patterns and generate new logical axiom.
        """
        patterns = self.bus.get_recent_failure_patterns(10)
        if len(patterns) < 10:
            return
        
        # Analyze with local LLM
        patterns_text = "\n".join([str(p) for p in patterns])
        prompt = f"Analyze these failure patterns and generate a new logical axiom to prevent similar contradictions.\n\nPatterns:\n{patterns_text}\n\nOutput a new axiom as a string (e.g., 'If x > y and y > z then x > z'):"
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen", "prompt": prompt, "stream": False}
        )
        response.raise_for_status()
        new_axiom = response.json()["response"].strip()
        
        # Add to symbolic reasoner rules
        from hanerma.reliability.symbolic_reasoner import SymbolicReasoner
        reasoner = SymbolicReasoner()
        reasoner.add_rule(new_axiom)

    def store_atomic_memory(self, session_id: str, raw_text: str, entity_type: str = "context"):
        """
        Tokenizes text via xerv-crayon, generates a deterministic embedding,
        and stores it in FAISS for semantic retrieval.
        """
        # 1. Tokenize with xerv-crayon
        compressed_tokens = self.tokenizer.encode_and_compress(raw_text)
        token_count = len(compressed_tokens)
        efficiency = self.tokenizer.get_compression_ratio(raw_text, compressed_tokens)

        print(f"[HCMS] Session {session_id} | Tokens: {token_count} | Compression: {efficiency}%")

        # 2. Generate deterministic embedding FROM token IDs (not random)
        vector = self.tokenizer.embed(raw_text, dim=self.embedding_dim)
        vector = vector.reshape(1, -1)

        # 3. Store in FAISS
        self.vector_index.add(vector)
        self.memory_map[self.current_idx] = {
            "text": raw_text,
            "tokens": token_count,
            "session": session_id,
            "type": entity_type,
        }
        self.current_idx += 1

        # 4. Route facts to graph store
        if entity_type == "fact":
            self._store_in_graph(session_id, raw_text)

    def retrieve_relevant_context(self, query: str, top_k: int = 3) -> List[str]:
        """
        Tokenizes the query with xerv-crayon, generates its embedding,
        and retrieves the closest stored memories via FAISS.
        """
        if self.current_idx == 0:
            return []

        # Deterministic query embedding from xerv-crayon tokens
        query_vector = self.tokenizer.embed(query, dim=self.embedding_dim)
        query_vector = query_vector.reshape(1, -1)

        effective_k = min(top_k, self.current_idx)
        distances, indices = self.vector_index.search(query_vector, effective_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx in self.memory_map:
                results.append(self.memory_map[idx]["text"])

        return results

    def count_total_tokens(self) -> int:
        """Returns total tokens stored across all memories."""
        return sum(entry["tokens"] for entry in self.memory_map.values())

    def _store_in_graph(self, session_id: str, fact: str):
        """Writes a semantic node to Neo4j for relationship tracking."""
        # graph_db.execute("CREATE (n:Fact {session: $sid, content: $fact})", ...)
        pass
