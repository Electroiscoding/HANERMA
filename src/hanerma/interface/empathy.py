import json
import requests
from typing import Dict, Any

class EmpathyHandler:
    """
    Emotional Failsafe: Sends tracebacks to local model for JSON mitigation strategies.
    """
    
    def get_mitigation(self, traceback_str: str) -> Dict[str, Any]:
        """
        Sends the raw traceback to local Qwen model via Ollama, outputs JSON mitigation.
        """
        system_prompt = """
        You are the Emotional Failsafe AI. Your role is to analyze error tracebacks and provide empathetic, actionable mitigation strategies.

        Analyze the traceback and output ONLY a valid JSON object in this exact format:
        {
            "human_readable_message": "A user-friendly explanation of what went wrong and why.",
            "action": "retry_with_new_prompt" | "ask_human" | "mock_data"
        }

        - "retry_with_new_prompt": Suggest retrying with a simplified or corrected prompt.
        - "ask_human": The error requires human intervention.
        - "mock_data": Provide safe mock data to continue execution.
        
        Be concise and helpful.
        """
        
        full_prompt = f"{system_prompt}\n\nTraceback:\n{traceback_str}\n\nOutput JSON:"
        
        # Send to local Ollama Qwen model
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen",
                "prompt": full_prompt,
                "stream": False
            },
            timeout=10
        )
        response.raise_for_status()
        json_str = response.json()["response"].strip()
        
        # Parse and return the JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback if parsing fails
            return {
                "human_readable_message": "Failed to parse mitigation response. Error in empathy handler.",
                "action": "ask_human"
            }

def friendly_fail(traceback_str: str) -> Dict[str, Any]:
    handler = EmpathyHandler()
    return handler.get_mitigation(traceback_str)
