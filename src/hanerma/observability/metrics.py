"""
Enterprise Prometheus Telemetry.

Exposes a /metrics FastAPI endpoint tracking:
  - dag_execution_time (Histogram)
  - hallucinations_caught (Counter)
  - tool_latency_seconds (Histogram)
  - tokens_consumed_total (Counter)
  - raft_commits_total (Counter)
  - healing_attempts_total (Counter)
  - routing_decisions_total (Counter)

Also provides MetricsTracker for in-process instrumentation.
"""

import time
from typing import Any, Dict, Optional

from hanerma.core.config import settings

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import FastAPI, Response

# ═══════════════════════════════════════════════════════════════════════════
#  Prometheus Metrics Registry
# ═══════════════════════════════════════════════════════════════════════════

registry = CollectorRegistry()

# Core execution
dag_execution_time = Histogram(
    "hanerma_dag_execution_seconds",
    "DAG execution time in seconds",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry,
)

dag_steps_total = Counter(
    "hanerma_dag_steps_total",
    "Total DAG steps executed",
    labelnames=["status"],
    registry=registry,
)

# LLM & tokens
tokens_consumed_total = Counter(
    "hanerma_tokens_total",
    "Total LLM tokens consumed",
    labelnames=["direction"],  # "input" or "output"
    registry=registry,
)

# Reliability
hallucinations_caught = Counter(
    "hanerma_hallucinations_caught_total",
    "Number of hallucinations caught by Z3 or Grammar Shield",
    registry=registry,
)

healing_attempts_total = Counter(
    "hanerma_healing_attempts_total",
    "Number of supervisor healing attempts",
    labelnames=["action", "success"],
    registry=registry,
)

# Tools
tool_latency_seconds = Histogram(
    "hanerma_tool_latency_seconds",
    "Tool execution latency",
    labelnames=["tool_name"],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry,
)

# Distributed
raft_commits_total = Counter(
    "hanerma_raft_commits_total",
    "Number of Raft consensus commits",
    registry=registry,
)

# Routing
routing_decisions_total = Counter(
    "hanerma_routing_decisions_total",
    "Model routing decisions",
    labelnames=["model", "reason"],
    registry=registry,
)

# Gauges
active_agents_gauge = Gauge(
    "hanerma_active_agents",
    "Number of active agents",
    registry=registry,
)

cluster_nodes_gauge = Gauge(
    "hanerma_cluster_nodes",
    "Number of Raft cluster nodes",
    registry=registry,
)


# ═══════════════════════════════════════════════════════════════════════════
#  MetricsTracker — In-process instrumentation
# ═══════════════════════════════════════════════════════════════════════════


class MetricsTracker:
    """
    Tracks token consumption, latency, and operations.
    Wires into Prometheus counters/histograms for export.
    """

    def __init__(self):
        self.active_traces: Dict[str, Dict[str, Any]] = {}

    def start_trace(self, trace_id: str) -> None:
        self.active_traces[trace_id] = {
            "start_time": time.time(),
            "tokens_in": 0,
            "tokens_out": 0,
            "nested_loops": 0,
            "tool_calls": 0,
        }

    def log_token_usage(self, trace_id: str, prompt_tokens: int, completion_tokens: int) -> None:
        if trace_id in self.active_traces:
            self.active_traces[trace_id]["tokens_in"] += prompt_tokens
            self.active_traces[trace_id]["tokens_out"] += completion_tokens
        tokens_consumed_total.labels(direction="input").inc(prompt_tokens)
        tokens_consumed_total.labels(direction="output").inc(completion_tokens)

    def record_nested_correction(self, trace_id: str) -> None:
        """Track when Z3/Grammar Shield catches a hallucination."""
        if trace_id in self.active_traces:
            self.active_traces[trace_id]["nested_loops"] += 1
        hallucinations_caught.inc()

    def record_tool_latency(self, tool_name: str, latency_seconds: float) -> None:
        tool_latency_seconds.labels(tool_name=tool_name).observe(latency_seconds)

    def record_dag_execution(self, execution_time_seconds: float) -> None:
        dag_execution_time.observe(execution_time_seconds)

    def record_dag_step(self, status: str = "success") -> None:
        dag_steps_total.labels(status=status).inc()

    def record_healing(self, action: str, success: bool) -> None:
        healing_attempts_total.labels(
            action=action, success=str(success).lower()
        ).inc()

    def record_routing(self, model: str, reason: str) -> None:
        routing_decisions_total.labels(model=model, reason=reason).inc()

    def record_raft_commit(self) -> None:
        raft_commits_total.inc()

    def set_active_agents(self, count: int) -> None:
        active_agents_gauge.set(count)

    def set_cluster_nodes(self, count: int) -> None:
        cluster_nodes_gauge.set(count)

    def end_trace(self, trace_id: str) -> Dict[str, Any]:
        if trace_id not in self.active_traces:
            return {}

        trace = self.active_traces.pop(trace_id)
        latency_ms = (time.time() - trace["start_time"]) * 1000

        # Record to Prometheus
        dag_execution_time.observe(latency_ms / 1000)

        return {
            "latency_ms": round(latency_ms, 2),
            "total_tokens": trace["tokens_in"] + trace["tokens_out"],
            "tokens_in": trace["tokens_in"],
            "tokens_out": trace["tokens_out"],
            "corrections_made": trace["nested_loops"],
            "tool_calls": trace["tool_calls"],
        }


# ═══════════════════════════════════════════════════════════════════════════
#  FastAPI /metrics endpoint
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(title="HANERMA Metrics")


@app.get("/metrics")
def metrics_endpoint():
    """Prometheus-compatible /metrics endpoint."""
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/metrics/json")
def metrics_json():
    """Human-readable JSON summary of key metrics."""
    return {
        "hallucinations_caught": hallucinations_caught._value.get(),
        "raft_commits": raft_commits_total._value.get(),
    }


def start_metrics_server(host: Optional[str] = None, port: Optional[int] = None):
    """Start the standalone metrics server."""
    import uvicorn
    h = host or settings.METRICS_HOST
    p = port or settings.METRICS_PORT
    print(f"[HANERMA] 📊 Prometheus metrics: http://{h}:{p}/metrics")
    uvicorn.run(app, host=h, port=p)
