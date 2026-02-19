from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseHyperTokenizer(ABC):
    """
    Abstract base class for HANERMA compression tokenizers.
    Standard OpenAI/Llama tokenizers are too bloated for O(1) infinite recall.
    Builders must implement these methods to achieve the 60% efficiency metric.
    """
    
    @abstractmethod
    def encode_and_compress(self, text: str) -> List[int]:
        """Converts raw text into a compressed token array."""
        pass

    @abstractmethod
    def decode(self, tokens: List[int]) -> str:
        """Reconstructs text from the token array."""
        pass
        
    @abstractmethod
    def get_compression_ratio(self, original_text: str, compressed_tokens: List[int]) -> float:
        """Calculates the token reduction percentage for telemetry."""
        pass
