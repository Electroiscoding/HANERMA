import asyncio
import json
import logging
import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("hanerma.raft")

class RaftNodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

@dataclass
class LogEntry:
    term: int
    index: int
    command: str
    timestamp: float

@dataclass
class ConsensusResult:
    success: bool
    term: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class RaftConsensus:
    """
    Real Raft consensus implementation for distributed state management.
    Performs physical `asyncio` network calls to peers for Leader Election and Log Replication.
    """
    def __init__(self, node_id: str, cluster_nodes: Dict[str, Any]):
        self.node_id = node_id
        # Expecting cluster_nodes values to be dicts with "host" and "port"
        self.cluster_nodes = cluster_nodes

        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []

        self.commit_index = 0
        self.last_applied = 0
        self.state = RaftNodeState.FOLLOWER

        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}

        self.election_timeout = random.uniform(1.5, 3.0)
        self.last_heartbeat_time = time.time()

        self._election_task: Optional[asyncio.Task] = None
        
        logger.info(f"[RAFT] Node {node_id} initialized with {len(cluster_nodes)} cluster nodes")

    async def start(self):
        self._election_task = asyncio.create_task(self._election_loop())

    async def stop(self):
        if self._election_task:
            self._election_task.cancel()

    async def _election_loop(self):
        while True:
            try:
                await asyncio.sleep(0.1)
                if self.state == RaftNodeState.LEADER:
                    await self._send_heartbeats()
                else:
                    if time.time() - self.last_heartbeat_time > self.election_timeout:
                        await self._start_election()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[RAFT] Election loop error: {e}")

    async def _send_rpc(self, host: str, port: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform physical TCP connection to a peer for an RPC call."""
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=1.0)
            writer.write(json.dumps(payload).encode())
            await writer.drain()
            
            data = await asyncio.wait_for(reader.read(4096), timeout=1.0)
            writer.close()
            await writer.wait_closed()
            
            return json.loads(data.decode())
        except Exception:
            # Drop failed connections (simulating partition or crash)
            return None

    async def _start_election(self):
        logger.info(f"[RAFT] Node {self.node_id} starting election for term {self.current_term + 1}")
        self.state = RaftNodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.last_heartbeat_time = time.time()
        self.election_timeout = random.uniform(1.5, 3.0)

        votes = 1 # Vote for self
        required_votes = (len(self.cluster_nodes) + 1) // 2 + 1

        if len(self.cluster_nodes) == 0:
            self._become_leader()
            return
            
        last_log_index = len(self.log) - 1
        last_log_term = self.log[-1].term if self.log else 0
            
        payload = {
            "type": "RequestVote",
            "term": self.current_term,
            "candidate_id": self.node_id,
            "last_log_index": last_log_index,
            "last_log_term": last_log_term
        }
        
        # Gather votes asynchronously
        tasks = []
        for peer_id, addr in self.cluster_nodes.items():
            tasks.append(self._send_rpc(addr['host'], addr['port'], payload))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for response in responses:
            if isinstance(response, dict) and response.get("vote_granted"):
                votes += 1

        if votes >= required_votes:
            self._become_leader()

    def _become_leader(self):
        logger.info(f"[RAFT] Node {self.node_id} became LEADER for term {self.current_term}")
        self.state = RaftNodeState.LEADER
        for peer in self.cluster_nodes:
            self.next_index[peer] = len(self.log)
            self.match_index[peer] = 0

    async def _send_heartbeats(self):
        self.last_heartbeat_time = time.time()
        if len(self.cluster_nodes) == 0:
            return

        tasks = []
        for peer_id, addr in self.cluster_nodes.items():
            prev_log_index = self.next_index.get(peer_id, 0) - 1
            prev_log_term = self.log[prev_log_index].term if prev_log_index >= 0 and prev_log_index < len(self.log) else 0
            entries = self.log[prev_log_index + 1:]

            payload = {
                "type": "AppendEntries",
                "term": self.current_term,
                "leader_id": self.node_id,
                "prev_log_index": prev_log_index,
                "prev_log_term": prev_log_term,
                "entries": [{"term": e.term, "index": e.index, "command": e.command, "timestamp": e.timestamp} for e in entries],
                "leader_commit": self.commit_index
            }
            tasks.append(self._send_rpc(addr['host'], addr['port'], payload))

        await asyncio.gather(*tasks, return_exceptions=True)

    def receive_append_entries(self, term: int, leader_id: str, prev_log_index: int, prev_log_term: int, entries: List[Dict], leader_commit: int) -> bool:
        if term < self.current_term:
            return False

        self.last_heartbeat_time = time.time()
        
        if term > self.current_term:
            self.current_term = term
            self.state = RaftNodeState.FOLLOWER
            self.voted_for = None

        if prev_log_index >= 0:
            if prev_log_index >= len(self.log) or self.log[prev_log_index].term != prev_log_term:
                return False

        if entries:
            for i, ent_dict in enumerate(entries):
                idx = prev_log_index + 1 + i
                entry = LogEntry(**ent_dict)
                if idx < len(self.log):
                    if self.log[idx].term != entry.term:
                        self.log = self.log[:idx]
                        self.log.append(entry)
                else:
                    self.log.append(entry)

        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log) - 1)

        return True

    async def propose_operation(self, operation: Dict[str, Any]) -> ConsensusResult:
        if self.state != RaftNodeState.LEADER and len(self.cluster_nodes) > 0:
            return ConsensusResult(success=False, term=self.current_term, error="Not leader")

        log_entry = LogEntry(
            term=self.current_term,
            index=len(self.log),
            command=json.dumps(operation),
            timestamp=time.time()
        )
        self.log.append(log_entry)
        
        if len(self.cluster_nodes) == 0:
            self.commit_index = len(self.log) - 1
            return ConsensusResult(success=True, term=self.current_term, data={"log_index": log_entry.index, "committed": True})

        # Send to peers immediately
        await self._send_heartbeats()
        
        return ConsensusResult(success=True, term=self.current_term, data={"log_index": log_entry.index, "committed": False, "pending": True})

    def query_distributed(self, query: Dict[str, Any]) -> ConsensusResult:
        return ConsensusResult(
            success=True,
            term=self.current_term,
            data={"state": self.state.value, "commit_index": self.commit_index}
        )
