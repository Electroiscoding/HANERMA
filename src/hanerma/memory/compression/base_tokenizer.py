from abc import ABC, abstractmethod
from typing import List, Dict
import numpy as np
from collections import defaultdict
import re

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
        vocab = self.build_vocab(text)
        self.merges = self.train_bpe(vocab, num_merges=100)
        tokens = self.tokenize_bpe(text, self.merges)
        return tokens

    @abstractmethod
    def decode(self, tokens: List[int]) -> str:
        """Reconstructs text from the token array with robust detokenization."""
        text_parts = []
        for token_id in tokens:
            token = self.id_to_token.get(token_id, '<unk>')
            text_parts.append(token)

        # Robust BPE Detokenizer
        text = ' '.join(text_parts)
        # BPE merges are just characters conjoined.
        # We need to split on </w> boundary markers instead of just stripping them
        text = text.replace(' </w>', '</w>').replace('</w> ', ' ').replace('</w>', '')
        # Handle residual spaces within merged tokens
        text = re.sub(r'(?<!\s)\s(?!\s)', '', text)
        return text.strip()

    @abstractmethod
    def get_compression_ratio(self, original_text: str, compressed_tokens: List[int]) -> float:
        original_words = len(original_text.split())
        compressed_tokens_count = len(compressed_tokens)
        if original_words == 0:
            return 1.0
        return compressed_tokens_count / original_words

    def build_vocab(self, text: str) -> Dict[str, int]:
        words = text.split()
        vocab = defaultdict(int)
        for word in words:
            word = ' '.join(list(word)) + ' </w>'
            vocab[word] += 1
        return vocab

    def get_stats(self, vocab: Dict[str, int]) -> Dict[tuple, int]:
        pairs = defaultdict(int)
        for word, freq in vocab.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        return pairs

    def merge_vocab(self, pair: tuple, v_in: Dict[str, int]) -> Dict[str, int]:
        v_out = {}
        bigram = ' '.join(pair)
        replacement = ''.join(pair)
        for word in v_in:
            w_out = word.replace(bigram, replacement)
            v_out[w_out] = v_in[word]
        return v_out

    def train_bpe(self, vocab: Dict[str, int], num_merges: int = 100) -> Dict[tuple, str]:
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
        words = text.split()
        tokens = []
        for word in words:
            word = ' '.join(list(word)) + ' </w>'
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
        return len(self.encode_and_compress(text))

    def embed(self, text: str, dim: int = 128) -> np.ndarray:
        tokens = self.encode_and_compress(text)
        if not tokens:
            return np.zeros(dim, dtype=np.float32)

        vec = np.zeros(dim, dtype=np.float64)
        for i, tid in enumerate(tokens):
            pos_weight = 1.0 / (1.0 + i * 0.1)
            for harmonic in range(1, 4):
                freq = tid * harmonic * 0.01
                idx_sin = (tid * harmonic) % dim
                idx_cos = (tid * harmonic + dim // 2) % dim
                vec[idx_sin] += np.sin(freq) * pos_weight
                vec[idx_cos] += np.cos(freq) * pos_weight

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.astype(np.float32)
