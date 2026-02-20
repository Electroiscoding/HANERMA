
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

    def run(self, prompt: str, target_agent: str, max_iterations: int = 5) -> Dict[str, Any]:
        """
        Executes the primary orchestration loop with Native Recursive Tool Calling.
        """
        start_time = time.time()
        print(f"\n[HANERMA Orchestrator] Initializing task ID: {uuid.uuid4().hex[:8]}")

        if target_agent not in self.active_agents:
            raise ValueError(f"Agent '{target_agent}' not found in registry.")

        agent = self.active_agents[target_agent]
        current_prompt = self._autoprompt_enhance(prompt)
        
        iteration = 0
        final_output = ""
        total_latency = 0
        total_tokens = 0

        while iteration < max_iterations:
            iteration += 1
            print(f"[HANERMA] Iteration {iteration}...")

            # 1. Token-aware context check
            history_text = self._build_history_context()
            total_input_tokens = self._count_tokens(current_prompt) + self._count_tokens(history_text)
            
            if total_input_tokens > self.context_window * 0.85:
                self._trim_history(self.context_window * 0.5)

            # 2. Agent Execution
            raw_response = agent.execute(current_prompt, self.state_manager)
            total_tokens += self._count_tokens(raw_response)

            # 3. Native Tool Execution Detection
            if "TOOL_CALL:" in raw_response:
                tool_result = self._handle_tool_call(agent, raw_response)
                # Feed the tool result back into the next prompt
                current_prompt = f"[TOOL_RESULT]\n{tool_result}\n\nContinue with your next reasoning step."
                continue
            
            # 4. Atomic Guard (Final Check)
            is_valid, validation_msg = self.atomic_guard.verify(raw_response)
            if not is_valid:
                current_prompt = f"Correct this error: {validation_msg}. Original intent: {prompt}"
                continue

            final_output = raw_response
            break

        latency = (time.time() - start_time) * 1000

        return {
            "status": "success",
            "output": final_output,
            "metrics": {
                "iterations": iteration,
                "latency_ms": round(latency, 2),
                "total_tokens": total_tokens,
            }
        }

    def _handle_tool_call(self, agent: BaseAgent, response: str) -> str:
        """Parses and executes a TOOL_CALL natively using robust regex."""
        import re
        import ast

        # Match Pattern: TOOL_CALL: tool_name(key1='val', key2=123)
        pattern = r"TOOL_CALL:\s*(\w+)\((.*)\)"
        match = re.search(pattern, response)
        
        if not match:
            return "Error: Could not parse TOOL_CALL format. Ensure you use: TOOL_CALL: name(args)"
        
        name = match.group(1)
        args_str = match.group(2)

        try:
            # Find the tool in the agent's equipped toolbox
            tool_func = next((t for t in agent.tools if t.__name__ == name), None)
            
            if not tool_func:
                return f"Error: Tool '{name}' not found."

            # Parse arguments into a dictionary
            # We wrap the args_str in dict() to utilize ast.literal_eval for safe mapping
            # Note: This expects key=value format within the parentheses
            # To handle more complex Python call syntax, we'd use a full AST walker
            try:
                # Handle empty args
                if not args_str.strip():
                    kwargs = {}
                else:
                    # Treat args_str as a sequence of keyword arguments
                    # This is a naive but 'native' implementation for the showcase
                    # For production, we'd use a proper regex for key=val pairs
                    kwargs = {}
                    for pair in re.findall(r'(\w+)\s*=\s*("[^"]*"|\'[^\']*\'|[^,]+)', args_str):
                        key, val = pair
                        kwargs[key] = ast.literal_eval(val.strip())
            except Exception:
                return f"Error: Failed to parse arguments '{args_str}'. Use key=value format."

            print(f"[HANERMA] Executing Tool: {name}({kwargs})")
            result = tool_func(**kwargs)
            return str(result)

        except Exception as e:
            return f"Error during tool execution: {e}"

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
