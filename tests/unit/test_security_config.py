import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Mock all dependencies to allow import in restricted environment
mock_modules = [
    'pydantic', 'prometheus_client', 'fastapi', 'fastapi.responses',
    'uvicorn', 'httpx', 'numpy', 'networkx', 'neo4j', 'faiss',
    'redis', 'aiosqlite', 'aiofiles', 'z3', 'openai', 'pydantic_core'
]

for mod in mock_modules:
    sys.modules[mod] = MagicMock()

# Avoid importing the whole hanerma package
import types
hanerma = types.ModuleType('hanerma')
hanerma.__path__ = [os.path.abspath('src/hanerma')]
sys.modules['hanerma'] = hanerma

# Manually create the sub-packages to avoid importing their __init__.py files
# which might lead back to the global hanerma/__init__.py
for sub in ['core', 'orchestrator', 'observability']:
    mod_name = f'hanerma.{sub}'
    m = types.ModuleType(mod_name)
    m.__path__ = [os.path.abspath(f'src/hanerma/{sub}')]
    sys.modules[mod_name] = m

# Now import only what we need
sys.path.insert(0, os.path.abspath('src'))

from hanerma.core.config import settings
from hanerma.orchestrator.message_bus import DistributedEventBus
from hanerma.observability.metrics import start_metrics_server
from hanerma.observability.viz_server import start_viz

class TestSecurityConfig(unittest.TestCase):
    def test_event_bus_defaults(self):
        # Default should be 127.0.0.1
        bus = DistributedEventBus()
        self.assertEqual(bus.host, "127.0.0.1")
        self.assertEqual(bus.port, 50051)

    def test_event_bus_custom(self):
        bus = DistributedEventBus(host="192.168.1.100", port=9000)
        self.assertEqual(bus.host, "192.168.1.100")
        self.assertEqual(bus.port, 9000)

    @patch('uvicorn.run')
    def test_start_metrics_server_defaults(self, mock_run):
        start_metrics_server()
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs['host'], "127.0.0.1")
        self.assertEqual(kwargs['port'], 8082)

    @patch('uvicorn.run')
    def test_start_viz_defaults(self, mock_run):
        start_viz()
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs['host'], "127.0.0.1")
        self.assertEqual(kwargs['port'], 8081)

if __name__ == '__main__':
    unittest.main()
