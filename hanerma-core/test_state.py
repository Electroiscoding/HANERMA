"""
Smoke test for the StateCapacitor (Hot/Cold tiered LSM store).

Run after `maturin develop`:
    python test_state.py
"""

import time
import os
import shutil
from hanerma_core import StateCapacitor


DB_PATH = "./test_state_db"


def cleanup():
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH, ignore_errors=True)


def test_basic_put_get():
    """Store and retrieve Python objects."""
    cap = StateCapacitor(DB_PATH, capacity=10)

    cap.put_state("config", {"model": "gpt-4", "temperature": 0.7})
    cap.put_state("score", 0.95)
    cap.put_state("tags", ["ai", "reasoning", "math"])

    assert cap.get_state("config") == {"model": "gpt-4", "temperature": 0.7}
    assert cap.get_state("score") == 0.95
    assert cap.get_state("tags") == ["ai", "reasoning", "math"]
    assert cap.get_state("missing") is None

    print("  ✓ basic put/get works")


def test_raw_bytes():
    """Store and retrieve raw bytes."""
    cap = StateCapacitor(DB_PATH, capacity=10)

    cap.put_bytes("binary", b"\x00\x01\x02\xff")
    result = cap.get_bytes("binary")
    assert result == b"\x00\x01\x02\xff"

    print("  ✓ raw bytes works")


def test_hot_cold_tiering():
    """Verify eviction: only `capacity` entries stay in hot."""
    cap = StateCapacitor(DB_PATH, capacity=10)
    cap.clear()

    # Insert 20 entries (capacity = 10)
    for i in range(20):
        cap.put_state(f"key_{i}", f"value_{i}")

    # Hot tier should be bounded (~10, after evictions)
    assert cap.hot_len <= 13, f"hot_len={cap.hot_len}, expected ≤13"
    # Cold tier has everything
    assert cap.total_len == 20

    # All 20 must still be retrievable (from cold)
    for i in range(20):
        val = cap.get_state(f"key_{i}")
        assert val == f"value_{i}", f"key_{i} returned {val}"

    print(f"  ✓ hot/cold tiering works (hot={cap.hot_len}, total={cap.total_len})")


def test_delete_and_contains():
    """Delete and membership check."""
    cap = StateCapacitor(DB_PATH, capacity=10)

    cap.put_state("ephemeral", 42)
    assert cap.contains("ephemeral")
    cap.delete("ephemeral")
    assert not cap.contains("ephemeral")
    assert cap.get_state("ephemeral") is None

    print("  ✓ delete and contains work")


def test_persistence():
    """Data survives re-opening the database."""
    cap = StateCapacitor(DB_PATH, capacity=10)
    cap.put_state("persistent", {"alive": True})
    del cap  # close

    cap2 = StateCapacitor(DB_PATH, capacity=10)
    assert cap2.get_state("persistent") == {"alive": True}

    print("  ✓ persistence across restarts works")


def test_write_throughput():
    """Measure write throughput."""
    cap = StateCapacitor(DB_PATH, capacity=100)
    cap.clear()

    n = 1000
    start = time.perf_counter()
    for i in range(n):
        cap.put_state(f"bench_{i}", {"index": i, "data": "x" * 100})
    elapsed = time.perf_counter() - start

    ops_per_sec = n / elapsed
    us_per_op = (elapsed / n) * 1_000_000

    print(f"  ✓ write throughput: {ops_per_sec:.0f} ops/s ({us_per_op:.1f} µs/op)")


def test_read_throughput():
    """Measure read throughput (hot path)."""
    cap = StateCapacitor(DB_PATH, capacity=100)

    # Pre-populate
    for i in range(100):
        cap.put_state(f"read_{i}", {"value": i})

    n = 5000
    start = time.perf_counter()
    for i in range(n):
        cap.get_state(f"read_{i % 100}")
    elapsed = time.perf_counter() - start

    ops_per_sec = n / elapsed
    us_per_op = (elapsed / n) * 1_000_000

    print(f"  ✓ read throughput:  {ops_per_sec:.0f} ops/s ({us_per_op:.1f} µs/op)")


def main():
    cleanup()
    print("StateCapacitor Tests")
    print("=" * 50)

    test_basic_put_get()
    test_raw_bytes()
    test_hot_cold_tiering()
    test_delete_and_contains()
    test_persistence()
    test_write_throughput()
    test_read_throughput()

    print("=" * 50)
    print("All tests passed! ✓")

    cleanup()


if __name__ == "__main__":
    main()
