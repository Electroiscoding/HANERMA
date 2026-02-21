from abc import ABC, abstractmethod
from typing import List, Dict
import numpy as np
from collections import defaultdict

class BaseHyperTokenizer(ABC):
    """
    Abstract base class for HANERMA tokenizers with BPE support.
    Any tokenizer plugged into HANERMA must implement these methods.
    """

    def __init__(self):
        self.token_to_id: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        self.merges: Dict[tuple, str] = {}

    @abstractmethod
    def encode_and_compress(self, text: str) -> List[int]:
        """Converts raw text into a compressed token array using BPE."""
        vocab = self.build_vocab(text)
        self.merges = self.train_bpe(vocab, num_merges=100)  # Train BPE on the fly for compression
        tokens = self.tokenize_bpe(text, self.merges)
        return tokens

    @abstractmethod
    def decode(self, tokens: List[int]) -> str:
        """Reconstructs text from the token array."""
        text_parts = []
        for token_id in tokens:
            token = self.id_to_token.get(token_id, '<unk>')
            text_parts.append(token)
        # Reverse BPE merges (simplified)
        text = ' '.join(text_parts)
        text = text.replace(' </w>', '').replace(' ', '')
        return text

    @abstractmethod
    def get_compression_ratio(self, original_text: str, compressed_tokens: List[int]) -> float:
        """Calculates the token reduction percentage for telemetry."""
        original_words = len(original_text.split())
        compressed_tokens_count = len(compressed_tokens)
        if original_words == 0:
            return 1.0
        return compressed_tokens_count / original_words

    def build_vocab(self, text: str) -> Dict[str, int]:
        """Builds initial vocabulary for BPE."""
        words = text.split()
        vocab = defaultdict(int)
        for word in words:
            word = ' '.join(list(word)) + ' </w>'
            vocab[word] += 1
        return vocab

    def get_stats(self, vocab: Dict[str, int]) -> Dict[tuple, int]:
        """Gets pair frequencies for BPE."""
        pairs = defaultdict(int)
        for word, freq in vocab.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        return pairs

    def merge_vocab(self, pair: tuple, v_in: Dict[str, int]) -> Dict[str, int]:
        """Merges a pair in the vocabulary."""
        v_out = {}
        bigram = ' '.join(pair)
        replacement = ''.join(pair)
        for word in v_in:
            w_out = word.replace(bigram, replacement)
            v_out[w_out] = v_in[word]
        return v_out

    def train_bpe(self, vocab: Dict[str, int], num_merges: int = 100) -> Dict[tuple, str]:
        """Trains BPE merges."""
        merges = {}
        for i in range(num_merges):
            pairs = self.get_stats(vocab)
            if not pairs:
                break
            best = max(pairs, key=pairs.get)
            vocab = self.merge_vocab(best, vocab)
            merges[best] = ''.join(best)
        return merges

    def tokenize_bpe(self, text: str, merges: Dict[tuple, str]) -> List[int]:
        """Tokenizes text using trained BPE merges."""
        words = text.split()
        tokens = []
        for word in words:
            word = ' '.join(list(word)) + ' </w>'
            # Apply merges
            for pair, merge in merges.items():
                word = word.replace(' '.join(pair), merge)
            symbols = word.split()
            for sym in symbols:
                if sym not in self.token_to_id:
                    token_id = len(self.token_to_id)
                    self.token_to_id[sym] = token_id
                    self.id_to_token[token_id] = sym
                tokens.append(self.token_to_id[sym])
        return tokens

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
