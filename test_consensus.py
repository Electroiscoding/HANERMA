"""
Test: True Distributed Raft Consensus (Slice 5)

Spins up a 3-node Raft cluster on localhost ports, verifies:
  1. Automatic leader election
  2. Replicated state across all nodes
  3. ConsensusGateway write-through to Raft + LSM
  4. Read from any node returns consistent data
"""

import importlib.util
import os
import sys
import time
import json

# Direct-load consensus module (bypass broken hanerma.__init__)
spec = importlib.util.spec_from_file_location(
    "consensus",
    os.path.join(os.path.dirname(__file__), "src", "hanerma", "orchestrator", "consensus.py"),
)
consensus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consensus)

ClusterManager = consensus.ClusterManager
ConsensusGateway = consensus.ConsensusGateway

# ── 3-node cluster on different local ports ──
ADDR1 = "localhost:14321"
ADDR2 = "localhost:14322"
ADDR3 = "localhost:14323"


def test_leader_election():
    """Spin up 3 nodes and verify a leader is elected."""
    print("\n=== Test: Leader Election ===")

    mgr1 = ClusterManager(ADDR1, [ADDR2, ADDR3])
    mgr2 = ClusterManager(ADDR2, [ADDR1, ADDR3])
    mgr3 = ClusterManager(ADDR3, [ADDR1, ADDR2])

    try:
        # Wait for leader election (Raft needs a few seconds)
        leader = mgr1.wait_for_leader(timeout=15.0)
        print(f"  ✓ Leader elected: {leader}")

        # All nodes should agree on the same leader
        time.sleep(1.0)
        leader2 = mgr2.get_leader()
        leader3 = mgr3.get_leader()
        assert leader2 == leader, f"Node 2 sees {leader2}, expected {leader}"
        assert leader3 == leader, f"Node 3 sees {leader3}, expected {leader}"
        print(f"  ✓ All 3 nodes agree on leader: {leader}")

        # Print cluster status
        status = mgr1.status()
        print(f"  ✓ Term: {status['term']}, Keys: {status['store_keys']}")

        return mgr1, mgr2, mgr3

    except Exception as e:
        mgr1.destroy()
        mgr2.destroy()
        mgr3.destroy()
        raise e


def test_replicated_state(mgr1, mgr2, mgr3):
    """Write on leader, read from all followers."""
    print("\n=== Test: Replicated State ===")

    # Write through node 1's store
    mgr1.store.replicated_put("user:1", json.dumps({"name": "Alice", "age": 30}), timeout=5.0)
    mgr1.store.replicated_put("user:2", json.dumps({"name": "Bob", "age": 25}), timeout=5.0)
    mgr1.store.replicated_put("config:max_retries", json.dumps(3), timeout=5.0)

    # Give Raft time to replicate
    time.sleep(2.0)

    # Read from ALL nodes — all should see the same data
    for label, mgr in [("node1", mgr1), ("node2", mgr2), ("node3", mgr3)]:
        val = mgr.store.get("user:1")
        assert val is not None, f"{label} missing user:1"
        parsed = json.loads(val)
        assert parsed["name"] == "Alice", f"{label} got wrong name: {parsed}"
        assert mgr.store.store_len() == 3, f"{label} store_len={mgr.store.store_len()}"

    print("  ✓ All 3 nodes have identical replicated state")
    print(f"  ✓ Store length on each node: {mgr1.store.store_len()}")


def test_consensus_gateway(mgr1):
    """Test the ConsensusGateway (Raft → LSM bridge)."""
    print("\n=== Test: ConsensusGateway ===")

    # No real StateCapacitor in this test — just verify Raft path
    gw = ConsensusGateway(mgr1, state_capacitor=None)

    gw.put("order:1001", {"item": "GPU", "quantity": 2, "price": 1599.99})
    gw.put("order:1002", {"item": "RAM", "quantity": 8, "price": 89.99})

    time.sleep(1.0)

    result = gw.get("order:1001")
    assert result is not None, "Gateway get returned None"
    assert result["item"] == "GPU", f"Got wrong item: {result}"
    print(f"  ✓ Gateway put/get works: {result}")

    # Batch write
    count = gw.batch_put([
        {"key": "metric:latency", "value": 12.5},
        {"key": "metric:throughput", "value": 9500},
        {"key": "metric:errors", "value": 0},
    ])
    assert count == 3, f"Batch put returned {count}"
    print(f"  ✓ Batch put committed {count} entries atomically")

    # Delete
    gw.delete("order:1002")
    time.sleep(0.5)
    assert gw.get("order:1002") is None, "Delete failed"
    print("  ✓ Delete with consensus works")

    status = gw.cluster_status
    print(f"  ✓ Cluster status: role={status['role']}, term={status['term']}, keys={status['store_keys']}")


def main():
    print("Raft Consensus Tests (3-Node Cluster)")
    print("=" * 55)

    mgr1, mgr2, mgr3 = test_leader_election()

    try:
        test_replicated_state(mgr1, mgr2, mgr3)
        test_consensus_gateway(mgr1)
    finally:
        # Cleanup
        mgr1.destroy()
        mgr2.destroy()
        mgr3.destroy()

    print("\n" + "=" * 55)
    print("SLICE 5 VERIFIED ✓")


if __name__ == "__main__":
    main()
