import sys
from unittest.mock import MagicMock

# Create mock objects for heavy dependencies that are missing
sys.modules['pydantic'] = MagicMock()
sys.modules['faiss'] = MagicMock()
sys.modules['neo4j'] = MagicMock()
sys.modules['openai'] = MagicMock()
