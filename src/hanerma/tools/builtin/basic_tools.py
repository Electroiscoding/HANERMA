
"""
Core tools (WebSearch, FileR/W, MathEval).
Built-in utilities for every agent.
"""

from ..registry import ToolRegistry
from typing import Dict, Any

@ToolRegistry.register(name="web_search", description="Search the web for up-to-date info.")
async def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search using external API (Google, DuckDuckGo, etc.).
    """
    # Real implementation would import requests
    return {
        "results": [
            {"title": f"Result for {query}", "snippet": "Sample snippet content."}
        ]
    }

@ToolRegistry.register(name="calculator", description="Perform math calculations.")
async def calculator(expression: str) -> float:
    """Safe math evaluation."""
    # Use eval with restricted globals? Or specialized lib.
    # For now, simple eval
    allowed_names = {"abs": abs, "round": round}
    return eval(expression, {"__builtins__": {}}, allowed_names)
