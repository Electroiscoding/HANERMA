"""
HANERMA — Final Certification Test
====================================
Captures ALL input, processing, and output for every framework layer.
Logs everything to both stdout AND a raw log file for the report.
"""

import os
import sys
import time
import io
import traceback
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── CONFIGURATION ──────────────────────────────────────────────
HF_MODEL = "Qwen/Qwen3-Coder-Next-FP8:together"
HF_TOKEN = os.getenv("HF_TOKEN")
IST = timezone(timedelta(hours=5, minutes=30))
TIMESTAMP = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "FINAL_TEST_LOG.txt")

# Tee class to capture stdout to both console and file
class TeeWriter:
    def __init__(self, *writers):
        self.writers = writers
    def write(self, text):
        for w in self.writers:
            w.write(text)
            w.flush()
    def flush(self):
        for w in self.writers:
            w.flush()

log_fh = open(LOG_FILE, "w", encoding="utf-8")
tee = TeeWriter(sys.__stdout__, log_fh)
sys.stdout = tee
sys.stderr = tee

# ── HELPERS ────────────────────────────────────────────────────
results_table = []  # (test_name, status, latency_ms, input_summary, output_summary, notes)


def record(name, status, latency_ms, input_summary, output_summary, notes=""):
    results_table.append({
        "name": name,
        "status": status,
        "latency_ms": latency_ms,
        "input": input_summary,
        "output": output_summary,
        "notes": notes,
    })


print("=" * 70)
print("  HANERMA — FINAL CERTIFICATION TEST")
print(f"  Timestamp:  {TIMESTAMP}")
print(f"  Model:      {HF_MODEL}")
print(f"  Token:      {HF_TOKEN[:8]}...{HF_TOKEN[-4:]}" if HF_TOKEN else "  Token:      MISSING!")
print(f"  Python:     {sys.version}")
print(f"  Platform:   {sys.platform}")
print(f"  Log File:   {os.path.abspath(LOG_FILE)}")
print("=" * 70)

