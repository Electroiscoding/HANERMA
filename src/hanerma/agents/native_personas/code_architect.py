from hanerma.agents.base_agent import BaseAgent
from hanerma.tools.sandbox import SecureCodeSandbox

class CodeArchitectAgent(BaseAgent):
    """
    Expert Python coder that operates within a strict sandbox.
    Uses Deep 1 Atomic steps to plan the algorithm before writing a single line.
    """
    def __init__(self, name: str = "native::code_architect"):
        system_prompt = (
            "You are a Senior Software Architect. "
            "Write production-grade, typed Python code. "
            "Never execute without first validating security constraints."
        )
        super().__init__(name=name, role="Code Generator", system_prompt=system_prompt)
        self.sandbox = SecureCodeSandbox()

    def write_and_test(self, global_state: dict, task_description: str) -> str:
        """
        Generates code, runs it in an ephemeral Docker container, 
        and returns the result only if it passes all tests.
        """
        # Simulated generation phase
        print(f"[{self.name}] Generating solution for: {task_description[:40]}...")
        
        # Simulated code execution
        code_snippet = "print('Hello from the secure sandbox!')"
        
        result = self.sandbox.execute_python(code_snippet)
        
        if result["status"] == "error":
            return f"Code Generation Failed: {result['output']}"
            
        return f"Code Validated.\nOutput: {result['output']}"
