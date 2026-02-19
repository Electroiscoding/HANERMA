
"""
Example 02: Spawning Grok-4.2 Sub-Agents
Demonstrates parallel execution of specialized roles.
"""
import asyncio
from hanerma.orchestrator.engine import HANERMAOrchestrator

async def main():
    # Initialize Orchestrator with Grok-4.2 model adaptor
    orch = HANERMAOrchestrator(model_name="grok-4.2")
    
    # Define a complex task
    task = "Analyze the sentiment of this crypto market trend and verify with latest news."
    
    # Run with specialized agents
    response = await orch.run(
        input_prompt=task, 
        agents=["MarketAnalyst", "NewsVerifier"]
    )
    
    print("\n--- Orchestrator Result ---")
    print(response["result"])
    print(f"Metrics: {response['metrics']}")

if __name__ == "__main__":
    asyncio.run(main())
