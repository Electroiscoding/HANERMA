import os, time, json
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import spawn_agent
from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter
from hanerma.tools.code_sandbox import NativeCodeSandbox
from dotenv import load_dotenv

load_dotenv()
MODEL = "Qwen/Qwen3-Coder-Next-FP8:together" if os.getenv("HF_TOKEN") else "local-llama3"

def apex_master_demo():
    print(f"\n{'='*75}\n💎 HANERMA APEX: MASTER INTEGRATION DEMO (SWARM V4)\n{'='*75}")
    
    # 1. Hardware & Memory Boot
    print("[XERV-CRAYON] Hardware Compression Active (L0).")
    tok = XervCrayonAdapter(profile="lite")
    orch = HANERMAOrchestrator(model=MODEL, tokenizer=tok)
    sandbox = NativeCodeSandbox()

    # 2. Tool Creation
    def run_safe_compute(**kwargs):
        """Executes Python code in a secure, isolated sandbox environment. Accept 'code'."""
        code = kwargs.get("code") or ""
        return sandbox.execute_code(code)

    # 3. Agent Spawning (Swarm Foundry)
    # We explicitly tell the Architect how to hand off.
    arch = spawn_agent("Code_Architect", model=MODEL, role="Architect")
    verifier = spawn_agent("Strict_Verifier", model=MODEL, role="Verifier", tools=[run_safe_compute])
    orch.register_agent(arch); orch.register_agent(verifier)

    # 4. Multi-Agent Reasoning Flow
    prompt = (
        "1. Architect: Write a Python function for age validation (reject < 18). "
        "2. Architect: Output 'DELEGATE: Strict_Verifier' to have it tested. "
        "3. Verifier: Use sandbox tool to test with birth year 2010."
    )
    print(f"[BUS] Orchestrator Input: {prompt}")
    
    start = time.time()
    result = orch.run(prompt, target_agent="Code_Architect", max_iterations=6)
    latency = (time.time() - start) * 1000

    # 5. The Verification Trap (Causal Report)
    print(f"\n{'-'*30} [SWARM VERIFICATION REPORT] {'-'*30}")
    print(result['output'])
    
    print(f"\n[TELEMETRY] Wall Clock: {latency:.2f}ms | Cycles: {result['metrics']['iterations']} | Tokens: {result['metrics']['total_tokens']}")
    print(f"{'='*75}")

if __name__ == "__main__":
    apex_master_demo()
