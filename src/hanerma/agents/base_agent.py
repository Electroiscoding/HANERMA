"""
BaseAgent — Grammar-Shield-enforced agent template.

Every agent in HANERMA inherits from this class.  The execute() method
FORCES all LLM output through the GrammarShield, producing validated
Pydantic models instead of raw text.

Tool calls are structured ToolCallRequest objects with exact JSON
schemas — the LLM cannot hallucinate tool names or arguments.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from hanerma.models.constrained import (
    AgentOutput,
    BackendType,
    GrammarShield,
    ReasoningStep,
    ToolCallRequest,
)

logger = logging.getLogger("hanerma.agent")


class BaseAgent:
    """
    The master template for all HANERMA agents.

    Key difference from v1: ALL LLM output is grammar-constrained.
    The agent literally cannot produce unstructured text for reasoning
    or tool calls.  Every output is a validated Pydantic model.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: Optional[str] = None,
        backend: BackendType = BackendType.AUTO,
        shield: Optional[GrammarShield] = None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model = model
        self.tools: List[Any] = []
        self._tool_schemas: List[Dict[str, Any]] = []

        # Grammar Shield — shared across agents if provided
        self._shield = shield or GrammarShield(
            backend=backend,
            model_name=model,
        )

    def equip_tools(self, tools: List[Any]) -> None:
        """
        Inject tools into this agent.  Automatically extracts JSON
        schemas for constrained tool-call generation.
        """
        for tool in tools:
            if tool is None:
                continue
            self.tools.append(tool)

            # Extract schema from Tool objects (from registry.py)
            if hasattr(tool, "schema") and hasattr(tool, "name"):
                self._tool_schemas.append({
                    "name": tool.name,
                    "description": getattr(tool, "description", ""),
                    "parameters": tool.schema,
                })
            # Extract schema from plain functions
            elif callable(tool):
                import inspect
                sig = inspect.signature(tool)
                params = {}
                for pname, param in sig.parameters.items():
                    ptype = "string"
                    if param.annotation is int:
                        ptype = "integer"
                    elif param.annotation is float:
                        ptype = "number"
                    elif param.annotation is bool:
                        ptype = "boolean"
                    params[pname] = {"type": ptype}

                self._tool_schemas.append({
                    "name": tool.__name__,
                    "description": tool.__doc__ or "",
                    "parameters": {
                        "type": "object",
                        "properties": params,
                    },
                })

        logger.info("[%s] Equipped %d tools", self.name, len(tools))

    async def execute(
        self,
        prompt: str,
        global_state: Dict[str, Any],
        output_schema: Optional[Type[BaseModel]] = None,
    ) -> AgentOutput:
        """
        Execute the agent with grammar-constrained output.

        Returns:
            AgentOutput — structured, validated reasoning chain
            with tool calls, confidence scores, and final answer.

        The LLM CANNOT produce raw text through this method.
        Every token is constrained to the AgentOutput JSON schema.
        """
        logger.info(
            "[%s] Thinking... (history=%d, tools=%d)",
            self.name,
            len(global_state.get("history", [])),
            len(self.tools),
        )

        # Build the full system prompt with tool manifest
        effective_system = self._build_system_prompt()

        # Use custom schema or default AgentOutput
        schema = output_schema or AgentOutput

        try:
            # ── Grammar-constrained generation ──
            result = self._shield.generate(
                prompt=prompt,
                schema=schema,
                system_prompt=effective_system,
            )

            # Track in global state
            if "history" in global_state:
                global_state["history"].append({
                    "role": self.name,
                    "content": result.model_dump_json(),
                    "structured": True,
                })

            # Execute any tool calls in the reasoning chain
            if isinstance(result, AgentOutput):
                await self._execute_tool_calls(result, global_state)

            return result

        except Exception as e:
            logger.error("[%s] Generation failed: %s", self.name, e)
            # Return a structured error — NEVER raw text
            return AgentOutput(
                reasoning=[
                    ReasoningStep(
                        thought=f"Generation failed: {e}",
                        action="respond",
                        confidence=0.0,
                        response=str(e),
                    )
                ],
                final_answer=f"Error: {e}",
            )

    async def execute_tool_call(
        self,
        prompt: str,
    ) -> ToolCallRequest:
        """
        Force the LLM to select and parameterize exactly one tool call.

        Returns:
            ToolCallRequest — validated tool name + arguments.
        """
        if not self._tool_schemas:
            raise ValueError(f"Agent '{self.name}' has no tools equipped")

        return self._shield.generate_tool_call(
            prompt=prompt,
            available_tools=self._tool_schemas,
            system_prompt=self.system_prompt,
        )

    async def _execute_tool_calls(
        self,
        output: AgentOutput,
        global_state: Dict[str, Any],
    ) -> None:
        """
        Execute any tool_call actions found in the reasoning chain.
        Results are injected back into global state.
        """
        for step in output.reasoning:
            if step.action == "tool_call" and step.tool_call is not None:
                call = step.tool_call
                tool = self._find_tool(call.tool_name)

                if tool is None:
                    logger.warning(
                        "[%s] Tool '%s' not found",
                        self.name, call.tool_name,
                    )
                    continue

                try:
                    # Execute the tool with validated arguments
                    if hasattr(tool, "call"):
                        result = tool.call(**call.arguments)
                    elif callable(tool):
                        result = tool(**call.arguments)
                    else:
                        result = f"Tool '{call.tool_name}' is not callable"

                    # Store result in global state
                    tool_key = f"tool_result:{call.tool_name}"
                    global_state[tool_key] = result
                    logger.info(
                        "[%s] Tool '%s' executed successfully",
                        self.name, call.tool_name,
                    )

                except Exception as e:
                    logger.error(
                        "[%s] Tool '%s' failed: %s",
                        self.name, call.tool_name, e,
                    )
                    global_state[f"tool_error:{call.tool_name}"] = str(e)

    def _find_tool(self, name: str) -> Any:
        """Look up a tool by name."""
        for tool in self.tools:
            if tool is None:
                continue
            if hasattr(tool, "name") and tool.name == name:
                return tool
            if callable(tool) and hasattr(tool, "__name__") and tool.__name__ == name:
                return tool
        return None

    def _build_system_prompt(self) -> str:
        """Build the full system prompt with tool schemas."""
        parts = [self.system_prompt]

        if self._tool_schemas:
            parts.append("\n[AVAILABLE TOOLS]")
            for ts in self._tool_schemas:
                parts.append(
                    f"  - {ts['name']}: {ts.get('description', '')}\n"
                    f"    Parameters: {json.dumps(ts.get('parameters', {}))}"
                )
            parts.append(
                "\nWhen using a tool, set action='tool_call' and fill the "
                "tool_call field with the exact tool name and arguments."
            )

        return "\n".join(parts)

    def __repr__(self) -> str:
        return (
            f"BaseAgent(name='{self.name}', role='{self.role}', "
            f"tools={len(self.tools)}, backend='{self._shield.backend_name}')"
        )
