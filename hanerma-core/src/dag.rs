//! Core DAG data structures, validator, and async work-stealing scheduler.

use std::collections::{HashMap, HashSet, VecDeque};
use std::time::Instant;

use pyo3::prelude::*;
use pyo3::types::PyDict;
use tokio::sync::mpsc;

// ───────────── Node status ─────────────

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NodeStatus {
    Completed,
    Failed,
    Cancelled,
}

impl NodeStatus {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Completed => "completed",
            Self::Failed    => "failed",
            Self::Cancelled => "cancelled",
        }
    }
}

// ───────────── Internal types ─────────────

pub struct DagNode {
    pub id: String,
    pub name: String,
    pub dependencies: Vec<String>,
    pub callable: PyObject,
}

enum Completion {
    Ok  { id: String, result: PyObject, ms: f64 },
    Err { id: String, error: String,    ms: f64 },
}

pub struct ExecResult {
    pub node_id:     String,
    pub status:      NodeStatus,
    pub result:      Option<PyObject>,
    pub error:       Option<String>,
    pub duration_ms: f64,
}

// ───────────── DAG validation (Kahn's algorithm) ─────────────

pub fn validate_dag(nodes: &HashMap<String, DagNode>) -> Result<Vec<String>, String> {
    let mut in_deg: HashMap<&str, usize>     = HashMap::with_capacity(nodes.len());
    let mut adj:    HashMap<&str, Vec<&str>>  = HashMap::with_capacity(nodes.len());

    for id in nodes.keys() {
        in_deg.entry(id.as_str()).or_insert(0);
    }
    for (id, node) in nodes {
        for dep in &node.dependencies {
            if !nodes.contains_key(dep) {
                return Err(format!("Node '{}' depends on unknown node '{}'", id, dep));
            }
            adj.entry(dep.as_str()).or_default().push(id.as_str());
            *in_deg.entry(id.as_str()).or_insert(0) += 1;
        }
    }

    let mut queue: VecDeque<&str> = in_deg.iter()
        .filter(|(_, &d)| d == 0).map(|(&id, _)| id).collect();
    let mut order: Vec<String> = Vec::with_capacity(nodes.len());

    while let Some(cur) = queue.pop_front() {
        order.push(cur.to_string());
        if let Some(nxt) = adj.get(cur) {
            for &n in nxt {
                let d = in_deg.get_mut(n).unwrap();
                *d -= 1;
                if *d == 0 { queue.push_back(n); }
            }
        }
    }

    if order.len() != nodes.len() {
        let stuck: Vec<&str> = in_deg.iter()
            .filter(|(_, &d)| d > 0).map(|(&id, _)| id).collect();
        Err(format!("Cycle detected involving nodes: {:?}", stuck))
    } else {
        Ok(order)
    }
}

// ───────────── Cascade-cancel downstream ─────────────

fn cascade_cancel(
    failed_id: &str,
    dependents: &HashMap<String, Vec<String>>,
    failed_set: &mut HashSet<String>,
    remaining: &mut HashMap<String, DagNode>,
) -> Vec<String> {
    let mut cancelled: Vec<String> = Vec::new();
    let mut queue: VecDeque<String> = VecDeque::new();
    if let Some(ds) = dependents.get(failed_id) {
        for d in ds { queue.push_back(d.clone()); }
    }
    while let Some(id) = queue.pop_front() {
        if failed_set.contains(&id) { continue; }
        failed_set.insert(id.clone());
        remaining.remove(&id);
        cancelled.push(id.clone());
        if let Some(ds) = dependents.get(&id) {
            for d in ds {
                if !failed_set.contains(d) { queue.push_back(d.clone()); }
            }
        }
    }
    cancelled
}

// ───────────── Execute single node (spawn_blocking + GIL) ─────────────

async fn run_node(
    node_id: String,
    callable: PyObject,
    dep_results: Vec<(String, PyObject)>,   // Vec of (key, value) — avoids Clone
    tx: mpsc::Sender<Completion>,
) {
    let start = Instant::now();
    let id = node_id.clone();

    let outcome = tokio::task::spawn_blocking(move || {
        Python::with_gil(|py| -> PyResult<PyObject> {
            let deps = PyDict::new(py);
            for (key, val) in &dep_results {
                deps.set_item(key, val.clone_ref(py))?;
            }
            let result = callable.call1(py, (&deps,))?;

            // Handle async callables transparently
            let inspect = py.import("inspect")?;
            let is_coro: bool = inspect
                .call_method1("iscoroutine", (result.bind(py),))?
                .extract()?;
            if is_coro {
                let asyncio = py.import("asyncio")?;
                let awaited = asyncio.call_method1("run", (result.bind(py),))?;
                Ok(awaited.unbind())
            } else {
                Ok(result)
            }
        })
    })
    .await;

    let ms = start.elapsed().as_secs_f64() * 1000.0;

    let msg = match outcome {
        Ok(Ok(r))  => Completion::Ok  { id, result: r, ms },
        Ok(Err(e)) => {
            let err = Python::with_gil(|py| format!("{}", e.value(py)));
            Completion::Err { id, error: err, ms }
        }
        Err(e) => Completion::Err { id, error: format!("Task panicked: {}", e), ms },
    };
    let _ = tx.send(msg).await;
}

