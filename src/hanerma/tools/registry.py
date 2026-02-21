from typing import Dict, Type, Any, Callable, List

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
        # Clean import from the consolidated builtin set
        try:
            from hanerma.tools.builtin.basic_tools import web_search, calculator, get_system_time, delegate_task, internal_search, execute_sandbox
            self.register_tool("web_search", web_search)
            self.register_tool("calculator", calculator)
            self.register_tool("get_system_time", get_system_time)
            self.register_tool("delegate_task", delegate_task)
            self.register_tool("internal_search", internal_search)
            self.register_tool("execute_sandbox", execute_sandbox)
        except ImportError as e:
            print(f"[Tool Registry] Warning: Could not load default tools: {e}")
        
        print(f"[Tool Registry] Apex Toolset Active: {list(self.tools.keys())}")

    def register_tool(self, name: str, tool_instance: Any):
        self.tools[name] = tool_instance

    def get_tool(self, name: str) -> Any:
        return self.tools.get(name)

    def list_available_tools(self) -> List[str]:
        return list(self.tools.keys())
