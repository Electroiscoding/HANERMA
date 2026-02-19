
"""
Translates user configs into active agents.
Allows builders to define bots via JSON/YAML.
"""

from typing import Dict, Any, Type
from ..base_agent import BaseAgent
from ..registry import AgentRegistry

class PersonaParser:
    """
    Compiles user definition into a runtime agent class.
    """
    
    @staticmethod
    def create_dynamic_agent(name: str, config: Dict[str, Any]) -> Type[BaseAgent]:
        """
        Dynamically creates a new Agent class based on config.
        """
        system_prompt = config.get("system_prompt", "You are a helpful assistant.")
        allowed_tools = config.get("tools", [])
        
        # Define dynamic class
        class DynamicAgent(BaseAgent):
            def __init__(self, tenant_id: str):
                super().__init__(role=name, tenant_id=tenant_id)
                self.config = config
                
            async def process(self, task: str):
                # Use specified model + system prompt
                full_prompt = f"{system_prompt}\nUser: {task}"
                return f"Dynamic Agent '{self.role}' responding to: {task}"
                
        # Register it
        AgentRegistry.register_custom_persona(name, DynamicAgent)
        return DynamicAgent
