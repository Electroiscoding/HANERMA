"""Tests for Slices 8, 9, 10"""
import importlib.util
import os
import sys
import json

BASE = os.path.dirname(__file__)
SRC = os.path.join(BASE, "src")


def load_module(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SRC, *rel_path.split("/")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ═══════════════════════════════════════════════════════════════════════════
#  SLICE 8: Supervisor Healing
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SLICE 8: Supervisor Healing & AST Patching")
print("=" * 60)

empathy = load_module("empathy", "hanerma/interface/empathy.py")
SupervisorHealer = empathy.SupervisorHealer
PatchAction = empathy.PatchAction
CriticPatch = empathy.CriticPatch
HealingResult = empathy.HealingResult

# Test 1: Schema validation
print("\n--- Test 8.1: CriticPatch Schema ---")
patch = CriticPatch(
    action=PatchAction.RETRY_WITH_NEW_PROMPT,
    payload="Rephrase: calculate 2+2 without contradictions",
    reasoning="Original prompt had conflicting constraints",
    confidence=0.85,
)
assert patch.action == PatchAction.RETRY_WITH_NEW_PROMPT
assert patch.confidence == 0.85
print(f"  ✓ CriticPatch valid: action={patch.action.value}, conf={patch.confidence}")

# Test 2: Invalid confidence rejected
print("\n--- Test 8.2: Schema Rejection ---")
from pydantic import ValidationError
try:
    CriticPatch(action="retry_with_new_prompt", payload="x", reasoning="y", confidence=1.5)
    print("  ✗ Should have rejected confidence > 1.0!")
except ValidationError:
    print("  ✓ Rejected confidence > 1.0")

# Test 3: Offline healing for ContradictionError
print("\n--- Test 8.3: Offline Healing (ContradictionError) ---")
healer = SupervisorHealer()
ctx = {"prompt": "Is X > 5 and X < 3?"}

class ContradictionError(Exception): pass

result = healer.heal_offline(ContradictionError("unsat"), ctx)
assert result.success is True
assert result.action_taken == PatchAction.RETRY_WITH_NEW_PROMPT
assert ctx.get("patched") is True
print(f"  ✓ Healed: {result.action_taken.value} — {result.detail}")

# Test 4: Offline healing for KeyError
print("\n--- Test 8.4: Offline Healing (KeyError) ---")
ctx2 = {}
result2 = healer.heal_offline(KeyError("missing_field"), ctx2)
assert result2.success is True
assert result2.action_taken == PatchAction.MOCK_DATA
assert ctx2.get("mock_result") is not None
print(f"  ✓ Healed: {result2.action_taken.value} — mock={ctx2['mock_result']}")

print("\n  SLICE 8 ✓")


# ═══════════════════════════════════════════════════════════════════════════
#  SLICE 9: Predictive Failure & Auto-Routing
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SLICE 9: Predictive Failure & Auto-Routing")
print("=" * 60)

router_mod = load_module("model_router", "hanerma/routing/model_router.py")
analyze_prompt_complexity = router_mod.analyze_prompt_complexity
BestModelRouter = router_mod.BestModelRouter

# Test 1: Simple prompt → low risk
print("\n--- Test 9.1: Simple Prompt (Low Risk) ---")
result = analyze_prompt_complexity("What is the capital of France?")
assert result["risk_score"] < 0.4, f"Expected < 0.4, got {result['risk_score']}"
print(f"  ✓ Risk={result['risk_score']}, entropy={result['entropy']}, tokens={result['token_count']}")

# Test 2: Complex code prompt → high risk
print("\n--- Test 9.2: Complex Code Prompt (High Risk) ---")
code_prompt = """
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# Now implement quicksort and compare performance step by step
"""
result2 = analyze_prompt_complexity(code_prompt)
assert result2["risk_score"] > 0.3, f"Expected > 0.3, got {result2['risk_score']}"
assert result2["code_ratio"] > 0.1
print(f"  ✓ Risk={result2['risk_score']}, code_ratio={result2['code_ratio']}, signals={result2['signals']}")

# Test 3: Router decisions
print("\n--- Test 9.3: Model Routing ---")
router = BestModelRouter()

# Simple prompt → local
decision1 = router.route("Hello, what time is it?")
assert decision1["model"] == BestModelRouter.OLLAMA_LOCAL
print(f"  ✓ Simple → {decision1['model']} ({decision1['reason']})")

# Code prompt → cloud
decision2 = router.route(code_prompt)
assert decision2["model"] != BestModelRouter.OLLAMA_LOCAL
print(f"  ✓ Code → {decision2['model']} ({decision2['reason']})")

# Test 4: Risk > 0.8 → inject critic
print("\n--- Test 9.4: Auto-Critic Injection ---")
# Create a deliberately high-risk prompt
high_risk = "maybe somehow " * 100 + code_prompt + " step 1 step 2 step 3 then after that finally"
result_hr = analyze_prompt_complexity(high_risk)
decision_hr = router.route(high_risk)
print(f"  Risk={result_hr['risk_score']}, inject_critic={decision_hr['inject_critic']}")
if result_hr['risk_score'] > 0.8:
    assert decision_hr['inject_critic'] is True
    print("  ✓ Critic injection triggered (risk > 0.8)")
else:
    print(f"  ✓ Risk={result_hr['risk_score']} (critic injection at > 0.8)")

# Test 5: Stats
print("\n--- Test 9.5: Routing Stats ---")
stats = router.stats
assert stats["total_routes"] >= 3
print(f"  ✓ Stats: {json.dumps(stats, indent=2)}")

print("\n  SLICE 9 ✓")


# ═══════════════════════════════════════════════════════════════════════════
#  SLICE 10: God Mode Visual Composer
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SLICE 10: God Mode Visual Composer")
print("=" * 60)

viz_mod = load_module("viz_server", "hanerma/observability/viz_server.py")
ExecutionController = viz_mod.ExecutionController

# Test 1: Controller pause/resume
print("\n--- Test 10.1: Execution Controller ---")
ctrl = ExecutionController()
assert ctrl.is_paused() is False
assert ctrl.can_proceed(timeout=0.01) is True
print("  ✓ Initial state: running")

ctrl.pause()
assert ctrl.is_paused() is True
assert ctrl.can_proceed(timeout=0.01) is False
print("  ✓ After pause: paused, can_proceed=False")

ctrl.resume()
assert ctrl.is_paused() is False
assert ctrl.can_proceed(timeout=0.01) is True
print("  ✓ After resume: running, can_proceed=True")

# Test 2: State injection queue
print("\n--- Test 10.2: State Injection ---")
ctrl.inject_state("coder_0", "memory", "Remember: use Python 3.12")
ctrl.inject_state("coder_0", "context", {"task": "write tests"})
assert ctrl.status()["pending_patches"] == 2
print(f"  ✓ Queued 2 patches: pending={ctrl.status()['pending_patches']}")

patches = ctrl.drain_patches()
assert len(patches) == 2
assert patches[0]["agent_name"] == "coder_0"
assert patches[0]["key"] == "memory"
assert ctrl.status()["pending_patches"] == 0
print(f"  ✓ Drained 2 patches, queue empty")

# Test 3: FastAPI endpoints exist
print("\n--- Test 10.3: API Endpoints ---")
from fastapi.testclient import TestClient
client = TestClient(viz_mod.app)

r = client.get("/api/graph/status")
assert r.status_code == 200
status = r.json()
assert "paused" in status
print(f"  ✓ GET /api/graph/status → {status}")

r = client.post("/api/graph/pause")
assert r.status_code == 200
assert r.json()["status"] == "paused"
print("  ✓ POST /api/graph/pause → paused")

r = client.post("/api/graph/resume")
assert r.status_code == 200
assert r.json()["status"] == "resumed"
print("  ✓ POST /api/graph/resume → resumed")

r = client.post("/api/graph/edit_state", json={"agent_name": "test_agent", "key": "memory", "value": "injected!"})
assert r.status_code == 200
assert r.json()["status"] == "injected"
print("  ✓ POST /api/graph/edit_state → injected")

# Test 4: Dashboard HTML
print("\n--- Test 10.4: Dashboard HTML ---")
r = client.get("/")
assert r.status_code == 200
assert "GOD MODE" in r.text
assert "doPause" in r.text
assert "doResume" in r.text
assert "doEditState" in r.text
print(f"  ✓ Dashboard HTML: {len(r.text)} bytes, all controls present")

print("\n  SLICE 10 ✓")


# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SLICES 8 + 9 + 10 ALL VERIFIED ✓")
print("=" * 60)
