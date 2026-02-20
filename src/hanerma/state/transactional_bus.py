import sqlite3
import json
import time
import uuid
from typing import Any, Dict, List, Optional

class TransactionalEventBus:
    """
    Ensures every atomic step of the HANERMA execution is persisted.
    Allows for sub-2s recovery from crashes/OOM by rebuilding state from the bus.
    """
    def __init__(self, db_path: str = "hanerma_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT,
                    step_index INTEGER,
                    event_type TEXT,
                    payload TEXT,
                    timestamp REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trace ON events(trace_id)")

    def record_step(self, trace_id: str, step_index: int, event_type: str, payload: Dict[str, Any]):
        """Records a single atomic step to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO events (trace_id, step_index, event_type, payload, timestamp) VALUES (?, ?, ?, ?, ?)",
                (trace_id, step_index, event_type, json.dumps(payload), time.time())
            )

    def recover_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Retrieves all steps for a given trace to reconstruct state."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT step_index, event_type, payload FROM events WHERE trace_id = ? ORDER BY step_index ASC",
                (trace_id,)
            )
            return [
                {"step_index": row[0], "event_type": row[1], "payload": json.loads(row[2])}
                for row in cursor.fetchall()
            ]

    def get_latest_trace_id(self) -> Optional[str]:
        """Finds the most recent trace ID for auto-recovery."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT trace_id FROM events ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else None
