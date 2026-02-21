# ⚡ HANERMA APEX (V1.0)
**Hierarchical Atomic Nested External Reasoning and Memory Architecture**

> [!WARNING]
> **ALPHA STATUS**: HANERMA is currently in active development. While the core architecture is stable, users should expect frequent updates to the reasoning kernel and tool schemas. Always verify sensitive sandbox outputs.

HANERMA APEX is an enterprise-grade orchestration framework designed for building autonomous, self-healing agentic workflows. By grounding LLM reasoning in a **Hardware-Rooted Transactional Bus**, Apex eliminates common agentic failures such as context drift, state loss, and logical hallucinations.

---

## 🚀 Key Features

### 🌐 Visual Intelligence OS (Layer 3)
Transform raw logs into a **Live Causal Execution Graph**.
*   **D3.js Visualization**: Watch "Agent Thinking" nodes, "Tool Execution" links, and "Symbolic Verification" checkpoints form in real-time.
*   **Transactional Auditing**: Select any node in the graph to inspect the exact input/output payloads from the SQLite bus.

### 🛡️ Transactional State Bus (Layer 1)
Experience 100% trace persistence through the **Atomic Event Bus**.
*   **SQLite Persistence**: Every thought, tool call, and model response is recorded natively.
*   **Time-Travel Debugging**: Restore agent states from any historical checkpoint.
*   **Reliability**: Prevents state loss during network interruptions or worker crashes.

### 🧠 Hierarchical Reasoning & Memory (HCMS)
*   **CRAYON Tokenization**: Hardware-level token counting and 60% memory compression.
*   **Vector Vault**: Long-term "System Truths" stored in FAISS-indexed vector embeddings.
*   **Nested Verification**: Deterministic cross-checking of LLM claims against verified memory records.

---

## 🛤️ Getting Started

### 1. ⚡ Mission Execution (CLI)
The most direct way to deploy the swarm. The CLI automatically discovers specialized agents (Architects, Verifiers) based on your natural language prompt.

```bash
# General Mission
hanerma run "Build a secure login system and verify it."

# Explicit Agent Deployment
hanerma run "Update the database schema" --agents Code_Architect Strict_Verifier
```

### 2. 🕹️ Visual Observation
Launch the dashboard to monitor reasoning chains in real-time.

```bash
hanerma viz
```
*Dashoard active at: `http://localhost:8081`*

### 3. 👩‍💻 Developer SDK
Integrate Apex directly into your Python backend.

```python
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import spawn_agent

# 1. Initialize Kernel
orch = HANERMAOrchestrator(model="Qwen/Qwen3-Coder-Next-FP8:together")

# 2. Spawn Specialized Agent
architect = spawn_agent("Architect", role="Senior Dev", tools=[my_custom_tool])
orch.register_agent(architect)

# 3. Execute
result = orch.run("Generate a secure API endpoint.", target_agent="Architect")
```

---

## 🏗️ The 100% Mastery Protocol: Architecture Deep-Dive

To leverage the full Apex stack, your implementation must utilize all four operational layers:

### Layer 0: CRAYON Hardware Root
*   **Function**: SIMD-accelerated tokenization and embedding generation.
*   **Logic**: High-speed processing of the vector cache to prevent context bottlenecks. Open source logic implemented in C++.

### Layer 1: Transactional State Bus
*   **Function**: SQLite-backed persistence for the entire causal chain.
*   **Logic**: Every AI thought and tool result is committed as an atomic transaction, ensuring zero state loss during crashes.

### Layer 2: Symbolic & Nested Verification
*   **Function**: Hallucination detection and fact-checking.
*   **Logic**: Uses the `SymbolicReasoner` and `NestedVerifier` to cross-reference LLM claims against verified memories in the FAISS-indexed `HCMS`.

### Layer 3: Visual Intelligence OS
*   **Function**: Observability into the reasoning swarm.
*   **Logic**: Real-time D3.js causal graph mapping of agent transitions and tool impacts.

---

## 🚀 Hyper-Logical Technical FAQ

### Q: How does memory management handle 100% platform scaling?
**Detailed Logical Steps:**
1.  **Ingestion**: Incoming telemetry is streamed into the **Layer 0 XERV-CRAYON** C++ kernel.
2.  **Spectral Compression**: CRAYON applies token-clustering, achieving up to 60% compression.
3.  **Vectorization**: Text is converted into hardware-aligned embeddings via `CrayonVocab`.
4.  **L2 FAISS Storage**: The `HCMSManager` maps these vectors into a **FAISS FlatL2 Index**.
5.  **Retrieval**: During turn `T+1`, the engine performs a similarity search to inject relevant historical "System Truths" back into the prompt.
6.  **Budget Protection**: `_trim_history` monitors token counts to maintain the context window under the `MAX_CONTEXT_TOKENS` ceiling.

### Q: How does the system handle multi-agent tool concurrency?
**Detailed Logical Steps:**
1.  **Static Analysis**: Tool calls are detected via regex in the `_handle_tool_call` loop.
2.  **Parallel Dispatch**: The engine uses `asyncio` to execute non-human-interposable tools (e.g., search, arithmetic) concurrently.
3.  **Shared Memory Locking**: Results are written to the `shared_memory` field within the global state, ensuring the result is available to the next agent in the swarm.
4.  **Conflict Resolution**: The `TransactionalEventBus` ensures that even if tools finish out of order, the causal log remains synchronous.

### Q: What is the exact logic behind "Recursive Intelligence" handoffs?
**Detailed Logical Steps:**
1.  **Handoff Detection**: The orchestrator identifies the `DELEGATE:` keyword in the LLM's response stream.
2.  **Context Encapsulation**: The current agent's short-term history is serialized into the `TransactionalBus`.
3.  **Blueprint Hydration**: The `PersonaRegistry` instantiates the target agent (e.g., `Strict_Verifier`).
4.  **Mission Forwarding**: The state is handed over with a recursive directive: *"Inherit context and complete delegated sub-task."*
5.  **Verification Check**: The new agent's output is subjected to Layer 2 symbolic checks before being accepted back into the primary history.

---

## 🛠️ Installation & Rapid Setup

```bash
# 1. Environment Setup
git clone https://github.com/hanerma/hanerma.git
cd hanerma
pip install -e .

# 2. Configure Credentials (.env)
HF_TOKEN="your_huggingface_token"
HANERMA_MODEL="Qwen/Qwen3-Coder-Next-FP8:together"
```

## 📜 License
Apache 2.0. Built with ⚡ by the HANERMA Core Team. 
Powered by **XERV-CRAYON** Technology.
