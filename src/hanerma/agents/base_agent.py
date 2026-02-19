from typing import Dict, Any, List

class BaseAgent:
    """
    The master template for all HANERMA agents. 
    Handles context inheritance and interaction with the message bus.
    """
    def __init__(self, name: str, role: str, system_prompt: str, model: str = None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        # If no specific model is passed, it inherits the orchestrator's default
        self.model = model 
        self.tools: List[Any] = []

    def equip_tools(self, tools: List[Any]):
        """Injects custom APIs or built-in tools (like code sandboxes) into the agent."""
        self.tools.extend(tools)
        print(f"[{self.name}] Equipped {len(tools)} tools.")

    def execute(self, prompt: str, global_state: Dict[str, Any]) -> str:
        """
        Simulates the LLM call. In production, this connects to models/cloud_llm.py 
        or models/local_llm.py depending on the self.model variable.
        """
        print(f"[{self.name}] Thinking... (Context loaded: {len(global_state['history'])} previous turns)")
        
        # Simulated LLM Inference for scaffolding purposes
        simulated_output = f"I am {self.name}, acting as a {self.role}. Here is the processed result for: '{prompt[-20:]}...'"
        
        # Update state
        global_state["history"].append({"role": self.name, "content": simulated_output})
        
        return simulated_output
