from abc import ABC, abstractmethod
from typing import List
import numpy as np


class BaseHyperTokenizer(ABC):
    """
    Abstract base class for HANERMA tokenizers.
    Any tokenizer plugged into HANERMA must implement these methods.
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

    def count_tokens(self, text: str) -> int:
        """Returns the number of tokens for a given text."""
        return len(self.encode_and_compress(text))

    def embed(self, text: str, dim: int = 128) -> np.ndarray:
        """
        Generates a deterministic embedding vector from token IDs.
        Uses spectral hashing: each token contributes sin/cos features
        at positions derived from its ID, creating a fixed-size fingerprint
        where texts with similar tokens produce similar vectors.
        """
        tokens = self.encode_and_compress(text)
        if not tokens:
            return np.zeros(dim, dtype=np.float32)

        vec = np.zeros(dim, dtype=np.float64)
        for i, tid in enumerate(tokens):
            # Position-aware spectral features
            pos_weight = 1.0 / (1.0 + i * 0.1)  # Decay for later tokens
            for harmonic in range(1, 4):
                freq = tid * harmonic * 0.01
                idx_sin = (tid * harmonic) % dim
                idx_cos = (tid * harmonic + dim // 2) % dim
                vec[idx_sin] += np.sin(freq) * pos_weight
                vec[idx_cos] += np.cos(freq) * pos_weight

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.astype(np.float32)
