#!/usr/bin/env python3
"""
HANERMA Production Contingency System Test

Tests all three contingency protocols to ensure they're ready for production use.
"""

import sys
import os

def test_contingency_system():
    """Test the complete contingency system."""
    print("🔧 Testing HANERMA Contingency Protocols")
    print("=" * 50)
    
    # Test 1: Rust compilation failure
    print("\n--- Test 1: Rust Compilation Failure ---")
    try:
        from contingency_protocols import rust_failed
        
        test_error = "error[E0499]: borrow of moved value: `self.data`"
        response = rust_failed(test_error)
        
        if "Do not rewrite entire file" in response and "Zero-Fluff mandate" in response:
            print("  ✓ Rust compilation contingency works")
        else:
            print("  ❌ Rust compilation contingency failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Test 2: Context cut-off
    print("\n--- Test 2: Context Cut-Off ---")
    try:
        from contingency_protocols import context_cut
        
        test_line = "fn process_data(&mut self) -> Result<()"
        response = context_cut(test_line)
        
        if "output token limit" in response and "DO NOT apologize" in response:
            print("  ✓ Context cut-off contingency works")
        else:
            print("  ❌ Context cut-off contingency failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Test 3: Integration mismatch
    print("\n--- Test 3: Integration Mismatch ---")
    try:
        from contingency_protocols import type_mismatch
        
        python_state = "{'agents': [{'name': 'coder', 'tools': []}]}"
        rust_signature = "struct DAGState { agents: Vec<AgentSpec> }"
        response = type_mismatch(python_state, rust_signature)
        
        if "Type bridging error" in response and "serialization/deserialization patch" in response:
            print("  ✓ Integration mismatch contingency works")
        else:
            print("  ❌ Integration mismatch contingency failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Test 4: Contingency files exist
    print("\n--- Test 4: File System Check ---")
    
    required_files = [
        "contingency_protocols.py",
        "CONTINGENCY_README.md"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"  ❌ Missing file: {file}")
            return False
    
    print("  ✓ All contingency files present")
    
    # Test 5: Quick access functions
    print("\n--- Test 5: Quick Access Functions ---")
    try:
        from contingency_protocols import contingency
        
        # Test failure detection
        rust_error = "error[E0505]: cannot move out of borrowed content"
        failure_type = contingency.detect_failure_type(rust_error)
        
        if failure_type == "rust_compilation":
            print("  ✓ Failure detection works")
        else:
            print(f"  ❌ Wrong failure type detected: {failure_type}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    print("\n✅ All contingency protocols are PRODUCTION READY!")
    print("\n🚀 Emergency Usage:")
    print("   rust_failed('error_output') - Rust compilation fixes")
    print("   context_cut('last_line') - Resume from cut-off")
    print("   type_mismatch('python', 'rust') - Fix type bridges")
    
    return True

if __name__ == "__main__":
    success = test_contingency_system()
    sys.exit(0 if success else 1)
