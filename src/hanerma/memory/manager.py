import faiss
import numpy as np
import requests
import json
import asyncio
import time
from typing import Dict, Any, List, Optional
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
        
        # User Style Extraction
        self.user_style: Dict[str, Any] = {
            "verbosity": "medium",
            "tone": "professional", 
            "tool_usage": "any",
            "interaction_count": 0
        }
        self.style_extraction_threshold = 5
        
        # Speculative Decoding (Latency Shield)
        self.speculative_model = "qwen:0.5b"  # Tiny model for fast predictions
        self.primary_model = "llama3"  # Main model
        self.speculative_cache: Dict[str, str] = {}
        
        print(f"[HCMS] Memory Store Online. Dimension: {self.embedding_dim}. Index: FAISS FlatL2.")
        print(f"[HCMS] User Style Extraction: Every {self.style_extraction_threshold} interactions")
        print(f"[HCMS] Speculative Decoding: {self.speculative_model} → {self.primary_model}")

    async def extract_user_style(self) -> Dict[str, Any]:
        """
        Background task: every 5 interactions, extract user style from prompts using local LLM.
        Stores preferences in Rust LSM tree for persistence.
        """
        self.user_style["interaction_count"] += 1
        
        # Only extract style every N interactions
        if self.user_style["interaction_count"] % self.style_extraction_threshold != 0:
            return self.user_style
        
        try:
            prompts = self.bus.get_recent_user_prompts(5)
            if len(prompts) < 3:  # Reduced threshold for better responsiveness
                return self.user_style
            
            combined = "\n".join([f"{i+1}. {prompt}" for i, prompt in enumerate(prompts)])
            analysis_prompt = f"""Analyze these user prompts and extract communication preferences:

{combined}

Output ONLY JSON with these exact keys:
{{
  "verbosity": "short|medium|long",
  "tone": "formal|casual|professional", 
  "tool_usage": "specific_tools|any",
  "complexity": "simple|technical|detailed"
}}"""
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen", 
                    "prompt": analysis_prompt, 
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=10
            )
            response.raise_for_status()
            
            # Extract JSON from response
            response_text = response.json()["response"].strip()
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                
                new_style = json.loads(json_str)
                
                # Update user style with new preferences
                self.user_style.update(new_style)
                
                # Store in Rust LSM tree via bus
                self.bus.record_step("user_style", 0, "update", self.user_style)
                
                print(f"[HCMS] User style updated: {self.user_style}")
                
        except Exception as e:
            print(f"[HCMS] Style extraction failed: {e}")
        
        return self.user_style

    def inject_user_style_into_prompt(self, base_prompt: str) -> str:
        """
        Inject user's communication style into system prompts.
        """
        style_instructions = {
            "short": "Keep responses concise and to the point.",
            "medium": "Provide balanced detail with clear explanations.",
            "long": "Give comprehensive, detailed responses with examples."
        }
        
        tone_instructions = {
            "formal": "Use professional, formal language.",
            "casual": "Use friendly, conversational language.",
            "professional": "Maintain professional but approachable tone."
        }
        
        complexity_instructions = {
            "simple": "Explain concepts simply, avoid jargon.",
            "technical": "Use precise technical terminology.",
            "detailed": "Provide thorough explanations with context."
        }
        
        style_prefix = f"""USER STYLE ADAPTATION:
- Verbosity: {style_instructions.get(self.user_style.get('verbosity', 'medium'), style_instructions['medium'])}
- Tone: {tone_instructions.get(self.user_style.get('tone', 'professional'), tone_instructions['professional'])}
- Complexity: {complexity_instructions.get(self.user_style.get('complexity', 'detailed'), complexity_instructions['detailed'])}

"""
        
        return style_prefix + base_prompt

    async def speculative_decode(self, prompt: str, max_tokens: int = 20) -> Dict[str, Any]:
        """
        Latency Shield: Use tiny model to predict first 20 tokens while primary model warms up.
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = hash(prompt[:100])  # Hash first 100 chars for cache key
            if cache_key in self.speculative_cache:
                cached_result = self.speculative_cache[cache_key]
                print(f"[HCMS] Speculative cache hit: {cached_result[:50]}...")
                return {
                    "speculative_tokens": cached_result,
                    "cache_hit": True,
                    "latency_ms": (time.time() - start_time) * 1000
                }
            
            # Generate speculative tokens with tiny model
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.speculative_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "max_tokens": max_tokens,
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                },
                timeout=5
            )
            response.raise_for_status()
            
            speculative_tokens = response.json()["response"].strip()
            
            # Cache the result
            self.speculative_cache[cache_key] = speculative_tokens
            
            # Limit cache size
            if len(self.speculative_cache) > 1000:
                # Remove oldest entries (simple FIFO)
                oldest_key = next(iter(self.speculative_cache))
                del self.speculative_cache[oldest_key]
            
            latency_ms = (time.time() - start_time) * 1000
            
            print(f"[HCMS] Speculative decode: {speculative_tokens[:50]}... ({latency_ms:.1f}ms)")
            
            return {
                "speculative_tokens": speculative_tokens,
                "cache_hit": False,
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            print(f"[HCMS] Speculative decode failed: {e}")
            return {
                "speculative_tokens": "",
                "cache_hit": False,
                "latency_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }

    def get_user_style_summary(self) -> str:
        """
        Get a human-readable summary of user's communication style.
        """
        style = self.user_style
        return f"Style: {style.get('verbosity', 'medium')} verbosity, {style.get('tone', 'professional')} tone, {style.get('complexity', 'detailed')} complexity (after {style.get('interaction_count', 0)} interactions)"

    def clear_speculative_cache(self):
        """Clear the speculative decoding cache."""
        self.speculative_cache.clear()
        print("[HCMS] Speculative cache cleared")

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
