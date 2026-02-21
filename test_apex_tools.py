
import os, time, json, asyncio
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import spawn_agent
from hanerma.tools.registry import ToolRegistry
from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter
from dotenv import load_dotenv

load_dotenv()
MODEL = "Qwen/Qwen3-Coder-Next-FP8:together" if os.getenv("HF_TOKEN") else "local-llama3"

async def test_apex_tools():
    print(f"\n{'='*75}\n🔍 HANERMA APEX: TOOL VALIDATION TEST (TIME & WEB SEARCH)\n{'='*75}")
    
    # 1. Initialize Stack
    tok = XervCrayonAdapter(profile="lite")
    orch = HANERMAOrchestrator(model=MODEL, tokenizer=tok)
    
    # 2. Prepare Tools from Registry
    reg = ToolRegistry()
    tools = [reg.get_tool(name) for name in ["web_search", "get_system_time"]]
    
    # 3. Spawn Tester Agent (Context awareness is now injected natively)
    tester = spawn_agent("TesterAgent", model=MODEL, tools=tools, role="Quality Assurance")
    orch.register_agent(tester)

    # 4. Multi-Tool Task
    prompt = (
        "1. Identify the current system date and time using the tool.\n"
        "2. Search the web for 'Python programming news 2024' (use this exact query) and summarize the top find.\n"
        "3. Report both clearly."
    )
    
    print(f"[BUS] Orchestrator Input: {prompt}\n")
    
    start = time.time()
    result = await orch.run(prompt, target_agent="TesterAgent", max_iterations=4)
    latency = (time.time() - start) * 1000

    print(f"\n{'-'*30} [VERIFICATION OUTPUT] {'-'*30}")
    print(result['output'])
    
    print(f"\n[TELEMETRY] Latency: {latency:.2f}ms | Iterations: {result['metrics']['iterations']}")
    print(f"{'='*75}")

if __name__ == "__main__":
    asyncio.run(test_apex_tools())
