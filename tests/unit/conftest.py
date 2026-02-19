
import pytest
import asyncio
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.memory.core import HCMS
# from hanerma.models.local_llm import OllamaConnector
# from hanerma.autoprompt.enhancer import AutoPromptEnhancer

@pytest.fixture
def orchestrator():
    return HANERMAOrchestrator()

@pytest.fixture
def memory_store():
    return HCMS(use_graph=False) # Use simple vector only for tests

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
