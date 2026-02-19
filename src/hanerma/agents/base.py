
"""
Context inheritance logic for all agents.
"""
from typing import Dict, Any, List

class BaseAgent:
    """
    Core agent logic with context inheritance.
    """
    
    def __init__(self, role: str, model: str = "gpt-4o"):
        self.role = role
        self.model = model
        self.memory_context: List[str] = []
        
    async def process(self, task: str) -> Any:
        # Call model API
        # Update context
        return {"role": self.role, "content": f"Performed {task}"}
        
    def inherit_context(self, parent_agent: "BaseAgent"):
        """Pass full context from parent to child sub-agent."""
        self.memory_context.extend(parent_agent.memory_context)
