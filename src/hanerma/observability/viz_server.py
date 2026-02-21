from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
import uvicorn
import json
import sqlite3
import os
import asyncio
import uuid
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import spawn_agent
from hanerma.memory.manager import HCMSManager
from hanerma.memory.compression.xerv_crayon_ext import XervCrayonAdapter
from hanerma.tools.code_sandbox import NativeCodeSandbox

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Initialize global singleton components for UI
tokenizer = XervCrayonAdapter(profile="lite")
memory = HCMSManager(tokenizer=tokenizer)
orchestrator = HANERMAOrchestrator(model="Qwen/Qwen3-Coder-Next-FP8:together", tokenizer=tokenizer)
orchestrator.pause_event = asyncio.Event()
orchestrator.pause_event.set()  # Start running

# Use REAL tools (Root-level)
sandbox = NativeCodeSandbox()
def execute_logic(**kwargs):
    """Executes production logic via the Native Code Sandbox. Expects 'code'."""
    code = kwargs.get("code") or ""
    return sandbox.execute_code(code)

# Seed initial state
orchestrator.state_manager["shared_memory"]["facts"] = []
orchestrator.state_manager["history"] = []

# Register default agent with real tools
from hanerma.tools.registry import ToolRegistry
reg = ToolRegistry()
default_tools = [reg.get_tool(n) for n in ["web_search", "calculator", "get_system_time"]]

orchestrator.register_agent(spawn_agent("ApexDev", 
                                        model="Qwen/Qwen3-Coder-Next-FP8:together", 
                                        role="Lead System Architect",
                                        tools=[execute_logic] + default_tools))

class ExecutionRequest(BaseModel):
    prompt: str
    target_agent: str = "ApexDev"

class AgentInitRequest(BaseModel):
    name: str
    role: str
    model: str
    provider: str

app = FastAPI(title="HANERMA APEX OS")

