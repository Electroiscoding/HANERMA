import json
import requests
from typing import Dict, Any, List
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.base_agent import BaseAgent

class NLPCompiler:
    """
    Compiles natural language prompts into executable HANERMA multi-agent graphs.
    """
    
    def compile_prompt_to_graph(self, english_prompt: str) -> Dict[str, Any]:
        """
        Sends the English prompt to local Qwen model via Ollama API, instructing it to output
        a JSON representation of a multi-agent DAG defining agents, roles, tools, and edges.
        """
        system_prompt = """
        You are a HANERMA Graph Compiler. Your task is to translate natural language descriptions of multi-agent workflows into a strict JSON format for HANERMA orchestration.

        Output JSON structure:
        {
            "agents": [
                {
                    "name": "agent_name",
                    "role": "agent_role_description",
                    "tools": ["tool1", "tool2"],
                    "model": "model_name"
                }
            ],
            "edges": [
                ["from_agent", "to_agent"]
            ]
        }

        Rules:
        - Agents should have meaningful names and roles.
        - Tools are from the registry: web_search, calculator, etc.
        - Model defaults to "qwen" for local.
        - Edges define communication flow (who delegates to who).
        - Output ONLY valid JSON, no extra text.
        """
        
        full_prompt = f"{system_prompt}\n\nDescription: {english_prompt}\n\nOutput JSON:"
        
        # Send to local Ollama Qwen model
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen",
                "prompt": full_prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        json_str = response.json()["response"]
        
        # Parse and return the JSON
        return json.loads(json_str.strip())
    
    def parse_and_spawn(self, graph_config: Dict[str, Any]) -> HANERMAOrchestrator:
        """
        Parses the graph JSON and spawns a HANERMAOrchestrator with registered agents and wired edges.
        """
        orchestrator = HANERMAOrchestrator()
        
        # Register agents
        for agent_config in graph_config["agents"]:
            agent = BaseAgent(
                name=agent_config["name"],
                model=agent_config.get("model", "qwen"),
                tools=agent_config.get("tools", [])
            )
            orchestrator.register_agent(agent)
        
        # Store edges for execution (linking who talks to who)
        orchestrator.graph_edges = graph_config.get("edges", [])
        
        return orchestrator

def compile_and_spawn(english_prompt: str) -> HANERMAOrchestrator:
    """
    Convenience function: compile prompt to graph and spawn orchestrator.
    """
    compiler = NLPCompiler()
    config = compiler.compile_prompt_to_graph(english_prompt)
    return compiler.parse_and_spawn(config)
