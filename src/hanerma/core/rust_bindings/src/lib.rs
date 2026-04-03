use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use sled::Db;

#[pyclass]
struct SledDB {
    db: Db,
}

#[pymethods]
impl SledDB {
    #[new]
    fn new(path: String) -> PyResult<Self> {
        let db = sled::open(&path).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        Ok(SledDB { db })
    }

    fn insert(&self, key: String, value: String) -> PyResult<()> {
        self.db.insert(key.as_bytes(), value.as_bytes())
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        Ok(())
    }

    fn get(&self, key: String) -> PyResult<Option<String>> {
        let result = self.db.get(key.as_bytes())
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        match result {
            Some(ivec) => {
                let s = String::from_utf8(ivec.to_vec())
                    .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
                Ok(Some(s))
            },
            None => Ok(None)
        }
    }
}

#[pymodule]
fn hanerma_rust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<SledDB>()?;
    Ok(())
}
