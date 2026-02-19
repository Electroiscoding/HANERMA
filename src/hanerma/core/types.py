from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any

class AgentConfig(BaseModel):
    name: str = Field(..., description="Unique identifier for the agent")
    role: str = Field(..., description="The persona the agent adopts")
    system_prompt: str = Field(..., min_length=10, description="Core instructions")
    tools_allowed: List[str] = Field(default_factory=list)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError('Agent name must be alphanumeric')
        return v

class OrchestrationResult(BaseModel):
    status: str
    output: str
    metrics: Dict[str, Any]
    trace_id: str

class ChatRequest(BaseModel):
    bot_id: str
    prompt: str

class AgentMessage(BaseModel):
    role: str
    content: str

class AgentRole:
    RESEARCHER = "researcher"
    VERIFIER = "verifier"
    CODER = "coder"
