import ast
import networkx as nx
from typing import List, Set, Dict, Any

class ParallelASTAnalyzer(ast.NodeVisitor):
    """
    Analyzes Python code to detect safe parallel execution regions by building a Directed Acyclic Graph (DAG)
    of statements based on variable dependencies. Uses topological sort to group nodes that can execute concurrently.
    """
    def __init__(self):
        self.nodes: List[Dict[str, Any]] = []

    def analyze(self, source_code: str) -> List[List[Dict[str, Any]]]:
        """
        Parses source code into AST, builds a DAG of variable dependencies, and returns batches of nodes
        that can be executed concurrently based on topological generations.
        """
        tree = ast.parse(source_code)
        self.nodes = []
        self.visit(tree)

        # Build DAG
        graph = nx.DiGraph()
        for node in self.nodes:
            graph.add_node(node['id'], data=node)

        for node_a in self.nodes:
            for node_b in self.nodes:
                if node_a != node_b and node_a['writes'] & node_b['reads']:
                    graph.add_edge(node_a['id'], node_b['id'])

        # Get topological generations
        try:
            generations = list(nx.topological_generations(graph))
            result = []
            for gen in generations:
                batch = [graph.nodes[n]['data'] for n in gen]
                result.append(batch)
            return result
        except nx.NetworkXError:
            # If not a DAG, return empty or handle, but assume it is
            return []

    def visit_Assign(self, node: ast.Assign):
        writes = set()
        for target in node.targets:
            if isinstance(target, ast.Name):
                writes.add(target.id)
        reads = self._collect_reads(node.value)
        self.nodes.append({
            'id': f'node_{len(self.nodes)}',
            'writes': writes,
            'reads': reads,
            'ast_node': node
        })

    def visit_Expr(self, node: ast.Expr):
        writes = set()
        reads = self._collect_reads(node.value)
        self.nodes.append({
            'id': f'node_{len(self.nodes)}',
            'writes': writes,
            'reads': reads,
            'ast_node': node
        })

    def _collect_reads(self, node: ast.AST) -> Set[str]:
        """Collect all variable names read in the AST subtree."""
        names = set()
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Name):
                names.add(subnode.id)
        return names


def detect_parallel_regions(code: str) -> List[List[Dict[str, Any]]]:
    analyzer = ParallelASTAnalyzer()
    return analyzer.analyze(code)


if __name__ == "__main__":
    # Test the analyzer
    test_code = """
a = 1
b = func1(a)
c = func2(2)
d = func3(b)
e = func4(c)
"""
    batches = detect_parallel_regions(test_code)
    print("Concurrent execution batches:")
    for i, batch in enumerate(batches):
        print(f"Batch {i}: {[node['id'] for node in batch]}")
        for node in batch:
            print(f"  {node['id']}: writes={node['writes']}, reads={node['reads']}")
