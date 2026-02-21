
"""
HANERMA APEX CLI - The Zero-Friction End-Game Interface.
Usage: hanerma run "Mission Description"
"""
import argparse
import asyncio
import os
import sys
import json
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv()

from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import spawn_agent
from hanerma.tools.registry import ToolRegistry
from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter
from hanerma.autoprompt.enhancer import AutoPromptEnhancer

async def run_mission(prompt: str, agents_list: Optional[List[str]] = None):
    """
    Sets up the hardware-rooted stack and executes the mission.
    """
    print(f"\n{'='*80}")
    print(f"🚀 HANERMA APEX MISSION START")
    print(f"{'='*80}")
    
    # 1. Initialize Bare-Metal Layer (Layer 0)
    print(f" [L0] Booting XERV-CRAYON Hardware Root...")
    tokenizer = XervCrayonAdapter(profile="lite")
    
    # 2. Setup Orchestrator (Layer 1)
    model_id = os.getenv("HANERMA_MODEL") or os.getenv("HF_DEFAULT_MODEL") or "Qwen/Qwen3-Coder-Next-FP8:together"
    print(f" [L1] Initializing Orchestrator (Model: {model_id})")
    orch = HANERMAOrchestrator(model=model_id, tokenizer=tokenizer)
    
    # 3. Equip Apex Tools
    reg = ToolRegistry()
    apex_tools = [reg.get_tool(n) for n in ["web_search", "calculator", "get_system_time", "delegate_task", "execute_sandbox"]]
    
    # 4. Agent Discovery & Spawning
    # We dynamically detect if the user requested specific roles
    requested_agents = []
    if agents_list:
        requested_agents = agents_list
    else:
        # Heuristic detection for common roles
        lower_prompt = prompt.lower()
        if "architect" in lower_prompt:
            requested_agents.append("Code_Architect")
        if "verifier" in lower_prompt:
            requested_agents.append("Strict_Verifier")
        
        if not requested_agents:
            requested_agents = ["Apex_Specialist"]

    # Register agents with specialized profiles
    primary_agent = requested_agents[0]
    for name in requested_agents:
        role = "System Specialist"
        if "Architect" in name: role = "Senior Software Architect"
        if "Verifier" in name: role = "Lead Security & Verification Engineer"
        
        agent = spawn_agent(name, model=model_id, tools=apex_tools, role=role)
        orch.register_agent(agent)
        print(f" [L2] Deployed Agent: {name} ({role})")

    # 5. Core Execution Loop
    print(f"\n [L3] Executing Reasoning Swarm...")
    try:
        result = await orch.run(prompt, target_agent=primary_agent)
        
        print("\n" + "💎" + "="*78 + "💎")
        print(" FINAL APEX MISSION OUTPUT")
        print("="*80)
        print(result.get('output', 'No output generated.'))
        print("="*80)
        
        # Telemetry
        metrics = result.get('metrics', {})
        print(f"\n [TELEMETRY] Latency: {metrics.get('latency_ms', 0):.2f}ms | Iterations: {metrics.get('iterations', 0)}")
        print(f" [PERSISTENCE] Trace ID: {orch.trace_id}")
        print(f" [PERSISTENCE] Database: hanerma_state.db")
        
    except Exception as e:
        print(f"\n❌ [CRITICAL] Mission Failure: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(prog="hanerma", description="HANERMA Apex Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run
    run_parser = subparsers.add_parser("run", help="Execute a mission prompt through the reasoning swarm")
    run_parser.add_argument("mission", help="The textual description of the task")
    run_parser.add_argument("--agents", nargs="+", help="Explicitly specify agent names to deploy")

    # Subcommand: viz
    viz_parser = subparsers.add_parser("viz", help="Launch the Visual Dashboard / Observation Center")
    viz_parser.add_argument("--port", type=int, default=8081, help="Port to run the dashboard on")

    # Subcommand: demo
    demo_parser = subparsers.add_parser("demo", help="Run the ultimate all-in-one stack demonstration")

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(run_mission(args.mission, args.agents))
    elif args.command == "viz":
        from hanerma.observability.viz_server import start_viz
        start_viz(port=args.port)
    elif args.command == "demo":
        try:
            from apex_all_in_one import run_ultimate_demo
        except ImportError:
            import sys
            sys.path.append(os.getcwd())
            from apex_all_in_one import run_ultimate_demo
        asyncio.run(run_ultimate_demo())

if __name__ == "__main__":
    main()
