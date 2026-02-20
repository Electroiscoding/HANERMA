"""
Example 02: Multi-Agent Swarm — Model Agnostic.
Spawns multiple specialized agents and routes tasks between them
using whatever backend is configured (Local, HF, or OpenRouter).
"""

from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import PersonaRegistry
from hanerma.agents.native_personas.deep_reasoner import DeepReasonerAgent
from hanerma.agents.native_personas.system_verifier import SystemVerifier
from hanerma.memory.manager import HCMSManager
from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter

def main():
    # Initialize Memory Store (required for Verifier)
    tokenizer = XervCrayonAdapter()
    hcms = HCMSManager(tokenizer=tokenizer)

    # Initialize Orchestrator with default local model
    orch = HANERMAOrchestrator(model="local-llama3")
    registry = PersonaRegistry()

    # Register Native Agents
    registry.register_native("native::deep_reasoner", DeepReasonerAgent)
    registry.register_native("native::system_verifier", SystemVerifier)

    # Spawn agents
    # For SystemVerifier, we need to pass memory_store manually if we spawn it directly 
    # OR we can update the registry spawn method to inject dependencies.
    # For simplicity, we just initialize them manually or update spawn logic.
    # But wait, registry.spawn_agent just calls class(name=id).
    # SystemVerifier needs memory_store.
    # So registry spawning won't work perfectly for SystemVerifier unless we fix registry 
    # OR unless SystemVerifier handles None gracefully (which we know it doesn't).
    
    # Let's manually instantiate them to ensure correct dependencies, 
    # demonstrating the "Power User" setup.
    reasoner = DeepReasonerAgent(name="native::deep_reasoner")
    verifier = SystemVerifier(name="native::system_verifier", memory_store=hcms)

    orch.register_agent(reasoner)
    orch.register_agent(verifier)

    print(f"[Swarm] Initialized {len(orch.active_agents)} agents: {[a.name for a in orch.active_agents.values()]}")

    # Run the swarm
    result = orch.run(
        prompt="What are the security risks of WebSocket without TLS?",
        target_agent=reasoner.name,
    )
    print("\n[Result Payload]")
    print(result["output"])

if __name__ == "__main__":
    main()
