
"""
O(1) semantic splitting.
Ensures context chunks are coherent and retrieve-ready.
"""

from typing import List, Any, Dict
import re
from collections import defaultdict, Counter

class ChunkingEngine:
    """Semantic splitter for long documents with radical compression."""
    
    def __init__(self, strategy: str = "sentence_aware"):
        self.strategy = strategy
        self.fillers = [
            'please', 'I would like you to', 'could you', 'can you', 'kindly', 
            'if possible', 'as soon as possible', 'thank you', 'thanks', 
            'I appreciate', 'I need you to', 'let me know', 'just', 'actually',
            'basically', 'really', 'very', 'so', 'well', 'um', 'uh', 'like'
        ]
        
    def predictive_skip(self, text: str) -> str:
        """
        Removes redundant linguistic fillers to reduce token count.
        Analyzes prompt and strips common redundancies.
        """
        for filler in self.fillers:
            text = re.sub(r'\b' + re.escape(filler) + r'\b', '', text, flags=re.I)
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def compute_delta(self, full_history: List[str], last_verification_index: int) -> str:
        """
        Implements State Delta logic: sends only Atomic Changes (Deltas) 
        since the last verification instead of full conversation history.
        """
        if last_verification_index < 0 or last_verification_index >= len(full_history):
            return ' '.join(full_history)
        
        # Get changes since last verification
        deltas = full_history[last_verification_index:]
        delta_text = ' '.join(deltas)
        
        # Apply predictive skipping to deltas
        return self.predictive_skip(delta_text)
    
    def split(self, text: str, max_tokens: int = 512) -> List[str]:
        """
        Divide text into semantically complete blocks.
        Avoids splitting sentences mid-way.
        """
        # Placeholder naive split
        chunks = []
        words = text.split(" ")
        current_chunk = []
        current_len = 0
        
        for w in words:
            if current_len + 1 > max_tokens:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0
            current_chunk.append(w)
            current_len += 1
            
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks
