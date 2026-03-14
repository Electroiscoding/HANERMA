# HANERMA Contingency Protocols - Quick Reference

## 🔧 Contingency 1: Rust Compilation Failure

**When to use:** Maturin build fails with borrow-checker, PyO3 lifetime, or tokio threading errors.

**Exact prompt to use:**
```
The Rust compilation failed with error above. Do not rewrite entire file. Analyze the borrow-checker or PyO3 lifetime error, explain exactly why it failed, and output ONLY the patched Rust function that fixes it. Maintain Zero-Fluff mandate.
```

**Quick access:** `python -c "from contingency_protocols import rust_failed; print(rust_failed('PASTE_ERROR_HERE'))"`

---

## 🔧 Contingency 2: Context Cut-Off

**When to use:** AI stops generating code mid-sentence due to output token limit.

**Exact prompt to use:**
```
You hit the output token limit. DO NOT apologize or explain. Resume outputting code snippet starting EXACTLY from the line: [paste last line here]
```

**Quick access:** `python -c "from contingency_protocols import context_cut; print(context_cut('PASTE_LAST_LINE_HERE'))"`

---

## 🔧 Contingency 3: Integration Mismatch

**When to use:** Python sends data that Rust doesn't expect, or type signatures don't match.

**Exact prompt to use:**
```
We have a Type bridging error between Python and Rust. The Python state is sending [paste Python print output], but the Rust PyO3 signature expects [paste Rust struct]. Write the exact serialization/deserialization patch needed in lib.rs to bridge these formats natively without slowing down execution.
```

**Quick access:** `python -c "from contingency_protocols import type_mismatch; print(type_mismatch('PASTE_PYTHON_OUTPUT', 'PASTE_RUST_SIGNATURE'))"`

---

## 🚨 Emergency Usage Examples

### Rust Borrow Checker Error:
```bash
# Build fails with borrow checker error
maturin build --release

# Copy error output and run:
python -c "from contingency_protocols import rust_failed; print(rust_failed('''PASTE_ERROR_HERE'''))"
```

### Context Cut-Off Mid-Function:
```bash
# AI stopped at line: fn process_data(&mut self) -> Result<() 
python -c "from contingency_protocols import context_cut; print(context_cut('fn process_data(&mut self) -> Result<()>'))"
```

### Type Mismatch Between Python/Rust:
```bash
# Python prints: {'agents': [{'name': 'coder', 'tools': []}]}
# Rust expects: struct DAGState { agents: Vec<AgentSpec> }

python -c "from contingency_protocols import type_mismatch; print(type_mismatch('{\"agents\": [{\"name\": \"coder\", \"tools\": []}]}', 'struct DAGState { agents: Vec<AgentSpec> }'))"
```

---

## 📋 Contingency Protocol Rules

1. **NEVER apologize** or explain in contingency responses
2. **ALWAYS use exact prompts** provided above
3. **NEVER rewrite entire files** - only patch specific functions
4. **MAINTAIN Zero-Fluff mandate** - minimal, targeted fixes
5. **LOG all contingency usage** automatically for debugging

---

## 🛠️  Common Error Patterns

### Rust Compilation:
- `error[E0499]`: borrow of moved value
- `error[E0505]`: cannot move out of borrowed content
- `error[E0621]`: mismatched types
- PyO3 lifetime errors with `&PyAny` or `&PyDict`
- Tokio `Send` trait bounds

### Context Cut-Off:
- Code ends mid-function
- Incomplete struct definitions
- Missing closing braces
- Truncated import statements

### Integration Mismatch:
- Python dict vs Rust struct
- Python list vs Rust Vec
- Python str vs Rust String
- Serde serialization issues

---

## ⚡ Production Deployment

The contingency protocols are automatically integrated into:
- `main.py` entry point
- CLI error handling
- Build system monitoring
- Runtime error detection

**Status:** PRODUCTION READY
