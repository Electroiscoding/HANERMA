import json
import requests
import ast
from typing import Dict, Any, Optional

class EmpathyHandler:
    """
    Emotional Failsafe: Sends tracebacks to local model for JSON mitigation strategies.
    Enhanced with autonomous AST patching capabilities.
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

    async def generate_ast_patch(self, error_str: str, node_data: Dict[str, Any]) -> Optional[ast.AST]:
        """
        Generates a new AST node to fix the error dynamically.
        Uses AI to analyze the error and create a patched version of the failing AST node.
        """
        system_prompt = """
        You are an AST Patching AI. Your task is to analyze Python errors and generate corrected AST code.

        Given an error message and the original AST node information, output a valid Python code snippet that fixes the error.
        The output should be executable Python code that can replace the failing node.

        Consider common fixes like:
        - Adding try/except blocks
        - Providing default values for missing variables
        - Correcting function calls
        - Adding type checks

        Output ONLY the corrected Python code, no explanations.
        """
        
        # Extract node info
        original_node = node_data.get('ast_node', {})
        node_type = type(original_node).__name__ if original_node else "Unknown"
        
        prompt = f"""
        Error: {error_str}
        Node Type: {node_type}
        Original Node: {ast.dump(original_node) if original_node else "N/A"}

        Generate corrected Python code:
        """
        
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            # Send to local Ollama Qwen model
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen",
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=15
            )
            response.raise_for_status()
            code_snippet = response.json()["response"].strip()
            
            # Parse the generated code into AST
            try:
                tree = ast.parse(code_snippet)
                # Return the first statement as the patch
                if tree.body:
                    return tree.body[0]
            except SyntaxError:
                return None
                
        except Exception:
            return None
            
        return None

def friendly_fail(traceback_str: str) -> Dict[str, Any]:
    handler = EmpathyHandler()
    return handler.get_mitigation(traceback_str)
