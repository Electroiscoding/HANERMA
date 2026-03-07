"""Quick import + schema verification for Grammar Shield.
Uses importlib to bypass the broken hanerma.__init__ import chain.
"""
import importlib.util
import sys
import os

# Load constrained.py directly without triggering hanerma.__init__
spec = importlib.util.spec_from_file_location(
    "constrained",
    os.path.join(os.path.dirname(__file__), "src", "hanerma", "models", "constrained.py"),
)
constrained = importlib.util.module_from_spec(spec)
spec.loader.exec_module(constrained)

GrammarShield = constrained.GrammarShield
AgentOutput = constrained.AgentOutput
ToolCallRequest = constrained.ToolCallRequest
ReasoningStep = constrained.ReasoningStep
MultiToolPlan = constrained.MultiToolPlan
BackendType = constrained.BackendType

print("All Grammar Shield imports OK")
print(f"AgentOutput fields:     {list(AgentOutput.model_json_schema()['properties'].keys())}")
print(f"ToolCallRequest fields: {list(ToolCallRequest.model_json_schema()['properties'].keys())}")
print(f"ReasoningStep fields:   {list(ReasoningStep.model_json_schema()['properties'].keys())}")
print(f"Backend types:          {[e.value for e in BackendType]}")

# Verify Pydantic validation works
out = AgentOutput(
    reasoning=[ReasoningStep(thought="analyzing data", action="respond", confidence=0.9, response="result is 42")],
    final_answer="The answer is 42",
    assertions=[{"fact": "answer", "operator": "==", "value": 42}],
)
print(f"\nAgentOutput validated: {out.final_answer}")
print(f"  Reasoning steps: {len(out.reasoning)}")
print(f"  Step 1 confidence: {out.reasoning[0].confidence}")
print(f"  Assertions: {out.assertions}")

call = ToolCallRequest(tool_name="web_search", arguments={"query": "AAPL stock"}, rationale="need price data")
print(f"ToolCallRequest validated: {call.tool_name}({call.arguments})")

plan = MultiToolPlan(
    plan=[
        ToolCallRequest(tool_name="web_search", arguments={"query": "AAPL"}),
        ToolCallRequest(tool_name="calculator", arguments={"expression": "150*100"}),
    ],
    goal="Calculate portfolio value",
)
print(f"MultiToolPlan validated: {len(plan.plan)} steps for '{plan.goal}'")

# Verify schema enforcement catches bad output
from pydantic import ValidationError
try:
    AgentOutput(reasoning=[], final_answer="")  # min_length=1 violated
    print("ERROR: Should have rejected empty reasoning!")
except ValidationError:
    print("Schema enforcement: rejected empty reasoning chain (as expected)")

try:
    ReasoningStep(thought="x", action="respond", confidence=1.5)  # max 1.0
    print("ERROR: Should have rejected confidence > 1.0!")
except ValidationError:
    print("Schema enforcement: rejected confidence > 1.0 (as expected)")

# Verify GrammarShield initializes
shield = GrammarShield(backend=BackendType.AUTO)
print(f"\nGrammarShield created (will auto-detect backend on first call)")

# Print full JSON schema for AgentOutput
import json
print("\n--- AgentOutput JSON Schema ---")
print(json.dumps(AgentOutput.model_json_schema(), indent=2))

print("\nSLICE 3 VERIFIED ✓")
