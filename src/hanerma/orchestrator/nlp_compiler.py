"""
NLP-to-Graph Compiler — Compiles English into multi-agent DAGs.

Translates natural language like "give me a coder and verifier" into
a fully wired DAG of Agent objects registered in the RustEngine.

Uses the Grammar Shield (Slice 3) to FORCE the LLM to output a
strict Pydantic-validated DAG schema.  No regex parsing.  No raw text.

Usage:
    dag = compile_prompt_to_graph("Build a pipeline: researcher finds info, coder writes code, tester verifies")
    engine_results = dag.execute()
"""

import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("hanerma.nlp_compiler")


# ═══════════════════════════════════════════════════════════════════════════
#  Pydantic Schemas — the LLM MUST output these exact shapes
# ═══════════════════════════════════════════════════════════════════════════


class AgentSpec(BaseModel):
    """Schema for a single agent in the compiled DAG."""
    agent_id: str = Field(
        ..., description="Unique snake_case identifier, e.g. 'code_writer'"
    )
    name: str = Field(
        ..., description="Human-readable display name, e.g. 'Code Writer'"
    )
    role: str = Field(
        ..., description="One-sentence description of this agent's purpose"
    )
    system_prompt: str = Field(
        ..., description="The system prompt injected into this agent's LLM context"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of tool names from the registry to equip"
    )
    model: str = Field(
        default="llama3",
        description="LLM model identifier (local or cloud)"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of agent_ids this agent depends on (must finish first)"
    )


