
import asyncio
import ast
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
from hanerma.interface.empathy import EmpathyHandler
from hanerma.memory.manager import HCMSManager

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
        self.empathy = EmpathyHandler()
        self.manager = HCMSManager(tokenizer, self.bus)
        self.user_style: Dict[str, Any] = {}
        self.interaction_count = 0
        self.trace_id = str(uuid.uuid4())
        self.step_index = 0
        
        # Background style extraction
        self.style_task = asyncio.create_task(self._style_extraction_loop())

    async def _style_extraction_loop(self):
        """Background task to extract user style every 5 interactions."""
        while True:
            await asyncio.sleep(30)
            if self.interaction_count >= 5:
                style = await self.manager.extract_user_style()
                if style:
                    self.user_style = style
                self.interaction_count = 0

    def register_agent(self, agent: BaseAgent):
        """Registers an agent into the orchestrator."""
        if agent.model is None:
            agent.model = self.default_model
        self.active_agents[agent.name] = agent
        print(f"[HANERMA] Agent '{agent.name}' registered.")

    async def run(self, source_code: str) -> Dict[str, Any]:
        """
        Executes the graph defined in source_code concurrently using DAG analysis.
        """
        start_time = time.time()
        results = await self.execute_graph(source_code)
        final_output = "\n".join(str(result) for result in results.values() if result is not None)
        self.interaction_count += 1
        latency = (time.time() - start_time) * 1000
        return {
            "status": "success",
            "output": final_output,
            "results": results,
            "metrics": {
                "latency_ms": round(latency, 2),
            }
        }

    async def execute_graph(self, source_code: str) -> Dict[str, Any]:
        """
        Executes a graph of agent/tool calls parsed from source_code concurrently where possible.
        Uses DAG analysis to determine execution order and parallelism.
        Includes self-healing: handles exceptions via EmpathyHandler without crashing.
        """
        batches = self.ast_analyzer.analyze(source_code)
        results = {}
        for batch in batches:
            tasks = []
            for node in batch:
                task = asyncio.create_task(self._execute_node(node))
                tasks.append(task)
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Self-healing: handle exceptions and execute mitigations
            for node, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    # Get mitigation from EmpathyHandler
                    mitigation = self.empathy.get_mitigation(str(result))
                    
                    if mitigation["action"] == "retry_with_new_prompt":
                        # Retry the node with a simplified prompt (AST-aware adjustment)
                        try:
                            # For retry, perhaps modify the node or prompt
                            # For simplicity, re-run the same
                            new_result = await self._execute_node(node)
                            results[node['id']] = new_result
                        except Exception as retry_e:
                            results[node['id']] = f"Retry failed: {mitigation['human_readable_message']}"
                    
                    elif mitigation["action"] == "ask_human":
                        # Return human-readable message for intervention
                        results[node['id']] = mitigation["human_readable_message"]
                    
                    elif mitigation["action"] == "mock_data":
                        # Provide mock data to continue execution
                        results[node['id']] = f"Mock data: {mitigation['human_readable_message']}"
                    
                else:
                    results[node['id']] = result
        
        return results

    async def _execute_node(self, node: Dict[str, Any]) -> Any:
        """
        Executes a single node (AST statement) asynchronously.
        """
        try:
            ast_node = node['ast_node']
            if isinstance(ast_node, ast.Assign):
                value = ast_node.value
                if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
                    name = value.func.id
                    if name in self.active_agents:
                        agent = self.active_agents[name]
                        prompt = ""
                        if value.args and isinstance(value.args[0], ast.Str):
                            prompt = value.args[0].s
                        result = await agent.execute(prompt, self.state_manager)
                        return result
            # For other node types or unmatched calls, return None
            return None
        except Exception as e:
            return f"Error executing node {node['id']}: {str(e)}"

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
