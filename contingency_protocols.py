"""
HANERMA Contingency Protocols - Production Failure Handling

This module provides standardized responses for the three critical failure scenarios:
1. Rust Compilation Failure
2. Context Cut-Off 
3. Integration Mismatch

Each contingency has a specific protocol to follow exactly.
"""

import sys
import subprocess
import json
from typing import Optional, Dict, Any


class ContingencyHandler:
    """Handles production contingencies with exact protocol responses."""
    
    def __init__(self):
        self.last_error = None
        self.last_line = None
        self.python_state = None
        self.rust_signature = None
    
    def handle_rust_compilation_failure(self, error_output: str) -> str:
        """
        Contingency 1: Rust Compilation Failure
        
        If maturin fails to build Rust core, analyze the exact error and provide
        targeted fix without rewriting entire files.
        """
        self.last_error = error_output
        
        # Extract key error patterns
        error_lines = error_output.split('\n')
        key_errors = []
        
        for line in error_lines:
            if any(keyword in line for keyword in [
                'error[E', 'borrow checker', 'PyO3', 'lifetime', 
                'tokio', 'threading', 'mismatch', 'expected', 'found'
            ]):
                key_errors.append(line.strip())
        
        return f"""The Rust compilation failed with error above. Do not rewrite entire file. Analyze the borrow-checker or PyO3 lifetime error, explain exactly why it failed, and output ONLY the patched Rust function that fixes it. Maintain Zero-Fluff mandate.

Key errors detected:
{chr(10).join(key_errors[:5])}

Focus on the specific function or struct that's failing and provide the minimal fix."""

    def handle_context_cut_off(self, last_line: str) -> str:
        """
        Contingency 2: Context Cut-Off
        
        If AI stops generating code mid-sentence due to token limit,
        resume from exact line without explanation.
        """
        self.last_line = last_line
        
        return f"""You hit the output token limit. DO NOT apologize or explain. Resume outputting code snippet starting EXACTLY from the line: {last_line}"""

    def handle_integration_mismatch(self, python_state: str, rust_signature: str) -> str:
        """
        Contingency 3: Integration Mismatch
        
        If Python and Rust data formats don't match, provide exact bridge code.
        """
        self.python_state = python_state
        self.rust_signature = rust_signature
        
        return f"""We have a Type bridging error between Python and Rust. The Python state is sending {python_state}, but the Rust PyO3 signature expects {rust_signature}. Write the exact serialization/deserialization patch needed in lib.rs to bridge these formats natively without slowing down execution."""

    def detect_failure_type(self, error_output: str) -> Optional[str]:
        """
        Auto-detect the type of failure from error output.
        """
        if "error[E" in error_output and ("borrow" in error_output or "lifetime" in error_output):
            return "rust_compilation"
        elif "token limit" in error_output.lower() or "cut off" in error_output.lower():
            return "context_cutoff"
        elif "type" in error_output.lower() and "mismatch" in error_output.lower():
            return "integration_mismatch"
        return None

    def execute_contingency(self, failure_type: str, **kwargs) -> str:
        """
        Execute the appropriate contingency response.
        """
        if failure_type == "rust_compilation":
            return self.handle_rust_compilation_failure(kwargs.get('error_output', ''))
        elif failure_type == "context_cutoff":
            return self.handle_context_cut_off(kwargs.get('last_line', ''))
        elif failure_type == "integration_mismatch":
            return self.handle_integration_mismatch(
                kwargs.get('python_state', ''),
                kwargs.get('rust_signature', '')
            )
        else:
            return "Unknown failure type. Please specify rust_compilation, context_cutoff, or integration_mismatch."

    def monitor_rust_build(self) -> Dict[str, Any]:
        """
        Monitor Rust build process and detect failures.
        """
        try:
            result = subprocess.run(
                ['maturin', 'build', '--release'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                failure_type = self.detect_failure_type(result.stderr)
                return {
                    'success': False,
                    'failure_type': failure_type,
                    'error_output': result.stderr,
                    'contingency_response': self.execute_contingency(
                        failure_type, 
                        error_output=result.stderr
                    ) if failure_type else None
                }
            
            return {'success': True}
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'failure_type': 'timeout',
                'error_output': 'Build timed out after 5 minutes'
            }
        except Exception as e:
            return {
                'success': False,
                'failure_type': 'unknown',
                'error_output': str(e)
            }

    def create_rust_hotfix_template(self, error_type: str, error_details: str) -> str:
        """
        Create a template for Rust hotfixes based on error type.
        """
        templates = {
            'borrow_checker': '''
// Fix for borrow checker error
#[allow(dead_code)]
fn fixed_function() -> Result<(), Box<dyn std::error::Error>> {
    // Clone instead of borrow to fix lifetime issues
    let data = get_data().clone();
    process_data(data)
}
''',
            'pyo3_lifetime': '''
// Fix for PyO3 lifetime error
use pyo3::prelude::*;
use pyo3::types::PyDict;

#[pyclass]
struct FixedStruct {
    #[pyo3(get, set)]
    data: Py<PyDict>,
}

#[pymethods]
impl FixedStruct {
    #[new]
    fn new() -> Self {
        Self {
            data: Py::new(PyDict::new()),
        }
    }
}
''',
            'tokio_threading': '''
// Fix for tokio threading mismatch
use tokio::runtime::Runtime;

#[pyfunction]
fn fixed_async_function() -> PyResult<String> {
    let rt = Runtime::new()?;
    rt.block_on(async_function())
}

async fn async_function() -> String {
    "Fixed async result".to_string()
}
'''
        }
        
        return templates.get(error_type, '// No template available for this error type')

    def log_contingency_usage(self, failure_type: str, details: str):
        """
        Log contingency usage for debugging.
        """
        log_entry = {
            'timestamp': str(subprocess.check_output(['date'], text=True).strip()),
            'failure_type': failure_type,
            'details': details,
            'contingency_applied': True
        }
        
        try:
            with open('contingency_log.json', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except:
            pass  # Silent failure for logging


# Global contingency handler instance
contingency = ContingencyHandler()


def apply_rust_contingency(error_output: str) -> str:
    """
    Apply Rust compilation contingency.
    
    Usage:
        response = apply_rust_contingency(error_output)
        print(response)  # Send to AI
    """
    return contingency.handle_rust_compilation_failure(error_output)


def resume_context_cut_off(last_line: str) -> str:
    """
    Resume from context cut-off.
    
    Usage:
        response = resume_context_cut_off(last_line_written)
        print(response)  # Send to AI
    """
    return contingency.handle_context_cut_off(last_line)


def fix_integration_mismatch(python_state: str, rust_signature: str) -> str:
    """
    Fix integration mismatch between Python and Rust.
    
    Usage:
        response = fix_integration_mismatch(python_output, rust_function_signature)
        print(response)  # Send to AI
    """
    return contingency.handle_integration_mismatch(python_state, rust_signature)


# Quick access functions for emergency use
def rust_failed(error: str) -> str:
    """Quick access for Rust compilation failure."""
    return apply_rust_contingency(error)


def context_cut(last_line: str) -> str:
    """Quick access for context cut-off."""
    return resume_context_cut_off(last_line)


def type_mismatch(python_output: str, rust_sig: str) -> str:
    """Quick access for type mismatch."""
    return fix_integration_mismatch(python_output, rust_sig)


print("[CONTINGENCY] Protocols loaded - Ready for production failures")
