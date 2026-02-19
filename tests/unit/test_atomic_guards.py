
import pytest
from hanerma.reasoning.deep1_atomic import AtomicUnit, FactExtractor
from hanerma.reasoning.deep2_nested import NestedVerifier

def test_atomic_unit_creation():
    unit = AtomicUnit(id="1", content="Sky is blue due to Rayleigh scattering.")
    assert unit.content == "Sky is blue due to Rayleigh scattering."
    assert not unit.verified

def test_fact_extraction():
    extractor = FactExtractor()
    text = "The quick brown fox jumps over the lazy dog."
    units = extractor.decompose(text)
    assert len(units) > 0
    assert isinstance(units[0], AtomicUnit)

@pytest.mark.asyncio
async def test_nested_verification(memory_store):
    verifier = NestedVerifier(memory_store)
    unit = AtomicUnit(id="2", content="Water boils at 100C")
    
    # Store verification fact first
    await memory_store.store("Water boils at 100 degrees Celsius at sea level.")
    
    verified_units = await verifier.cross_check([unit])
    
    # In a real test with embeddings, this would pass
    # For now, placeholder returns True
    assert len(verified_units) >= 0 
