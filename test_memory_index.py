"""Test: Crayon Memory Engine — Pure-Rust Vector Index (Slice 7)"""
import time
import math
import random

from hanerma_core import MemoryIndex

DIM = 128  # embedding dimensionality
HOT_CAP = 5  # small hot tier for testing eviction


def make_embedding(seed: float) -> list:
    """Generate a deterministic pseudo-embedding."""
    random.seed(seed)
    vec = [random.gauss(0, 1) for _ in range(DIM)]
    # Normalize
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


def test_basic_add_search():
    print("\n=== Test 1: Basic Add & Search ===")
    idx = MemoryIndex(dim=DIM, hot_capacity=HOT_CAP)

    emb1 = make_embedding(1.0)
    emb2 = make_embedding(2.0)

    id1 = idx.add_turn("user", "What is Python?", emb1)
    id2 = idx.add_turn("assistant", "Python is a programming language.", emb2)

    assert id1 == 0
    assert id2 == 1
    assert idx.hot_len == 2
    assert idx.cold_len == 0
    assert idx.total_len == 2
    print(f"  ✓ Added 2 turns, hot={idx.hot_len}, cold={idx.cold_len}")

    # Search for something similar to emb1
    results = idx.search(emb1, k=2)
    assert len(results) == 2
    assert results[0][0] == 0  # Most similar to itself
    assert results[0][1] > 0.99  # Near-perfect self-similarity
    print(f"  ✓ Search: top result id={results[0][0]}, sim={results[0][1]:.4f}")


def test_hot_cold_eviction():
    print("\n=== Test 2: Hot→Cold Eviction ===")
    idx = MemoryIndex(dim=DIM, hot_capacity=HOT_CAP)

    # Add HOT_CAP + 5 turns → first 5 should evict to cold
    for i in range(HOT_CAP + 5):
        emb = make_embedding(float(i))
        idx.add_turn("user", f"Turn number {i}", emb)

    assert idx.hot_len == HOT_CAP, f"Expected hot={HOT_CAP}, got {idx.hot_len}"
    assert idx.cold_len == 5, f"Expected cold=5, got {idx.cold_len}"
    assert idx.total_len == HOT_CAP + 5
    print(f"  ✓ Eviction works: hot={idx.hot_len}, cold={idx.cold_len}, total={idx.total_len}")

    # Search should find turns from BOTH tiers
    query = make_embedding(0.0)  # Similar to turn 0 (evicted to cold)
    results = idx.search(query, k=3)
    assert len(results) == 3
    # Turn 0 should be the top result (exact match, now in cold tier)
    assert results[0][0] == 0, f"Expected turn 0 as top result, got {results[0][0]}"
    assert results[0][1] > 0.99
    print(f"  ✓ Cross-tier search: found evicted turn 0 in cold tier (sim={results[0][1]:.4f})")


def test_batch_add():
    print("\n=== Test 3: Batch Add ===")
    idx = MemoryIndex(dim=DIM, hot_capacity=50)

    turns = [
        ("user", f"Batch turn {i}", make_embedding(float(i + 100)))
        for i in range(20)
    ]
    ids = idx.add_turns(turns)
    assert len(ids) == 20
    assert ids[0] == 0
    assert ids[-1] == 19
    assert idx.total_len == 20
    print(f"  ✓ Batch added {len(ids)} turns")


def test_dim_mismatch():
    print("\n=== Test 4: Dim Mismatch Guard ===")
    idx = MemoryIndex(dim=DIM, hot_capacity=10)

    try:
        idx.add_turn("user", "wrong dim", [1.0, 2.0, 3.0])  # DIM=128, sending 3
        print("  ✗ ERROR: Should have raised on dim mismatch!")
    except RuntimeError as e:
        assert "mismatch" in str(e).lower()
        print(f"  ✓ Caught dim mismatch: {e}")


def test_search_performance():
    print("\n=== Test 5: Search Performance ===")
    idx = MemoryIndex(dim=DIM, hot_capacity=100)

    # Add 1000 turns (100 hot, 900 cold)
    for i in range(1000):
        emb = make_embedding(float(i))
        idx.add_turn("user", f"Perf turn {i}", emb)

    assert idx.hot_len == 100
    assert idx.cold_len == 900
    print(f"  Index: hot={idx.hot_len}, cold={idx.cold_len}")

    query = make_embedding(500.0)

    # Benchmark search
    start = time.perf_counter()
    N_SEARCHES = 100
    for _ in range(N_SEARCHES):
        results = idx.search(query, k=10)
    elapsed = time.perf_counter() - start

    avg_us = (elapsed / N_SEARCHES) * 1_000_000
    print(f"  ✓ {N_SEARCHES} searches over 1000 vectors: avg {avg_us:.0f}µs/search")
    assert avg_us < 50_000, f"Search too slow: {avg_us}µs"  # Should be < 50ms

    # Verify result quality
    assert results[0][0] == 500  # Exact match
    assert results[0][1] > 0.99
    print(f"  ✓ Top result: id={results[0][0]}, sim={results[0][1]:.4f}")


def test_repr():
    print("\n=== Test 6: Repr ===")
    idx = MemoryIndex(dim=DIM, hot_capacity=10)
    idx.add_turn("user", "hello", make_embedding(42.0))
    r = repr(idx)
    assert "MemoryIndex" in r
    assert "dim=128" in r
    print(f"  ✓ {r}")


if __name__ == "__main__":
    print("Crayon Memory Engine Tests (Pure-Rust Vector Index)")
    print("=" * 55)

    test_basic_add_search()
    test_hot_cold_eviction()
    test_batch_add()
    test_dim_mismatch()
    test_search_performance()
    test_repr()

    print("\n" + "=" * 55)
    print("SLICE 7 VERIFIED ✓")