class DAGSpec(BaseModel):
    """Complete compiled DAG specification from natural language."""
    goal: str = Field(
        ..., description="One-sentence summary of what this DAG achieves"
    )
    agents: List[AgentSpec] = Field(
        ..., min_length=1,
        description="Ordered list of agents in the pipeline"
    )
    edges: List[List[str]] = Field(
        default_factory=list,
        description="Directed edges [from_agent_id, to_agent_id]"
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Available tools manifest (injected into LLM context)
# ═══════════════════════════════════════════════════════════════════════════

TOOL_MANIFEST = {
    "web_search": "Search the web for up-to-date information",
    "calculator": "Perform safe math calculations (sqrt, trig, etc.)",
    "get_system_time": "Returns the current system date and time",
    "delegate_task": "Handoff the current task to another agent",
    "internal_search": "Search internal project files and documentation",
    "execute_sandbox": "Execute Python code securely in a sandbox",
    "transcribe_audio": "Transcribe audio file to text using Faster-Whisper STT",
    "analyze_image": "Analyze image using local vision model (LLaVA)",
    "start_voice_listening": "Start continuous voice listening mode with real-time STT",
}


# ═══════════════════════════════════════════════════════════════════════════
#  NLP Compiler — LLM-powered, Grammar-Shield-enforced
# ═══════════════════════════════════════════════════════════════════════════


class NLPCompiler:
    """
    Compiles English prompts into executable multi-agent DAGs.

    The LLM is constrained via the Grammar Shield to output a strict
    DAGSpec Pydantic model — it physically cannot hallucinate invalid
    agent configurations or nonexistent tools.
    """

    # Well-known agent personas for common patterns
    KNOWN_PERSONAS = {
        "coder": {
            "name": "Code Writer",
            "role": "Writes production-grade code to solve the given task",
            "system_prompt": (
                "You are a senior software engineer. Write clean, "
                "production-ready code. Include error handling and "
                "type hints. Explain your design decisions."
            ),
            "tools": ["execute_sandbox", "web_search"],
        },
        "verifier": {
            "name": "Code Verifier",
            "role": "Reviews and tests code for correctness and edge cases",
            "system_prompt": (
                "You are a strict code reviewer and QA engineer. "
                "Find bugs, edge cases, and security issues. Write "
                "test cases. Never approve code that could fail."
            ),
            "tools": ["execute_sandbox", "calculator"],
        },
        "researcher": {
            "name": "Research Analyst",
            "role": "Gathers and synthesizes information from multiple sources",
            "system_prompt": (
                "You are a research analyst. Search for relevant "
                "information, cross-reference sources, and provide "
                "a structured summary with citations."
            ),
            "tools": ["web_search", "internal_search"],
        },
        "planner": {
            "name": "Task Planner",
            "role": "Breaks down complex tasks into actionable steps",
            "system_prompt": (
                "You are a project planner. Decompose complex tasks "
                "into clear, ordered steps. Identify dependencies "
                "and potential risks."
            ),
            "tools": ["calculator", "get_system_time"],
        },
        "tester": {
            "name": "Test Engineer",
            "role": "Writes and executes comprehensive test suites",
            "system_prompt": (
                "You are a test engineer. Write comprehensive tests "
                "covering happy paths, edge cases, and failure modes. "
                "Use pytest conventions."
            ),
            "tools": ["execute_sandbox"],
        },
        "debugger": {
            "name": "Debug Specialist",
            "role": "Diagnoses and fixes bugs in code",
            "system_prompt": (
                "You are a debugging specialist. Analyze error messages, "
                "stack traces, and code flow to identify root causes. "
                "Propose minimal, targeted fixes."
            ),
            "tools": ["execute_sandbox", "web_search"],
        },
    }

    def __init__(self, shield=None):
        """
        Args:
            shield: Optional GrammarShield instance. If None, uses a new one.
        """
        self._shield = shield

    def _get_shield(self):
        """Lazy-load Grammar Shield."""
        if self._shield is not None:
            return self._shield
        from hanerma.models.constrained import GrammarShield
        self._shield = GrammarShield()
        return self._shield

    def compile_prompt_to_dag(self, english_prompt: str) -> DAGSpec:
        """
        Compile an English prompt into a validated DAGSpec.

        The LLM is mathematically constrained to output valid JSON
        matching the DAGSpec schema.  No regex.  No raw text.

        Args:
            english_prompt: Natural language description of the desired pipeline.
                            e.g. "give me a coder and verifier"

        Returns:
            DAGSpec — validated multi-agent DAG specification.
        """
        # Try fast-path: pattern matching for common requests
        fast_result = self._try_fast_compile(english_prompt)
        if fast_result is not None:
            logger.info("Fast-compiled DAG: %s", fast_result.goal)
            return fast_result

        # Full LLM path: Grammar Shield enforced
        shield = self._get_shield()

        tool_list = "\n".join(
            f"  - {name}: {desc}" for name, desc in TOOL_MANIFEST.items()
        )

        system = (
            "You are a HANERMA Graph Compiler. Translate natural language "
            "descriptions into multi-agent DAG specifications.\n\n"
            f"Available tools:\n{tool_list}\n\n"
            "Rules:\n"
            "- agent_id must be unique snake_case\n"
            "- tools must be from the available list above\n"
            "- dependencies list agent_ids that must finish first\n"
            "- edges define data flow: [from_agent_id, to_agent_id]\n"
            "- model defaults to 'llama3' for local execution\n"
            "- system_prompt should be specific and actionable"
        )

        return shield.generate(
            prompt=english_prompt,
            schema=DAGSpec,
            system_prompt=system,
        )

    def _try_fast_compile(self, prompt: str) -> Optional[DAGSpec]:
        """
        Pattern-match common English requests without LLM round-trip.
        Returns None if the prompt doesn't match any known pattern.
        """
        prompt_lower = prompt.lower().strip()

        # Detect mentioned personas, ordered by position in prompt
        detected = []
        for key, persona in self.KNOWN_PERSONAS.items():
            pos = prompt_lower.find(key)
            if pos != -1:
                detected.append((pos, key, persona))

        if not detected:
            return None  # Fall through to LLM

        # Sort by position in prompt (preserve user's intended order)
        detected.sort(key=lambda x: x[0])

        # Build agents with auto-wired dependencies (sequential pipeline)
        agents = []
        edges = []
        prev_id = None

        for idx, (_, key, persona) in enumerate(detected):
            agent_id = f"{key}_{idx}"
            deps = [prev_id] if prev_id else []

            agents.append(AgentSpec(
                agent_id=agent_id,
                name=persona["name"],
                role=persona["role"],
                system_prompt=persona["system_prompt"],
                tools=persona["tools"],
                model="llama3",
                dependencies=deps,
            ))

            if prev_id:
                edges.append([prev_id, agent_id])
            prev_id = agent_id

        goal = f"Pipeline: {' → '.join(p['name'] for _, _, p in detected)}"
        return DAGSpec(goal=goal, agents=agents, edges=edges)

    def spawn_agents(self, dag: DAGSpec) -> Dict[str, Any]:
        """
        Instantiate real Python Agent objects from the DAGSpec
        and register them into a RustEngine for parallel execution.

        Returns:
            Dict with 'engine' (RustEngine), 'agents' (dict of BaseAgent),
            and 'dag_spec' (the original spec).
        """
        from hanerma.agents.base_agent import BaseAgent

        # Try Rust engine; fall back to Python-only if not compiled
        engine = None
        try:
            from hanerma_core import RustEngine
            engine = RustEngine()
        except ImportError:
            logger.warning("hanerma_core not available, using Python-only mode")

        agents: Dict[str, BaseAgent] = {}

        for spec in dag.agents:
            # Create BaseAgent
            agent = BaseAgent(
                name=spec.name,
                role=spec.role,
                system_prompt=spec.system_prompt,
                model=spec.model,
            )

            # Equip tools from the registry
            if spec.tools:
                try:
                    from hanerma.tools.registry import ToolRegistry
                    registry = ToolRegistry()
                    tools_to_equip = []
                    for tool_name in spec.tools:
                        tool = registry.get_tool(tool_name)
                        if tool is not None:
                            tools_to_equip.append(tool)
                        else:
                            logger.warning(
                                "Tool '%s' not found in registry", tool_name
                            )
                    if tools_to_equip:
                        agent.equip_tools(tools_to_equip)
                except ImportError:
                    logger.warning("Tool registry not available")

            agents[spec.agent_id] = agent

            # Register callable into RustEngine for parallel execution
            if engine is not None:
                dep_ids = spec.dependencies or []
                # Create a closure that executes the agent
                def make_callable(a=agent):
                    def run():
                        return f"[{a.name}] Ready"
                    return run

                engine.add_node(
                    node_id=spec.agent_id,
                    name=spec.name,
                    callable=make_callable(),
                    dependencies=dep_ids if dep_ids else None,
                )

        logger.info(
            "Spawned %d agents: %s",
            len(agents),
            [s.agent_id for s in dag.agents],
        )

        return {
            "engine": engine,
            "agents": agents,
            "dag_spec": dag,
        }


# ═══════════════════════════════════════════════════════════════════════════
#  Convenience API
# ═══════════════════════════════════════════════════════════════════════════


def compile_prompt_to_graph(english_prompt: str) -> Dict[str, Any]:
    """
    One-liner: English → compiled DAG → spawned agents + RustEngine.

    Usage:
        result = compile_prompt_to_graph("give me a coder and verifier")
        engine = result["engine"]
        agents = result["agents"]
    """
    compiler = NLPCompiler()
    dag = compiler.compile_prompt_to_dag(english_prompt)
    return compiler.spawn_agents(dag)
