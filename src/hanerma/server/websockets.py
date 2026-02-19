from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
import asyncio

ws_router = APIRouter()

class ConnectionManager:
    """Manages active WebSockets for live agent thought-streaming."""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"[WebSocket] User connected to session: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def stream_thought(self, session_id: str, message: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(json.dumps({
                "type": "agent_thought",
                "content": message
            }))

manager = ConnectionManager()

@ws_router.websocket("/ws/stream/{session_id}")
async def agent_stream_endpoint(websocket: WebSocket, session_id: str):
    """
    Allows a frontend UI to connect and watch the agent's internal monologue 
    as it executes the Atomic -> Nested -> External pipeline.
    """
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive and listen for client interruptions
            data = await websocket.receive_text()
            # If the user types "STOP", it halts the agent
            if data == "STOP":
                await manager.stream_thought(session_id, "[System: Execution Halted by User]")
    except WebSocketDisconnect:
        manager.disconnect(session_id)
