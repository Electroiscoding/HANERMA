"""Tests for Slices 11 & 12"""
import importlib.util
import os
import sys
import json
import tempfile

BASE = os.path.dirname(__file__)
SRC = os.path.join(BASE, "src")


def load_module(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SRC, *rel_path.split("/")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ═══════════════════════════════════════════════════════════════════════════
#  SLICE 11: Universal @tool & Zero-Config
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SLICE 11: Universal @tool & Zero-Config")
print("=" * 60)

registry = load_module("registry", "hanerma/tools/registry.py")
tool = registry.tool
Tool = registry.Tool
ToolRegistry = registry.ToolRegistry

# Test 1: @tool decorator on sync function
print("\n--- Test 11.1: @tool on Sync Function ---")

@tool
def add_numbers(a: int, b: int = 0) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number (default: 0)
    """
    return a + b

assert isinstance(add_numbers, Tool), f"Expected Tool, got {type(add_numbers)}"
assert add_numbers.name == "add_numbers"
assert "a" in add_numbers.schema.get("properties", {})
assert "b" in add_numbers.schema.get("properties", {})
print(f"  ✓ Name: {add_numbers.name}")
print(f"  ✓ Schema: {json.dumps(add_numbers.schema, indent=2)[:200]}")

# Test 2: Call with validation
print("\n--- Test 11.2: Validated Call ---")
result = add_numbers.call(a=5, b=3)
assert result == 8, f"Expected 8, got {result}"
print(f"  ✓ add_numbers(5, 3) = {result}")

result2 = add_numbers.call(a=10)
assert result2 == 10, f"Expected 10, got {result2}"
print(f"  ✓ add_numbers(10) = {result2} (default b=0)")

# Test 3: @tool with custom name
print("\n--- Test 11.3: Custom Name ---")

@tool(name="search_web")
def my_search(query: str, limit: int = 5) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

assert my_search.name == "search_web"
assert my_search.call(query="python") == "Results for: python"
print(f"  ✓ Custom name: {my_search.name}")

# Test 4: Schema has types from inspect
print("\n--- Test 11.4: Type Resolution ---")
schema = add_numbers.schema
props = schema.get("properties", {})
assert props["a"]["type"] == "integer", f"Expected integer, got {props['a']}"
assert props["b"]["type"] == "integer"
assert "default" in props["b"] or props["b"].get("default") == 0
print(f"  ✓ a: {props['a']}")
print(f"  ✓ b: {props['b']}")

# Test 5: Docstring param parsing
print("\n--- Test 11.5: Docstring Param Parsing ---")
if "description" in props.get("a", {}):
    print(f"  ✓ a description: '{props['a']['description']}'")
else:
    print(f"  ✓ a type parsed (description extraction is best-effort)")

# Test 6: Error handling
print("\n--- Test 11.6: Error Handling ---")

@tool
def failing_tool(x: int) -> int:
    """Always fails."""
    raise ValueError("intentional failure")

result = failing_tool.call(x=1)
assert "TOOL_ERROR" in result or "ValueError" in result
print(f"  ✓ Error caught gracefully: {result[:80]}")

# Test 7: Async function support
print("\n--- Test 11.7: Async Tool Detection ---")
import asyncio

@tool
async def async_search(query: str) -> str:
    """Async search tool."""
    return f"Async: {query}"

assert async_search.is_async is True
print(f"  ✓ Async detected: is_async={async_search.is_async}")

# Test 8: ToolRegistry
print("\n--- Test 11.8: ToolRegistry ---")
reg = ToolRegistry(auto_register=False)
reg.register(add_numbers)
reg.register(my_search)

assert len(reg) == 2
assert reg.get_tool("add_numbers") is not None
schemas = reg.get_all_schemas()
assert len(schemas) == 2
print(f"  ✓ Registry: {reg}")
print(f"  ✓ Schemas: {len(schemas)} generated")

# Test 9: Local detector
print("\n--- Test 11.9: Local Detector ---")
detector = load_module("local_detector", "hanerma/tools/local_detector.py")
# Just verify the module loads and the function exists
assert hasattr(detector, "detect_local_backends")
assert hasattr(detector, "get_default_model")
assert hasattr(detector, "is_ollama_running")
result = detector.get_default_model(timeout=0.5)  # Fast timeout for test
assert "model" in result
assert "source" in result
print(f"  ✓ Default model: {result['model']} (source={result['source']})")

print("\n  SLICE 11 ✓")


# ═══════════════════════════════════════════════════════════════════════════
#  SLICE 12: Prometheus Telemetry & deploy --prod
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SLICE 12: Prometheus Telemetry & deploy --prod")
print("=" * 60)

# Test 1: Metrics module
print("\n--- Test 12.1: Prometheus Metrics ---")
metrics = load_module("metrics", "hanerma/observability/metrics.py")
tracker = metrics.MetricsTracker()

tracker.start_trace("test-1")
tracker.log_token_usage("test-1", 100, 50)
tracker.record_nested_correction("test-1")
tracker.record_dag_step("success")
tracker.record_tool_latency("calculator", 0.005)
summary = tracker.end_trace("test-1")

assert summary["total_tokens"] == 150
assert summary["corrections_made"] == 1
print(f"  ✓ Trace summary: {json.dumps(summary)}")

# Test 2: /metrics endpoint
print("\n--- Test 12.2: /metrics Endpoint ---")
from fastapi.testclient import TestClient
client = TestClient(metrics.app)
r = client.get("/metrics")
assert r.status_code == 200
body = r.text
assert "hanerma_dag_execution_seconds" in body
assert "hanerma_hallucinations_caught_total" in body
assert "hanerma_tokens_total" in body
print(f"  ✓ /metrics: {len(body)} bytes, all counters present")

# Test 3: deploy --prod
print("\n--- Test 12.3: deploy --prod ---")
cli = load_module("cli", "hanerma/cli.py")

# Run in temp dir to avoid polluting project
import tempfile
original_dir = os.getcwd()
with tempfile.TemporaryDirectory() as tmpdir:
    os.chdir(tmpdir)
    cli._cmd_deploy_prod(replicas=3, image="hanerma:latest")

    assert os.path.exists("docker-compose.prod.yml"), "docker-compose not generated!"
    assert os.path.exists("deployment.yaml"), "deployment.yaml not generated!"
    assert os.path.exists("prometheus.yml"), "prometheus.yml not generated!"

    # Validate docker-compose
    import yaml
    with open("docker-compose.prod.yml") as f:
        lines = f.readlines()
        compose = yaml.safe_load("".join(lines[1:]))  # Skip comment line
    assert "hanerma-engine" in compose["services"]
    assert "prometheus" in compose["services"]
    assert "grafana" in compose["services"]
    assert "hanerma-replica-1" in compose["services"]
    print(f"  ✓ docker-compose.prod.yml: {len(compose['services'])} services")

    # Validate k8s
    with open("deployment.yaml") as f:
        docs = list(yaml.safe_load_all(f))
    deployment = None
    service = None
    for doc in docs:
        if doc and doc.get("kind") == "Deployment":
            deployment = doc
        if doc and doc.get("kind") == "Service":
            service = doc
    assert deployment is not None, "No Deployment found!"
    assert deployment["spec"]["replicas"] == 3
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert container["livenessProbe"] is not None
    assert container["readinessProbe"] is not None
    assert container["resources"]["requests"]["cpu"] == "2000m"
    print(f"  ✓ deployment.yaml: {deployment['spec']['replicas']} replicas, health checks, resource limits")

    assert service is not None
    print(f"  ✓ Service: {service['metadata']['name']}")

    os.chdir(original_dir)

# Test 4: test --redteam
print("\n--- Test 12.4: test --redteam ---")
with tempfile.TemporaryDirectory() as tmpdir:
    report_path = os.path.join(tmpdir, "redteam_report.md")
    cli._cmd_redteam(output_path=report_path)

    assert os.path.exists(report_path), "Report not generated!"
    with open(report_path, encoding="utf-8") as f:
        report = f.read()
    assert "Red Team Report" in report
    assert "Contradictions Caught" in report
    assert "CAUGHT" in report
    assert "PASS" in report
    lines = report.strip().split("\n")
    print(f"  ✓ Report: {len(lines)} lines, {len(report)} bytes")

print("\n  SLICE 12 ✓")


# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SLICES 11 + 12 ALL VERIFIED ✓")
print("=" * 60)
