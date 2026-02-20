from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import PersonaRegistry
from hanerma.agents.native_personas.system_verifier import SystemVerifier

def main():
    """
    Demonstrates the Zero-Error Atomic Agent in action.
    This example specifically triggers the Deep 2 Verification loop
    by attempting to inject a false fact.
    """
    orch = HANERMAOrchestrator(model="local-llama3")
    registry = PersonaRegistry()
    
    # 1. Register the System Verifier
    verifier = SystemVerifier()
    registry.register_native("system_verifier", SystemVerifier)
    orch.register_agent(verifier)
    
    # 2. Simulate a user asking for a verifiable fact
    prompt = "Is the speed of light exactly 300,000 km/s?"
    print(f"User: {prompt}")
    
    # 3. Run the orchestration
    result = orch.run(prompt=prompt, target_agent="system_verifier")
    
    print("\n[Result Payload]")
    print(result.get("output", "No Output"))
    print(f"Metrics: {result.get('metrics', {})}")
    
if __name__ == "__main__":
    main()
