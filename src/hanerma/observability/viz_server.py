from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import json
import sqlite3
import os
import asyncio
import uuid
from pydantic import BaseModel
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.interface.minimalist import create_agent

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(title="HANERMA Viz")

# Simple HTML dashboard template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HANERMA APEX | AI Orchestration OS</title>
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@100;300;400;600;800&family=Raleway:wght@200;400;700&display=swap" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        :root { 
            --bg: #030712; 
            --card: rgba(30, 41, 59, 0.7); 
            --accent: #38bdf8; 
            --accent-glow: rgba(56, 189, 248, 0.3);
            --text: #f8fafc; 
            --risk: #f43f5e; 
            --success: #10b981;
            --glass: rgba(255, 255, 255, 0.03);
            --border: rgba(255, 255, 255, 0.1);
        }
        
        * { box-sizing: border-box; transition: all 0.2s ease; }
        body { 
            background: radial-gradient(circle at top right, #0f172a, #030712); 
            color: var(--text); 
            font-family: 'Be Vietnam Pro', sans-serif; 
            margin: 0; 
            padding: 1.5rem; 
            overflow: hidden; 
            height: 100vh; 
            display: flex; 
            flex-direction: column; 
        }

        header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
            background: var(--glass);
            padding: 1rem 2rem;
            border-radius: 1rem;
            border: 1px solid var(--border);
        }

        h1 { 
            font-family: 'Raleway', sans-serif;
            font-weight: 800;
            font-size: 1.5rem;
            margin: 0;
            letter-spacing: 2px;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .main-layout { 
            display: grid; 
            grid-template-columns: 1fr 2fr 1fr; 
            gap: 1.5rem; 
            flex: 1; 
            min-height: 0; 
        }

        .card { 
            background: var(--card); 
            backdrop-filter: blur(12px);
            border-radius: 1.25rem; 
            border: 1px solid var(--border); 
            display: flex; 
            flex-direction: column; 
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .card-header {
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-family: 'Raleway', sans-serif;
            font-weight: 700;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #94a3b8;
        }

        /* Chat Interface */
        #chat-section { display: flex; flex-direction: column; height: 100%; }
        #chat-messages { flex: 1; overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
        .msg { padding: 1rem; border-radius: 1rem; max-width: 85%; font-size: 0.9rem; line-height: 1.5; }
        .msg.user { align-self: flex-end; background: #3b82f6; color: white; border-bottom-right-radius: 0.2rem; }
        .msg.bot { align-self: flex-start; background: var(--glass); border: 1px solid var(--border); border-bottom-left-radius: 0.2rem; }
        
        #input-area { 
            padding: 1rem; 
            background: rgba(0,0,0,0.2); 
            border-top: 1px solid var(--border);
            display: flex;
            gap: 0.5rem;
        }
        input { 
            flex: 1; 
            background: var(--glass); 
            border: 1px solid var(--border); 
            color: white; 
            padding: 0.75rem 1rem; 
            border-radius: 0.75rem;
            outline: none;
        }
        input:focus { border-color: var(--accent); }
        button { 
            background: var(--accent); 
            color: var(--bg); 
            border: none; 
            padding: 0.75rem 1.25rem; 
            border-radius: 0.75rem; 
            font-weight: 800; 
            cursor: pointer;
        }
        button:hover { filter: brightness(1.1); transform: translateY(-1px); }

        /* Graph Styling */
        #graph-container { flex: 1; cursor: grab; background: radial-gradient(circle at center, #1e293b 0%, #030712 100%); }
        .node circle { fill: var(--accent); filter: drop-shadow(0 0 8px var(--accent-glow)); stroke: #fff; stroke-width: 1.5px; }
        .node text { fill: #94a3b8; font-size: 11px; font-weight: 600; font-family: 'Raleway'; }
        .link { stroke: #334155; stroke-opacity: 0.4; stroke-width: 1.5px; marker-end: url(#arrowhead); }

        /* Trace Logs */
        #trace-log { flex: 1; overflow-y: auto; padding: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; }
        .log-entry { 
            padding: 0.75rem; 
            background: rgba(0,0,0,0.2); 
            border-radius: 0.5rem; 
            margin-bottom: 0.75rem; 
            border-left: 3px solid var(--accent);
            animation: fadeIn 0.4s ease;
        }
        .log-entry.risk { border-left-color: var(--risk); background: rgba(244, 63, 94, 0.05); }

        @keyframes fadeIn { from { opacity: 0; opacity: 0; } to { opacity: 1; } }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
    </style>
</head>
<body>
    <header>
        <h1>HANERMA APEX <span style="font-weight: 300; font-size: 0.6em; color: #94a3b8;">ORCHESTRATION OS</span></h1>
        <div style="display: flex; gap: 2rem; align-items: center;">
            <div id="status" style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; font-weight: 600;">
                <span style="width: 8px; height: 8px; border-radius: 50%; background: #4ade80; display: inline-block;"></span> 
                ENGINE ACTIVE
            </div>
            <button onclick="clearSystem()" style="background: transparent; border: 1px solid var(--risk); color: var(--risk); padding: 4px 12px; font-size: 0.7rem;">RESET CORE</button>
        </div>
    </header>

    <div class="main-layout">
        <!-- Dashboard / Metrics -->
        <div class="card">
            <div class="card-header"><span class="card-title">System Metrics</span></div>
            <div id="metrics" style="padding: 1.5rem; display: grid; gap: 1rem;">
                <div style="background: var(--glass); padding: 1rem; border-radius: 0.75rem; border: 1px solid var(--border);">
                    <div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 0.25rem;">LATENCY</div>
                    <div id="m-latency" style="font-size: 1.5rem; font-weight: 800; color: var(--accent);">0.00ms</div>
                </div>
                <div style="background: var(--glass); padding: 1rem; border-radius: 0.75rem; border: 1px solid var(--border);">
                    <div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 0.25rem;">TOTAL TOKENS</div>
                    <div id="m-tokens" style="font-size: 1.5rem; font-weight: 800; color: #818cf8;">0</div>
                </div>
                <div style="background: var(--glass); padding: 1rem; border-radius: 0.75rem; border: 1px solid var(--border);">
                    <div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 0.25rem;">RISK SCORE</div>
                    <div id="m-risk" style="font-size: 1.5rem; font-weight: 800; color: var(--success);">0.02</div>
                </div>
            </div>
            <div class="card-header" style="border-top: 1px solid var(--border);"><span class="card-title">Causal Trace</span></div>
            <div id="trace-log"></div>
        </div>

        <!-- Causal Graph -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Causal Execution Map</span>
                <span id="trace-id" style="font-size: 0.6rem; color: #64748b; font-family: monospace;">UUID: 0000-0000-0000</span>
            </div>
            <div id="graph-container"></div>
        </div>

        <!-- Execution / Chat -->
        <div class="card" id="chat-section">
            <div class="card-header"><span class="card-title">Interactive Terminal</span></div>
            <div id="chat-messages">
                <div class="msg bot">System initialized. Ready for Apex flow execution.</div>
            </div>
            <div id="input-area">
                <input type="text" id="prompt-input" placeholder="Initiate complex task..." onkeypress="handleKey(event)">
                <button onclick="executeTask()">RUN</button>
            </div>
        </div>
    </div>

    <script>
        // --- D3 Graph Logic ---
        const gc = d3.select("#graph-container");
        let width = gc.node().getBoundingClientRect().width;
        let height = gc.node().getBoundingClientRect().height;

        const svg = gc.append("svg").attr("width", "100%").attr("height", "100%")
                    .call(d3.zoom().on("zoom", (e) => g.attr("transform", e.transform)));
        
        // Marker for directed links
        svg.append("defs").append("marker")
            .attr("id", "arrowhead").attr("viewBox", "-0 -5 10 10").attr("refX", 20).attr("refY", 0)
            .attr("orient", "auto").attr("markerWidth", 6).attr("markerHeight", 6).attr("xoverflow", "visible")
            .append("svg:path").attr("d", "M 0,-5 L 10 ,0 L 0,5").attr("fill", "#334155").style("stroke","none");

        const g = svg.append("g");
        const linkGroup = g.append("g").attr("class", "links");
        const nodeGroup = g.append("g").attr("class", "nodes");

        let nodes = [];
        let links = [];

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .on("tick", () => {
                linkGroup.selectAll("line").attr("x1", d => d.source.x).attr("y1", d => d.source.y).attr("x2", d => d.target.x).attr("y2", d => d.target.y);
                nodeGroup.selectAll("g").attr("transform", d => `translate(${d.x},${d.y})`);
            });

        function updateGraph(data) {
            if (nodes.find(n => n.id === data.id)) return;
            
            const newNode = { id: data.id, label: data.event_type.toUpperCase().replace(/_/g, ' '), type: data.event_type };
            nodes.push(newNode);
            if (nodes.length > 1) links.push({source: nodes[nodes.length-2].id, target: newNode.id});

            const l = linkGroup.selectAll("line").data(links, d => d.source.id + "-" + d.target.id);
            l.enter().append("line").attr("class", "link");

            const n = nodeGroup.selectAll("g").data(nodes, d => d.id);
            const nEnter = n.enter().append("g").attr("class", "node").call(d3.drag().on("start", ds).on("drag", d).on("end", de));
            
            nEnter.append("circle").attr("r", 9).style("fill", d => d.type.includes('risk') ? 'var(--risk)' : (d.type.includes('complete') ? 'var(--success)' : 'var(--accent)'));
            nEnter.append("text").attr("dx", 15).attr("dy", ".35em").text(d => d.label);

            simulation.nodes(nodes);
            simulation.force("link").links(links);
            simulation.alpha(1).restart();
        }

        function ds(e) { if (!e.active) simulation.alphaTarget(0.3).restart(); e.subject.fx = e.subject.x; e.subject.fy = e.subject.y; }
        function d(e) { e.subject.fx = e.x; e.subject.fy = e.y; }
        function de(e) { if (!e.active) simulation.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; }

        // --- Communication ---
        const ws = new WebSocket(`ws://${location.host}/ws`);
        const traceLog = document.getElementById('trace-log');
        const chatBox = document.getElementById('chat-messages');

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // Update Trace
            const entry = document.createElement('div');
            entry.className = "log-entry " + data.event_type;
            entry.innerHTML = `<div style="color: var(--accent); font-weight: 800; font-size: 0.6rem;">${data.event_type}</div>
                               <div style="color: #cbd5e1; white-space: pre-wrap; font-size: 0.65rem;">${JSON.stringify(data.payload, null, 2)}</div>`;
            traceLog.prepend(entry);
            
            // Update Graph
            updateGraph(data);

            // Update Metrics
            if (data.event_type === 'task_start') document.getElementById('trace-id').innerText = "TRACE: " + data.id;
            if (data.payload.metrics) {
                document.getElementById('m-latency').innerText = data.payload.metrics.latency_ms + "ms";
                document.getElementById('m-tokens').innerText = data.payload.metrics.total_tokens;
            }
        };

        async function executeTask() {
            const input = document.getElementById('prompt-input');
            const prompt = input.value;
            if (!prompt) return;

            // Add User Message
            const uMsg = document.createElement('div');
            uMsg.className = "msg user";
            uMsg.innerText = prompt;
            chatBox.appendChild(uMsg);
            chatBox.scrollTop = chatBox.scrollHeight;
            input.value = "";

            try {
                const res = await fetch('/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt, target_agent: 'ApexDev' })
                });
                const data = await res.json();
                
                const bMsg = document.createElement('div');
                bMsg.className = "msg bot";
                bMsg.innerText = data.output;
                chatBox.appendChild(bMsg);
                chatBox.scrollTop = chatBox.scrollHeight;
            } catch (e) {
                console.error(e);
            }
        }

        function handleKey(e) { if (e.key === 'Enter') executeTask(); }

        async function clearSystem() {
            await fetch('/clear');
            location.reload();
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(content=DASHBOARD_HTML)

class ExecutionRequest(BaseModel):
    prompt: str
    target_agent: str = "ApexDev"

# Global Orchestrator for the UI
orchestrator = HANERMAOrchestrator(model="Qwen/Qwen3-Coder-Next-FP8:together")
# Setup tools for the demo
def search_expert_docs(query: str = "SymbolicReasoner"):
    return f"Documentation for '{query}': Use HANERMA SymbolicReasoner to catch logical drift."
def git_commit_changes(message: str):
    return f"Successfully committed: {message}"

dev_agent = create_agent("ApexDev", role="Senior Engineer", tools=[search_expert_docs, git_commit_changes])
orchestrator.register_agent(dev_agent)

@app.post("/execute")
async def execute_task(req: ExecutionRequest):
    try:
        # Move state ID to a fresh trace for each UI click
        orchestrator.trace_id = str(uuid.uuid4())
        orchestrator.step_index = 0
        result = orchestrator.run(req.prompt, target_agent=req.target_agent)
        return result
    except Exception as e:
        return {"output": f"Error: {str(e)}", "status": "error"}

@app.get("/clear")
async def clear_logs():
    db_path = "hanerma_state.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    return {"status": "cleared"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_id = 0
    db_path = "hanerma_state.db"
    
    # 1. First, send ALL historical logs
    try:
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT id, event_type, payload FROM events ORDER BY id ASC")
                rows = cursor.fetchall()
                for row in rows:
                    last_id = row[0]
                    await websocket.send_json({
                        "id": row[0],
                        "event_type": row[1],
                        "payload": json.loads(row[2])
                    })
    except Exception as e:
        print(f"[Viz History Error] {e}")

    # 2. Then, tail the database for new logs
    while True:
        try:
            if os.path.exists(db_path):
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.execute(
                        "SELECT id, event_type, payload FROM events WHERE id > ? ORDER BY id ASC", 
                        (last_id,)
                    )
                    rows = cursor.fetchall()
                    for row in rows:
                        last_id = row[0]
                        await websocket.send_json({
                            "id": row[0],
                            "event_type": row[1],
                            "payload": json.loads(row[2])
                        })
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[Viz WS Error] {e}")
            break

def start_viz(port: int = 8081):
    print(f"[HANERMA] Launching Visual Dashboard on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_viz()
