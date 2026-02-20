"""
Example 02: Multi-Agent Swarm — Model Agnostic.
Spawns multiple specialized agents and routes tasks between them
using whatever backend is configured (Local, HF, or OpenRouter).
"""

from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import PersonaRegistry

def main():
    # Initialize Orchestrator with default local model
    orch = HANERMAOrchestrator(model="local-llama3")
    registry = PersonaRegistry()

    # Spawn agents
    reasoner = registry.spawn_agent("native::deep_reasoner")
    verifier = registry.spawn_agent("native::system_verifier")

    orch.register_agent(reasoner)
    orch.register_agent(verifier)

    # Run the swarm
    result = orch.run(
        prompt="What are the security risks of WebSocket without TLS?",
        target_agent=reasoner.name,
    )
    print(result["output"])

if __name__ == "__main__":
    main()
