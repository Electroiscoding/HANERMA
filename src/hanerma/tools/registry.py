"""
Universal Tool Registry — @tool decorator with auto-schema generation.

The @tool decorator uses `inspect` to read type hints and docstrings,
then `pydantic.create_model` to auto-generate strict JSON schemas
for the Grammar Shield's constrained generation engine.

No hardcoded schemas.  No boilerplate.  Just:

    @tool
    def search(query: str, limit: int = 5) -> str:
        '''Search the web.'''
        ...

And the schema is generated automatically from the function signature.
"""

import asyncio
import inspect
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, get_type_hints

from pydantic import BaseModel, Field, create_model

logger = logging.getLogger("hanerma.tools")


# ═══════════════════════════════════════════════════════════════════════════
#  Tool — Universal wrapper with auto-schema
# ═══════════════════════════════════════════════════════════════════════════


class Tool:
    """
    Universal tool wrapper.

    Reads type hints + docstrings via `inspect`, generates a Pydantic
    model via `create_model`, and exposes the JSON schema for the
    Grammar Shield's constrained decoding engine.
    """

    def __init__(self, func: Callable, name: Optional[str] = None):
        self.func = func
        self.name = name or func.__name__
        self.description = (inspect.getdoc(func) or "").strip()
        self.is_async = asyncio.iscoroutinefunction(func)

        # ── Parse signature ──
        sig = inspect.signature(func)
        hints = {}
        try:
            hints = get_type_hints(func)
        except Exception:
            pass

        fields: Dict[str, Any] = {}
        param_docs = self._parse_param_docs(self.description)

        for pname, param in sig.parameters.items():
            # Skip **kwargs / *args
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            # Type
            ptype = hints.get(pname, Any)

            # Default
            if param.default is not param.empty:
                default = param.default
            else:
                default = ...  # Required

            # Per-parameter description from docstring
            pdesc = param_docs.get(pname, "")

            if pdesc:
                fields[pname] = (ptype, Field(default=default, description=pdesc))
            else:
                fields[pname] = (ptype, default)

        # Return type
        self.return_type = hints.get("return", Any)

        # Pydantic model
        self.model = create_model(
            f"{self.name}_Schema",
            **fields,
        )

        # JSON schema (cached)
        self._schema = self.model.model_json_schema()
        self._schema["description"] = self.description
        self._schema["name"] = self.name

    @staticmethod
    def _parse_param_docs(docstring: str) -> Dict[str, str]:
        """
        Extract parameter descriptions from numpy/google-style docstrings.
        Returns {param_name: description}.
        """
        docs: Dict[str, str] = {}
        if not docstring:
            return docs

        lines = docstring.split("\n")
        in_params = False
        current_param = None

        for line in lines:
            stripped = line.strip()

            # Detect param section headers
            if stripped.lower() in ("args:", "arguments:", "parameters:", "params:"):
                in_params = True
                continue
            if stripped.lower() in ("returns:", "return:", "raises:", "yields:"):
                in_params = False
                continue

            if in_params and stripped:
                # google-style: "param_name (type): description"
                # or simple:    "param_name: description"
                if ":" in stripped and not stripped.startswith("-"):
                    parts = stripped.split(":", 1)
                    pname = parts[0].strip().split("(")[0].strip().strip("-").strip()
                    if pname and pname.isidentifier():
                        current_param = pname
                        docs[pname] = parts[1].strip()
                elif current_param:
                    # Continuation line
                    docs[current_param] += " " + stripped

        return docs

    @property
    def schema(self) -> Dict[str, Any]:
        """JSON schema for Grammar Shield integration."""
        return self._schema

    def validate(self, **kwargs) -> BaseModel:
        """Validate kwargs against the auto-generated schema."""
        return self.model(**kwargs)

    def call(self, **kwargs) -> Any:
        """
        Call the tool with validated arguments.
        Handles both sync and async functions.
        Returns traceback string on failure (never raises).
        """
        try:
            validated = self.model(**kwargs)
            args = validated.model_dump()

            if self.is_async:
                try:
                    loop = asyncio.get_running_loop()
                    # Can't await in sync context, create task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        return pool.submit(
                            asyncio.run, self.func(**args)
                        ).result(timeout=30)
                except RuntimeError:
                    return asyncio.run(self.func(**args))
            else:
                return self.func(**args)
        except Exception:
            return f"[TOOL_ERROR] {traceback.format_exc()}"

    async def acall(self, **kwargs) -> Any:
        """Async version of call."""
        try:
            validated = self.model(**kwargs)
            args = validated.model_dump()

            if self.is_async:
                return await self.func(**args)
            else:
                return self.func(**args)
        except Exception:
            return f"[TOOL_ERROR] {traceback.format_exc()}"

    def __repr__(self) -> str:
        params = list(self.model.model_fields.keys())
        return f"Tool({self.name}, params={params})"


