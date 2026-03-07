//! State Capacitor — Hot/Cold tiered LSM key-value store.
//!
//! Hot tier  : DashMap (lock-free concurrent RAM cache, bounded capacity).
//! Cold tier : sled   (crash-proof LSM tree on disk, sub-ms latency).
//!
//! Write path: write-through to BOTH tiers (crash-safe).
//! Read path : hot first → cold fallback (promotes to hot on miss).
//! Eviction  : when hot exceeds capacity, oldest 25 % removed (data safe in cold).
//!
//! Python API stores/retrieves arbitrary Python objects via pickle.

use std::sync::atomic::{AtomicU64, Ordering};

use dashmap::DashMap;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

// ───────────────────────────────────────────────────────────────────────────
// Hot tier entry
// ───────────────────────────────────────────────────────────────────────────

struct HotEntry {
    value: Vec<u8>,
    access_order: u64,
}

// ───────────────────────────────────────────────────────────────────────────
// Core engine (pure Rust, no PyO3)
// ───────────────────────────────────────────────────────────────────────────

struct StateEngine {
    hot: DashMap<String, HotEntry>,
    cold: sled::Db,
    counter: AtomicU64,
    capacity: usize,
}

impl StateEngine {
    /// Open or create the state database at `path`.
    fn open(path: &str, capacity: usize) -> Result<Self, String> {
        let cold = sled::open(path).map_err(|e| {
            format!("Failed to open sled database at '{}': {}", path, e)
        })?;

        // Seed the access counter from current cold entry count so we
        // never collide with a previous session's ordering values.
        let seed = cold.len() as u64;

        Ok(Self {
            hot: DashMap::with_capacity(capacity),
            cold,
            counter: AtomicU64::new(seed),
            capacity,
        })
    }

    /// Store a key-value pair (write-through: hot + cold).
    fn put(&self, key: &str, value: &[u8]) -> Result<(), String> {
        let order = self.counter.fetch_add(1, Ordering::Relaxed);

        // Write-through to cold (crash-safe persistence)
        self.cold
            .insert(key.as_bytes(), value)
            .map_err(|e| format!("sled insert error: {}", e))?;

        // Insert into hot tier
        self.hot.insert(
            key.to_string(),
            HotEntry {
                value: value.to_vec(),
                access_order: order,
            },
        );

        self.maybe_evict();
        Ok(())
    }

    /// Retrieve a value.  Hot → Cold fallback (promotes to hot on cold hit).
    fn get(&self, key: &str) -> Result<Option<Vec<u8>>, String> {
        // ── Hot path (sub-microsecond) ──
        if let Some(mut entry) = self.hot.get_mut(key) {
            // Touch access order (LRU refresh)
            entry.access_order = self.counter.fetch_add(1, Ordering::Relaxed);
            return Ok(Some(entry.value.clone()));
        }

        // ── Cold path (sub-millisecond, disk) ──
        match self.cold.get(key.as_bytes()) {
            Ok(Some(ivec)) => {
                let data = ivec.to_vec();
                // Promote to hot tier for future fast reads
                let order = self.counter.fetch_add(1, Ordering::Relaxed);
                self.hot.insert(
                    key.to_string(),
                    HotEntry {
                        value: data.clone(),
                        access_order: order,
                    },
                );
                self.maybe_evict();
                Ok(Some(data))
            }
            Ok(None) => Ok(None),
            Err(e) => Err(format!("sled get error: {}", e)),
        }
    }

    /// Delete from both tiers.
    fn delete(&self, key: &str) -> Result<(), String> {
        self.hot.remove(key);
        self.cold
            .remove(key.as_bytes())
            .map_err(|e| format!("sled remove error: {}", e))?;
        Ok(())
    }

    /// Check if a key exists in either tier.
    fn contains(&self, key: &str) -> Result<bool, String> {
        if self.hot.contains_key(key) {
            return Ok(true);
        }
        self.cold
            .contains_key(key.as_bytes())
            .map_err(|e| format!("sled contains_key error: {}", e))
    }

    /// Evict oldest entries from hot tier when capacity is exceeded.
    /// Data is safe — it was already written through to cold.
    fn maybe_evict(&self) {
        let current = self.hot.len();
        if current <= self.capacity {
            return;
        }

        // Evict oldest 25 % (with minimum of 1)
        let to_evict = (self.capacity / 4).max(1);

        // Collect (key, access_order) pairs
        let mut entries: Vec<(String, u64)> = self
            .hot
            .iter()
            .map(|e| (e.key().clone(), e.value().access_order))
            .collect();

        // Sort oldest-first
        entries.sort_by_key(|(_, order)| *order);

        // Remove oldest entries from hot (they persist in cold)
        for (key, _) in entries.into_iter().take(to_evict) {
            self.hot.remove(&key);
        }
    }

    /// Flush cold tier to disk (ensures durability).
    fn flush(&self) -> Result<usize, String> {
        self.cold
            .flush()
            .map_err(|e| format!("sled flush error: {}", e))
    }

    /// List all persisted keys (from cold tier).
    fn keys(&self) -> Result<Vec<String>, String> {
        let mut out = Vec::new();
        for entry in self.cold.iter() {
            let (k, _) = entry.map_err(|e| format!("sled iter error: {}", e))?;
            if let Ok(s) = std::str::from_utf8(&k) {
                out.push(s.to_string());
            }
        }
        Ok(out)
    }

