from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from hanerma.core.types import ChatRequest, OrchestrationResult
# In production, these singletons are injected via dependencies
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import PersonaRegistry

api_router = APIRouter()

# Dependency Injection for clean architecture
def get_orchestrator():
    return HANERMAOrchestrator(model="local-llama3")

def get_registry():
    return PersonaRegistry()

@api_router.post("/execute", response_model=OrchestrationResult)
async def execute_agent_task(
    req: ChatRequest, 
    orch: HANERMAOrchestrator = Depends(get_orchestrator),
    registry: PersonaRegistry = Depends(get_registry)
):
    """
    The primary ingestion point for all REST-based agent commands.
    """
    try:
        active_agent = registry.spawn_agent(req.bot_id)
        orch.register_agent(active_agent)
        
        # Execute the Three-Deep Engine
        result = orch.run(prompt=req.prompt, target_agent=active_agent.name)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
