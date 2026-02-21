from typing import Dict, Type, Any
from hanerma.agents.base_agent import BaseAgent
# In a full build, this imports the native, hardened classes
# from hanerma.agents.native_personas import DeepReasoner, SystemVerifier

class PersonaRegistry:
    """
    Dynamic loader separating framework-native agents from builder-defined custom bots.
    Ensures safe multi-tenant injection.
    """
    def __init__(self):
        self.native_blueprints: Dict[str, Type[BaseAgent]] = {}
        self.builder_blueprints: Dict[str, Dict[str, Any]] = {}

    def register_native(self, name: str, agent_class: Type[BaseAgent]):
        """Locks in the zero-error framework agents (e.g., the core verifiers)."""
        self.native_blueprints[name] = agent_class
        print(f"[Registry] Framework Native locked: {name}")

    def inject_builder_persona(self, builder_id: str, bot_name: str, seed_content: str):
        """
        Takes raw seed content from a user platform and dynamically builds an agent 
        that natively inherits HANERMA's memory and safety guardrails.
        """
        bot_id = f"{builder_id}::{bot_name}"
        
        # We store the config, not the instantiated class, to save memory.
        # It is only instantiated when a user routes a request to it.
        self.builder_blueprints[bot_id] = {
            "name": bot_name,
            "role": "Custom Persona",
            "system_prompt": f"You are {bot_name}. Core instructions: {seed_content}. You MUST adhere to Atomic Guard constraints."
        }
        print(f"[Registry] Deployed builder persona: {bot_id}")

    def spawn_agent(self, bot_id: str) -> BaseAgent:
        """Hydrates the agent configuration into an active instance for the orchestrator."""
        if bot_id in self.native_blueprints:
            return self.native_blueprints[bot_id](name=bot_id)
            
        if bot_id in self.builder_blueprints:
            config = self.builder_blueprints[bot_id]
            # Wraps the custom persona in the hardened base framework
            return BaseAgent(
                name=config["name"],
                role=config["role"],
                system_prompt=config["system_prompt"]
            )
            
        raise ValueError(f"CRITICAL: Persona '{bot_id}' does not exist in registry.")

# Global instance for high-speed access
global_registry = PersonaRegistry()

def spawn_agent(name: str, model: str = None, tools: list = None, role: str = "Senior Apex Engineer") -> BaseAgent:
    """Helper for the orchestrator to quickly hydrated a named agent."""
    # Check if native blueprint exists, else create a standard Apex agent
    if name in global_registry.native_blueprints:
        agent = global_registry.spawn_agent(name)
    else:
        system_prompt = (
            f"You are {name}, a {role} in the HANERMA Apex Swarm.\n"
            "CRITICAL APEX PROTOCOLS:\n"
            "1. TOOL_CALLS: Use TOOL_CALL: tool_name(key='val'). Ensure key names match tool documentation.\n"
            "2. SANDBOX_OUTPUT: If executing code, ALWAYS use print() for every result you wish to see. Resulting variables are not visible unless explicitly printed.\n"
            "3. HANDOFFS: To transfer the task to another agent, output 'DELEGATE: agent_name'. Currently available: Code_Architect, Strict_Verifier.\n"
            "4. VERIFICATION: Focus on zero-error execution and cross-check all tool outputs against requirements."
        )
        agent = BaseAgent(name=name, role=role, system_prompt=system_prompt, model=model)
    
    if tools:
        agent.equip_tools(tools)
    if model:
        agent.model = model
    return agent
