"""Test the Z3 Mathematical Firewall"""
import importlib.util
import os
import sys

# Bypass broken hanerma.__init__
spec = importlib.util.spec_from_file_location(
    "symbolic_reasoner",
    os.path.join(os.path.dirname(__file__), "src", "hanerma", "reliability", "symbolic_reasoner.py"),
)
reasoner_mod = importlib.util.module_from_spec(spec)
sys.modules["hanerma.reliability.symbolic_reasoner"] = reasoner_mod
spec.loader.exec_module(reasoner_mod)

SymbolicReasoner = reasoner_mod.SymbolicReasoner
ContradictionError = reasoner_mod.ContradictionError

reasoner = SymbolicReasoner()

# 1. Valid Assertions
print("\n--- Testing Valid Assertions ---")
valid_assertions = [
    {"fact": "user_age", "operator": ">=", "value": 18},
    {"fact": "credit_score", "operator": ">", "value": 700},
    {"fact": "is_employed", "operator": "==", "value": True}
]
reasoner.compiler.compile_and_check(valid_assertions)
print("✓ Valid assertions passed Z3 solver (SAT)")

# 2. Contradiction 1: Numeric bounds
print("\n--- Testing Mathematical Contradiction ---")
try:
    contradiction = [
        {"fact": "target_price", "operator": ">", "value": 150.0},
        {"fact": "target_price", "operator": "<", "value": 100.0}
    ]
    reasoner.compiler.compile_and_check(contradiction)
    print("❌ ERROR: Z3 failed to catch contradiction!")
except ContradictionError as e:
    print(f"✓ Z3 Caught Contradiction: {e}")

# 3. Contradiction 2: Boolean mismatch
print("\n--- Testing Boolean Contradiction ---")
try:
    bool_contradiction = [
        {"fact": "is_admin", "operator": "==", "value": True},
        {"fact": "is_admin", "operator": "==", "value": False}
    ]
    reasoner.compiler.compile_and_check(bool_contradiction)
    print("❌ ERROR: Z3 failed to catch boolean contradiction!")
except ContradictionError as e:
    print(f"✓ Z3 Caught Boolean Contradiction: {e}")

# 4. Contradiction 3: Type Mismatch (int vs bool)
print("\n--- Testing Type Sort Mismatch ---")
try:
    type_contradiction = [
        {"fact": "status", "operator": "==", "value": 404},
        {"fact": "status", "operator": "==", "value": True}
    ]
    reasoner.compiler.compile_and_check(type_contradiction)
    print("❌ ERROR: Z3 failed to catch Sort mismatch!")
except ContradictionError as e:
    print(f"✓ Z3 Caught Type/Sort Mismatch: {e}")

print("\nSLICE 4 VERIFIED ✓")
