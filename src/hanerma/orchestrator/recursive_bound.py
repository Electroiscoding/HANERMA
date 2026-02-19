from typing import Dict, Any, List
# from hanerma.orchestrator.engine import HANERMAOrchestrator #(Recursive import loop fix)

class RecursiveBound:
    """
    Limits the number of times an agent can self-correct or delegate.
    Critically, this prevents infinite billing loops if a model gets stuck.
    """
    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        self.call_stack: List[str] = []

    def enter_frame(self, agent_name: str, task_hash: str) -> bool:
        """Pushes a new execution frame."""
        self.call_stack.append(f"{agent_name}::{task_hash}")
        
        if len(self.call_stack) > self.max_depth:
            print(f"[RecursiveBound] Stack Overflow detected! {len(self.call_stack)} > {self.max_depth}")
            # Force-pop to unwind the stack
            self.call_stack.pop()
            return False 
            
        print(f"[Orchestrator] Entering recursion depth: {len(self.call_stack)}")
        return True

    def exit_frame(self):
        if self.call_stack:
            self.call_stack.pop()
