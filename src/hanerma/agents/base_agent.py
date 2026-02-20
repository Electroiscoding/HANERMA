from typing import Dict, Any, List

class BaseAgent:
    """
    The master template for all HANERMA agents. 
    Handles context inheritance and interaction with the message bus.
    """
    def __init__(self, name: str, role: str, system_prompt: str, model: str = None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        # If no specific model is passed, it inherits the orchestrator's default
        self.model = model 
        self.tools: List[Any] = []

    def equip_tools(self, tools: List[Any]):
        """Injects custom APIs or built-in tools (like code sandboxes) into the agent."""
        self.tools.extend(tools)
        print(f"[{self.name}] Equipped {len(tools)} tools.")

    def execute(self, prompt: str, global_state: Dict[str, Any]) -> str:
        """
        Executes the agent's logic using the configured LLM backend.
        Now injects equipped tool definitions into the system context.
        """
        print(f"[{self.name}] Thinking... (Context loaded: {len(global_state.get('history', []))} previous turns)")
        
        # 1. Dynamic Tool Injection
        # We transform the Python functions in self.tools into a readable manifest for the LLM
        tool_manifest = ""
        if self.tools:
            tool_manifest = "\n\n[AVAILABLE TOOLS]\n"
            for tool in self.tools:
                doc = tool.__doc__ or "No description provided."
                tool_manifest += f"- {tool.__name__}: {doc}\n"
            tool_manifest += "\nTo use a tool, output: TOOL_CALL: tool_name(args)"

        effective_system_prompt = self.system_prompt + tool_manifest

        # 2. Resolve Adapter based on model string
        model_id = self.model or "local-llama3"
        llm_backend = None

        try:
            if "gpt-" in model_id or "claude-" in model_id or "openrouter/" in model_id:
                from hanerma.models.cloud_llm import OpenRouterAdapter
                llm_backend = OpenRouterAdapter(model_name=model_id)
            
            elif "hf/" in model_id or "huggingface/" in model_id or ":" in model_id or "Qwen/" in model_id:
                from hanerma.models.cloud_llm import HuggingFaceAdapter
                llm_backend = HuggingFaceAdapter(model_name=model_id)

            else:
                from hanerma.models.local_llm import LocalLLMAdapter
                llm_backend = LocalLLMAdapter(model_name=model_id)

            # 3. Generate Real Intelligence
            response = llm_backend.generate(prompt=prompt, system_prompt=effective_system_prompt)
            
            # 4. Update State
            if "history" in global_state:
                global_state["history"].append({"role": self.name, "content": response})
            
            return response

        except Exception as e:
            error_msg = f"[Agent Error] Failed to generate: {e}"
            print(error_msg)
            return error_msg
