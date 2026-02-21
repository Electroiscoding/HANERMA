"""
HANERMA Quickstart: 5-Line Multi-Agent Flow
"""
import asyncio
from hanerma.orchestrator.nlp_compiler import compile_and_spawn

class Natural:
    """
    Simplified API for natural language multi-agent flows.
    """
    
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.app = None
    
    def run(self):
        """
        Compiles prompt to graph and runs the flow.
        """
        self.app = compile_and_spawn(self.prompt)
        asyncio.run(self.app.run())
