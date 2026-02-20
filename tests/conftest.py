import pytest
from typing import Dict, Any
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.memory.manager import HCMSManager
from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter

@pytest.fixture
def mock_tokenizer():
    """Provides the competitive XERV CRAYON adapter for O(1) compression tests."""
    return XervCrayonAdapter()

@pytest.fixture
def hcms_store(mock_tokenizer):
    """Provides an isolated, ephemeral vector/graph store for testing Deep 2."""
    return HCMSManager(tokenizer=mock_tokenizer, embedding_dim=128)

@pytest.fixture
def orchestrator(hcms_store):
    """Returns a fresh orchestrator instance for testing swarm handoffs."""
    orch = HANERMAOrchestrator(model="local-llama3", tokenizer_adapter=mock_tokenizer)
    # Inject the mocked memory
    orch.state_manager["shared_memory"] = hcms_store
    return orch

@pytest.fixture
def sample_builder_seed():
    """Simulates a NeTuArk platform user injecting custom bot instructions."""
    return "You are a highly analytical trading bot. Never hallucinate financial metrics."
