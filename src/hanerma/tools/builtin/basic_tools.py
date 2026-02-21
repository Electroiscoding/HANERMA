
"""
Core tools (WebSearch, FileR/W, MathEval, Time, Handoff).
Built-in utilities for every agent to ensure zero-error execution.
"""
import math
import datetime
from typing import Dict, Any
from ..web_search import SafeWebSearch

async def web_search(**kwargs) -> Dict[str, Any]:
    """
    Search the web for up-to-date info. 
    Accepts: 'query' (string), 'max_results' (int).
    """
    query = kwargs.get("query") or kwargs.get("q") or ""
    limit = int(kwargs.get("max_results") or kwargs.get("limit") or 5)
    
    search_engine = SafeWebSearch()
    print(f"[DEBUG] WebSearch Tool Inbound: query='{query}', limit={limit}")
    results = await search_engine.search(query, limit=limit)
    return {"query": query, "results": results}

async def calculator(**kwargs) -> Any:
    """
    Perform safe math calculations. 
    Accepts: 'expression' (string, e.g., 'sqrt(16) * 2').
    """
    expression = kwargs.get("expression") or kwargs.get("expr") or ""
    allowed_names = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
    try:
        return eval(expression, {"__builtins__": {}}, allowed_names)
    except Exception as e:
        return f"Math Error: {str(e)}"

async def get_system_time(**kwargs) -> str:
    """
    Returns the current system date and time. Use this for time-aware logic.
    """
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

async def delegate_task(**kwargs) -> str:
    """
    Handoff the current task to another agent.
    Accepts: 'agent' (name of target agent), 'reason' (string).
    Usage: TOOL_CALL: delegate_task(agent='Strict_Verifier', reason='Needs testing')
    """
    agent = kwargs.get("agent") or kwargs.get("target") or ""
    reason = kwargs.get("reason") or "Delegating task for specialized processing."
    if not agent:
        return "Error: No target agent specified for delegation."
    # The orchestrator picks up 'DELEGATE:' in the output. 
    # Returning it here ensures the message bus triggers the handoff.
    return f"DELEGATE: {agent}\nReason: {reason}"

async def internal_search(**kwargs) -> Dict[str, Any]:
    """
    Search internal project files and documentation.
    Accepts: 'query' (string).
    """
    query = kwargs.get("query") or ""
    search_engine = SafeWebSearch()
    results = await search_engine.search(f"site:hanerma.ai {query}", limit=3)
    return {"query": query, "internal_results": results}

async def execute_sandbox(**kwargs) -> str:
    """
    Alias for run_safe_compute. Executes Python code securely.
    Accepts: 'code' (string).
    """
    from ..code_sandbox import NativeCodeSandbox
    sandbox = NativeCodeSandbox()
    code = kwargs.get("code") or ""
    return sandbox.execute_code(code)