# ═══════════════════════════════════════════════════════════════════════════
#  @tool Decorator
# ═══════════════════════════════════════════════════════════════════════════


def tool(func: Optional[Callable] = None, *, name: Optional[str] = None):
    """
    Universal @tool decorator.

    Usage:
        @tool
        def search(query: str, limit: int = 5) -> str:
            '''Search the web for information.'''
            ...

        @tool(name="custom_name")
        def my_func(x: int) -> int:
            ...

    The decorator auto-generates a Pydantic model + JSON schema
    from the function's type hints and docstring.
    """
    def decorator(fn: Callable) -> Tool:
        return Tool(fn, name=name)

    if func is not None:
        # Called as @tool without parens
        return Tool(func)
    else:
        # Called as @tool(name="...")
        return decorator


# ═══════════════════════════════════════════════════════════════════════════
#  Tool Registry — Central repository
# ═══════════════════════════════════════════════════════════════════════════


class ToolRegistry:
    """
    Central repository for all agent capabilities.

    Supports both @tool-decorated functions and raw callables.
    Auto-registers the standard toolset on creation.
    """

    def __init__(self, auto_register: bool = True):
        self.tools: Dict[str, Any] = {}
        if auto_register:
            self._register_defaults()

    def _register_defaults(self):
        """Load the standard HANERMA toolset."""
        try:
            from hanerma.tools.builtin.basic_tools import (
                web_search,
                calculator,
                get_system_time,
                delegate_task,
                internal_search,
                execute_sandbox,
            )
            self.register_tool("web_search", web_search)
            self.register_tool("calculator", calculator)
            self.register_tool("get_system_time", get_system_time)
            self.register_tool("delegate_task", delegate_task)
            self.register_tool("internal_search", internal_search)
            self.register_tool("execute_sandbox", execute_sandbox)
        except ImportError as e:
            logger.debug("Default tools not loaded: %s", e)

    def register_tool(self, name: str, tool_instance: Any) -> None:
        """Register a tool (Tool instance or raw callable)."""
        if isinstance(tool_instance, Tool):
            self.tools[name] = tool_instance
        elif callable(tool_instance):
            self.tools[name] = tool_instance
        else:
            raise TypeError(f"Expected Tool or callable, got {type(tool_instance)}")

    def register(self, func_or_tool) -> Any:
        """
        Register via decorator pattern:
            registry = ToolRegistry()

            @registry.register
            def my_tool(x: int) -> str:
                ...
        """
        if isinstance(func_or_tool, Tool):
            self.tools[func_or_tool.name] = func_or_tool
            return func_or_tool
        elif callable(func_or_tool):
            t = Tool(func_or_tool)
            self.tools[t.name] = t
            return t
        raise TypeError(f"Expected callable, got {type(func_or_tool)}")

    def get_tool(self, name: str) -> Any:
        return self.tools.get(name)

    def list_available_tools(self) -> List[str]:
        return list(self.tools.keys())

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Return JSON schemas for all registered Tool objects."""
        schemas = []
        for name, t in self.tools.items():
            if isinstance(t, Tool):
                schemas.append(t.schema)
            elif callable(t):
                # Wrap raw callable on-the-fly
                wrapped = Tool(t)
                schemas.append(wrapped.schema)
        return schemas

    def __len__(self) -> int:
        return len(self.tools)

    def __repr__(self) -> str:
        return f"ToolRegistry({list(self.tools.keys())})"
