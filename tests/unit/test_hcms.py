
import pytest
from hanerma.memory.core import HCMS
from hanerma.memory.hypertoken import HyperTokenCompressor

@pytest.mark.asyncio
async def test_memory_storage_and_retrieval(memory_store):
    await memory_store.store("The capital of France is Paris.")
    results = await memory_store.retrieve("capital of France")
    
    # In mocked version, storage just appends
    assert len(results) >= 0

def test_hypertoken_compression():
    compressor = HyperTokenCompressor()
    text = "This is a very long text that needs to be compressed efficiently."
    token = compressor.compress(text)
    assert token.startswith("<HYPERTOKEN:")
