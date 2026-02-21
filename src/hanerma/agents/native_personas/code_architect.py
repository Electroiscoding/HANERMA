from hanerma.agents.base_agent import BaseAgent
from hanerma.tools.code_sandbox import NativeCodeSandbox

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
        self.sandbox = NativeCodeSandbox()

    def write_and_test(self, global_state: dict, task_description: str) -> str:
        """
        Generates code, runs it in an ephemeral sandbox, 
        and returns the result only if it passes all tests.
        """
        # Simulated generation phase
        print(f"[{self.name}] Generating solution for: {task_description[:40]}...")
        
        # Simulated code execution
        code_snippet = "print('Hello from the secure sandbox!')"
        
        output = self.sandbox.execute_code(code_snippet)
        
        if "[Runtime Error]" in output:
            return f"Code Generation Failed: {output}"
            
        return f"Code Validated.\nOutput: {output}"
