
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
from hanerma.autoprompt.enhancer import AutoPromptEnhancer

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
        self.step_index = 0
        
        # Apex Modules
        self.enhancer = AutoPromptEnhancer()
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

    async def run(self, prompt: str, target_agent: str, max_iterations: int = 5) -> Dict[str, Any]:
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
        current_prompt = await self._autoprompt_enhance(prompt)
        
        iteration = 0
        final_output = ""
        total_tokens = 0

        while iteration < max_iterations:
            iteration += 1
            print(f"[HANERMA] Iteration {iteration}...")
            
            # 1. Build Context-Aware Prompt
            history_text = self._build_history_context()
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            system_meta = (
                f"[SYSTEM_METADATA]\n"
                f"Global Time: {current_time}\n"
                f"Protocol: Apex/V4 Stable\n"
                f"Model Context: {self.default_model}\n"
                "[System: Maintain strictly verified reasoning. All tool calls must be explicit.]"
            )
            iteration_context = f"\n\n[Current Task]: {prompt}\n[Iteration]: {iteration}/{max_iterations}"
            
            # Combine history + current state
            full_context_prompt = f"{system_meta}\n{history_text}\n{iteration_context}\n\n{current_prompt}"
            
            # 2. Agent Execution
            self.bus.record_step(self.trace_id, self.step_index, "agent_thinking", {"agent": agent.name, "iteration": iteration})
            self.step_index += 1

            raw_response = await agent.execute(full_context_prompt, self.state_manager)
            total_tokens += self._count_tokens(raw_response)
            
            self.bus.record_step(self.trace_id, self.step_index, "agent_response", {"agent": agent.name, "response_preview": raw_response[:150]})
            self.step_index += 1

            # 3. Native Tool Execution Detection (Case Insensitive)
            if "TOOL_CALL" in raw_response.upper():
                self.bus.record_step(self.trace_id, self.step_index, "tool_execution", {"agent": agent.name, "raw": raw_response})
                self.step_index += 1
                
                tool_result = await self._handle_tool_call(agent, raw_response)
                
                self.bus.record_step(self.trace_id, self.step_index, "tool_result", {"result": str(tool_result)[:250]})
                self.step_index += 1
                
                # Append the tool result to history so the next turn sees what happened
                self.state_manager["history"].append({"role": "tool_output", "content": f"Result from tool: {tool_result}"})
                
                # Feed the tool result back into the next step
                current_prompt = f"[TOOL_RESULT]\n{tool_result}\n\nEvaluate this result and proceed to the next step of the task."
                continue

            # 3.5 Native Agent Handoff (DELEGATE)
            if "DELEGATE:" in raw_response.upper():
                import re
                target_match = re.search(r"DELEGATE:\s*(\w+)", raw_response, re.IGNORECASE)
                if target_match:
                    new_agent_name = target_match.group(1)
                    if new_agent_name in self.active_agents:
                        old_agent_name = agent.name
                        print(f"[HANERMA] Handoff: {old_agent_name} ➔ {new_agent_name}")
                        agent = self.active_agents[new_agent_name]
                        self.bus.record_step(self.trace_id, self.step_index, "agent_handoff", {"from": old_agent_name, "to": new_agent_name})
                        self.step_index += 1
                        current_prompt = "You have been delegated this task. Review the context and complete the next step."
                        continue
            
            # 4. Symbolic Reasoner (Deterministic Final Check)
            self.bus.record_step(self.trace_id, self.step_index, "symbolic_verification", {"facts": len(self.state_manager.get("shared_memory", {}).get("facts", []))})
            self.step_index += 1

            is_valid, validation_msg = self.symbolic_reasoner.verify_consistency(raw_response, self.state_manager.get("shared_memory", {}).get("facts", []))
            
            if not is_valid:
                self.bus.record_step(self.trace_id, self.step_index, "verification_failed", {"msg": validation_msg})
                self.step_index += 1
                current_prompt = f"Correct this logical error: {validation_msg}. Original intent: {prompt}"
                # Add failure to history to prevent repeat errors
                self.state_manager["history"].append({"role": "system", "content": f"Verification failed: {validation_msg}"})
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

    async def _autoprompt_enhance(self, prompt: str) -> str:
        """Structural upgrade to the user's prompt."""
        return await self.enhancer.enhance(prompt)

    async def _handle_tool_call(self, agent: BaseAgent, response: str) -> str:
        """Parses and executes a TOOL_CALL natively with robust extraction."""
        import re
        # Support both TOOL_CALL: func(args) and TOOL_CALL func(args)
        pattern = r"TOOL_CALL:?\s*(\w+)\(([\s\S]*?)\)"
        match = re.search(pattern, response, re.IGNORECASE)
        if not match: return "Error: Tool call syntax not recognized. Use TOOL_CALL: tool_name(key='val')"
        
        name, args_str = match.group(1), match.group(2)
        print(f"[DEBUG] Raw Tool Args: {args_str}")
        tool_func = next((t for t in agent.tools if t.__name__ == name), None)
        if not tool_func: return f"Error: Tool '{name}' not available to this agent."
        
        kwargs = {}
        # Advanced extraction for multi-line and code-heavy arguments
        arg_pattern = r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^, \n\)]+)'
        for key, val in re.findall(arg_pattern, args_str, re.DOTALL):
            cleaned_val = val.strip()
            if (cleaned_val.startswith('"') and cleaned_val.endswith('"')) or \
               (cleaned_val.startswith("'") and cleaned_val.endswith("'")):
                cleaned_val = cleaned_val[1:-1].replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
            kwargs[key] = cleaned_val
            
        print(f"[HANERMA] Dispatching: {name} (Keys: {list(kwargs.keys())})")
        try:
            import inspect
            sig = inspect.signature(tool_func)
            has_var_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            
            if has_var_kwargs:
                valid_kwargs = kwargs
            else:
                valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
            
            # Execute tool (Handle both Sync and Async)
            if inspect.iscoroutinefunction(tool_func):
                result = await tool_func(**valid_kwargs)
            else:
                result = tool_func(**valid_kwargs)
                
            return str(result)
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    def _trim_history(self, target_tokens: float):
        """Remove oldest history entries until total tokens is within budget."""
        history = self.state_manager.get("history", [])
        while history and self._count_tokens(self._build_history_context()) > target_tokens:
            removed = history.pop(0)
            print(f"[HANERMA] Trimmed oldest entry from '{removed['role']}' (token budget)")
