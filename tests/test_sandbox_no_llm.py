
import sys
import os

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from hanerma.tools.code_sandbox import NativeCodeSandbox

def run_pure_sandbox_test():
    print("="*60)
    print(" 🛡️  HANERMA NATIVE SANDBOX: BARE-METAL UNIT TEST")
    print("="*60)

    sandbox = NativeCodeSandbox()

    # TEST 1: Basic Math & Output
    print("\n[TEST 1] Basic Execution")
    code_1 = """
def calculate_factorial(n):
    if n == 0: return 1
    return n * calculate_factorial(n-1)

print(f"Factorial of 5: {calculate_factorial(5)}")
"""
    result_1 = sandbox.execute_code(code_1)
    print(f"CODE:\n{code_1.strip()}")
    print(f"OUTPUT: {result_1.strip()}")

    # TEST 2: State Persistence (Persistent Namespace)
    print("\n[TEST 2] State Persistence (Defining variables for the next call)")
    code_2 = "SHARED_VARIABLE = 42\nprint('Variable set.')"
    sandbox.execute_code(code_2)
    
    code_3 = "print(f'Retrieved from shared namespace: {SHARED_VARIABLE}')"
    result_3 = sandbox.execute_code(code_3)
    print(f"CODE:\n{code_3.strip()}")
    print(f"OUTPUT: {result_3.strip()}")

    # TEST 3: Error Handling (Exceptions)
    print("\n[TEST 3] Native Exception Handling")
    code_4 = "x = 1 / 0  # Trigger DivisionByZero"
    result_4 = sandbox.execute_code(code_4)
    print(f"CODE:\n{code_4.strip()}")
    print(f"OUTPUT:\n{result_4.strip()}")

    # TEST 4: Complexity Test (Imports)
    print("\n[TEST 4] Advanced Logic (Imports & List Comprehensions)")
    code_5 = """
import math
primes = [x for x in range(2, 50) if all(x % d != 0 for d in range(2, int(math.sqrt(x)) + 1))]
print(f"Primes up to 50: {primes}")
"""
    result_5 = sandbox.execute_code(code_5)
    print(f"CODE:\n{code_5.strip()}")
    print(f"OUTPUT: {result_5.strip()}")

    print("\n" + "="*60)
    print(" ✅ SANDBOX UNIT TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_pure_sandbox_test()
