import os
import sys
import time
from dotenv import load_dotenv

# 1. Boilerplate Setup
load_dotenv()
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.native_personas.deep_reasoner import DeepReasonerAgent
from hanerma.agents.native_personas.system_verifier import SystemVerifier
from hanerma.memory.manager import HCMSManager
from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter

# 2. Define a Developer Tool
def get_vulnerable_code() -> str:
    """Simulates a tool that retrieves code from a repository."""
    return (
        "import sqlite3\n"
        "def get_user_data(user_id):\n"
        "    conn = sqlite3.connect('users.db')\n"
        "    cursor = conn.cursor()\n"
        "    # ATTN: VULNERABLE TO SQL INJECTION\n"
        "    query = f'SELECT * FROM users WHERE id = {user_id}'\n"
        "    cursor.execute(query)\n"
        "    return cursor.fetchall()"
    )

def main():
    print("="*80)
    print(" ⚡ HANERMA DEVELOPER SHOWCASE: COMPLEX SECURITY AUDIT WORKFLOW")
    print("="*80)

    # 3. Model Configuration (HuggingFace Together API)
    MODEL_ID = "Qwen/Qwen3-Coder-Next-FP8:together"
    
    # 4. Initialize Root Infrastructure
    # Crayon + HCMS provides the semantic background
    tokenizer = XervCrayonAdapter(profile="lite", device="auto")
    memory = HCMSManager(tokenizer=tokenizer)
    
    # Seed HCMS with the "Golden Rule" for this project
    memory.store_atomic_memory("global", "SECURITY POLICY: Never use f-strings for SQL queries. Always use parameterized queries.", "fact")

    # 5. Initialize Orchestrator & Agents
    orch = HANERMAOrchestrator(model=MODEL_ID, tokenizer=tokenizer)
    
    reasoner = DeepReasonerAgent(name="Security_Analyst")
    reasoner.equip_tools([get_vulnerable_code])
    
    verifier = SystemVerifier(name="Compliance_Checker", memory_store=memory)

    orch.register_agent(reasoner)
    orch.register_agent(verifier)

    # 6. EXECUTION PHASE A: Complex Reasoning & Patching
    print("\n[STEP 1] Running Deep Security Audit...")
    prompt_a = (
        "Call the 'get_vulnerable_code' tool to fetch the target module. "
        "Identify the vulnerability and provide a corrected version of the 'get_user_data' function. "
        "Be mathematically precise in your reasoning."
    )
    
    res_a = orch.run(prompt=prompt_a, target_agent="Security_Analyst")
    
    print(f"\nANALYST OUTPUT:\n{res_a['output']}")
    print(f"Metrics: {res_a['metrics']['total_tokens']} tokens | {res_a['metrics']['latency_ms']}ms")

    # 7. EXECUTION PHASE B: Nested Cross-Verification
    print("\n" + "-"*40)
    print("[STEP 2] Running Fact-Check against HCMS Security Policies...")
    
    # The verifier checks if the analyst's fix complies with the Golden Rule seeded in memory
    claim_to_verify = f"The proposed fix for get_user_data uses parameterized queries: {res_a['output']}"
    res_b = orch.run(prompt=claim_to_verify, target_agent="Compliance_Checker")
    
    print(f"\nVERIFIER REPORT: {res_b['output']}")
    
    # 8. Final Status
    print("\n" + "="*80)
    print(" ✅ WORKFLOW COMPLETE")
    print(f" Total Cumulative Latency: {res_a['metrics']['latency_ms'] + res_b['metrics']['latency_ms']}ms")
    print(f" Total Crayon Tokens Consumed: {res_a['metrics']['total_tokens'] + res_b['metrics']['total_tokens']}")
    print("="*80)

if __name__ == "__main__":
    main()
