import logging
from typing import List, Dict, Any, Optional
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.getLogger(__name__).warning("faiss not available. FaissVectorProvider will fail.")

logger = logging.getLogger(__name__)

class FaissVectorProvider:
    """
    Actual FAISS Vector Provider.
    Manages similarity search across memory embeddings without mocking.
    """
    def __init__(self, dimension: int = 128, index_type: str = "L2"):
        self.dimension = dimension
        self.index_type = index_type
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self._current_id = 0

        if FAISS_AVAILABLE:
            if index_type == "L2":
                self.index = faiss.IndexFlatL2(dimension)
            elif index_type == "IP":
                self.index = faiss.IndexFlatIP(dimension)
            else:
                self.index = faiss.IndexFlatL2(dimension)
        else:
            self.index = None

    def add_vector(self, vector: np.ndarray, metadata: Dict[str, Any]) -> int:
        if not FAISS_AVAILABLE or self.index is None:
            raise RuntimeError("FAISS is not available.")

        if len(vector.shape) == 1:
            vector = np.expand_dims(vector, axis=0)

        vector = vector.astype(np.float32)

        # Ensure dimensions match
        if vector.shape[1] != self.dimension:
            # Pad or truncate
            if vector.shape[1] < self.dimension:
                padded = np.zeros((1, self.dimension), dtype=np.float32)
                padded[0, :vector.shape[1]] = vector[0]
                vector = padded
            else:
                vector = vector[:, :self.dimension]

        self.index.add(vector)

        vid = self._current_id
        self.metadata[vid] = metadata
        self._current_id += 1

        return vid

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        if not FAISS_AVAILABLE or self.index is None:
            raise RuntimeError("FAISS is not available.")

        if self.index.ntotal == 0:
            return []

        if len(query_vector.shape) == 1:
            query_vector = np.expand_dims(query_vector, axis=0)

        query_vector = query_vector.astype(np.float32)

        if query_vector.shape[1] != self.dimension:
            if query_vector.shape[1] < self.dimension:
                padded = np.zeros((1, self.dimension), dtype=np.float32)
                padded[0, :query_vector.shape[1]] = query_vector[0]
                query_vector = padded
            else:
                query_vector = query_vector[:, :self.dimension]

        distances, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx in self.metadata: # -1 means no neighbor found
                res = self.metadata[idx].copy()
                res["score"] = float(distances[0][i])
                results.append(res)

        return results
        
    def get_stats(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "total_vectors": self.index.ntotal if self.index else 0,
            "index_type": self.index_type
        }
