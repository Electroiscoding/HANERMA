
from hanerma.tools.code_sandbox import NativeCodeSandbox

sandbox = NativeCodeSandbox()

print("="*60)
print(" 🏁 SUPER-SANDBOX NATIVE CAPABILITIES")
print("="*60)

# 1. REPL Style (No prints, just an expression)
print("\n[SCENARIO 1] REPL-Style Expression Return")
code1 = """
a = 50
b = 50
a + b
"""
print(f"CODE:\n{code1.strip()}")
print(f"RESULT:\n{sandbox.execute_code(code1)}")

# 2. STDERR + Value Return
print("\n[SCENARIO 2] Combined Stdout, Stderr, and Return")
code2 = """
import sys
print("Logic starting...")
sys.stderr.write("Warn: Complexity high.")
math_result = (100 * 2) / 4
math_result
"""
print(f"CODE:\n{code2.strip()}")
print(f"RESULT:\n{sandbox.execute_code(code2)}")

# 3. Scope Persistence
print("\n[SCENARIO 3] Scope Persistence (Using 'math_result' from previous call)")
code3 = "f'Previous result was {math_result}'"
print(f"CODE: {code3}")
print(f"RESULT: {sandbox.execute_code(code3)}")

print("\n" + "="*60)
