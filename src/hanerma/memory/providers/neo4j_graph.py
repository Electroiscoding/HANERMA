import os
import logging
from typing import Dict, Any, Optional

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.getLogger(__name__).warning("neo4j driver not installed. Neo4jGraphProvider will fail.")

logger = logging.getLogger(__name__)

class Neo4jGraphProvider:
    """
    Graph database provider for HANERMA architecture.
    Stores relational connections between thoughts, actions, and states.
    """

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.environ.get("NEO4J_USER", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD")
        
        if not self.password:
            raise ValueError("Neo4j credentials missing. Set NEO4J_PASSWORD environment variable.")

        if NEO4J_AVAILABLE:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        else:
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def write_node(self, node_label: str, properties: Dict[str, Any]) -> str:
        """Write a node to the graph and return its ID."""
        if not self.driver:
            raise RuntimeError("neo4j is not available")

        with self.driver.session() as session:
            result = session.write_transaction(self._create_node_tx, node_label, properties)
            return str(result)

    def _create_node_tx(self, tx, node_label: str, properties: Dict[str, Any]):
        # Construct SET string from properties dictionary
        props_str = ", ".join([f"n.{k} = ${k}" for k in properties.keys()])
        query = f"CREATE (n:{node_label}) SET {props_str} RETURN id(n) as node_id"
        result = tx.run(query, **properties)
        record = result.single()
        return record["node_id"] if record else None

    def read_node(self, node_id: int) -> Dict[str, Any]:
        """Read a node from the graph by ID."""
        if not self.driver:
            raise RuntimeError("neo4j is not available")

        with self.driver.session() as session:
            result = session.read_transaction(self._read_node_tx, node_id)
            return result

    def _read_node_tx(self, tx, node_id: int):
        query = "MATCH (n) WHERE id(n) = $node_id RETURN properties(n) as props"
        result = tx.run(query, node_id=node_id)
        record = result.single()
        return record["props"] if record else {}
        
    def link_nodes(self, from_id: int, to_id: int, relationship: str, properties: Dict[str, Any] = None):
        """Create a relationship between two existing nodes."""
        if not self.driver:
            raise RuntimeError("neo4j is not available")

        properties = properties or {}
        with self.driver.session() as session:
            session.write_transaction(self._link_nodes_tx, from_id, to_id, relationship, properties)

    def _link_nodes_tx(self, tx, from_id: int, to_id: int, relationship: str, properties: Dict[str, Any]):
        props_str = "{" + ", ".join([f"{k}: ${k}" for k in properties.keys()]) + "}" if properties else ""
        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $from_id AND id(b) = $to_id
        CREATE (a)-[r:{relationship} {props_str}]->(b)
        """
        tx.run(query, from_id=from_id, to_id=to_id, **properties)
