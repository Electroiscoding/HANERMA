import time

class HumanInTheLoop:
    """
    Safety circuit breaker for high-stakes external actions.
    Pauses orchestration until explicit approval is granted via CLI or API.
    """
    def __init__(self, timeout_seconds: int = 300):
        self.timeout = timeout_seconds

    def request_approval(self, agent_name: str, intended_action: str) -> bool:
        """Halts the execution thread and waits for a boolean response."""
        print("\n" + "="*50)
        print(f"🚨 [AUTHORIZATION REQUIRED] 🚨")
        print(f"Agent '{agent_name}' is requesting to execute:")
        print(f"Action: {intended_action}")
        print("="*50)
        
        # In a CLI environment, this uses input(). In the FastAPI server, 
        # this sends a WebSocket push to the frontend and awaits a callback.
        user_input = input("Approve action? (Y/N): ").strip().upper()
        
        if user_input == "Y":
            print("[System] Action Approved. Resuming execution...")
            return True
            
        print("[System] Action REJECTED. Routing denial back to agent.")
        return False
