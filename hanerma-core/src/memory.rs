//! Crayon Memory Engine — Pure-Rust semantic memory tiering + vector index.
//!
//! High-performance memory system with three tiers:
//!   - Hot tier:  Recent conversation turns stored verbatim in RAM
//!   - Cold tier: Older turns evicted into a pure-Rust vector index
//!                using brute-force cosine search (optimized with rayon
//!                parallelism for large indices)
//!
//! No C++ dependencies.  Compiles on every platform.
//! Exposed to Python via PyO3 as `MemoryIndex`.

use std::collections::{HashMap, VecDeque};
use std::sync::Mutex;

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use rayon::prelude::*;

// ═══════════════════════════════════════════════════════════════════════════
//  Pure-Rust Vector Index (brute-force cosine, rayon-parallel)
// ═══════════════════════════════════════════════════════════════════════════

/// A single indexed vector with metadata.
struct VectorEntry {
    id: u64,
    /// Flat f32 embedding, length == dim.
    embedding: Vec<f32>,
    /// Pre-computed L2 norm for fast cosine.
    norm: f32,
}

/// Pure-Rust vector index.
/// For conversation memory scale (< 100K vectors), brute-force cosine
/// with rayon parallelism matches or beats HNSW on latency while
/// guaranteeing exact results (no approximation error).
struct VectorIndex {
    entries: Vec<VectorEntry>,
    dim: usize,
}

impl VectorIndex {
    fn new(dim: usize) -> Self {
        Self {
            entries: Vec::new(),
            dim,
        }
    }

    fn add(&mut self, id: u64, embedding: &[f32]) -> Result<(), String> {
        if embedding.len() != self.dim {
            return Err(format!(
                "Dim mismatch: index expects {}, got {}",
                self.dim,
                embedding.len()
            ));
        }
        let norm = l2_norm(embedding);
        self.entries.push(VectorEntry {
            id,
            embedding: embedding.to_vec(),
            norm,
        });
        Ok(())
    }

    fn search(&self, query: &[f32], k: usize) -> Vec<(u64, f32)> {
        if self.entries.is_empty() || k == 0 {
            return Vec::new();
        }

        let query_norm = l2_norm(query);
        if query_norm < 1e-10 {
            return Vec::new();
        }

        // Parallel cosine similarity computation via rayon
        let mut scored: Vec<(u64, f32)> = if self.entries.len() > 500 {
            // Rayon parallel for large indices
            self.entries
                .par_iter()
                .map(|entry| {
                    let sim = cosine_similarity_prenorm(
                        &entry.embedding,
                        entry.norm,
                        query,
                        query_norm,
                    );
                    (entry.id, sim)
                })
                .collect()
        } else {
            // Sequential for small indices (less overhead)
            self.entries
                .iter()
                .map(|entry| {
                    let sim = cosine_similarity_prenorm(
                        &entry.embedding,
                        entry.norm,
                        query,
                        query_norm,
                    );
                    (entry.id, sim)
                })
                .collect()
        };

        // Partial sort: get top-k
        scored.sort_unstable_by(|a, b| {
            b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal)
        });
        scored.truncate(k);
        scored
    }

    fn len(&self) -> usize {
        self.entries.len()
    }

    fn clear(&mut self) {
        self.entries.clear();
    }
}

/// L2 norm of a vector.
#[inline]
fn l2_norm(v: &[f32]) -> f32 {
    v.iter().map(|x| x * x).sum::<f32>().sqrt()
}

/// Cosine similarity with pre-computed norms.
#[inline]
fn cosine_similarity_prenorm(a: &[f32], norm_a: f32, b: &[f32], norm_b: f32) -> f32 {
    let denom = norm_a * norm_b;
    if denom < 1e-10 {
        return 0.0;
    }
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    dot / denom
}

// ═══════════════════════════════════════════════════════════════════════════
//  Memory Engine — Hot/Cold tiering with auto-eviction
// ═══════════════════════════════════════════════════════════════════════════

/// A conversation turn stored in the hot tier.
struct ConversationTurn {
    turn_id: u64,
    role: String,
    content: String,
    embedding: Vec<f32>,
    norm: f32,
}

/// Core memory engine combining hot RAM tier + cold vector index.
struct MemoryEngine {
    hot_turns: VecDeque<ConversationTurn>,
    hot_capacity: usize,
    next_id: u64,
    cold_index: VectorIndex,
    /// Stored content for cold retrieval (turn_id → content string).
    content_store: HashMap<u64, String>,
    dim: usize,
}

impl MemoryEngine {
    fn new(dim: usize, hot_capacity: usize) -> Self {
        Self {
            hot_turns: VecDeque::with_capacity(hot_capacity),
            hot_capacity,
            next_id: 0,
            cold_index: VectorIndex::new(dim),
            content_store: HashMap::new(),
            dim,
        }
    }

    /// Add a conversation turn.  Auto-evicts oldest to cold tier on overflow.
    fn add_turn(&mut self, role: &str, content: &str, embedding: &[f32]) -> Result<u64, String> {
        if embedding.len() != self.dim {
            return Err(format!(
                "Embedding dim mismatch: expected {}, got {}",
                self.dim,
                embedding.len()
            ));
        }

        let id = self.next_id;
        self.next_id += 1;

        let norm = l2_norm(embedding);
        self.hot_turns.push_back(ConversationTurn {
            turn_id: id,
            role: role.to_string(),
            content: content.to_string(),
            embedding: embedding.to_vec(),
            norm,
        });

        // Evict oldest turns to cold tier when hot tier overflows
        while self.hot_turns.len() > self.hot_capacity {
            if let Some(evicted) = self.hot_turns.pop_front() {
                self.cold_index
                    .add(evicted.turn_id, &evicted.embedding)?;
                self.content_store
                    .insert(evicted.turn_id, evicted.content);
            }
        }

        Ok(id)
    }

