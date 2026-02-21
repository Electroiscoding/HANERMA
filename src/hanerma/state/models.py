from pydantic import BaseModel, Field, RootModel
from typing import Dict, List, Any, Optional
import hashlib
import json

class HistoryEntry(BaseModel):
    role: str
    content: str

class SharedMemory(RootModel):
    root: Dict[str, Any] = Field(default_factory=dict)

class HANERMAState(BaseModel):
    history: List[HistoryEntry] = Field(default_factory=list)
    shared_memory: SharedMemory = Field(default_factory=SharedMemory)

    def compute_hash(self) -> str:
        """Compute a SHA256 hash of the current state for MVCC versioning."""
        state_dict = self.dict()
        state_json = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HANERMAState':
        """Create state from dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return self.dict()
