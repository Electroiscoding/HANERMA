import sys
from unittest.mock import MagicMock

class MockBaseModel:
    pass

class MockField:
    def __init__(self, *args, **kwargs):
        pass

pydantic_mock = MagicMock()
pydantic_mock.BaseModel = MockBaseModel
pydantic_mock.Field = MockField
sys.modules['pydantic'] = pydantic_mock
sys.modules['faiss'] = MagicMock()
sys.modules['neo4j'] = MagicMock()
sys.modules['openai'] = MagicMock()

# Instead of importing pytest directly into our namespace where it might not exist,
# we add our mocks to sitecustomize.py or directly call pytest with python -m pytest
# Wait, actually we can't import pytest from system python if it's not installed in this pyenv.
