from typing import Dict, Type, Any, Callable
from hanerma.tools.builtin.web_search import WebSearchTool
from hanerma.agents.swarm_protocol import SwarmHandoffTool

class ToolRegistry:
    """
    Central repository for all external capabilities.
    Agents query this registry to see what actions they are allowed to perform.
    """
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        
        # Load standard toolset by default
        self._register_defaults()

    def _register_defaults(self):
        self.register_tool("web_search", WebSearchTool())
        # Other tools (sandbox, handoff) are injected dynamically during agent spawn
        print(f"[Tool Registry] Default toolset loaded: {list(self.tools.keys())}")

    def register_tool(self, name: str, tool_instance: Any):
        self.tools[name] = tool_instance

    def get_tool(self, name: str) -> Any:
        return self.tools.get(name)

    def list_available_tools(self) -> List[str]:
        return list(self.tools.keys())