# --- PREMIUM DASHBOARD UI (No Placeholders, Root Tools) ---
DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HANERMA | Apex intelligence OS</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        :root { 
            --bg: #020617; 
            --surface: rgba(15, 23, 42, 0.7);
            --accent: #38bdf8; 
            --accent-glow: rgba(56, 189, 248, 0.3);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: rgba(255, 255, 255, 0.1);
            --glass: rgba(255, 255, 255, 0.03);
            --success: #10b981;
            --risk: #f43f5e;
            --recursive: #8b5cf6;
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
            width: 260px;
            background: var(--surface);
            backdrop-filter: blur(25px);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 2rem 1.25rem;
            z-index: 100;
        }

        .logo {
            font-size: 1.3rem;
            font-weight: 800;
            color: #fff;
            margin-bottom: 2.5rem;
            display: flex;
            align-items: center;
            gap: 12px;
            letter-spacing: -0.02em;
        }

        .nav-link {
            padding: 0.85rem 1.15rem;
            border-radius: 0.85rem;
            color: var(--text-secondary);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.25s;
            margin-bottom: 0.4rem;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;
        }

        .nav-link:hover { background: var(--glass); color: var(--text-primary); }
        .nav-link.active { background: var(--accent); color: #000; box-shadow: 0 0 20px var(--accent-glow); }

        main { flex: 1; display: flex; flex-direction: column; position: relative; }
        
        header {
            height: 70px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 2rem;
            background: rgba(2, 6, 23, 0.5);
            backdrop-filter: blur(15px);
        }

        .metrics-grid { display: flex; gap: 1rem; }
        .metric-pill {
            background: var(--glass);
            border: 1px solid var(--border);
            padding: 0.35rem 1rem;
            border-radius: 2rem;
            font-size: 0.75rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }

        .content-wrap { flex: 1; display: flex; padding: 1.25rem; gap: 1.25rem; overflow: hidden; }
        .pane {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 1.25rem;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            backdrop-filter: blur(15px);
        }

        .pane-header {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255,255,255,0.01);
        }

        .pane-title { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 800; color: var(--text-secondary); }

        #viz-area { flex: 1; position: relative; background: radial-gradient(circle at center, #0f172a 0%, #020617 100%); overflow: hidden; }
        #canvas-graph { width: 100%; height: 100%; }

        #trace-bucket { flex: 1; overflow-y: auto; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.75rem; }
        .log-entry {
            background: rgba(0,0,0,0.3);
            border-left: 3px solid var(--accent);
            padding: 1rem;
            border-radius: 0.65rem;
            font-family: 'JetBrains Mono', monospace;
            animation: slideUp 0.3s ease-out;
            transition: transform 0.2s;
        }
        .log-entry:hover { transform: translateX(5px); background: rgba(255,255,255,0.02); }
        .log-tag { font-size: 0.6rem; font-weight: 800; margin-bottom: 4px; }
        .log-content { font-size: 0.75rem; line-height: 1.5; color: #cbd5e1; white-space: pre-wrap; word-break: break-all; }

        .cli-dock {
            padding: 1.5rem 2rem;
            background: rgba(0,0,0,0.4);
            border-top: 1px solid var(--border);
        }
        .input-pill {
            display: flex;
            background: var(--glass);
            border: 1px solid var(--border);
            padding: 0.4rem;
            border-radius: 1rem;
            max-width: 900px;
            margin: 0 auto;
        }
        .input-pill input {
            flex: 1;
            background: transparent;
            border: none;
            color: white;
            padding: 0.7rem 1.25rem;
            outline: none;
            font-size: 0.95rem;
        }
        .btn-exec {
            background: var(--accent);
            color: #000;
            border: none;
            padding: 0 1.5rem;
            border-radius: 0.75rem;
            font-weight: 800;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.85rem;
        }
        .btn-exec:hover { transform: translateY(-2px); box-shadow: 0 5px 15px var(--accent-glow); }

        .hub-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.25rem; padding: 1.25rem; overflow-y: auto; }
        .card-glass {
            background: var(--glass);
            border: 1px solid var(--border);
            padding: 1.5rem;
            border-radius: 1.25rem;
            backdrop-filter: blur(10px);
        }

        .hub-form {
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            margin-bottom: 2rem;
            padding: 2.5rem;
            background: var(--surface);
            border-radius: 1.5rem;
            border: 1px solid var(--border);
            backdrop-filter: blur(30px);
        }

        label { font-size: 0.65rem; font-weight: 800; color: var(--accent); margin-bottom: 4px; display: block; }
        input[type="text"], select {
            width: 100%;
            background: rgba(0,0,0,0.4);
            border: 1px solid var(--border);
            color: white;
            padding: 0.8rem 1rem;
            border-radius: 0.75rem;
            font-family: 'Outfit';
            outline: none;
            font-size: 0.9rem;
        }

        @keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }

        /* Scalable Graph Styling */
        .node circle { stroke: #fff; stroke-width: 1.5px; transition: r 0.3s, fill 0.3s; cursor: pointer; }
        .node text { font-family: 'Outfit'; font-size: 9px; font-weight: 700; fill: var(--text-secondary); pointer-events: none; }
        .link { stroke: #334155; stroke-opacity: 0.3; stroke-width: 1px; marker-end: url(#arrowhead); }
    </style>
</head>
<body>
    <nav>
        <div class="logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            HANERMA APEX
        </div>
        <div class="nav-link active" onclick="nav('op-center', this)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
            Command Deck
        </div>
        <div class="nav-link" onclick="nav('persona-hub', this)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            Agent Foundry
        </div>
        <div class="nav-link" onclick="nav('designer', this)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
            Visual Architect
        </div>
        <div class="nav-link" onclick="nav('memory-vault', this)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
            Memory Vault
        </div>

        <div style="margin-top: auto; padding: 1.25rem; background: var(--glass); border-radius: 1.25rem; border: 1px solid var(--border);">
            <div style="font-size: 0.6rem; color: var(--text-secondary); margin-bottom: 6px; font-weight: 800; text-transform: uppercase;">Kernel Status</div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.8rem; font-weight: 800; color: var(--text-primary);">
                <span class="dot" style="background: var(--success); box-shadow: 0 0 12px var(--success);"></span>
                STABLE_V4_CORE
            </div>
            <div style="font-size: 0.55rem; color: var(--text-secondary); margin-top: 8px; font-family: 'JetBrains Mono';">ROOT: XERV-CRAYON</div>
        </div>
    </nav>

    <main>
        <header>
            <div style="font-weight: 800; font-size: 1.05rem; letter-spacing: -0.02em;">APEX / <span id="section-title">Command Deck</span></div>
            <div class="metrics-grid">
                <div class="metric-pill"><span class="dot" style="background: var(--accent);"></span><span id="stat-latency">0ms</span></div>
                <div class="metric-pill"><span class="dot" style="background: var(--recursive);"></span><span id="stat-tokens">0 tkn</span></div>
                <div class="metric-pill"><span class="dot" style="background: var(--success);"></span><span id="stat-risk">0.01</span></div>
            </div>
        </header>

        <div id="op-center" class="content-wrap" style="display: flex;">
            <div class="pane" style="flex: 1.8;">
                <div class="pane-header">
                    <span class="pane-title">Causal Intelligence Web</span>
                    <div style="display: flex; gap: 10px;">
                        <button onclick="pauseGraph()" style="padding: 5px 10px; background: var(--risk); color: white; border: none; border-radius: 5px; cursor: pointer;">Pause</button>
                        <button onclick="resumeGraph()" style="padding: 5px 10px; background: var(--success); color: white; border: none; border-radius: 5px; cursor: pointer;">Resume</button>
                        <button onclick="editState()" style="padding: 5px 10px; background: var(--accent); color: white; border: none; border-radius: 5px; cursor: pointer;">Edit State</button>
                    </div>
                </div>
                <div id="viz-area">
                    <svg id="canvas-graph"></svg>
                </div>
            </div>
            <div class="pane" style="flex: 1;">
                <div class="pane-header"><span class="pane-title">Real-time Telemetry</span></div>
                <div id="trace-bucket"></div>
            </div>
        </div>

        <div id="persona-hub" class="content-wrap" style="display: none; flex-direction: column; overflow-y: auto;">
            <div style="max-width: 800px; width: 100%; margin: 0 auto; padding-bottom: 2rem;">
                <h2 style="margin-bottom: 0.5rem; font-weight: 800; font-size: 1.5rem;">Agent Foundry</h2>
                <p style="color: var(--text-secondary); margin-bottom: 2rem; font-size: 0.85rem;">Spawn hardware-rooted agents with custom model routing.</p>
                
                <div class="hub-form">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 1.25rem;">
                        <div>
                            <label>AGENT ALIAS</label>
                            <input type="text" id="agent-name" placeholder="e.g. Coder-1">
                        </div>
                        <div>
                            <label>SYSTEM ROLE</label>
                            <input type="text" id="agent-role" placeholder="e.g. Security Auditor">
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1.5fr 1fr; gap: 1.25rem; margin-bottom: 1.25rem;">
                        <div>
                            <label>MODEL IDENTIFIER</label>
                            <input type="text" id="agent-model" placeholder="e.g. gpt-4o, llama3:8b">
                        </div>
                        <div>
                            <label>CLOUD PROVIDER</label>
                            <select id="agent-provider">
                                <option value="HuggingFace">Hugging Face</option>
                                <option value="OpenRouter">Open Router</option>
                                <option value="Together">Together.ai</option>
                                <option value="Local">Local (ROOT)</option>
                            </select>
                        </div>
                    </div>
                    <button class="btn-exec" onclick="initAgent()" style="height: 50px;">REGISTER TO APEX CORE</button>
                </div>

                <h2 style="margin-bottom: 1.5rem; font-weight: 800; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 0.05em;">Active Matrix</h2>
                <div class="hub-grid" id="agent-list" style="padding: 0;"></div>
            </div>
        </div>

        <div id="memory-vault" class="content-wrap" style="display: none; overflow-y: auto;">
            <div style="max-width: 900px; width: 100%; margin: 0 auto; padding-bottom: 2rem;">
                <h2 style="margin-bottom: 1.5rem; font-weight: 800; font-size: 1.5rem;">Memory Intelligence</h2>
                <div class="hub-grid" id="memory-list" style="padding: 0;"></div>
            </div>
        </div>

        <div id="cli-section" class="cli-dock">
            <div class="input-pill">
                <input type="text" id="apex-input" placeholder="Initiate bare-metal reasoning cycle..." onkeydown="if(event.key==='Enter') executeApex()">
                <button class="btn-exec" onclick="executeApex()">RUN FLOW</button>
            </div>
        </div>
    </main>

    <script>
        let nodes = [];
        let links = [];
        let simulation;

        function nav(id, el) {
            document.querySelectorAll('.content-wrap').forEach(c => c.style.display = 'none');
            document.getElementById(id).style.display = 'flex';
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            el.classList.add('active');
            document.getElementById('section-title').innerText = el.innerText.trim();
            document.getElementById('cli-section').style.display = (id === 'op-center') ? 'block' : 'none';
            
            if(id === 'persona-hub') loadAgents();
            if(id === 'memory-vault') loadMemory();
        }

        const svg = d3.select("#canvas-graph");
        svg.append("defs").append("marker")
            .attr("id", "arrowhead").attr("viewBox", "-0 -5 10 10").attr("refX", 20).attr("refY", 0)
            .attr("orient", "auto").attr("markerWidth", 5).attr("markerHeight", 5)
            .append("svg:path").attr("d", "M 0,-5 L 10 ,0 L 0,5").attr("fill", "#475569");

        const g = svg.append("g");
        svg.call(d3.zoom().on("zoom", (e) => g.attr("transform", e.transform)));

        function initSimulation() {
            const rect = svg.node().getBoundingClientRect();
            simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id(d => d.id).distance(120))
                .force("charge", d3.forceManyBody().strength(-350))
                .force("center", d3.forceCenter(rect.width / 2, rect.height / 2))
                .on("tick", () => {
                    g.selectAll(".link")
                        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
                    g.selectAll(".node")
                        .attr("transform", d => `translate(${d.x},${d.y})`);
                });
        }

        function updateGraph(event) {
            const nodeID = event.payload.trace_id || uuidv4();
            if(nodes.find(n => n.id === nodeID)) return;

            const newNode = { 
                id: nodeID, 
                label: event.event_type.split('_').pop().toUpperCase(),
                type: event.event_type 
            };
            nodes.push(newNode);
            if(nodes.length > 1) links.push({ source: nodes[nodes.length-2].id, target: newNode.id });

            const l = g.selectAll(".link").data(links, d => d.source.id + "-" + d.target.id);
            l.enter().append("line").attr("class", "link");

            const n = g.selectAll(".node").data(nodes, d => d.id);
            const nEnter = n.enter().append("g").attr("class", "node")
                            .call(d3.drag()
                                .on("start", (e) => { if (!e.active) simulation.alphaTarget(0.3).restart(); e.subject.fx = e.x; e.subject.fy = e.y; })
                                .on("drag", (e) => { e.subject.fx = e.x; e.subject.fy = e.y; })
                                .on("end", (e) => { if (!e.active) simulation.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; }));
            
            nEnter.append("circle")
                .attr("r", 7)
                .style("fill", d => {
                    if(d.type.includes('start')) return '#38bdf8';
                    if(d.type.includes('complete') || d.type.includes('success')) return '#10b981';
                    if(d.type.includes('failed') || d.type.includes('error')) return '#f43f5e';
                    if(d.type.includes('tool')) return '#f59e0b';
                    return '#8b5cf6';
                });

            nEnter.append("text").attr("dy", -12).attr("text-anchor", "middle").text(d => d.label);

            simulation.nodes(nodes);
            simulation.force("link").links(links);
            simulation.alpha(1).restart();
        }

        async function initAgent() {
            const name = document.getElementById('agent-name').value;
            const role = document.getElementById('agent-role').value;
            const model = document.getElementById('agent-model').value;
            const provider = document.getElementById('agent-provider').value;
            if(!name || !model) return;

            await fetch('/api/agents/init', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name, role, model, provider })
            });

            loadAgents();
            document.getElementById('agent-name').value = "";
            document.getElementById('agent-model').value = "";
        }

        async function loadAgents() {
            const res = await fetch('/api/agents');
            const data = await res.json();
            document.getElementById('agent-list').innerHTML = data.map(a => `
                <div class="card-glass">
                    <div style="color: var(--accent); font-size: 0.6rem; font-weight: 800; margin-bottom: 0.6rem; text-transform: uppercase;">Apex Node</div>
                    <div style="font-weight: 800; margin-bottom: 0.4rem;">${a.name}</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">${a.role}</div>
                    <div style="margin-top: 1rem; padding: 0.6rem; background: rgba(0,0,0,0.3); border-radius: 0.5rem; font-family: 'JetBrains Mono'; font-size: 0.7rem; color: var(--success); border: 1px solid var(--border);">${a.model}</div>
                </div>
            `).join('');
        }

        async function loadMemory() {
            const res = await fetch('/api/memory');
            const data = await res.json();
            document.getElementById('memory-list').innerHTML = data.map(m => `
                <div class="card-glass">
                    <div style="color: var(--recursive); font-size: 0.6rem; font-weight: 800; margin-bottom: 0.75rem; text-transform: uppercase;">Atomic Atom</div>
                    <div style="font-size: 0.75rem; color: var(--accent); margin-bottom: 0.5rem; font-weight: 700;">${m.type}</div>
                    <div style="font-size: 0.85rem; line-height: 1.5; color: #e2e8f0;">${m.content}</div>
                </div>
            `).join('');
        }

        async function executeApex() {
            const input = document.getElementById('apex-input');
            const prompt = input.value;
            if(!prompt) return;
            input.value = "";
            await fetch('/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ prompt, target_agent: 'ApexDev' })
            });
        }

        function pauseGraph() {
            fetch('/api/graph/pause', {method: 'POST'});
        }

        function resumeGraph() {
            fetch('/api/graph/resume', {method: 'POST'});
        }

        function editState() {
            const agent = prompt("Agent name:");
            const memory = prompt("New memory:");
            if (agent && memory) {
                fetch('/api/graph/edit_state', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({agent_name: agent, new_memory: memory})
                });
            }
        }

        function connectWS() {
            const ws = new WebSocket(`ws://${location.host}/ws`);
            const bucket = document.getElementById('trace-bucket');

            ws.onmessage = (e) => {
                const event = JSON.parse(e.data);
                const log = document.createElement('div');
                log.className = 'log-entry';
                let color = 'var(--accent)';
                if(event.event_type.includes('complete') || event.event_type.includes('success')) color = 'var(--success)';
                if(event.event_type.includes('failed') || event.event_type.includes('error')) color = 'var(--risk)';
                if(event.event_type.includes('tool')) color = '#f59e0b';
                log.style.borderColor = color;
                log.innerHTML = `
                    <div class="log-tag" style="color: ${color}">${event.event_type.toUpperCase()}</div>
                    <div class="log-content">${JSON.stringify(event.payload, null, 2)}</div>
                `;
                bucket.prepend(log);
                updateGraph(event);
                if(event.payload.metrics) {
                    document.getElementById('stat-latency').innerText = event.payload.metrics.latency_ms + "ms";
                    document.getElementById('stat-tokens').innerText = event.payload.metrics.total_tokens + " tkn";
                }
            };
            ws.onclose = () => setTimeout(connectWS, 2000);
        }

        function uuidv4() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }

        window.onload = () => {
            initSimulation();
            connectWS();
        };
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/api/memory")
async def get_memory():
    memory_items = []
    for fact in orchestrator.state_manager["shared_memory"].get("facts", []):
        memory_items.append({"type": "FACT", "content": fact})
    history = orchestrator.state_manager.get("history", [])
    for entry in history[-20:]:
        memory_items.append({"type": entry.get("role", "CONTEXT"), "content": entry.get("content", "")})
    return memory_items

