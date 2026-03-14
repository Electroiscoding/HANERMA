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

faiss_mock = MagicMock()
sys.modules['faiss'] = faiss_mock
neo4j_mock = MagicMock()
sys.modules['neo4j'] = neo4j_mock
openai_mock = MagicMock()
sys.modules['openai'] = openai_mock

import pytest
sys.exit(pytest.main(['tests/unit/']))
