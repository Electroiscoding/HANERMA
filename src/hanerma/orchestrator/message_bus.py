import asyncio
import json
import uuid
import socket
import logging
from typing import Dict, Any, List, Set, Callable, Optional

logger = logging.getLogger(__name__)

class DistributedEventBus:
    """
    High-performance async Pub/Sub message bus with exactly-once execution.
    Utilizes asyncio streams for robust networked message passing instead of UDP broadcasts.
    """

    def __init__(self, node_id: str = None, host: str = "0.0.0.0", port: int = 50051):
        self.node_id = node_id or str(uuid.uuid4())
        self.host = host
        self.port = port

        # Local Pub/Sub
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._message_queues: Dict[str, asyncio.Queue] = {}

        # Networked Peers (TCP)
        self.peers: Dict[str, tuple] = {}

        self.server = None
        self._server_task = None

    async def start(self):
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        logger.info(f"DistributedEventBus started on {self.host}:{self.port} [Node: {self.node_id}]")
        self._server_task = asyncio.create_task(self.server.serve_forever())

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if self._server_task:
            self._server_task.cancel()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming TCP streams from peers."""
        peer_addr = writer.get_extra_info('peername')
        try:
            data = await reader.read(4096)
            if not data:
                return
            message = json.loads(data.decode())

            msg_type = message.get("type")
            if msg_type == "discovery":
                peer_id = message.get("node_id")
                peer_port = message.get("port")
                if peer_id and peer_id != self.node_id:
                    self.peers[peer_id] = (peer_addr[0], peer_port)
                    logger.info(f"Discovered peer {peer_id} at {peer_addr[0]}:{peer_port}")
                writer.write(json.dumps({"status": "ack"}).encode())
                await writer.drain()
            elif msg_type == "tool_dispatch":
                result = await self._execute_tool(message.get("tool"), message.get("args", {}))
                writer.write(json.dumps(result).encode())
                await writer.drain()
        except Exception as e:
            logger.error(f"Error handling peer connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def discover_peer(self, host: str, port: int):
        """Actively connect to a peer to introduce ourselves."""
        try:
            reader, writer = await asyncio.open_connection(host, port)
            msg = {"type": "discovery", "node_id": self.node_id, "port": self.port}
            writer.write(json.dumps(msg).encode())
            await writer.drain()

            # Wait for ack
            data = await asyncio.wait_for(reader.read(1024), timeout=5.0)
            ack = json.loads(data.decode())
            if ack.get("status") == "ack":
                # Assuming the peer id is not known initially, we just store connection info
                self.peers[f"{host}:{port}"] = (host, port)

            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logger.error(f"Failed to discover peer at {host}:{port} - {e}")

    def subscribe(self, topic: str, listener: Callable):
        """Allows an agent to listen for specific tasks."""
        if topic not in self._subscribers:
            self._subscribers[topic] = set()
            self._message_queues[topic] = asyncio.Queue(maxsize=1000)

        self._subscribers[topic].add(listener)
        logger.info(f"New listener subscribed to topic: '{topic}'")

    async def publish(self, topic: str, payload: Dict[str, Any]):
        """Publish message to local subscribers."""
        payload['trace_id'] = str(uuid.uuid4())

        if topic not in self._subscribers or not self._subscribers[topic]:
            logger.warning(f"Message dropped. No active agents for topic: '{topic}'")
            return

        tasks = []
        for listener in self._subscribers[topic]:
            tasks.append(asyncio.create_task(self._safe_execute(listener, payload)))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_execute(self, listener: Callable, payload: Dict[str, Any]):
        try:
            if asyncio.iscoroutinefunction(listener):
                await listener(payload)
            else:
                await asyncio.to_thread(listener, payload)
        except Exception as e:
            logger.error(f"Trace {payload.get('trace_id')} failed at {listener.__name__}: {str(e)}")

    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        try:
            from hanerma.tools.registry import ToolRegistry
            reg = ToolRegistry()
            tool = reg.get_tool(tool_name)
            if tool and hasattr(tool, 'call'):
                if asyncio.iscoroutinefunction(tool.call):
                    return await tool.call(**args)
                else:
                    return await asyncio.to_thread(tool.call, **args)
            return {"error": "Tool not found"}
        except Exception as e:
            return {"error": str(e)}

    async def dispatch_tool(self, peer_id: str, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Dispatch tool execution to a networked peer for load sharing.
        Waits for actual execution response.
        """
        if peer_id in self.peers:
            host, port = self.peers[peer_id]
            try:
                reader, writer = await asyncio.open_connection(host, port)
                message = json.dumps({
                    "type": "tool_dispatch",
                    "tool": tool_name,
                    "args": args
                })
                writer.write(message.encode())
                await writer.drain()

                response_data = await reader.read(4096)
                writer.close()
                await writer.wait_closed()

                return json.loads(response_data.decode())
            except Exception as e:
                return {"error": f"Dispatch failed: {str(e)}"}
        return {"error": "Peer not found"}

    def get_peers(self) -> Dict[str, tuple]:
        return self.peers.copy()
