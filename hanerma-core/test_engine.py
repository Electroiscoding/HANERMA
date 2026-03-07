"""
Smoke test for the hanerma_core Rust DAG engine.

Run after `pip install -e .` inside hanerma-core/:
    python test_engine.py
"""

import time
from hanerma_core import RustEngine, NodeResult


# ── Simulated workloads (sleep = fake I/O like an LLM call) ────────────────

def fetch_data(deps: dict):
    """Root node — no dependencies."""
    time.sleep(0.3)
    return {"rows": [1, 2, 3, 4, 5]}


def process_a(deps: dict):
    """Depends on fetch_data — runs in PARALLEL with process_b."""
    data = deps["fetch"]
    time.sleep(0.5)
    return {"sum": sum(data["rows"])}


def process_b(deps: dict):
    """Depends on fetch_data — runs in PARALLEL with process_a."""
    data = deps["fetch"]
    time.sleep(0.5)
    return {"count": len(data["rows"])}


def merge(deps: dict):
    """Depends on BOTH process_a and process_b."""
    a = deps["proc_a"]
    b = deps["proc_b"]
    return {"average": a["sum"] / b["count"]}


# ── Build and execute the DAG ──────────────────────────────────────────────

def main():
    engine = RustEngine()

    engine.add_node("fetch", "Fetch Data", fetch_data, [])
    engine.add_node("proc_a", "Process A", process_a, ["fetch"])
    engine.add_node("proc_b", "Process B", process_b, ["fetch"])
    engine.add_node("merge", "Merge Results", merge, ["proc_a", "proc_b"])

    print(f"Registered {engine.node_count()} nodes")
    print(f"Topological order: {engine.validate()}")

    # Sequential would take 0.3 + 0.5 + 0.5 + ~0 = 1.3s
    # Parallel should take  0.3 + 0.5 + ~0         = ~0.8s
    wall_start = time.perf_counter()
    results = engine.execute()
    wall_ms = (time.perf_counter() - wall_start) * 1000

    print(f"\n{'='*60}")
    print(f"  DAG completed in {wall_ms:.1f} ms  (sequential would be ~1300 ms)")
    print(f"{'='*60}\n")

    for r in results:
        print(r)
        if r.result is not None:
            print(f"    → {r.result}")
        if r.error is not None:
            print(f"    ✗ {r.error}")


if __name__ == "__main__":
    main()
