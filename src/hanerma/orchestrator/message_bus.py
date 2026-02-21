import asyncio
import socket
import threading
import json
import time
from typing import Dict, Set, Callable, Any
import uuid

class DistributedEventBus:
    """
    High-performance async Pub/Sub message bus with networked nodes support.
    Enables zero-lock-in distributed execution across local machines.
    """
    
    def __init__(self):
        # Local Pub/Sub
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._message_queues: Dict[str, asyncio.Queue] = {}
        
        # Networked peers
        self.peers: Dict[str, tuple] = {}  # peer_id: (host, port)
        self.my_id = str(uuid.uuid4())
        self.my_port = 50051
        
        # Start networking threads
        self.discovery_thread = threading.Thread(target=self._peer_discovery, daemon=True)
        self.discovery_thread.start()
        
        self.listener_thread = threading.Thread(target=self._listen_for_peers, daemon=True)
        self.listener_thread.start()
        
        self.tool_listener_thread = threading.Thread(target=self._listen_for_tools, daemon=True)
        self.tool_listener_thread.start()

    def subscribe(self, topic: str, listener: Callable):
        """Allows an agent to listen for specific tasks."""
        if topic not in self._subscribers:
            self._subscribers[topic] = set()
            self._message_queues[topic] = asyncio.Queue(maxsize=1000)
        
        self._subscribers[topic].add(listener)
        print(f"[DistributedEventBus] A new listener subscribed to topic: '{topic}'")

    async def publish(self, topic: str, payload: Dict[str, Any]):
        """
        Fires an event asynchronously, including to networked peers.
        """
        payload['trace_id'] = str(uuid.uuid4())
        
        if topic not in self._subscribers or not self._subscribers[topic]:
            print(f"[DistributedEventBus Warning] Message dropped. No active agents for topic: '{topic}'")
            return

        # Route locally
        for listener in self._subscribers[topic]:
            asyncio.create_task(self._safe_execute(listener, payload))

    async def _safe_execute(self, listener: Callable, payload: Dict[str, Any]):
        """Wraps the execution to prevent a single failing agent from crashing the bus."""
        try:
            await listener(payload)
        except Exception as e:
            print(f"[DistributedEventBus Error] Trace {payload.get('trace_id')} failed at {listener.__name__}: {str(e)}")

    def _peer_discovery(self):
        """UDP broadcast for peer discovery."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            try:
                sock.sendto(self.my_id.encode(), ('<broadcast>', 50052))
                time.sleep(10)
            except:
                break

    def _listen_for_peers(self):
        """Listen for UDP discovery messages."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 50052))
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                peer_id = data.decode()
                if peer_id != self.my_id:
                    self.peers[peer_id] = (addr[0], self.my_port)
                    print(f"[DistributedEventBus] Discovered peer: {peer_id} at {addr[0]}")
            except:
                break

    def _listen_for_tools(self):
        """TCP listener for incoming tool dispatches."""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(('', self.my_port))
        server_sock.listen(5)
        while True:
            try:
                client_sock, addr = server_sock.accept()
                threading.Thread(target=self._handle_tool_dispatch, args=(client_sock,), daemon=True).start()
            except:
                break

    def _handle_tool_dispatch(self, sock):
        """Handle incoming tool dispatch."""
        try:
            data = sock.recv(4096).decode()
            message = json.loads(data)
            if message["type"] == "tool_dispatch":
                result = self._execute_tool(message["tool"], message["args"])
                sock.send(json.dumps(result).encode())
        except Exception as e:
            sock.send(json.dumps({"error": str(e)}).encode())
        finally:
            sock.close()

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute tool locally."""
        from hanerma.tools.registry import ToolRegistry
        reg = ToolRegistry()
        tool = reg.get_tool(tool_name)
        if tool and hasattr(tool, 'call'):
            return tool.call(**args)
        return {"error": "Tool not found"}

    def dispatch_tool(self, peer_id: str, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Dispatch tool execution to a networked peer for load sharing.
        """
        if peer_id in self.peers:
            host, port = self.peers[peer_id]
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((host, port))
                message = json.dumps({"type": "tool_dispatch", "tool": tool_name, "args": args})
                sock.send(message.encode())
                response = sock.recv(4096).decode()
                sock.close()
                return json.loads(response)
            except Exception as e:
                return {"error": f"Dispatch failed: {str(e)}"}
        return {"error": "Peer not found"}

    def get_peers(self) -> Dict[str, tuple]:
        """Get discovered peers for load balancing."""
        return self.peers.copy()