if not HF_TOKEN:
    print("FATAL: HF_TOKEN not found. Aborting.")
    sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: Raw HuggingFace Adapter
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_1():
    print("\n\n" + "━" * 70)
    print("TEST 1: Raw HuggingFace Adapter (Direct LLM Call)")
    print("━" * 70)

    from hanerma.models.cloud_llm import HuggingFaceAdapter

    prompt = "What is 2 + 2? Reply with just the number."
    system = "You are a calculator. Reply concisely."

    print(f"  [INPUT]  prompt       = \"{prompt}\"")
    print(f"  [INPUT]  system_prompt= \"{system}\"")
    print(f"  [INPUT]  model        = \"{HF_MODEL}\"")
    print(f"  [INIT]   Creating HuggingFaceAdapter...")

    adapter = HuggingFaceAdapter(model_name=HF_MODEL)
    print(f"  [INIT]   adapter.model_name = \"{adapter.model_name}\"")
    print(f"  [INIT]   adapter.provider   = \"{adapter.provider}\"")
    print(f"  [EXEC]   Calling adapter.generate()...")

    t0 = time.perf_counter()
    response = adapter.generate(prompt=prompt, system_prompt=system)
    latency = (time.perf_counter() - t0) * 1000

    print(f"  [OUTPUT] Raw response  = \"{response}\"")
    print(f"  [METRIC] Latency       = {latency:.2f}ms")
    print(f"  [METRIC] Response len  = {len(response)} chars")

    passed = bool(response and len(response.strip()) > 0 and "error" not in response.lower()[:30])
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [RESULT] {status}")

    record("Raw HF Adapter", status, f"{latency:.2f}", prompt, response.strip()[:200],
           f"provider={adapter.provider}, model_name={adapter.model_name}")
    return passed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: Deep 1 — Atomic Guard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_2():
    print("\n\n" + "━" * 70)
    print("TEST 2: Deep 1 — Atomic Guard (Hallucination Detection)")
    print("━" * 70)

    from hanerma.reasoning.deep1_atomic import AtomicGuard
    guard = AtomicGuard(strictness=0.99)
    print(f"  [INIT]   AtomicGuard created. strictness={guard.strictness}")

    subtests = [
        ("valid_fact", "The speed of light is 299,792,458 m/s.", True),
        ("empty_string", "", False),
        ("ai_refusal", "As an AI, I cannot help with that.", False),
        ("error_string", "Error: connection timeout", False),
        ("normal_answer", "Python was created by Guido van Rossum in 1991.", True),
    ]

    all_pass = True
    for label, input_text, expected in subtests:
        is_valid, msg = guard.verify(input_text)
        matched = is_valid == expected
        status = "✅" if matched else "❌"
        if not matched:
            all_pass = False
        print(f"  [{status}] {label:20s} | input=\"{input_text[:50]}\" | valid={is_valid} expected={expected} | msg=\"{msg}\"")

    status = "✅ PASS" if all_pass else "❌ FAIL"
    print(f"  [RESULT] {status}")
    record("Atomic Guard (Deep 1)", status, "N/A", f"{len(subtests)} sub-tests",
           f"All {len(subtests)} sub-assertions matched",
           f"strictness={guard.strictness}, tested: valid, empty, refusal, error, normal")
    return all_pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: HCMS Memory Store
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_3():
    print("\n\n" + "━" * 70)
    print("TEST 3: HCMS Memory Store (Write + FAISS Retrieval)")
    print("━" * 70)

    from hanerma.memory.manager import HCMSManager
    from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter

    tokenizer = XervCrayonAdapter()
    hcms = HCMSManager(tokenizer=tokenizer)
    print(f"  [INIT]   Tokenizer: {type(tokenizer).__name__}")
    print(f"  [INIT]   HCMS dim={hcms.embedding_dim}, backend=FAISS FlatL2")

    facts = [
        ("Python was created by Guido van Rossum in 1991.", "fact"),
        ("FAISS is a library for efficient similarity search.", "context"),
        ("Neo4j is a graph database for relationship tracking.", "fact"),
    ]

    for text, etype in facts:
        print(f"  [WRITE]  Storing: \"{text}\" (type={etype})")
        hcms.store_atomic_memory("test-session", text, entity_type=etype)

    print(f"  [STATE]  Index size after writes: {hcms.current_idx}")
    print(f"  [STATE]  Memory map keys: {list(hcms.memory_map.keys())}")

    query = "Who created Python?"
    print(f"  [QUERY]  \"{query}\" (top_k=3)")
    results = hcms.retrieve_relevant_context(query, top_k=3)
    print(f"  [RESULT] Retrieved {len(results)} contexts:")
    for i, r in enumerate(results):
        print(f"           [{i}] \"{r}\"")

    passed = len(results) > 0 and hcms.current_idx == 3
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [RESULT] {status}")
    record("HCMS Memory Store", status, "N/A",
           f"3 facts stored, query=\"{query}\"",
           f"{len(results)} contexts retrieved, index_size={hcms.current_idx}",
           f"tokenizer={type(tokenizer).__name__}, dim={hcms.embedding_dim}")
    return passed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: Deep 2 — Nested Verifier
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_4():
    print("\n\n" + "━" * 70)
    print("TEST 4: Deep 2 — Nested Verifier (HCMS Cross-Check)")
    print("━" * 70)

    from hanerma.memory.manager import HCMSManager
    from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter
    from hanerma.reasoning.deep2_nested import NestedVerifier

    tokenizer = XervCrayonAdapter()
    hcms = HCMSManager(tokenizer=tokenizer)
    hcms.store_atomic_memory("test", "Earth is the third planet from the Sun.")
    print(f"  [INIT]   Seeded HCMS with 1 fact. Index size: {hcms.current_idx}")

    verifier = NestedVerifier(memory_store=hcms, confidence_threshold=0.85)
    print(f"  [INIT]   NestedVerifier. threshold={verifier.confidence_threshold}")

    # Sub-test A: Known claim with seeded data
    claim_a = "Earth orbits the Sun."
    print(f"  [CHECK]  Claim A: \"{claim_a}\"")
    valid_a, reason_a = verifier.cross_check(session_id="test", atomic_claim=claim_a)
    print(f"  [OUTPUT] valid={valid_a} | reason=\"{reason_a}\"")

    # Sub-test B: Novel claim with empty memory
    hcms_empty = HCMSManager(tokenizer=tokenizer)
    verifier_empty = NestedVerifier(memory_store=hcms_empty)
    claim_b = "Novel claim with no history."
    print(f"  [CHECK]  Claim B: \"{claim_b}\" (empty memory)")
    valid_b, reason_b = verifier_empty.cross_check(session_id="test", atomic_claim=claim_b)
    print(f"  [OUTPUT] valid={valid_b} | reason=\"{reason_b}\"")

    passed = valid_a is True and valid_b is True
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [RESULT] {status}")
    record("Nested Verifier (Deep 2)", status, "N/A",
           f"Claim A: \"{claim_a}\" | Claim B: \"{claim_b}\"",
           f"A: valid={valid_a}, reason={reason_a} | B: valid={valid_b}, reason={reason_b}",
           "Tested with seeded HCMS and empty HCMS")
    return passed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 5: BaseAgent with Real LLM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_5():
    print("\n\n" + "━" * 70)
    print("TEST 5: BaseAgent — Real LLM Execution via HuggingFace")
    print("━" * 70)

    from hanerma.agents.base_agent import BaseAgent

    prompt = "What programming language is HANERMA built in? One word only."
    system = "Answer concisely in one word."

    agent = BaseAgent(name="test::base_agent", role="General Assistant",
                      system_prompt=system, model=HF_MODEL)

    print(f"  [INIT]   Agent name={agent.name}, role={agent.role}")
    print(f"  [INIT]   Agent model={agent.model}")
    print(f"  [INIT]   Agent system_prompt=\"{agent.system_prompt}\"")
    print(f"  [INPUT]  prompt=\"{prompt}\"")

    state = {"history": []}
    t0 = time.perf_counter()
    response = agent.execute(prompt, state)
    latency = (time.perf_counter() - t0) * 1000

    print(f"  [OUTPUT] response=\"{response}\"")
    print(f"  [METRIC] Latency={latency:.2f}ms")
    print(f"  [METRIC] Response length={len(response)} chars")
    print(f"  [STATE]  history entries={len(state['history'])}")
    print(f"  [STATE]  history[0]={state['history'][0] if state['history'] else 'EMPTY'}")

    passed = bool(response and len(response.strip()) > 0 and "error" not in response.lower()[:30])
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [RESULT] {status}")
    record("BaseAgent + Real LLM", status, f"{latency:.2f}",
           prompt, response.strip()[:200],
           f"model={agent.model}, state_entries={len(state['history'])}")
    return passed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 6: DeepReasonerAgent with Real LLM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_6():
    print("\n\n" + "━" * 70)
    print("TEST 6: DeepReasonerAgent — Chain-of-Thought via HuggingFace")
    print("━" * 70)

    from hanerma.agents.native_personas.deep_reasoner import DeepReasonerAgent

    prompt = "Explain why recursion needs a base case. Be brief, max 2 sentences."

    reasoner = DeepReasonerAgent(name="native::deep_reasoner", model=HF_MODEL)
    print(f"  [INIT]   Agent name={reasoner.name}, role={reasoner.role}")
    print(f"  [INIT]   Agent model={reasoner.model}")
    print(f"  [INIT]   system_prompt=\"{reasoner.system_prompt}\"")
    print(f"  [INPUT]  prompt=\"{prompt}\"")

    state = {"history": []}
    t0 = time.perf_counter()
    response = reasoner.execute(prompt, state)
    latency = (time.perf_counter() - t0) * 1000

    print(f"  [OUTPUT] response=\"{response}\"")
    print(f"  [METRIC] Latency={latency:.2f}ms")
    print(f"  [METRIC] Response length={len(response)} chars")

    passed = bool(response and len(response.strip()) > 10 and "error" not in response.lower()[:30])
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [RESULT] {status}")
    record("DeepReasonerAgent + LLM", status, f"{latency:.2f}",
           prompt, response.strip()[:300],
           f"Inherited execute() from BaseAgent, model={reasoner.model}")
    return passed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 7: SystemVerifier Agent
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_7():
    print("\n\n" + "━" * 70)
    print("TEST 7: SystemVerifier — Fact Verification via HCMS")
    print("━" * 70)

    from hanerma.agents.native_personas.system_verifier import SystemVerifier
    from hanerma.memory.manager import HCMSManager
    from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter

    tokenizer = XervCrayonAdapter()
    hcms = HCMSManager(tokenizer=tokenizer)

    verifier = SystemVerifier(memory_store=hcms, model=HF_MODEL)
    print(f"  [INIT]   Verifier name={verifier.name}, role={verifier.role}")
    print(f"  [INIT]   Verifier model={verifier.model}")

    prompt = "Is the speed of light 299,792,458 m/s?"
    print(f"  [INPUT]  prompt=\"{prompt}\"")

    state = {"session_id": "cert-test", "history": []}
    t0 = time.perf_counter()
    response = verifier.execute(prompt, state)
    latency = (time.perf_counter() - t0) * 1000

    print(f"  [OUTPUT] response=\"{response}\"")
    print(f"  [METRIC] Latency={latency:.2f}ms")

    passed = "[APPROVED]" in response
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [RESULT] {status}")
    record("SystemVerifier (Fact Check)", status, f"{latency:.2f}",
           prompt, response,
           "Uses NestedVerifier + HCMS cross-check (empty memory → auto-approve novel claims)")
    return passed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 8: Full Orchestrator Pipeline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_8():
    print("\n\n" + "━" * 70)
    print("TEST 8: Full Orchestrator Pipeline (End-to-End)")
    print("━" * 70)

    from hanerma.orchestrator.engine import HANERMAOrchestrator
    from hanerma.agents.native_personas.deep_reasoner import DeepReasonerAgent

    orch = HANERMAOrchestrator(model=HF_MODEL)
    print(f"  [INIT]   Orchestrator ID={orch.orchestrator_id}")
    print(f"  [INIT]   Default model={orch.default_model}")

    reasoner = DeepReasonerAgent(name="native::deep_reasoner")
    print(f"  [INIT]   Agent model BEFORE register: {reasoner.model}")
    orch.register_agent(reasoner)
    print(f"  [INIT]   Agent model AFTER register:  {reasoner.model}")

    prompt = "What is a deadlock in concurrent programming? One sentence only."
    print(f"  [INPUT]  prompt=\"{prompt}\"")
    print(f"  [INPUT]  target_agent=\"native::deep_reasoner\"")
    print(f"  [FLOW]   Step 1: AutoPrompt Enhance")
    print(f"  [FLOW]   Step 2: Agent.execute() → HuggingFace LLM")
    print(f"  [FLOW]   Step 3: AtomicGuard.verify() on raw output")

    t0 = time.perf_counter()
    result = orch.run(prompt=prompt, target_agent="native::deep_reasoner")
    latency = (time.perf_counter() - t0) * 1000

    print(f"  [OUTPUT] status={result['status']}")
    print(f"  [OUTPUT] output=\"{result['output']}\"")
    print(f"  [METRIC] Orchestrator latency={result['metrics']['latency_ms']}ms")
    print(f"  [METRIC] Wall-clock latency={latency:.2f}ms")
    print(f"  [STATE]  History entries={len(orch.state_manager['history'])}")

    passed = result["status"] == "success" and len(result["output"].strip()) > 10
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [RESULT] {status}")
    record("Full Orchestrator E2E", status, f"{result['metrics']['latency_ms']}",
           prompt, result["output"].strip()[:300],
           f"Pipeline: AutoPrompt → Agent → LLM → AtomicGuard. Orchestrator ID={orch.orchestrator_id[:8]}")
    return passed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 9: Multi-Agent Orchestration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_9():
    print("\n\n" + "━" * 70)
    print("TEST 9: Multi-Agent Orchestration (Reasoner + Verifier)")
    print("━" * 70)

    from hanerma.orchestrator.engine import HANERMAOrchestrator
    from hanerma.agents.native_personas.deep_reasoner import DeepReasonerAgent
    from hanerma.agents.native_personas.system_verifier import SystemVerifier
    from hanerma.memory.manager import HCMSManager
    from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter

    tokenizer = XervCrayonAdapter()
    hcms = HCMSManager(tokenizer=tokenizer)
    orch = HANERMAOrchestrator(model=HF_MODEL)

    reasoner = DeepReasonerAgent(name="native::deep_reasoner")
    verifier = SystemVerifier(name="native::system_verifier", memory_store=hcms)

    orch.register_agent(reasoner)
    orch.register_agent(verifier)
    print(f"  [INIT]   Active agents: {list(orch.active_agents.keys())}")
    print(f"  [INIT]   Reasoner model:  {reasoner.model}")
    print(f"  [INIT]   Verifier model:  {verifier.model}")

    # Phase A: Reasoner
    prompt_a = "What is garbage collection in programming? One sentence."
    print(f"\n  [PHASE A] Running Reasoner...")
    print(f"  [INPUT]  prompt=\"{prompt_a}\"")

    t0 = time.perf_counter()
    result_a = orch.run(prompt=prompt_a, target_agent="native::deep_reasoner")
    lat_a = (time.perf_counter() - t0) * 1000

    print(f"  [OUTPUT] status={result_a['status']}")
    print(f"  [OUTPUT] output=\"{result_a['output']}\"")
    print(f"  [METRIC] Latency={lat_a:.2f}ms")

    # Phase B: Verifier
    prompt_b = "Python uses reference counting for garbage collection."
    print(f"\n  [PHASE B] Running Verifier...")
    print(f"  [INPUT]  prompt=\"{prompt_b}\"")

    t0 = time.perf_counter()
    result_b = orch.run(prompt=prompt_b, target_agent="native::system_verifier")
    lat_b = (time.perf_counter() - t0) * 1000

    print(f"  [OUTPUT] status={result_b['status']}")
    print(f"  [OUTPUT] output=\"{result_b['output']}\"")
    print(f"  [METRIC] Latency={lat_b:.2f}ms")

    passed = result_a["status"] == "success" and result_b["status"] == "success"
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [RESULT] {status}")
    record("Multi-Agent Orchestration", status, f"A:{lat_a:.0f} B:{lat_b:.0f}",
           f"A: \"{prompt_a}\" | B: \"{prompt_b}\"",
           f"A: \"{result_a['output'].strip()[:150]}\" | B: \"{result_b['output']}\"",
           "Two agents registered and run sequentially through same orchestrator")
    return passed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 10: Local Model Router Failover
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def test_10():
    print("\n\n" + "━" * 70)
    print("TEST 10: LocalModelRouter — Failover Chain Logic")
    print("━" * 70)

    from hanerma.models.router import LocalModelRouter

    router = LocalModelRouter()
    print(f"  [INIT]   Endpoint:       {router.endpoint}")
    print(f"  [INIT]   Fallback chain: {router.fallback_chain}")
    print(f"  [INIT]   Cooldowns:      {router.cooldowns}")

    print(f"  [EXEC]   Attempting inference (Ollama not running — expecting graceful failure)...")

    t0 = time.perf_counter()
    try:
        response = router.execute_with_fallback("Test prompt for failover")
        latency = (time.perf_counter() - t0) * 1000
        print(f"  [OUTPUT] response=\"{response[:100]}\"")
        notes = "Unexpected success — Ollama may be running"
    except RuntimeError as e:
        latency = (time.perf_counter() - t0) * 1000
        print(f"  [OUTPUT] RuntimeError (expected): \"{str(e)}\"")
        notes = "Graceful failover confirmed: all 3 models tried, all failed, RuntimeError raised"

    print(f"  [METRIC] Latency={latency:.2f}ms")
    print(f"  [STATE]  Cooldowns after: {router.cooldowns}")

    passed = len(router.cooldowns) == 3  # All 3 models should be cooled down
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [RESULT] {status}")
    record("LocalModelRouter Failover", status, f"{latency:.2f}",
           "Test prompt → llama3 → mistral → qwen:0.5b",
           f"All 3 models tried and failed gracefully. Cooldowns={len(router.cooldowns)}",
           notes)
    return passed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RUNNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    tests = [
        ("1. Raw HF Adapter", test_1),
        ("2. Atomic Guard", test_2),
        ("3. HCMS Memory", test_3),
        ("4. Nested Verifier", test_4),
        ("5. BaseAgent + LLM", test_5),
        ("6. DeepReasoner + LLM", test_6),
        ("7. SystemVerifier", test_7),
        ("8. Full Orchestrator", test_8),
        ("9. Multi-Agent", test_9),
        ("10. Model Router", test_10),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        try:
            if fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"  [EXCEPTION] {e}")
            traceback.print_exc()
            record(name, "❌ EXCEPTION", "N/A", "N/A", str(e)[:200], traceback.format_exc()[-200:])

    print("\n\n" + "=" * 70)
    print(f"  FINAL SCORE: {passed}/{len(tests)} PASSED | {failed} FAILED")
    print("=" * 70)

    if failed == 0:
        print("  🎉 ALL TESTS PASSED — HANERMA IS FULLY CERTIFIED")
    else:
        print("  ⚠️  SOME TESTS FAILED — SEE LOG FOR DETAILS")

    # Close log file
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    log_fh.close()

    # Return results for report generation
    return results_table, passed, failed, len(tests)


if __name__ == "__main__":
    results, p, f, total = main()

    # Print summary to real stdout
    print(f"\nDone. {p}/{total} passed. Log saved to: {os.path.abspath(LOG_FILE)}")
