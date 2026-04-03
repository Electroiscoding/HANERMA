import ast
import networkx as nx
from typing import List, Dict, Any, Set
import logging
import asyncio

logger = logging.getLogger(__name__)

class ASTParallelizer:
    """
    Parses agent-written scripts to identify non-overlapping variables
    for parallel DAG execution.
    """

    def __init__(self):
        self.dag = nx.DiGraph()

    def analyze_script(self, source_code: str) -> List[List[ast.stmt]]:
        """
        Parses source code into an AST and determines independent execution paths.
        Returns a list of independent code blocks that can be executed in parallel.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.error(f"Syntax error during AST analysis: {e}")
            return []

        # Find top-level independent functions or blocks
        blocks = []
        for node in tree.body:
            blocks.append(node)

        # Simplified dependency graph: assumes functions without shared globals are independent
        # In a real compiler, this uses def-use chains.
        dependencies = self._build_dependency_graph(blocks)

        # Find weakly connected components (independent parallelizable paths)
        parallel_paths = []
        for component in nx.weakly_connected_components(dependencies):
            path_nodes = [node for node in blocks if id(node) in component]
            if path_nodes:
                parallel_paths.append(path_nodes)

        return parallel_paths

    def _build_dependency_graph(self, blocks: List[ast.stmt]) -> nx.DiGraph:
        G = nx.DiGraph()

        # Add nodes
        for block in blocks:
            G.add_node(id(block), block=block)

        # Find dependencies (simplified variables read/write analysis)
        writes = {} # var_name -> node_id

        for block in blocks:
            reads, block_writes = self._extract_vars(block)
            block_id = id(block)

            # If block reads a variable written by a previous block, add an edge
            for r in reads:
                if r in writes:
                    G.add_edge(writes[r], block_id)

            # Record writes
            for w in block_writes:
                writes[w] = block_id

        return G

    def _extract_vars(self, node: ast.stmt) -> tuple[Set[str], Set[str]]:
        reads = set()
        writes = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if isinstance(child.ctx, ast.Store):
                    writes.add(child.id)
                elif isinstance(child.ctx, ast.Load):
                    reads.add(child.id)

        return reads, writes

    async def execute_parallel(self, parallel_paths: List[List[ast.stmt]], global_env: Dict[str, Any]):
        """Executes independent AST paths in parallel asyncio tasks."""
        async def run_path(path_nodes: List[ast.stmt]):
            # Convert AST nodes back to executable module
            module = ast.Module(body=path_nodes, type_ignores=[])
            code = compile(module, filename="<ast>", mode="exec")
            # Execute in thread to avoid blocking event loop
            await asyncio.to_thread(exec, code, global_env)

        tasks = [asyncio.create_task(run_path(path)) for path in parallel_paths]
        await asyncio.gather(*tasks)
