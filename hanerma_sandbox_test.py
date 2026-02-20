
import os
from dotenv import load_dotenv
load_dotenv()

from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.native_personas.deep_reasoner import DeepReasonerAgent
from hanerma.tools.code_sandbox import NativeCodeSandbox
from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter

def main():
    print("="*80)
    print(" 🛠️  HANERMA NATIVE POWER: RECURSIVE SANDBOXING")
    print("="*80)

    MODEL_ID = "Qwen/Qwen3-Coder-Next-FP8:together"
    tokenizer = XervCrayonAdapter()
    orch = HANERMAOrchestrator(model=MODEL_ID, tokenizer=tokenizer)
    
    sandbox = NativeCodeSandbox()
    agent = DeepReasonerAgent(name="Sandbox_Analyst")
    agent.equip_tools([sandbox.execute_code])
    
    orch.register_agent(agent)

    # We use a task that is mathematically verifiable
    prompt = (
        "Calculate the 100th prime number. "
        "Strictly follow these steps:\n"
        "1. Write a Python function to find primes.\n"
        "2. Call 'execute_code' with your code to get the answer.\n"
        "3. State the final resulting number based on the tool output.\n\n"
        "FORMAT: TOOL_CALL: execute_code(code='...')"
    )

    print(f"\n[TASK] {prompt}\n")
    
    # Run the recursive loop
    result = orch.run(prompt=prompt, target_agent="Sandbox_Analyst", max_iterations=5)

    print("\n" + "="*80)
    print(f" FINAL VERIFIED ANSWER:\n {result['output']}")
    print("-" * 80)
    print(f" Metrics: Iterations={result['metrics']['iterations']} | Tokens={result['metrics']['total_tokens']}")
    print("="*80)

if __name__ == "__main__":
    main()
