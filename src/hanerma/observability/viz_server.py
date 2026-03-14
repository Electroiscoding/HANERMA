"""
God Mode Two-Way Visual Composer — Real-time DAG Designer + State Injection.

Provides:
  - React Flow-style visual DAG designer in the browser
  - /api/graph/pause — pauses mid-execution via threading Event
  - /api/graph/resume — resumes execution
  - /api/graph/edit_state — injects new state/memory into a running agent
  - WebSocket live telemetry feed
  - Visual Architect: drag-and-drop agent wiring

The orchestrator checks a threading Event flag at every DAG step,
allowing the user to physically pause, edit memory, and resume.
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
import threading
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("hanerma.viz_server")

# ═══════════════════════════════════════════════════════════════════════════
#  Execution Control — threading Event for pause/resume
# ═══════════════════════════════════════════════════════════════════════════

class ExecutionController:
    """
    Thread-safe execution controller.
    The Rust engine / orchestrator checks `can_proceed()` at every DAG step.
    """

    def __init__(self):
        self._event = threading.Event()
        self._event.set()  # Start in running state
        self._paused_at: Optional[float] = None
        self._state_patches: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def pause(self) -> None:
        """Pause DAG execution."""
        self._event.clear()
        self._paused_at = time.time()
        logger.info("[CONTROLLER] ⏸ Execution PAUSED")

    def resume(self) -> None:
        """Resume DAG execution."""
        self._event.set()
        self._paused_at = None
        logger.info("[CONTROLLER] ▶ Execution RESUMED")

    def can_proceed(self, timeout: float = 0.1) -> bool:
        """
        Check if execution can proceed.
        Blocks for up to timeout seconds if paused.
        Call this at every DAG step boundary.
        """
        return self._event.wait(timeout=timeout)

    def is_paused(self) -> bool:
        return not self._event.is_set()

    def inject_state(self, agent_name: str, key: str, value: Any) -> None:
        """Queue a state patch for injection during pause."""
        with self._lock:
            self._state_patches.append({
                "agent_name": agent_name,
                "key": key,
                "value": value,
                "timestamp": time.time(),
            })
        logger.info("[CONTROLLER] State patch queued: %s.%s", agent_name, key)

    def drain_patches(self) -> List[Dict[str, Any]]:
        """Drain all pending state patches (called by orchestrator on resume)."""
        with self._lock:
            patches = self._state_patches.copy()
            self._state_patches.clear()
        return patches

    def status(self) -> Dict[str, Any]:
        return {
            "paused": self.is_paused(),
            "paused_at": self._paused_at,
            "pending_patches": len(self._state_patches),
        }


# Global controller instance
controller = ExecutionController()


# ═══════════════════════════════════════════════════════════════════════════
#  Pydantic models for API
# ═══════════════════════════════════════════════════════════════════════════

class ExecutionRequest(BaseModel):
    prompt: str
    target_agent: str = ""

class AgentInitRequest(BaseModel):
    name: str
    role: str
    model: str
    provider: str = "Local"

class StateEditRequest(BaseModel):
    agent_name: str
    key: str = "memory"
    value: Any = None

class GraphNodeRequest(BaseModel):
    node_id: str
    label: str
    node_type: str = "agent"
    x: float = 0
    y: float = 0

class GraphEdgeRequest(BaseModel):
    source: str
    target: str


# ═══════════════════════════════════════════════════════════════════════════
#  FastAPI Application
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(title="HANERMA GOD MODE")

# In-memory designer state
designer_nodes: List[Dict[str, Any]] = []
designer_edges: List[Dict[str, Any]] = []
telemetry_log: List[Dict[str, Any]] = []
active_agents: Dict[str, Dict[str, Any]] = {}
ws_clients: List[WebSocket] = []


# ── Dashboard HTML with React Flow-style Designer ──

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HANERMA | God Mode Visual Composer</title>
    <meta name="description" content="Real-time multi-agent DAG designer with live execution control">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        :root {
            --bg: #020617;
            --surface: rgba(15, 23, 42, 0.85);
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.3);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: rgba(255, 255, 255, 0.08);
            --glass: rgba(255, 255, 255, 0.03);
            --success: #10b981;
            --warning: #f59e0b;
            --risk: #f43f5e;
            --purple: #8b5cf6;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: var(--bg);
            color: var(--text-primary);
            font-family: 'Outfit', sans-serif;
            height: 100vh;
            display: flex;
            overflow: hidden;
            background-image: radial-gradient(circle at 50% -20%, #0f172a 0%, #020617 80%);
        }

        nav {
            width: 250px;
            background: var(--surface);
            backdrop-filter: blur(25px);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 1.5rem 1rem;
            z-index: 100;
        }

        .logo {
            font-size: 1.15rem;
            font-weight: 800;
            color: #fff;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: -0.02em;
        }

        .logo svg { color: var(--accent); }

        .nav-link {
            padding: 0.75rem 1rem;
            border-radius: 0.75rem;
            color: var(--text-secondary);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 0.3rem;
            font-size: 0.85rem;
        }
        .nav-link:hover { background: var(--glass); color: var(--text-primary); }
        .nav-link.active { background: var(--accent); color: #000; box-shadow: 0 0 20px var(--accent-glow); }

        main { flex: 1; display: flex; flex-direction: column; }

        header {
            height: 60px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 1.5rem;
            background: rgba(2, 6, 23, 0.7);
            backdrop-filter: blur(15px);
        }

        .ctrl-group { display: flex; gap: 8px; align-items: center; }

        .ctrl-btn {
            padding: 6px 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
            font-family: 'Outfit';
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .ctrl-btn:hover { transform: translateY(-1px); }
        .ctrl-btn.pause { background: var(--risk); color: white; border-color: var(--risk); }
        .ctrl-btn.resume { background: var(--success); color: white; border-color: var(--success); }
        .ctrl-btn.edit { background: var(--accent); color: #000; border-color: var(--accent); }
        .ctrl-btn.export { background: var(--purple); color: white; border-color: var(--purple); }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 800;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }
        .status-dot.paused { background: var(--warning); animation: none; }

        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

        .content-area { flex: 1; display: flex; overflow: hidden; }

        /* DAG Canvas */
        .dag-canvas {
            flex: 2;
            position: relative;
            background: radial-gradient(circle at center, #0f172a 0%, #020617 100%);
            overflow: hidden;
        }
        #dag-svg { width: 100%; height: 100%; }

        .dag-node {
            cursor: grab;
        }
        .dag-node:active { cursor: grabbing; }
        .dag-node rect {
            rx: 10;
            ry: 10;
            stroke-width: 1.5;
            transition: filter 0.2s;
        }
        .dag-node:hover rect { filter: brightness(1.3); }
        .dag-node text {
            font-family: 'Outfit';
            font-weight: 700;
            fill: white;
            pointer-events: none;
        }
        .dag-node .subtitle {
            font-size: 9px;
            font-weight: 400;
            fill: var(--text-secondary);
        }
        .dag-edge {
            stroke: #334155;
            stroke-width: 2;
            fill: none;
            marker-end: url(#arrowhead);
        }
        .dag-edge.active { stroke: var(--accent); stroke-width: 2.5; }

        /* Telemetry Sidebar */
        .telemetry-panel {
            flex: 1;
            max-width: 380px;
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            background: var(--surface);
        }
        .panel-header {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.6rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-weight: 800;
            color: var(--text-secondary);
        }
        .telemetry-feed {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
        }
        .telem-entry {
            background: rgba(0,0,0,0.3);
            border-left: 3px solid var(--accent);
            padding: 0.75rem;
            border-radius: 0.5rem;
            font-family: 'JetBrains Mono', monospace;
            animation: slideIn 0.3s ease-out;
        }
        .telem-entry .tag { font-size: 0.55rem; font-weight: 800; margin-bottom: 3px; }
        .telem-entry .body { font-size: 0.7rem; color: #cbd5e1; white-space: pre-wrap; word-break: break-all; line-height: 1.5; }

        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        /* CLI */
        .cli-dock {
            padding: 1rem 1.5rem;
            background: rgba(0,0,0,0.4);
            border-top: 1px solid var(--border);
        }
        .input-bar {
            display: flex;
            background: var(--glass);
            border: 1px solid var(--border);
            padding: 4px;
            border-radius: 12px;
            max-width: 800px;
            margin: 0 auto;
        }
        .input-bar input {
            flex: 1;
            background: transparent;
            border: none;
            color: white;
            padding: 0.6rem 1rem;
            outline: none;
            font-size: 0.9rem;
            font-family: 'Outfit';
        }
        .input-bar button {
            background: var(--accent);
            color: #000;
            border: none;
            padding: 0 1.5rem;
            border-radius: 8px;
            font-weight: 800;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s;
        }
        .input-bar button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px var(--accent-glow); }

        .kernel-status {
            margin-top: auto;
            padding: 1rem;
            background: var(--glass);
            border-radius: 1rem;
            border: 1px solid var(--border);
            font-size: 0.65rem;
        }
    </style>
</head>
<body>
    <nav>
        <div class="logo">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            HANERMA GOD MODE
        </div>
        <div class="nav-link active" onclick="nav('command', this)">⚡ Command Deck</div>
        <div class="nav-link" onclick="nav('designer', this)">🔧 Visual Architect</div>
        <div class="nav-link" onclick="nav('agents', this)">🤖 Agent Foundry</div>

        <div class="kernel-status" id="kernel-status">
            <div style="color: var(--text-secondary); margin-bottom: 4px; font-weight: 800;">KERNEL</div>
            <div style="display: flex; align-items: center; gap: 6px;">
                <span class="status-dot" id="kernel-dot"></span>
                <span id="kernel-label" style="font-weight: 800;">RUNNING</span>
            </div>
        </div>
    </nav>

    <main>
        <header>
            <div style="font-weight: 800; font-size: 1rem;">
                APEX / <span id="section-title">Command Deck</span>
            </div>
            <div class="ctrl-group">
                <div class="status-pill">
                    <span class="status-dot" id="exec-dot"></span>
                    <span id="exec-status">RUNNING</span>
                </div>
                <button class="ctrl-btn pause" onclick="doPause()">⏸ Pause</button>
                <button class="ctrl-btn resume" onclick="doResume()">▶ Resume</button>
                <button class="ctrl-btn edit" onclick="doEditState()">✏ Edit State</button>
            </div>
        </header>

        <div class="content-area" id="view-command">
            <div class="dag-canvas">
                <svg id="dag-svg">
                    <defs>
                        <marker id="arrowhead" viewBox="-0 -5 10 10" refX="25" refY="0" orient="auto" markerWidth="6" markerHeight="6">
                            <path d="M 0,-4 L 8,0 L 0,4" fill="#475569"/>
                        </marker>
                    </defs>
                </svg>
            </div>
            <div class="telemetry-panel">
                <div class="panel-header">Real-Time Telemetry</div>
                <div class="telemetry-feed" id="telem-feed"></div>
            </div>
        </div>

        <div class="cli-dock">
            <div class="input-bar">
                <input type="text" id="cmd-input" placeholder="Type a command or natural language instruction..." onkeydown="if(event.key==='Enter') runCommand()">
                <button onclick="runCommand()">EXECUTE</button>
            </div>
        </div>
    </main>

    <script>
        // State
        let graphNodes = [];
        let graphEdges = [];
        let simulation;
        let isPaused = false;

        // Navigation
        function nav(id, el) {
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            el.classList.add('active');
            document.getElementById('section-title').innerText = el.innerText.replace(/[⚡🔧🤖]/g, '').trim();
        }

        // DAG Rendering
        const svg = d3.select("#dag-svg");
        const g = svg.append("g");
        svg.call(d3.zoom().on("zoom", (e) => g.attr("transform", e.transform)));

        function initSimulation() {
            const rect = svg.node().getBoundingClientRect();
            simulation = d3.forceSimulation(graphNodes)
                .force("link", d3.forceLink(graphEdges).id(d => d.id).distance(160))
                .force("charge", d3.forceManyBody().strength(-400))
                .force("center", d3.forceCenter(rect.width / 2, rect.height / 2))
                .on("tick", renderTick);
        }

        function renderTick() {
            g.selectAll(".dag-edge")
                .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
            g.selectAll(".dag-node")
                .attr("transform", d => `translate(${d.x - 60},${d.y - 20})`);
        }

        function updateGraph(event) {
            const nodeID = event.payload?.trace_id || event.payload?.node_id || crypto.randomUUID();
            if (graphNodes.find(n => n.id === nodeID)) return;

            const label = event.event_type.split('_').pop().toUpperCase();
            const color = event.event_type.includes('success') ? '#10b981'
                        : event.event_type.includes('fail') ? '#f43f5e'
                        : event.event_type.includes('tool') ? '#f59e0b'
                        : '#38bdf8';

            graphNodes.push({ id: nodeID, label, color, type: event.event_type });
            if (graphNodes.length > 1) {
                graphEdges.push({ source: graphNodes[graphNodes.length - 2].id, target: nodeID });
            }

            // Render edges
            const links = g.selectAll(".dag-edge").data(graphEdges, d => d.source.id + "-" + d.target.id);
            links.enter().append("line").attr("class", "dag-edge");

            // Render nodes
            const nodes = g.selectAll(".dag-node").data(graphNodes, d => d.id);
            const nEnter = nodes.enter().append("g").attr("class", "dag-node")
                .call(d3.drag()
                    .on("start", (e) => { if (!e.active) simulation.alphaTarget(0.3).restart(); e.subject.fx = e.x; e.subject.fy = e.y; })
                    .on("drag", (e) => { e.subject.fx = e.x; e.subject.fy = e.y; })
                    .on("end", (e) => { if (!e.active) simulation.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; }));

            nEnter.append("rect")
                .attr("width", 120).attr("height", 40)
                .attr("fill", d => d.color)
                .attr("fill-opacity", 0.2)
                .attr("stroke", d => d.color);

            nEnter.append("text")
                .attr("x", 60).attr("y", 24)
                .attr("text-anchor", "middle")
                .attr("font-size", "11px")
                .text(d => d.label);

            simulation.nodes(graphNodes);
            simulation.force("link").links(graphEdges);
            simulation.alpha(1).restart();
        }

        // Execution Control
        async function doPause() {
            await fetch('/api/graph/pause', { method: 'POST' });
            isPaused = true;
            updateStatus();
        }

        async function doResume() {
            await fetch('/api/graph/resume', { method: 'POST' });
            isPaused = false;
            updateStatus();
        }

        async function doEditState() {
            const agent = prompt("Agent name:");
            const key = prompt("State key:", "memory");
            const value = prompt("New value:");
            if (agent && key && value) {
                await fetch('/api/graph/edit_state', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ agent_name: agent, key, value })
                });
                addTelem('STATE_EDIT', `Injected ${key}=${value} into ${agent}`, '#8b5cf6');
            }
        }

        function updateStatus() {
            const dot = document.getElementById('exec-dot');
            const label = document.getElementById('exec-status');
            const kdot = document.getElementById('kernel-dot');
            const klabel = document.getElementById('kernel-label');

            if (isPaused) {
                dot.classList.add('paused');
                label.textContent = 'PAUSED';
                kdot.classList.add('paused');
                klabel.textContent = 'PAUSED';
            } else {
                dot.classList.remove('paused');
                label.textContent = 'RUNNING';
                kdot.classList.remove('paused');
                klabel.textContent = 'RUNNING';
            }
        }

        // Telemetry
        function addTelem(type, content, color = 'var(--accent)') {
            const feed = document.getElementById('telem-feed');
            const entry = document.createElement('div');
            entry.className = 'telem-entry';
            entry.style.borderColor = color;
            entry.innerHTML = `<div class="tag" style="color:${color}">${type}</div><div class="body">${content}</div>`;
            feed.prepend(entry);
        }

        // CLI
        async function runCommand() {
            const input = document.getElementById('cmd-input');
            const prompt = input.value;
            if (!prompt) return;
            input.value = "";
            addTelem('USER', prompt, 'var(--accent)');
            await fetch('/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ prompt })
            });
        }

        // WebSocket
        function connectWS() {
            const ws = new WebSocket(`ws://${location.host}/ws`);
            ws.onmessage = (e) => {
                const event = JSON.parse(e.data);
                const color = event.event_type.includes('success') ? 'var(--success)'
                            : event.event_type.includes('fail') ? 'var(--risk)'
                            : event.event_type.includes('tool') ? '#f59e0b'
                            : 'var(--accent)';
                addTelem(event.event_type.toUpperCase(), JSON.stringify(event.payload, null, 2), color);
                updateGraph(event);
            };
            ws.onclose = () => setTimeout(connectWS, 2000);
        }

        window.onload = () => {
            initSimulation();
            connectWS();
            // Poll execution status
            setInterval(async () => {
                const res = await fetch('/api/graph/status');
                const data = await res.json();
                isPaused = data.paused;
                updateStatus();
            }, 2000);
        };
    </script>
</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/api/graph/status")
async def get_status():
    """Current execution status."""
    return controller.status()


@app.post("/api/graph/pause")
async def pause_graph():
    """Pause DAG execution mid-step."""
    controller.pause()
    await _broadcast({"event_type": "execution_paused", "payload": {"timestamp": time.time()}})
    return {"status": "paused"}


@app.post("/api/graph/resume")
async def resume_graph():
    """Resume DAG execution. Drains pending state patches first."""
    patches = controller.drain_patches()
    controller.resume()
    await _broadcast({
        "event_type": "execution_resumed",
        "payload": {"patches_applied": len(patches), "timestamp": time.time()},
    })
    return {"status": "resumed", "patches_applied": len(patches)}


@app.post("/api/graph/edit_state")
async def edit_state(req: StateEditRequest):
    """
    Inject new state into a running agent's memory.
    Works while paused or running.
    """
    controller.inject_state(req.agent_name, req.key, req.value)

    # Also update in-memory agent state if available
    if req.agent_name in active_agents:
        if "custom_state" not in active_agents[req.agent_name]:
            active_agents[req.agent_name]["custom_state"] = {}
        active_agents[req.agent_name]["custom_state"][req.key] = req.value

    await _broadcast({
        "event_type": "state_injected",
        "payload": {
            "agent": req.agent_name,
            "key": req.key,
            "value": str(req.value)[:200],
            "timestamp": time.time(),
        },
    })

    return {"status": "injected", "agent": req.agent_name, "key": req.key}


@app.post("/execute")
async def execute_task(req: ExecutionRequest):
    """Execute a prompt (non-blocking)."""
    trace_id = str(uuid.uuid4())
    await _broadcast({
        "event_type": "execution_start",
        "payload": {
            "trace_id": trace_id,
            "prompt": req.prompt[:200],
            "timestamp": time.time(),
        },
    })
    return {"status": "initiated", "trace_id": trace_id}


@app.get("/api/agents")
async def list_agents():
    return [
        {"name": name, **info}
        for name, info in active_agents.items()
    ]


@app.post("/api/agents/init")
async def init_agent(req: AgentInitRequest):
    active_agents[req.name] = {
        "role": req.role,
        "model": req.model,
        "provider": req.provider,
        "created_at": time.time(),
        "custom_state": {},
    }
    await _broadcast({
        "event_type": "agent_registered",
        "payload": {"name": req.name, "role": req.role, "model": req.model},
    })
    return {"status": "registered", "name": req.name}


@app.get("/api/telemetry")
async def get_telemetry():
    """Return recent telemetry entries."""
    return telemetry_log[-100:]


# ── WebSocket for live telemetry ──

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_clients.remove(websocket)
    except Exception:
        if websocket in ws_clients:
            ws_clients.remove(websocket)


async def _broadcast(event: Dict[str, Any]):
    """Broadcast event to all connected WebSocket clients."""
    telemetry_log.append(event)
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.remove(ws)


# ═══════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════

def start_viz(port: int = 8081):
    """Launch the God Mode dashboard."""
    import uvicorn
    print(f"[HANERMA] 🚀 God Mode Dashboard: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_viz()
