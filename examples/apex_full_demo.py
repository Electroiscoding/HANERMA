from hanerma.interface.minimalist import quick_flow, create_agent
from hanerma.orchestrator.engine import HANERMAOrchestrator
import time
import os

# Set token for cloud demo
# HF_TOKEN should be set in environment or .env
if not os.getenv("HF_TOKEN"):
    print("[Warning] HF_TOKEN not found. Cloud demos may fail.")

def demo_simple():
    print("\n--- [LEVEL 1: SIMPLE FLOW] ---")
    def get_time():
        return f"The current time is {time.ctime()}."
    
    timer = create_agent("Timer", tools=[get_time])
    res = quick_flow("What time is it?", agents=[timer])
    print(f"RESULT: {res}")

def demo_qwen3_real_task():
    print("\n--- [LEVEL 4: REAL-WORLD TASK - QWEN3 CLOUD] ---")
    # Use the specific Qwen3 model via HF together provider
    model_id = "Qwen/Qwen3-Coder-Next-FP8:together"
    
    def search_expert_docs(query: str = "SymbolicReasoner"):
        """Searches the HANERMA documentation."""
        return f"Documentation for '{query}': Use HANERMA SymbolicReasoner to catch logical drift."

    def git_commit_changes(message: str):
        """Commits changes to the git repository."""
        return f"Successfully committed: {message}"

    dev_agent = create_agent(
        "ApexDev", 
        role="Senior Engineer", 
        system_prompt="You are an expert coder. Solve the task using tools.",
        tools=[search_expert_docs, git_commit_changes],
        model=model_id
    )
    
    print(f"Connecting to {model_id}...")
    task = "Research how to use SymbolicReasoner and then commit the findings to git."
    
    # We use the full Orchestrator to see Parallelism and Risk checks
    orch = HANERMAOrchestrator(model=model_id)
    orch.register_agent(dev_agent)
    
    result = orch.run(task, target_agent="ApexDev")
    print(f"\nQWEN3 OUTPUT:\n{result['output']}")
    print(f"TRACING ID: {orch.trace_id}")

if __name__ == "__main__":
    import os
    if os.path.exists("hanerma_state.db"):
        try: os.remove("hanerma_state.db")
        except: pass
    demo_simple()
    time.sleep(1)
    demo_qwen3_real_task()
    print("\nDemo complete. See 'hanerma viz' dashboard for live trace.")
