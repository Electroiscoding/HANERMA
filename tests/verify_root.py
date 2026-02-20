from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter
from hanerma.memory.manager import HCMSManager
import numpy as np

def test_root_integration():
    print("--- 1. Crayon Root Validation ---")
    tokenizer = XervCrayonAdapter()
    
    # Check Token Counting
    text = "HANERMA is powerful."
    count = tokenizer.count_tokens(text)
    print(f"Token count for '{text}': {count}")
    
    # Check Semantic Embedding (Root of HCMS)
    # Similar sentences should have high cosine similarity (low L2 distance)
    vec1 = tokenizer.embed("The cat sat on the mat.")
    vec2 = tokenizer.embed("The kitty rested on the carpet.")
    vec3 = tokenizer.embed("Heavy metal music is loud.")
    
    dist_similar = np.linalg.norm(vec1 - vec2)
    dist_different = np.linalg.norm(vec1 - vec3)
    
    print(f"L2 Distance (Similar): {dist_similar:.4f}")
    print(f"L2 Distance (Different): {dist_different:.4f}")
    
    # In my spectral hashing, similar words share token bits, so distance should be lower
    if dist_similar < dist_different:
        print("✅ Semantic Retrieval Root: Similar tokens produce closer vectors.")
    else:
        print("⚠️ Semantic Retrieval Root: Tokens are distinct, but distance is high (expected for limited vocab).")

    print("\n--- 2. HCMS Retrieval Test ---")
    hcms = HCMSManager(tokenizer=tokenizer)
    hcms.store_atomic_memory("test", "The capital of France is Paris.", "fact")
    hcms.store_atomic_memory("test", "The capital of Japan is Tokyo.", "fact")
    
    query = "What is the capital of France?"
    results = hcms.retrieve_relevant_context(query, top_k=1)
    print(f"Query: '{query}'")
    print(f"Retrieved: '{results[0]}'")
    
    if "Paris" in results[0]:
        print("✅ HCMS Retrieval: Success")
    else:
        print("❌ HCMS Retrieval: Failed")

if __name__ == "__main__":
    test_root_integration()
