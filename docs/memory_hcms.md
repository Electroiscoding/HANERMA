
# HCMS: Hyperfast Infinite Memory Store

## Overview
Traditional context windows (100k, 1M, 2M) are fundamentally limited by:
1. Retrieval Latency (O(N) search)
2. Cost (re-encoding input)
3. "Loss in the Middle" errors

HCMS solves this via **HyperToken Compression** and a **Graph-Vector Hybrid Store**.

## Vector + Graph Hybrid
- **Vector Store (FAISS)**: Captures semantic similarity. "What context is *like* this query?"
- **Graph Store (Neo4j)**: Captures structured relationships. "What entities are *related* to this query?"

## Algorithm 1: HyperToken Compression
Input -> Tokenizer -> [Vector Cluster] -> {HyperToken ID}
A 10,000-word document becomes ~500 HyperTokens.

### Retrieval:
Query -> Relational Prefetch (Graph) -> Expanded Set -> Vector Similarity (HyperTokens) -> Full Context Decompression
Latency: <20ms for 1M tokens.

## Persistence
Memory is stored on disk and persisted across sessions in `data/hcms_store/`.
