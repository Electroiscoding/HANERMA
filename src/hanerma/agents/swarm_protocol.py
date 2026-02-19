from typing import Dict, Any, Optional
import uuid

class SwarmHandoffTool:
    """
    Enables autonomous agent-to-agent task delegation.
    If an agent recognizes a task is outside its domain, it uses this protocol
    to securely pass the state and context to a specialist peer.
    """
    def __init__(self, registry_access: Any, message_bus: Any):
        self.registry = registry_access
        self.bus = message_bus

    async def handoff_to_specialist(self, target_agent_name: str, task_context: str, current_state: Dict[str, Any]) -> Dict[str, str]:
        """
        Transfers execution control while maintaining the infinite memory context.
        """
        print(f"[Swarm Protocol] Initiating handoff to: {target_agent_name}")
        
        handoff_payload = {
            "trace_id": str(uuid.uuid4()),
            "target": target_agent_name,
            "context": task_context,
            "inherited_state": current_state
        }
        
        # Fire-and-forget payload to the async message bus
        await self.bus.publish("agent_handoff", handoff_payload)
        
        return {"status": "handoff_initiated", "target": target_agent_name}
