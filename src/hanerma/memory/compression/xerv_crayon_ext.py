from typing import List
from hanerma.memory.compression.base_tokenizer import BaseHyperTokenizer


class XervCrayonAdapter(BaseHyperTokenizer):
    """
    Production adapter for the XERV CRAYON tokenizer (xerv-crayon on PyPI).
    Uses the real CrayonVocab API for tokenization, embedding, and token counting.
    """

    def __init__(self, profile: str = "lite", device: str = "auto"):
        from crayon import CrayonVocab

        self.vocab = CrayonVocab(device=device)
        self.vocab.load_profile(profile)
        self.profile = profile
        self._vocab_size = self.vocab.vocab_size
        print(f"[XERV-CRAYON] Initialized (profile={profile}, device={device}, vocab_size={self._vocab_size})")

    def encode_and_compress(self, text: str) -> List[int]:
        return self.vocab.tokenize(text)

    def decode(self, tokens: List[int]) -> str:
        return self.vocab.decode(tokens)

    def get_compression_ratio(self, original_text: str, compressed_tokens: List[int]) -> float:
        # Rough estimate: standard tokenizers average ~4 chars per token
        standard_length = len(original_text) / 4.0
        crayon_length = len(compressed_tokens)
        if standard_length == 0:
            return 0.0
        reduction = (1 - (crayon_length / standard_length)) * 100
        return round(max(0.0, min(reduction, 99.9)), 2)

    @property
    def vocab_size(self) -> int:
        return self._vocab_size
