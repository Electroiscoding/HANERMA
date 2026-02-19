# pip install fastapi uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import time

# Internal framework imports
from hanerma.orchestrator.engine import HANERMAOrchestrator
from hanerma.agents.registry import PersonaRegistry

app = FastAPI(title="HANERMA OS API", version="1.0.0")

# Initialize global framework singletons
registry = PersonaRegistry()
orchestrator = HANERMAOrchestrator(model="grok-4.2")

class SetupPersonaRequest(BaseModel):
    builder_id: str
    bot_name: str
    seed_content: str

class ChatRequest(BaseModel):
    bot_id: str
    prompt: str

@app.post("/v1/builder/setup")
async def setup_custom_persona(req: SetupPersonaRequest):
    """Endpoint for platforms to inject new user-defined bots."""
    registry.inject_builder_persona(req.builder_id, req.bot_name, req.seed_content)
    return {"status": "success", "bot_id": f"{req.builder_id}::{req.bot_name}"}

@app.post("/v1/chat")
async def chat_with_agent(req: ChatRequest):
    """Main routing endpoint for inference."""
    try:
        # 1. Fetch the requested persona (Native or Builder-defined)
        active_agent = registry.spawn_agent(req.bot_id)
        
        # 2. Register with orchestrator for this specific session
        orchestrator.register_agent(active_agent)
        
        # 3. Execute the Three-Deep framework
        # (In production, this is fully async to prevent API blocking)
        result = orchestrator.run(prompt=req.prompt, target_agent=active_agent.name)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal orchestration failure.")

# To run locally: uvicorn main:app --reload
