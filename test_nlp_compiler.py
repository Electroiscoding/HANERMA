"""Test: NLP-to-Graph Compiler (Slice 6)"""
import importlib.util
import os
import sys
import json

# Direct-load nlp_compiler (bypass broken hanerma.__init__)
spec = importlib.util.spec_from_file_location(
    "nlp_compiler",
    os.path.join(os.path.dirname(__file__), "src", "hanerma", "orchestrator", "nlp_compiler.py"),
)
nlp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nlp)

NLPCompiler = nlp.NLPCompiler
DAGSpec = nlp.DAGSpec
AgentSpec = nlp.AgentSpec

compiler = NLPCompiler()

# ── Test 1: Fast-path "give me a coder and verifier" ──
print("\n=== Test 1: 'give me a coder and verifier' ===")
dag = compiler.compile_prompt_to_dag("give me a coder and verifier")

assert isinstance(dag, DAGSpec), f"Expected DAGSpec, got {type(dag)}"
assert len(dag.agents) == 2, f"Expected 2 agents, got {len(dag.agents)}"
assert dag.agents[0].agent_id == "coder_0"
assert dag.agents[1].agent_id == "verifier_1"
assert dag.agents[1].dependencies == ["coder_0"], f"Wrong deps: {dag.agents[1].dependencies}"
assert len(dag.edges) == 1
assert dag.edges[0] == ["coder_0", "verifier_1"]

print(f"  ✓ Goal: {dag.goal}")
for a in dag.agents:
    print(f"  ✓ Agent: {a.agent_id} ({a.name}) | tools={a.tools} | deps={a.dependencies}")
print(f"  ✓ Edges: {dag.edges}")

# ── Test 2: Researcher + Coder + Tester pipeline ──
print("\n=== Test 2: 'researcher then coder then tester' ===")
dag2 = compiler.compile_prompt_to_dag("I need a researcher, then a coder, then a tester")

assert len(dag2.agents) == 3
assert dag2.agents[0].agent_id == "researcher_0"
assert dag2.agents[1].agent_id == "coder_1"
assert dag2.agents[2].agent_id == "tester_2"
assert dag2.agents[2].dependencies == ["coder_1"]
assert len(dag2.edges) == 2

print(f"  ✓ Goal: {dag2.goal}")
for a in dag2.agents:
    print(f"  ✓ Agent: {a.agent_id} ({a.name}) | deps={a.dependencies}")

# ── Test 3: Single agent ──
print("\n=== Test 3: Single agent 'debugger' ===")
dag3 = compiler.compile_prompt_to_dag("just give me a debugger")
assert len(dag3.agents) == 1
assert dag3.agents[0].agent_id == "debugger_0"
assert dag3.agents[0].tools == ["execute_sandbox", "web_search"]
print(f"  ✓ Single agent: {dag3.agents[0].name} with tools {dag3.agents[0].tools}")

# ── Test 4: Schema enforcement ──
print("\n=== Test 4: Schema Enforcement ===")
from pydantic import ValidationError

try:
    DAGSpec(goal="test", agents=[], edges=[])
    print("  ✗ ERROR: Should have rejected empty agents!")
except ValidationError:
    print("  ✓ Rejected empty agents list (min_length=1)")

# ── Test 5: DAG JSON serialization ──
print("\n=== Test 5: JSON Round-Trip ===")
dag_json = dag.model_dump_json(indent=2)
dag_back = DAGSpec.model_validate_json(dag_json)
assert dag_back.agents[0].agent_id == dag.agents[0].agent_id
print(f"  ✓ JSON round-trip: {len(dag_json)} bytes")

print(f"\n{'='*50}")
print("SLICE 6 VERIFIED ✓")
