import asyncio
from typing import List, Callable, Any

class DAGRouter:
    """
    Parallel execution engine for the orchestrator.
    If Deep 3 External Reasoning requires Web Search, Code Execution, and DB Query,
    this routes them concurrently rather than sequentially to hit the <100ms benchmark.
    """
    def __init__(self):
        self.tasks: List[asyncio.Task] = []

    async def execute_parallel(self, operations: List[Callable[[], Any]]) -> List[Any]:
        """Runs multiple agent tasks at the exact same time."""
        print(f"[Graph Router] Spawning {len(operations)} parallel execution threads.")
        
        # Wrap operations in asyncio tasks
        self.tasks = [asyncio.create_task(op()) for op in operations]
        
        # Await all concurrently and return aggregated results
        results = await asyncio.gather(*self.tasks, return_exceptions=True)
        return results
