from typing import List, Dict, Any
from hanerma.tools.code_sandbox import NativeCodeSandbox

class ExternalReasoner:
    """
    Deep 3 - External Integration Layer.
    Routes agent requests to external systems (APIs, Web, Sandboxes) safely.
    """
    def __init__(self):
        self.sandbox = NativeCodeSandbox()
        # Additional tools like WebSearch would be initialized here

    def execute_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Safely maps an agent's intended action to a physical execution environment.
        """
        print(f"[Deep 3] Agent requested external tool: {tool_name}")
        
        if tool_name == "python_sandbox":
            code = parameters.get("code", "")
            output = self.sandbox.execute_code(code)
            
            if "[Runtime Error]" in output:
                print(f"[Deep 3 WARNING] Tool failed. Routing error back to agent for self-correction.")
            
            return f"Sandbox Output:\n{output}"
            
        elif tool_name == "web_search":
            # Simulated external API call
            query = parameters.get("query", "")
            return f"Search Results for '{query}': [Data retrieved]"
            
        else:
            return f"System Error: Tool '{tool_name}' is not registered."