@app.get("/api/agents")
async def get_agents():
    return [{"name": n, "role": a.role, "model": a.model} for n, a in orchestrator.active_agents.items()]

@app.post("/api/agents/init")
async def init_agent(req: AgentInitRequest):
    model_str = req.model
    if req.provider == "Together":
        if ":" not in model_str: model_str += ":together"
    elif req.provider == "OpenRouter":
        if "openrouter/" not in model_str: model_str = f"openrouter/{model_str}"
    
    agent = spawn_agent(req.name, model=model_str, role=req.role, tools=[execute_logic])
    orchestrator.register_agent(agent)
    return {"status": "success"}

@app.post("/execute")
async def execute_task(req: ExecutionRequest):
    try:
        orchestrator.trace_id = str(uuid.uuid4())
        orchestrator.step_index = 0
        asyncio.create_task(async_run(req.prompt, req.target_agent))
        return {"status": "initiated"}
    except Exception as e:
        return {"error": str(e)}

async def async_run(prompt, agent):
    await orchestrator.run(prompt, target_agent=agent)

@app.post("/api/graph/pause")
async def pause_graph():
    orchestrator.pause_event.clear()
    return {"status": "paused"}

@app.post("/api/graph/resume")
async def resume_graph():
    orchestrator.pause_event.set()
    return {"status": "resumed"}

