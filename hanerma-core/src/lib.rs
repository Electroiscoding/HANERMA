//! hanerma_core — Python module exposing the Rust DAG engine via PyO3.

mod dag;
mod state;
mod memory;

use std::collections::HashMap;

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyList;

use dag::{DagNode, ExecResult};

// ───────────── NodeResult (returned to Python) ─────────────

#[pyclass(name = "NodeResult")]
pub struct PyNodeResult {
    #[pyo3(get)]
    pub node_id: String,
    #[pyo3(get)]
    pub status: String,
    #[pyo3(get)]
    pub error: Option<String>,
    #[pyo3(get)]
    pub duration_ms: f64,
    // result stored separately — returned via getter with GIL
    result_obj: Option<PyObject>,
}

#[pymethods]
impl PyNodeResult {
    #[getter]
    fn result(&self, py: Python<'_>) -> Option<PyObject> {
        self.result_obj.as_ref().map(|r| r.clone_ref(py))
    }

    fn __repr__(&self) -> String {
        format!(
            "NodeResult(id='{}', status='{}', duration={:.2}ms)",
            self.node_id, self.status, self.duration_ms
        )
    }
}

impl PyNodeResult {
    fn from_exec(r: ExecResult) -> Self {
        Self {
            node_id:     r.node_id,
            status:      r.status.as_str().to_string(),
            result_obj:  r.result,
            error:       r.error,
            duration_ms: r.duration_ms,
        }
    }
}

// ───────────── RustEngine ─────────────

#[pyclass(name = "RustEngine")]
pub struct PyRustEngine {
    nodes: HashMap<String, DagNode>,
}

#[pymethods]
impl PyRustEngine {
    #[new]
    fn new() -> Self {
        Self { nodes: HashMap::new() }
    }

    #[pyo3(signature = (node_id, name, callable, dependencies=None))]
    fn add_node(
        &mut self,
        node_id: String,
        name: String,
        callable: PyObject,
        dependencies: Option<Bound<'_, PyList>>,
    ) -> PyResult<()> {
        if self.nodes.contains_key(&node_id) {
            return Err(PyRuntimeError::new_err(format!(
                "Duplicate node id: '{}'", node_id
            )));
        }
        let deps: Vec<String> = match dependencies {
            Some(list) => list.iter()
                .map(|item| item.extract::<String>())
                .collect::<PyResult<Vec<String>>>()?,
            None => Vec::new(),
        };
        self.nodes.insert(node_id.clone(), DagNode {
            id: node_id, name, dependencies: deps, callable,
        });
        Ok(())
    }

    fn validate(&self) -> PyResult<Vec<String>> {
        dag::validate_dag(&self.nodes).map_err(PyRuntimeError::new_err)
    }

    fn node_count(&self) -> usize { self.nodes.len() }

    fn clear(&mut self) { self.nodes.clear(); }

    fn execute(&mut self, py: Python<'_>) -> PyResult<Vec<PyNodeResult>> {
        if self.nodes.is_empty() { return Ok(Vec::new()); }
        let nodes = std::mem::take(&mut self.nodes);
        let raw = py.allow_threads(|| dag::execute_dag(nodes));
        match raw {
            Ok(results) => Ok(results.into_iter().map(PyNodeResult::from_exec).collect()),
            Err(e) => Err(PyRuntimeError::new_err(e)),
        }
    }

    fn __repr__(&self) -> String {
        format!("RustEngine(nodes={})", self.nodes.len())
    }
}

// ───────────── Module ─────────────

#[pymodule]
fn hanerma_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyRustEngine>()?;
    m.add_class::<PyNodeResult>()?;
    m.add_class::<state::PyStateCapacitor>()?;
    m.add_class::<memory::PyMemoryIndex>()?;
    Ok(())
}
