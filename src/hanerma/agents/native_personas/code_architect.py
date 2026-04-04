from hanerma.agents.base_agent import BaseAgent
from hanerma.tools.code_sandbox import NativeCodeSandbox
import json
import logging

try:
    from hanerma.models.cloud_llm import OpenRouterProvider
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)

class CodeArchitectAgent(BaseAgent):
    """
    Expert Python coder that operates within a strict sandbox.
    Uses Deep 1 Atomic steps to plan the algorithm before writing a single line.
    """
    def __init__(self, name: str = "native::code_architect"):
        system_prompt = (
            "You are a Senior Software Architect. "
            "Write production-grade, typed Python code. "
            "Output ONLY valid Python code inside a markdown block. No explanations."
        )
        super().__init__(name=name, role="Code Generator", system_prompt=system_prompt)
        self.sandbox = NativeCodeSandbox()
        self.llm = OpenRouterProvider() if LLM_AVAILABLE else None

    async def write_and_test(self, global_state: dict, task_description: str) -> str:
        """
        Generates code using LLM, runs it in an ephemeral sandbox,
        and returns the result only if it passes execution.
        """
        logger.info(f"[{self.name}] Generating solution for: {task_description[:40]}...")
        
        if not self.llm:
            return "Code Generation Failed: LLM Provider not available to generate code."

        prompt = f"Write Python code to solve this task: {task_description}\nGlobal State context: {json.dumps(global_state)}\nOutput ONLY code in a ```python block."
        
        # Genuine LLM generation phase
        try:
            llm_response = await self.llm.generate(prompt, system_prompt=self.system_prompt)
        except Exception as e:
            return f"Code Generation Failed: LLM call error: {e}"

        # Extract code block
        code_snippet = self._extract_code(llm_response)

        if not code_snippet.strip():
            return "Code Generation Failed: LLM did not return any code."

        # Real code execution in Sandbox
        output = self.sandbox.execute_code(code_snippet)
        
        if "[Runtime Error]" in output or "Exception:" in output or "Traceback" in output:
            return f"Code Execution Failed:\n{output}\n\nGenerated Code:\n{code_snippet}"
            
        return f"Code Validated.\nOutput: {output}\n\nFinal Code:\n{code_snippet}"

    def _extract_code(self, response: str) -> str:
        import re
        match = re.search(r'```(?:python)?\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            return match.group(1)
        return response