@app.post("/api/composer/export")
async def export_composer(request: Request):
    """Compile graph JSON into executable HANERMA script."""
    graph = await request.json()
    
    # Extract nodes and links from graph
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    
    # Generate script based on nodes
    script_lines = [
        "from hanerma.orchestrator.nlp_compiler import compile_and_spawn",
        "",
        "# Compiled from Visual Architect",
    ]
    
    # Map node types to actions
    agent_nodes = [n for n in nodes if n.get("type") == "agent"]
    if agent_nodes:
        agent_prompt = "Create agents: " + ", ".join([n["label"] for n in agent_nodes])
        script_lines.append(f"app = compile_and_spawn(\"{agent_prompt}\")")
        script_lines.append("result = app.run()")
        script_lines.append("print(result)")
    
    script = "\n".join(script_lines)
    return {"script": script, "filename": "compiled_dag.py"}

@app.post("/api/graph/edit_state")
async def edit_state(request: Request):
    """Allow manual variable injection during paused execution."""
    data = await request.json()
    agent_name = data.get("agent_name")
    variable_name = data.get("variable_name")
    new_value = data.get("new_value")
    
    # Find and update agent's state
    if agent_name in orchestrator.active_agents:
        agent = orchestrator.active_agents[agent_name]
        # Assume agent has a state dict
        if not hasattr(agent, 'custom_state'):
            agent.custom_state = {}
        agent.custom_state[variable_name] = new_value
        
        # Resume if paused
        if hasattr(orchestrator, 'pause_event'):
            orchestrator.pause_event.set()
        
        return {"status": "updated", "agent": agent_name, "variable": variable_name}
    
    return {"error": "Agent not found"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_id = 0
    db_path = "hanerma_state.db"
    while True:
        try:
            if os.path.exists(db_path):
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.execute("SELECT id, event_type, payload FROM events WHERE id > ? ORDER BY id ASC", (last_id,))
                    rows = cursor.fetchall()
                    for row in rows:
                        last_id = row[0]
                        await websocket.send_json({"id": row[0], "event_type": row[1], "payload": json.loads(row[2])})
            await asyncio.sleep(0.5)
        except Exception:
            break

def start_viz(port: int = 8081):
    print(f"[HANERMA] Launching Visual Dashboard on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_viz()