    /// Search for semantically similar turns across both tiers.
    fn search(&self, query: &[f32], k: usize) -> Result<Vec<(u64, f32, String)>, String> {
        if query.len() != self.dim {
            return Err(format!(
                "Query dim mismatch: expected {}, got {}",
                self.dim,
                query.len()
            ));
        }

        let query_norm = l2_norm(query);
        let mut results: Vec<(u64, f32, String)> = Vec::with_capacity(k * 2);

        // 1. Search hot tier (brute-force, always small)
        for turn in &self.hot_turns {
            let sim = cosine_similarity_prenorm(
                &turn.embedding,
                turn.norm,
                query,
                query_norm,
            );
            results.push((turn.turn_id, sim, turn.content.clone()));
        }

        // 2. Search cold tier (rayon-parallel vector index)
        let cold_results = self.cold_index.search(query, k);
        for (tid, sim) in cold_results {
            let content = self
                .content_store
                .get(&tid)
                .cloned()
                .unwrap_or_default();
            results.push((tid, sim, content));
        }

        // Sort by similarity descending, take top-k
        results.sort_by(|a, b| {
            b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal)
        });
        results.truncate(k);

        Ok(results)
    }

    fn hot_len(&self) -> usize {
        self.hot_turns.len()
    }

    fn cold_len(&self) -> usize {
        self.cold_index.len()
    }

    fn total_len(&self) -> usize {
        self.hot_len() + self.cold_len()
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  PyO3 Wrapper — exposed to Python as `MemoryIndex`
// ═══════════════════════════════════════════════════════════════════════════

#[pyclass(name = "MemoryIndex")]
pub struct PyMemoryIndex {
    inner: Mutex<MemoryEngine>,
}

#[pymethods]
impl PyMemoryIndex {
    /// Create a new MemoryIndex.
    ///
    /// Args:
    ///     dim: Dimensionality of embedding vectors.
    ///     hot_capacity: Max turns in RAM before evicting to vector index.
    #[new]
    #[pyo3(signature = (dim, hot_capacity=50))]
    fn new(dim: usize, hot_capacity: usize) -> PyResult<Self> {
        Ok(Self {
            inner: Mutex::new(MemoryEngine::new(dim, hot_capacity)),
        })
    }

    /// Add a conversation turn with its embedding vector.
    /// Returns the assigned turn_id.
    fn add_turn(
        &self,
        role: &str,
        content: &str,
        embedding: Vec<f32>,
    ) -> PyResult<u64> {
        let mut engine = self.inner.lock().map_err(|e| {
            PyRuntimeError::new_err(format!("Lock poisoned: {e}"))
        })?;
        engine
            .add_turn(role, content, &embedding)
            .map_err(PyRuntimeError::new_err)
    }

    /// Batch-add multiple turns.
    /// turns: list of (role, content, embedding) tuples.
    /// Returns list of assigned turn_ids.
    fn add_turns(&self, turns: Vec<(String, String, Vec<f32>)>) -> PyResult<Vec<u64>> {
        let mut engine = self.inner.lock().map_err(|e| {
            PyRuntimeError::new_err(format!("Lock poisoned: {e}"))
        })?;
        let mut ids = Vec::with_capacity(turns.len());
        for (role, content, emb) in &turns {
            let id = engine
                .add_turn(role, content, emb)
                .map_err(PyRuntimeError::new_err)?;
            ids.push(id);
        }
        Ok(ids)
    }

    /// Search for the top-k most similar turns.
    /// Returns list of (turn_id, similarity, content) tuples.
    #[pyo3(signature = (query_embedding, k=5))]
    fn search(
        &self,
        query_embedding: Vec<f32>,
        k: usize,
    ) -> PyResult<Vec<(u64, f32, String)>> {
        let engine = self.inner.lock().map_err(|e| {
            PyRuntimeError::new_err(format!("Lock poisoned: {e}"))
        })?;
        engine
            .search(&query_embedding, k)
            .map_err(PyRuntimeError::new_err)
    }

    /// Number of turns in the hot (RAM) tier.
    #[getter]
    fn hot_len(&self) -> PyResult<usize> {
        let engine = self.inner.lock().map_err(|e| {
            PyRuntimeError::new_err(format!("Lock poisoned: {e}"))
        })?;
        Ok(engine.hot_len())
    }

    /// Number of turns in the cold (vector index) tier.
    #[getter]
    fn cold_len(&self) -> PyResult<usize> {
        let engine = self.inner.lock().map_err(|e| {
            PyRuntimeError::new_err(format!("Lock poisoned: {e}"))
        })?;
        Ok(engine.cold_len())
    }

    /// Total turns across all tiers.
    #[getter]
    fn total_len(&self) -> PyResult<usize> {
        let engine = self.inner.lock().map_err(|e| {
            PyRuntimeError::new_err(format!("Lock poisoned: {e}"))
        })?;
        Ok(engine.total_len())
    }

    /// Embedding dimensionality.
    #[getter]
    fn dim(&self) -> PyResult<usize> {
        let engine = self.inner.lock().map_err(|e| {
            PyRuntimeError::new_err(format!("Lock poisoned: {e}"))
        })?;
        Ok(engine.dim)
    }

    fn __repr__(&self) -> String {
        match self.inner.lock() {
            Ok(engine) => format!(
                "MemoryIndex(dim={}, hot={}, cold={}, total={})",
                engine.dim,
                engine.hot_len(),
                engine.cold_len(),
                engine.total_len(),
            ),
            Err(_) => "MemoryIndex(locked)".to_string(),
        }
    }
}
