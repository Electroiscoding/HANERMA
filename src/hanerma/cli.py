
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

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

async def run_mission(prompt: str, agents_list: Optional[List[str]] = None):
    """
    Sets up the hardware-rooted stack and executes the mission.
    """
    console.print()
    console.print(Panel(
        Text(f"🚀 HANERMA APEX MISSION: {prompt}", style="bold cyan"),
        title="[NEON-PULSE]",
        subtitle="[LAYER-0 BOOT SEQUENCE]",
        border_style="bright_cyan",
        box=box.DOUBLE_EDGE
    ))
    
    # 1. Initialize Bare-Metal Layer (Layer 0)
    console.print(" [grey42]◈[/] [L0] [cyan]Booting XERV-CRAYON Hardware Root...[/]")
    tokenizer = XervCrayonAdapter(profile="lite")
    
    # 2. Setup Orchestrator (Layer 1)
    model_id = os.getenv("HANERMA_MODEL") or os.getenv("HF_DEFAULT_MODEL") or "Qwen/Qwen3-Coder-Next-FP8:together"
    console.print(f" [grey42]◈[/] [L1] [cyan]Initializing Orchestrator[/] [grey37](Kernel: {model_id})[/]")
    orch = HANERMAOrchestrator(model=model_id, tokenizer=tokenizer)
    
    # 3. Equip Apex Tools
    reg = ToolRegistry()
    apex_tools = [reg.get_tool(n) for n in ["web_search", "calculator", "get_system_time", "delegate_task", "execute_sandbox"]]
    
    # 4. Agent Discovery & Spawning
    requested_agents = []
    if agents_list:
        requested_agents = agents_list
    else:
        lower_prompt = prompt.lower()
        if "architect" in lower_prompt:
            requested_agents.append("Code_Architect")
        if "verifier" in lower_prompt:
            requested_agents.append("Strict_Verifier")
        
        if not requested_agents:
            requested_agents = ["Apex_Specialist"]

    primary_agent = requested_agents[0]
    for name in requested_agents:
        role = "System Specialist"
        if "Architect" in name: role = "Senior Software Architect"
        if "Verifier" in name: role = "Lead Security & Verification Engineer"
        
        agent = spawn_agent(name, model=model_id, tools=apex_tools, role=role)
        orch.register_agent(agent)
        console.print(f" [grey42]◈[/] [L2] [spring_green3]Deployed Agent:[/] [bold]{name}[/] [grey37]({role})[/]")

    # 5. Core Execution Loop
    console.print(f"\n [grey42]◈[/] [L3] [bold bright_yellow]Executing Reasoning Swarm...[/]")
    try:
        result = await orch.run(prompt, target_agent=primary_agent)
        
        output_content = result.get('output', 'No output generated.')
        console.print()
        console.print(Panel(
            Text(output_content, style="bright_white"),
            title="💎 [bold bright_magenta]FINAL APEX MISSION OUTPUT[/] 💎",
            border_style="bright_magenta",
            box=box.ROUNDED,
            padding=(1, 2)
        ))
        
        # Telemetry
        metrics = result.get('metrics', {})
        latency = metrics.get('latency_ms', 0)
        iterations = metrics.get('iterations', 0)
        
        telemetry_text = Text()
        telemetry_text.append("\n [TELEMETRY] ", style="bold grey50")
        telemetry_text.append(f"Latency: {latency:.2f}ms", style="bright_cyan")
        telemetry_text.append(" | ", style="grey37")
        telemetry_text.append(f"Iterations: {iterations}", style="bright_green")
        telemetry_text.append(" | ", style="grey37")
        telemetry_text.append(f"Trace ID: {orch.trace_id}", style="grey50")
        
        console.print(telemetry_text)
        console.print(f" [PERSISTENCE] Database: [grey70]hanerma_state.db[/]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ [CRITICAL] Mission Failure:[/] {e}")
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
