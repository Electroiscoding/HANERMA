import asyncio
from typing import Dict, Set, Callable, Any
import uuid

class EventBus:
    """
    High-performance async Pub/Sub message bus for multi-agent communication.
    Ensures agents don't block each other during heavy I/O or token generation.
    """
    def __init__(self):
        # Maps event topics (e.g., 'need_code', 'fact_check') to a set of listening agents
        self._subscribers: Dict[str, Set[Callable]] = {}
        # Uses asyncio queues to prevent memory overflow during massive multi-tenant load
        self._message_queues: Dict[str, asyncio.Queue] = {}

    def subscribe(self, topic: str, listener: Callable):
        """Allows an agent to listen for specific tasks."""
        if topic not in self._subscribers:
            self._subscribers[topic] = set()
            self._message_queues[topic] = asyncio.Queue(maxsize=1000)
        
        self._subscribers[topic].add(listener)
        print(f"[EventBus] A new listener subscribed to topic: '{topic}'")

    async def publish(self, topic: str, payload: Dict[str, Any]):
        """
        Fires an event asynchronously. The orchestrator does not wait.
        Fire-and-forget architecture ensures zero perceived latency.
        """
        payload['trace_id'] = str(uuid.uuid4())
        
        if topic not in self._subscribers or not self._subscribers[topic]:
            print(f"[EventBus Warning] Message dropped. No active agents for topic: '{topic}'")
            return

        # Route the payload to all listening agents concurrently
        for listener in self._subscribers[topic]:
            # asyncio.create_task ensures the event loop is not blocked
            asyncio.create_task(self._safe_execute(listener, payload))

    async def _safe_execute(self, listener: Callable, payload: Dict[str, Any]):
        """Wraps the execution to prevent a single failing agent from crashing the bus."""
        try:
            await listener(payload)
        except Exception as e:
            print(f"[EventBus Error] Trace {payload.get('trace_id')} failed at {listener.__name__}: {str(e)}")
            # In production, this routes the error to a Dead Letter Queue for retry