// ───────────── Main entry: execute_dag ─────────────

pub fn execute_dag(mut nodes: HashMap<String, DagNode>) -> Result<Vec<ExecResult>, String> {
    let _topo = validate_dag(&nodes)?;
    let total = nodes.len();
    if total == 0 { return Ok(Vec::new()); }

    // Reverse deps + pending counts
    let mut dependents: HashMap<String, Vec<String>> = HashMap::new();
    let mut pending:    HashMap<String, usize>       = HashMap::new();
    for (id, node) in &nodes {
        pending.insert(id.clone(), node.dependencies.len());
        for dep in &node.dependencies {
            dependents.entry(dep.clone()).or_default().push(id.clone());
        }
    }

    let cpus = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4);
    let rt = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(cpus.max(2).min(16))
        .enable_all()
        .build()
        .map_err(|e| format!("Failed to create tokio runtime: {}", e))?;

    rt.block_on(async move {
        let (tx, mut rx) = mpsc::channel::<Completion>(total.max(1));

        // Store results as Vec<(key, PyObject)> to avoid Clone requirement
        let mut results_store: HashMap<String, PyObject> = HashMap::new();
        let mut exec_results: Vec<ExecResult> = Vec::with_capacity(total);
        let mut completed: usize = 0;
        let mut failed_set: HashSet<String> = HashSet::new();

        // Spawn root nodes
        let roots: Vec<String> = pending.iter()
            .filter(|(_, &c)| c == 0).map(|(id, _)| id.clone()).collect();
        for id in roots {
            if let Some(node) = nodes.remove(&id) {
                let sender = tx.clone();
                tokio::task::spawn(async move {
                    run_node(node.id, node.callable, Vec::new(), sender).await;
                });
            }
        }

        // Scheduling loop
        while completed < total {
            match rx.recv().await {
                Some(Completion::Ok { id, result, ms }) => {
                    // Store result (need GIL to clone_ref)
                    Python::with_gil(|py| {
                        results_store.insert(id.clone(), result.clone_ref(py));
                    });
                    exec_results.push(ExecResult {
                        node_id: id.clone(),
                        status: NodeStatus::Completed,
                        result: Some(result),
                        error: None,
                        duration_ms: ms,
                    });
                    completed += 1;

                    // Propagate
                    if let Some(ds) = dependents.get(&id) {
                        for dep_id in ds {
                            if failed_set.contains(dep_id) { continue; }
                            if let Some(cnt) = pending.get_mut(dep_id) {
                                *cnt -= 1;
                                if *cnt == 0 {
                                    if let Some(node) = nodes.remove(dep_id) {
                                        // Gather deps as Vec<(String, PyObject)>
                                        let dep_data: Vec<(String, PyObject)> =
                                            Python::with_gil(|py| {
                                                node.dependencies.iter().filter_map(|d| {
                                                    results_store.get(d).map(|r| {
                                                        (d.clone(), r.clone_ref(py))
                                                    })
                                                }).collect()
                                            });
                                        let sender = tx.clone();
                                        tokio::task::spawn(async move {
                                            run_node(
                                                node.id, node.callable,
                                                dep_data, sender,
                                            ).await;
                                        });
                                    }
                                }
                            }
                        }
                    }
                }

                Some(Completion::Err { id, error, ms }) => {
                    failed_set.insert(id.clone());
                    exec_results.push(ExecResult {
                        node_id: id.clone(),
                        status: NodeStatus::Failed,
                        result: None,
                        error: Some(error.clone()),
                        duration_ms: ms,
                    });
                    completed += 1;
                    let cancelled = cascade_cancel(&id, &dependents, &mut failed_set, &mut nodes);
                    for cid in cancelled {
                        exec_results.push(ExecResult {
                            node_id: cid,
                            status: NodeStatus::Cancelled,
                            result: None,
                            error: Some(format!("Cancelled: upstream '{}' failed", id)),
                            duration_ms: 0.0,
                        });
                        completed += 1;
                    }
                }

                None => break,
            }
        }

        Ok(exec_results)
    })
}
