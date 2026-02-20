from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.base_agent import BaseAgent
from typing import List, Callable, Optional

def quick_flow(prompt: str, agents: List[BaseAgent], model: str = "auto") -> str:
    """
    The ultimate zero-boilerplate entry point.
    5-7 lines of code to get a multi-agent flow running.
    """
    # 1. Zero-config orchestrator
    orchestrator = HANERMAOrchestrator(model=model)
    
    # 2. Auto-registration
    for agent in agents:
        orchestrator.register_agent(agent)
    
    # 3. Execution
    target = agents[0].name
    result = orchestrator.run(prompt, target_agent=target)
    
    return result["output"]

def create_agent(name: str, role: str = "Assistant", system_prompt: str = "You are a helpful assistant.", tools: List[Callable] = None, model: Optional[str] = None) -> BaseAgent:
    """Helper to create an agent with minimal boilerplate."""
    agent = BaseAgent(name=name, role=role, system_prompt=system_prompt, model=model)
    if tools:
        agent.equip_tools(tools)
    return agent
