
from hanerma.orchestrator.telemetry import TelemetryManager
import time

def test_telemetry_metrics():
    telemetry = TelemetryManager()
    
    start_time = telemetry.start_timer()
    time.sleep(0.01) # Sleep 10ms
    metrics = telemetry.stop_timer(start_time)
    
    assert "latency_ms" in metrics
    assert metrics["latency_ms"] >= 10.0 # roughly

def test_token_counting():
    telemetry = TelemetryManager()
    count = telemetry.count_tokens("This has about 6 tokens")
    assert count > 0
