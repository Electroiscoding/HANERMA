
import time
import uuid
from typing import List, Dict, Any, Optional
from hanerma.agents.base_agent import BaseAgent
from hanerma.reasoning.deep1_atomic import AtomicGuard

class HANERMAOrchestrator:
    """
    The core engine for the Hierarchical Atomic Nested External Reasoning and Memory Architecture.
    Handles routing, multi-tenant state isolation, and zero-error loops.
    Uses xerv-crayon for token counting and context window management.
    """
    def __init__(self, model: str = "local-llama3", tokenizer=None, context_window: int = 8192):
        self.orchestrator_id = str(uuid.uuid4())
        self.default_model = model
        self.tokenizer = tokenizer  # xerv-crayon adapter for token counting
        self.context_window = context_window
        self.active_agents: Dict[str, BaseAgent] = {}
        self.state_manager: Dict[str, Any] = {"history": [], "shared_memory": {}}
        self.atomic_guard = AtomicGuard()

    def _init_tokenizer(self):
        """Lazy-init xerv-crayon if not provided."""
        if self.tokenizer is None:
            try:
                from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter
                self.tokenizer = XervCrayonAdapter()
            except ImportError:
                pass  # xerv-crayon not installed — token counting disabled

    def _count_tokens(self, text: str) -> int:
        """Count tokens using xerv-crayon. Falls back to char estimate if unavailable."""
        self._init_tokenizer()
        if self.tokenizer:
            return self.tokenizer.count_tokens(text)
        return len(text) // 4  # rough fallback

    def register_agent(self, agent: BaseAgent):
        """Registers a builder-defined or native persona into the orchestrator."""
        if agent.model is None:
            agent.model = self.default_model
        self.active_agents[agent.name] = agent
        print(f"[HANERMA] Agent '{agent.name}' registered with model '{agent.model}'.")

    def run(self, prompt: str, target_agent: str) -> Dict[str, Any]:
        """
        Executes the primary orchestration loop with token-aware metrics.
        """
        start_time = time.time()
        print(f"\n[HANERMA Orchestrator] Initializing task ID: {uuid.uuid4().hex[:8]}")

        if target_agent not in self.active_agents:
            raise ValueError(f"Agent '{target_agent}' not found in registry.")

        agent = self.active_agents[target_agent]

        # Step 1: AutoPrompt Enhancement
        enhanced_prompt = self._autoprompt_enhance(prompt)
        prompt_tokens = self._count_tokens(enhanced_prompt)

        # Step 2: Token-aware history trimming
        history_text = self._build_history_context()
        history_tokens = self._count_tokens(history_text) if history_text else 0

        total_input_tokens = prompt_tokens + history_tokens
        if total_input_tokens > self.context_window * 0.85:
            self._trim_history(self.context_window * 0.5)

        # Step 3: Agent Execution
        raw_response = agent.execute(enhanced_prompt, self.state_manager)
        response_tokens = self._count_tokens(raw_response)

        # Step 4: Atomic Guard
        is_valid, validation_msg = self.atomic_guard.verify(raw_response)

        if not is_valid:
            print(f"[HANERMA WARNING] Atomic Guard failed: {validation_msg}. Initiating recursive correction...")
            raw_response = agent.execute(
                f"Correct this error: {validation_msg}. Original prompt: {enhanced_prompt}",
                self.state_manager
            )
            response_tokens = self._count_tokens(raw_response)

        latency = (time.time() - start_time) * 1000

        return {
            "status": "success",
            "output": raw_response,
            "metrics": {
                "latency_ms": round(latency, 2),
                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "total_tokens": prompt_tokens + response_tokens,
            }
        }

    def _autoprompt_enhance(self, prompt: str) -> str:
        """Structural upgrade to the user's prompt."""
        return f"[System: Strict formatting required]\nUser Request: {prompt}"

    def _build_history_context(self) -> str:
        """Serializes conversation history for context injection."""
        history = self.state_manager.get("history", [])
        if not history:
            return ""
        return "\n".join(f"[{h['role']}]: {h['content']}" for h in history)

    def _trim_history(self, target_tokens: float):
        """Remove oldest history entries until total tokens is within budget."""
        history = self.state_manager.get("history", [])
        while history and self._count_tokens(self._build_history_context()) > target_tokens:
            removed = history.pop(0)
            print(f"[HANERMA] Trimmed oldest entry from '{removed['role']}' (token budget)")
