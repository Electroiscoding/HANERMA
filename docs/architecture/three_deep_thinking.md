
# Deep dives into Three-Deep Thinking

HANERMA's core logic is split into 3 verified execution layers.

### 1. Atomic (Deep1)
- **Goal**: Granularity.
- **Process**: LLM output is split by sentence/proposition.
- **Storage**: Each unit gets a GUID and embedding in HCMS.

### 2. Nested (Deep2)
- **Goal**: Consistency.
- **Process**:
  - `verifier` agent checks units against memory.
  - `logic` checker ensures no contradictions in the chain.

### 3. External (Deep3)
- **Goal**: Grounding.
- **Process**: If confidence < threshold, tools (Web/Code) are invoked.
- **Result**: Data is fed back into Deep1 for re-evaluation.
