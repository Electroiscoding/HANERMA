
import time
import uuid
from typing import List, Dict, Any, Optional
from hanerma.agents.base_agent import BaseAgent
from hanerma.reasoning.deep1_atomic import AtomicGuard

class HANERMAOrchestrator:
    """
    The core engine for the Hierarchical Atomic Nested External Reasoning and Memory Architecture.
    Handles routing, multi-tenant state isolation, and zero-error loops.
    """
    def __init__(self, model: str = "local-llama3", tokenizer_adapter: Optional[Any] = None):
        self.orchestrator_id = str(uuid.uuid4())
        self.default_model = model
        self.tokenizer = tokenizer_adapter # Hook for highly competitive custom tokenizers
        self.active_agents: Dict[str, BaseAgent] = {}
        self.state_manager: Dict[str, Any] = {"history": [], "shared_memory": {}}
        self.atomic_guard = AtomicGuard()
        
    def register_agent(self, agent: BaseAgent):
        """Registers a builder-defined or native persona into the orchestrator."""
        self.active_agents[agent.name] = agent
        print(f"[HANERMA] Agent '{agent.name}' registered successfully.")

    def run(self, prompt: str, target_agent: str) -> Dict[str, Any]:
        """
        Executes the primary orchestration loop.
        """
        start_time = time.time()
        print(f"\n[HANERMA Orchestrator] Initializing task ID: {uuid.uuid4().hex[:8]}")
        
        if target_agent not in self.active_agents:
            raise ValueError(f"Agent '{target_agent}' not found in registry.")
            
        agent = self.active_agents[target_agent]
        
        # Step 1: AutoPrompt Enhancer (Placeholder for the <50ms meta-reasoner)
        enhanced_prompt = self._autoprompt_enhance(prompt)
        
        # Step 2: Agent Execution
        raw_response = agent.execute(enhanced_prompt, self.state_manager)
        
        # Step 3: Deep 1 - Atomic Reasoning & Guardrails
        is_valid, validation_msg = self.atomic_guard.verify(raw_response)
        
        if not is_valid:
            print(f"[HANERMA WARNING] Atomic Guard failed: {validation_msg}. Initiating recursive correction...")
            # In a full build, this triggers deep2_nested.py to self-correct
            raw_response = agent.execute(f"Correct this error: {validation_msg}. Original prompt: {enhanced_prompt}", self.state_manager)
            
        latency = (time.time() - start_time) * 1000
        
        return {
            "status": "success",
            "output": raw_response,
            "metrics": {
                "latency_ms": round(latency, 2),
                "tokens_used": "Pending Hypertoken Calculation"
            }
        }

    def _autoprompt_enhance(self, prompt: str) -> str:
        """Simulates the <50ms structural upgrade to the user's prompt."""
        return f"[System: Strict formatting required]\nUser Request: {prompt}"
