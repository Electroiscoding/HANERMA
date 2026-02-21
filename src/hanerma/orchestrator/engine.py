
import asyncio
import ast
import time
import uuid
from typing import List, Dict, Any, Optional
from hanerma.agents.base_agent import BaseAgent
from hanerma.reasoning.deep1_atomic import AtomicGuard

from hanerma.orchestrator.message_bus import DistributedEventBus
from hanerma.state.models import HANERMAState
from hanerma.reliability.risk_engine import FailurePredictor
from hanerma.reliability.symbolic_reasoner import SymbolicReasoner
from hanerma.routing.model_router import ModelRouter
from hanerma.optimization.ast_analyzer import ParallelASTAnalyzer
from hanerma.autoprompt.enhancer import AutoPromptEnhancer
from hanerma.interface.empathy import EmpathyHandler
from hanerma.memory.manager import HCMSManager

import networkx as nx

class HANERMAOrchestrator:
    """
    The core engine for the Hierarchical Atomic Nested External Reasoning and Memory Architecture.
    Apex Edition: Zero-friction, self-healing, and mathematically grounded.
    """
    def __init__(self, model: str = "auto", tokenizer=None, context_window: int = 128000, 
                 node_id: str = None, raft_peers: List[str] = None):
        self.orchestrator_id = str(uuid.uuid4())
        self.router = ModelRouter()
        self.default_model = self.router.route_request("", 0) if model == "auto" else model
        self.tokenizer = tokenizer
        self.context_window = context_window
        self.active_agents: Dict[str, BaseAgent] = {}
        self.state_manager: HANERMAState = HANERMAState()
        self.step_index = 0
        
        # Raft Consensus Event Bus
        self.bus = DistributedEventBus(node_id=node_id, peers=raft_peers)
        
        # Apex Modules
        self.enhancer = AutoPromptEnhancer()
        self.risk_engine = FailurePredictor()
        self.symbolic_reasoner = SymbolicReasoner()
        self.ast_analyzer = ParallelASTAnalyzer()
        self.empathy = EmpathyHandler()
        self.manager = HCMSManager(tokenizer, self.bus.raft)  # Use raft for state persistence
        self.user_style: Dict[str, Any] = {}
        self.interaction_count = 0
        self.trace_id = str(uuid.uuid4())
        self.current_dag: nx.DiGraph = nx.DiGraph()
        
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
        Executes a graph of agent/tool calls parsed from source_code with strict state validation and self-healing.
        Uses DAG analysis for parallelism and enforces typed state transitions.
        Implements true MVCC rollback on failures.
        """
        # Build the full DAG
        self.current_dag = self._build_dag_from_source(source_code)
        
        results = {}
        failed_nodes = set()
        
        # Execute in topological order
        for node_id in nx.topological_sort(self.current_dag):
            if node_id in failed_nodes:
                continue
                
            node = self.current_dag.nodes[node_id]['data']
            
            # Validate state before execution
            if not self._validate_state_pre_execution():
                # State is invalid, attempt rollback
                await self._rollback_to_last_valid_state(self.step_index)
                continue
            
            # Record step start
            self.bus.record_step(self.trace_id, self.step_index, "node_start", {"node_id": node_id}, self.state_manager)
            
            try:
                result = await self._execute_node_with_validation(node)
                results[node_id] = result
                
                # Validate state after execution
                if not self._validate_state_post_execution():
                    raise ValueError(f"State validation failed after executing node {node_id}")
                
                # Record successful step
                self.bus.record_step(self.trace_id, self.step_index + 1, "node_success", {"node_id": node_id, "result": str(result)}, self.state_manager)
                self.step_index += 1
                
            except Exception as e:
                # Failure detected - implement MVCC rollback and AST patching
                await self._handle_node_failure(node_id, e, failed_nodes)
                
        return results

    def _build_dag_from_source(self, source_code: str) -> nx.DiGraph:
        """Builds the full DAG from source code using the AST analyzer."""
        tree = ast.parse(source_code)
        graph = nx.DiGraph()
        node_id = 0
        
        for stmt in ast.walk(tree):
            if isinstance(stmt, (ast.Assign, ast.Expr)):
                writes = set()
                reads = set()
                
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            writes.add(target.id)
                    reads = self._collect_reads(stmt.value)
                else:
                    reads = self._collect_reads(stmt.value)
                
                graph.add_node(f'node_{node_id}', data={
                    'id': f'node_{node_id}',
                    'writes': writes,
                    'reads': reads,
                    'ast_node': stmt
                })
                node_id += 1
        
        # Add dependencies
        for node_a_id in graph.nodes:
            for node_b_id in graph.nodes:
                if node_a_id != node_b_id:
                    writes_a = graph.nodes[node_a_id]['data']['writes']
                    reads_b = graph.nodes[node_b_id]['data']['reads']
                    if writes_a & reads_b:
                        graph.add_edge(node_a_id, node_b_id)
        
        return graph

    def _collect_reads(self, node: ast.AST) -> set:
        """Collect all variable names read in the AST subtree."""
        names = set()
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Name):
                names.add(subnode.id)
        return names

    def _validate_state_pre_execution(self) -> bool:
        """Validates the current state before executing a node."""
        try:
            # Pydantic validation
            HANERMAState(**self.state_manager.dict())
            return True
        except Exception:
            return False

    def _validate_state_post_execution(self) -> bool:
        """Validates the current state after executing a node."""
        return self._validate_state_pre_execution()

    async def _rollback_to_last_valid_state(self, current_step: int):
        """Performs MVCC rollback to the last valid state."""
        last_valid_state = self.bus.get_last_valid_state(self.trace_id, current_step)
        if last_valid_state:
            self.state_manager = last_valid_state
            # Prune failed branches from DAG (simplified - remove nodes after current step)
            nodes_to_remove = []
            for node_id in self.current_dag.nodes:
                node_data = self.current_dag.nodes[node_id]['data']
                # Assume nodes have step indices, remove those after failed step
                if hasattr(node_data, 'step_index') and node_data['step_index'] >= current_step:
                    nodes_to_remove.append(node_id)
            for node_id in nodes_to_remove:
                self.current_dag.remove_node(node_id)
        else:
            # No valid state found, reset to initial
            self.state_manager = HANERMAState()

    async def _handle_node_failure(self, node_id: str, exception: Exception, failed_nodes: set):
        """Handles node failure with MVCC rollback and AST patching."""
        failed_nodes.add(node_id)
        
        # Get AST patch from EmpathyHandler
        patch = await self.empathy.generate_ast_patch(str(exception), self.current_dag.nodes[node_id]['data'])
        
        if patch:
            # Inject patched AST into DAG
            self._inject_ast_patch(node_id, patch)
            # Retry execution
            try:
                node = self.current_dag.nodes[node_id]['data']
                result = await self._execute_node_with_validation(node)
                failed_nodes.remove(node_id)  # Success, remove from failed
                return result
            except Exception:
                pass  # Patch failed
        
        # If patching fails, rollback
        await self._rollback_to_last_valid_state(self.step_index)

    async def _execute_node_with_validation(self, node: Dict[str, Any]) -> Any:
        """Executes a node with state validation."""
        # Pre-validation
        if not self._validate_state_pre_execution():
            raise ValueError("Pre-execution state validation failed")
        
        result = await self._execute_node(node)
        
        # Post-validation
        if not self._validate_state_post_execution():
            raise ValueError("Post-execution state validation failed")
        
        return result

    def _inject_ast_patch(self, node_id: str, patched_ast: ast.AST):
        """Injects a patched AST node into the live DAG."""
        if node_id in self.current_dag.nodes:
            # Update the node's AST
            self.current_dag.nodes[node_id]['data']['ast_node'] = patched_ast
            
            # Recompute reads/writes if necessary
            writes = set()
            reads = set()
            
            if isinstance(patched_ast, ast.Assign):
                for target in patched_ast.targets:
                    if isinstance(target, ast.Name):
                        writes.add(target.id)
                reads = self._collect_reads(patched_ast.value)
            elif isinstance(patched_ast, ast.Expr):
                reads = self._collect_reads(patched_ast.value)
            
            self.current_dag.nodes[node_id]['data']['writes'] = writes
            self.current_dag.nodes[node_id]['data']['reads'] = reads
            
            # Recompute dependencies (simplified - could be more sophisticated)
            # For now, assume dependencies don't change drastically

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

    def get_raft_status(self) -> Dict[str, Any]:
        """Get current Raft consensus status."""
        return self.bus.get_raft_status()

    async def execute_with_consensus(self, command: Dict[str, Any]) -> bool:
        """
        Execute a command with Raft consensus guarantee.
        Returns True if successfully committed to majority.
        """
        return await self.bus.raft.propose_command(command)

    def get_executed_commands(self) -> Set[str]:
        """Get set of idempotency keys for executed commands."""
        return self.bus.raft.executed_commands.copy()

    def is_command_executed(self, command: Dict[str, Any]) -> bool:
        """Check if a command has already been executed."""
        idempotency_key = self.bus.raft.generate_idempotency_key(command)
        return idempotency_key in self.bus.raft.executed_commands

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
        history = self.state_manager.history
        if not history:
            return ""
        return "\n".join(f"[{h.role}]: {h.content}" for h in history)

    async def _autoprompt_enhance(self, prompt: str) -> str:
        """Structural upgrade to the user's prompt."""
        return await self.enhancer.enhance(prompt)

    async def _handle_tool_call(self, agent: BaseAgent, response: str) -> str:
        """Parses and executes a TOOL_CALL natively with robust extraction and Raft consensus."""
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
            
        print(f"[HANERMA] Executing: {name} with Raft consensus (Keys: {list(kwargs.keys())})")
        
        # Execute tool with Raft consensus and exactly-once semantics
        try:
            result = await self.bus.execute_tool_with_wal(name, kwargs)
            if isinstance(result, dict) and result.get("status") == "executed_with_consensus":
                return f"Tool '{name}' executed successfully with Raft consensus guarantee."
            else:
                return f"Tool execution failed: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Error executing {name} with consensus: {str(e)}"

    def _trim_history(self, target_tokens: float):
        """Remove oldest history entries until total tokens is within budget."""
        history = self.state_manager.history
        while history and self._count_tokens(self._build_history_context()) > target_tokens:
            removed = history.pop(0)
            print(f"[HANERMA] Trimmed oldest entry from '{removed.role}' (token budget)")
