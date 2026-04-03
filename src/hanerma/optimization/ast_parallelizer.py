import ast
import networkx as nx
from typing import List, Dict, Any, Set, Tuple
import logging
import asyncio

logger = logging.getLogger(__name__)

class VariableDefUseAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.reads = set()
        self.writes = set()

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.writes.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.reads.add(node.id)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # The targets are written to, the value is read from
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.writes.add(target.id)
        self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign):
        if isinstance(node.target, ast.Name):
            self.reads.add(node.target.id)
            self.writes.add(node.target.id)
        self.visit(node.value)

    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)

class ASTParallelizer:
    """
    Parses agent-written scripts to identify non-overlapping variables
    for parallel DAG execution using actual Use-Def chain analysis.
    """

    def __init__(self):
        self.dag = nx.DiGraph()

    def analyze_script(self, source_code: str) -> List[List[ast.stmt]]:
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.error(f"Syntax error during AST analysis: {e}")
            return []

        blocks = []
        for node in tree.body:
            blocks.append(node)

        dependencies = self._build_dependency_graph(blocks)

        parallel_paths = []
        for component in nx.weakly_connected_components(dependencies):
            path_nodes = [node for node in blocks if id(node) in component]
            if path_nodes:
                parallel_paths.append(path_nodes)

        return parallel_paths

    def _build_dependency_graph(self, blocks: List[ast.stmt]) -> nx.DiGraph:
        G = nx.DiGraph()

        for block in blocks:
            G.add_node(id(block), block=block)

        writes_registry = {} # var_name -> list of node_ids that wrote it

        for block in blocks:
            reads, block_writes = self._extract_vars(block)
            block_id = id(block)

            # Use-Def edge (Read-after-Write)
            for r in reads:
                if r in writes_registry:
                    for prev_writer in writes_registry[r]:
                        if prev_writer != block_id:
                            G.add_edge(prev_writer, block_id)

            # Write-after-Write edge (Output dependency)
            for w in block_writes:
                if w in writes_registry:
                    for prev_writer in writes_registry[w]:
                        if prev_writer != block_id:
                            G.add_edge(prev_writer, block_id)

            for w in block_writes:
                if w not in writes_registry:
                    writes_registry[w] = []
                writes_registry[w].append(block_id)

        # To avoid components breaking on completely independent statements,
        # we still treat isolated nodes as their own path
        if len(G.nodes) > 0 and len(G.edges) == 0:
            for n in G.nodes:
                G.add_edge(n, n) # Self loop to make it a component

        return G

    def _extract_vars(self, node: ast.stmt) -> Tuple[Set[str], Set[str]]:
        analyzer = VariableDefUseAnalyzer()
        analyzer.visit(node)
        return analyzer.reads, analyzer.writes

    async def execute_parallel(self, parallel_paths: List[List[ast.stmt]], global_env: Dict[str, Any]):
        async def run_path(path_nodes: List[ast.stmt]):
            module = ast.Module(body=path_nodes, type_ignores=[])
            code = compile(module, filename="<ast>", mode="exec")
            await asyncio.to_thread(exec, code, global_env)

        tasks = [asyncio.create_task(run_path(path)) for path in parallel_paths]
        await asyncio.gather(*tasks)
