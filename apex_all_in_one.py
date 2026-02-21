"""
🚀 HANERMA APEX | THE ULTIMATE ALL-IN-ONE DEMO (PRODUCTION)
==========================================================
This script demonstrates the full power of the Apex Architecture (V1.0)
from Layer 0 (Hardware Root) to Layer 3 (Recursive Orchestration).

ALL TOOLS ARE BARE-METAL (No Placeholders).
"""

import os
import time
import uuid
import json
from dotenv import load_dotenv

# Import Core HANERMA Apex Stack
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import spawn_agent
from hanerma.memory.manager import HCMSManager
from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter
from hanerma.tools.code_sandbox import NativeCodeSandbox

# Load environment
load_dotenv()

def print_header(title):
    print(f"\n{'='*70}")
    print(f"💎 {title}")
    print(f"{'='*70}")

import asyncio

async def run_ultimate_demo():
    # --- PHASE 1: HARDWARE ROOT (XERV-CRAYON) ---
    print_header("PHASE 1: HARDWARE ROOT (XERV-CRAYON)")
    tokenizer = XervCrayonAdapter(profile="lite")
    text = "The HANERMA Apex Architecture utilizes Xerv-Crayon for bare-metal tokenization and spectral hashing."
    
    start = time.time()
    tokens = tokenizer.count_tokens(text)
    embedding = tokenizer.embed(text, dim=128)
    latency = (time.time() - start) * 1000
    
    print(f"[CRAYON] Token Count: {tokens}")
    print(f"[CRAYON] Vector Dim: {len(embedding)}")
    print(f"[CRAYON] Latency: {latency:.4f}ms (Hardware Accelerated Layer 0)")

    # --- PHASE 2: MEMORY VAULT (HCMS) ---
    print_header("PHASE 2: MEMORY VAULT (HYPERFAST COMPRESSED MEMORY)")
    memory_manager = HCMSManager(tokenizer=tokenizer)
    
    architectural_truth = "Base Logic: Every recursive frame must be bound by Layer 1 verification guards."
    memory_manager.store_atomic_memory(session_id="root_demo", raw_text=architectural_truth, entity_type="fact")
    
    print("[HCMS] Stored atomic truth in FAISS-indexed vector space.")
    print(f"[HCMS] Persisted Fact: {architectural_truth}")

    # --- PHASE 3: APEX ORCHESTRATION ---
    print_header("PHASE 3: APEX ORCHESTRATION & AGENT FOUNDRY")
    
    # Model failover chain logic
    model_id = "Qwen/Qwen3-Coder-Next-FP8:together" if os.getenv("HF_TOKEN") else "local-llama3"
    orch = HANERMAOrchestrator(model=model_id, tokenizer=tokenizer)
    
    # Initialize real, production-grade Sandbox
    sandbox = NativeCodeSandbox()
    
    def run_safe_compute(**kwargs):
        """Executes Python code in a secure, isolated sandbox environment. Accept 'code' or 'logic'."""
        code = kwargs.get("code") or kwargs.get("logic") or ""
        return sandbox.execute_code(code)

    # Spawn and Register Agents with REAL capabilities
    from hanerma.tools.registry import ToolRegistry
    reg = ToolRegistry()
    default_tools = [reg.get_tool(name) for name in ["web_search", "calculator", "get_system_time", "delegate_task"]]
    
    engineer = spawn_agent("ApexArchitect", model=model_id, tools=[run_safe_compute] + default_tools)
    orch.register_agent(engineer)
    
    print(f"[ORCH] Kernel initialized. Current Model: {model_id}")
    print(f"[ORCH] Agent 'ApexArchitect' deployed with Native Code Sandbox (Root Tool).")

    # --- PHASE 4: RECURSIVE REASONING CYCLE ---
    print_header("PHASE 4: TRANSACTIONAL REASONING & VERIFICATION")
    
    complex_prompt = (
        "Analyze the following architectural requirement: 'System must calculate the recursive depth of 4' "
        "and execute a Python script in the sandbox to verify the result. Then store the result as a fact."
    )
    
    print(f"KERNEL_INPUT: '{complex_prompt}'\n")
    print("[HANERMA] Initiating Transactional Bus (SQLite Persistence)...")
    
    start_time = time.time()
    result = await orch.run(complex_prompt, target_agent="ApexArchitect")
    end_time = time.time()
    
    print("\n--- KERNEL_OUTPUT ---")
    print(result['output'])
    
    # Show real metrics from the orchestration bus
    print("\n--- CAUSAL TELEMETRY ---")
    metrics = result.get('metrics', {})
    metrics['wall_clock_ms'] = round((end_time - start_time) * 1000, 2)
    print(json.dumps(metrics, indent=4))

    # --- PHASE 5: VISUAL INTELLIGENCE ---
    print_header("PHASE 5: VISUAL OS (LAYER 3)")
    print("The entire trace above has been persisted to 'hanerma_state.db'.")
    print("Launch the Premium Apex OS Dashboard to visualize the causal graph:")
    print("\n   COMMAND: python src/hanerma/observability/viz_server.py")
    print("   URL: http://localhost:8081")

if __name__ == "__main__":
    try:
        asyncio.run(run_ultimate_demo())
    except Exception as e:
        print(f"\n❌ [CRITICAL] Execution interrupted: {e}")
        import traceback
        traceback.print_exc()
