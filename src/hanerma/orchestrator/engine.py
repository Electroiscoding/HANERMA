
import time
import uuid
from typing import List, Dict, Any, Optional
from hanerma.agents.base_agent import BaseAgent
from hanerma.reasoning.deep1_atomic import AtomicGuard

from hanerma.state.transactional_bus import TransactionalEventBus
from hanerma.reliability.risk_engine import FailurePredictor
from hanerma.reliability.symbolic_reasoner import SymbolicReasoner
from hanerma.routing.model_router import ModelRouter
from hanerma.optimization.ast_analyzer import ParallelASTAnalyzer

class HANERMAOrchestrator:
    """
    The core engine for the Hierarchical Atomic Nested External Reasoning and Memory Architecture.
    Apex Edition: Zero-friction, self-healing, and mathematically grounded.
    """
    def __init__(self, model: str = "auto", tokenizer=None, context_window: int = 128000):
        self.orchestrator_id = str(uuid.uuid4())
        self.router = ModelRouter()
        self.default_model = self.router.route_request("", 0) if model == "auto" else model
        self.tokenizer = tokenizer
        self.context_window = context_window
        self.active_agents: Dict[str, BaseAgent] = {}
        self.state_manager: Dict[str, Any] = {"history": [], "shared_memory": {}}
        
        # Apex Modules
        self.bus = TransactionalEventBus()
        self.risk_engine = FailurePredictor()
        self.symbolic_reasoner = SymbolicReasoner()
        self.ast_analyzer = ParallelASTAnalyzer()
        self.trace_id = str(uuid.uuid4())
        self.step_index = 0

    def register_agent(self, agent: BaseAgent):
        """Registers an agent into the orchestrator."""
        if agent.model is None:
            agent.model = self.default_model
        self.active_agents[agent.name] = agent
        print(f"[HANERMA] Agent '{agent.name}' registered.")

    def run(self, prompt: str, target_agent: str, max_iterations: int = 5) -> Dict[str, Any]:
        """
        Executes with Predictive Failure Avoidance and Transactional Persistence.
        """
        start_time = time.time()
        
        # 0. Risk Scoring
        risk = self.risk_engine.compute_risk(prompt, self.default_model, 0)
        if risk["action"] == "block":
            return {"status": "error", "message": f"Task blocked by Risk Engine: {risk['reasons']}"}

        # 1. Transactional Start
        self.bus.record_step(self.trace_id, self.step_index, "task_start", {"prompt": prompt})
        self.step_index += 1

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
            
            # 1. Agent Execution
            self.bus.record_step(self.trace_id, self.step_index, "agent_thinking", {"agent": agent.name, "iteration": iteration})
            self.step_index += 1

            raw_response = agent.execute(current_prompt, self.state_manager)
            total_tokens += self._count_tokens(raw_response)
            
            self.bus.record_step(self.trace_id, self.step_index, "agent_response", {"agent": agent.name, "response_preview": raw_response[:150]})
            self.step_index += 1

            # 2. Native Tool Execution Detection (Case Insensitive)
            if "TOOL_CALL" in raw_response.upper():
                self.bus.record_step(self.trace_id, self.step_index, "tool_execution", {"agent": agent.name, "raw": raw_response})
                self.step_index += 1
                
                tool_result = self._handle_tool_call(agent, raw_response)
                
                self.bus.record_step(self.trace_id, self.step_index, "tool_result", {"result": str(tool_result)[:150]})
                self.step_index += 1
                
                # Feed the tool result back into the next prompt
                current_prompt = f"[TOOL_RESULT]\n{tool_result}\n\nContinue with your next reasoning step."
                continue
            
            # 3. Symbolic Reasoner (Deterministic Final Check)
            self.bus.record_step(self.trace_id, self.step_index, "symbolic_verification", {"facts": len(self.state_manager.get("shared_memory", {}).get("facts", []))})
            self.step_index += 1

            is_valid, validation_msg = self.symbolic_reasoner.verify_consistency(raw_response, self.state_manager.get("shared_memory", {}).get("facts", []))
            
            if not is_valid:
                self.bus.record_step(self.trace_id, self.step_index, "verification_failed", {"msg": validation_msg})
                self.step_index += 1
                current_prompt = f"Correct this logical error: {validation_msg}. Original intent: {prompt}"
                continue

            self.bus.record_step(self.trace_id, self.step_index, "task_complete", {"output": raw_response[:150]})
            self.step_index += 1
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

    def _init_tokenizer(self):
        """Lazy-init xerv-crayon if not provided."""
        if self.tokenizer is None:
            try:
                from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter
                self.tokenizer = XervCrayonAdapter()
            except ImportError:
                pass 

    def _count_tokens(self, text: str) -> int:
        """Count tokens using xerv-crayon. Falls back to char estimate if unavailable."""
        self._init_tokenizer()
        if self.tokenizer:
            # Check if tokenizer has count_tokens or requires encoding
            if hasattr(self.tokenizer, 'count_tokens'):
                return self.tokenizer.count_tokens(text)
        return len(text) // 4 

    def _build_history_context(self) -> str:
        """Serializes conversation history for context injection."""
        history = self.state_manager.get("history", [])
        if not history:
            return ""
        return "\n".join(f"[{h['role']}]: {h['content']}" for h in history)

    def _autoprompt_enhance(self, prompt: str) -> str:
        """Structural upgrade to the user's prompt."""
        return f"[System: Strict formatting required]\nUser Request: {prompt}"

    def _handle_tool_call(self, agent: BaseAgent, response: str) -> str:
        """Parses and executes a TOOL_CALL natively."""
        import re
        # Robust case-insensitive search
        pattern = r"TOOL_CALL:?\s*(\w+)\((.*)\)"
        match = re.search(pattern, response, re.IGNORECASE)
        if not match: return "Error Parsing Tool Call"
        name, args_str = match.group(1), match.group(2)
        tool_func = next((t for t in agent.tools if t.__name__ == name), None)
        if not tool_func: return f"Tool {name} Not Found"
        
        kwargs = {}
        # Extract named arguments: key="val" or key='val' or key=val
        for pair in re.findall(r'(\w+)\s*=\s*(("[^"]*")|(\'[^\']*\')|([^, \n\)]+))', args_str):
            key = pair[0]
            val = pair[1].strip("'\"")
            kwargs[key] = val
            
        print(f"[HANERMA] Executing: {name}({kwargs})")
        try:
            return str(tool_func(**kwargs))
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    def _trim_history(self, target_tokens: float):
        """Remove oldest history entries until total tokens is within budget."""
        history = self.state_manager.get("history", [])
        while history and self._count_tokens(self._build_history_context()) > target_tokens:
            removed = history.pop(0)
            print(f"[HANERMA] Trimmed oldest entry from '{removed['role']}' (token budget)")