    /// Total persisted entries (cold tier is the source of truth).
    fn total_len(&self) -> usize {
        self.cold.len()
    }

    /// Current hot-tier occupancy.
    fn hot_len(&self) -> usize {
        self.hot.len()
    }

    /// Wipe both tiers.
    fn clear(&self) -> Result<(), String> {
        self.hot.clear();
        self.cold
            .clear()
            .map_err(|e| format!("sled clear error: {}", e))?;
        Ok(())
    }
}

// ───────────────────────────────────────────────────────────────────────────
// Python-facing wrapper
// ───────────────────────────────────────────────────────────────────────────

/// Crash-proof state persistence with hot/cold tiering.
///
/// Hot tier  = DashMap (RAM, bounded).
/// Cold tier = sled LSM tree (disk, unbounded).
///
/// ```python
/// cap = StateCapacitor("./my_state", capacity=100)
/// cap.put_state("agent_result", {"score": 0.95, "model": "gpt-4"})
/// print(cap.get_state("agent_result"))     # → {'score': 0.95, 'model': 'gpt-4'}
/// cap.put_bytes("raw", b"\x00\x01\x02")
/// print(cap.get_bytes("raw"))              # → b'\x00\x01\x02'
/// ```
#[pyclass(name = "StateCapacitor")]
pub struct PyStateCapacitor {
    engine: StateEngine,
}

#[pymethods]
impl PyStateCapacitor {
    /// Create / open a StateCapacitor.
    ///
    /// Args:
    ///     path:     Directory for the sled database (default: "./hanerma_state").
    ///     capacity: Max entries in the hot (RAM) tier (default: 100).
    #[new]
    #[pyo3(signature = (path="./hanerma_state", capacity=100))]
    fn new(path: &str, capacity: usize) -> PyResult<Self> {
        let engine =
            StateEngine::open(path, capacity).map_err(PyRuntimeError::new_err)?;
        Ok(Self { engine })
    }

    /// Store any pickle-able Python object.
    fn put_state(
        &self,
        py: Python<'_>,
        key: String,
        value: Bound<'_, PyAny>,
    ) -> PyResult<()> {
        let pickle = py.import("pickle")?;
        let dumped = pickle.call_method1("dumps", (&value,))?;
        let bytes: Vec<u8> = dumped.extract()?;
        self.engine
            .put(&key, &bytes)
            .map_err(PyRuntimeError::new_err)
    }

    /// Retrieve a previously stored Python object (or None).
    fn get_state(
        &self,
        py: Python<'_>,
        key: String,
    ) -> PyResult<Option<PyObject>> {
        match self.engine.get(&key).map_err(PyRuntimeError::new_err)? {
            Some(data) => {
                let pickle = py.import("pickle")?;
                let bytes_obj = PyBytes::new(py, &data);
                let obj = pickle.call_method1("loads", (&bytes_obj,))?;
                Ok(Some(obj.unbind()))
            }
            None => Ok(None),
        }
    }

    /// Store raw bytes (no serialisation overhead).
    fn put_bytes(&self, key: String, value: Vec<u8>) -> PyResult<()> {
        self.engine
            .put(&key, &value)
            .map_err(PyRuntimeError::new_err)
    }

    /// Retrieve raw bytes (or None).
    fn get_bytes(
        &self,
        py: Python<'_>,
        key: String,
    ) -> PyResult<Option<PyObject>> {
        match self.engine.get(&key).map_err(PyRuntimeError::new_err)? {
            Some(data) => {
                Ok(Some(PyBytes::new(py, &data).into_any().unbind()))
            }
            None => Ok(None),
        }
    }

    /// Delete a key from both tiers.
    fn delete(&self, key: String) -> PyResult<()> {
        self.engine
            .delete(&key)
            .map_err(PyRuntimeError::new_err)
    }

    /// Check if a key exists.
    fn contains(&self, key: String) -> PyResult<bool> {
        self.engine
            .contains(&key)
            .map_err(PyRuntimeError::new_err)
    }

    /// List all persisted keys.
    fn keys(&self) -> PyResult<Vec<String>> {
        self.engine.keys().map_err(PyRuntimeError::new_err)
    }

    /// Flush cold tier to disk (ensures full durability).
    fn flush(&self) -> PyResult<usize> {
        self.engine.flush().map_err(PyRuntimeError::new_err)
    }

    /// Wipe all data from both tiers.
    fn clear(&self) -> PyResult<()> {
        self.engine.clear().map_err(PyRuntimeError::new_err)
    }

    /// Total persisted entries.
    #[getter]
    fn total_len(&self) -> usize {
        self.engine.total_len()
    }

    /// Current hot-tier occupancy.
    #[getter]
    fn hot_len(&self) -> usize {
        self.engine.hot_len()
    }

    /// Hot-tier capacity setting.
    #[getter]
    fn capacity(&self) -> usize {
        self.engine.capacity
    }

    fn __repr__(&self) -> String {
        format!(
            "StateCapacitor(hot={}, total={}, capacity={})",
            self.engine.hot_len(),
            self.engine.total_len(),
            self.engine.capacity,
        )
    }

    fn __len__(&self) -> usize {
        self.engine.total_len()
    }

    fn __contains__(&self, key: String) -> PyResult<bool> {
        self.engine
            .contains(&key)
            .map_err(PyRuntimeError::new_err)
    }
}
