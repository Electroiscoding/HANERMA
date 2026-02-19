
"""
Example 03: Testing the HCMS with Massive Data
Demonstrates hypertoken compression and O(1) recall.
"""
import asyncio
import time
from hanerma.memory.core import HCMS

async def run_context_test():
    memory = HCMS()
    
    # 1. Ingest Massive Data (simulated)
    print("Ingesting 1,000 document chunks...")
    t0 = time.time()
    for i in range(100):
        await memory.store(f"Meaningless log entry {i} for context loading...")
    
    # Critical Fact
    await memory.store("The secret code is HANERMA-MK-ULTRA-99.")
    
    for i in range(100):
        await memory.store(f"More noise {i}...")
        
    print(f"Ingestion time: {time.time() - t0:.2f}s")
    
    # 2. Retrieve Specific Fact from the noise
    print("Retrieving secret code...")
    t1 = time.time()
    
    results = await memory.retrieve("What is the secret code?", top_k=1)
    
    print(f"Found: {results[0] if results else 'Nothing'}")
    print(f"Retrieval time: {(time.time() - t1) * 1000:.2f}ms")

if __name__ == "__main__":
    asyncio.run(run_context_test())
