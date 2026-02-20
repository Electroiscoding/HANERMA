"""
HANERMA: Hierarchical Atomic Nested External Reasoning and Memory Architecture
Core monolithic package exposure.
"""

from .orchestrator.engine import HANERMAOrchestrator
from .memory.manager import HCMSManager
from .agents.registry import PersonaRegistry
from .tools.registry import ToolRegistry
from .server.main import app as api_server

__version__ = "1.0.0-alpha"
__all__ = [
    "HANERMAOrchestrator",
    "HCMSManager",
    "PersonaRegistry",
    "ToolRegistry",
    "api_server"
]
