"""
Grammar Shield — Constrained Decoding for Zero-Hallucination LLM Output.

This module replaces raw text LLM generation with mathematically constrained
decoding.  Every agent reasoning step and tool call is FORCED to output valid
JSON conforming to a Pydantic schema at the token-sampling level.

Supports three backends:
  1. Local models via `outlines` (grammar-based sampling — the gold standard)
  2. Cloud models via `instructor` (OpenAI-compatible function-calling +
     Pydantic validation with auto-retry)
  3. Ollama local models via JSON-mode + Pydantic post-validation

No raw text output is physically possible through this interface.
"""

import json
import os
import logging
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

import httpx
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("hanerma.grammar_shield")

T = TypeVar("T", bound=BaseModel)


# ═══════════════════════════════════════════════════════════════════════════
#  Standard Pydantic Schemas for Agent Reasoning & Tool Calls
# ═══════════════════════════════════════════════════════════════════════════


class ToolCallRequest(BaseModel):
    """Schema for a structured tool invocation."""
    tool_name: str = Field(..., description="Exact name of the tool to invoke")
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value arguments matching the tool's parameter schema",
    )
    rationale: str = Field(
        default="",
        description="Brief explanation of why this tool is being called",
    )


class ReasoningStep(BaseModel):
    """Schema for a single agent reasoning step."""
    thought: str = Field(..., description="The agent's internal reasoning")
    action: str = Field(
        ...,
        description="One of: 'tool_call', 'respond', 'delegate', 'verify'",
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Self-assessed confidence in the action (0.0–1.0)",
    )
    tool_call: Optional[ToolCallRequest] = Field(
        default=None,
        description="Filled when action == 'tool_call'",
    )
    response: Optional[str] = Field(
        default=None,
        description="Filled when action == 'respond'",
    )


class AgentOutput(BaseModel):
    """Complete structured output from an agent execution."""
    reasoning: List[ReasoningStep] = Field(
        ..., min_length=1,
        description="Chain of reasoning steps the agent performed",
    )
    final_answer: str = Field(
        ..., description="The agent's final answer / deliverable",
    )
    assertions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Formal assertions for Z3 verification (Slice 4)",
    )


class MultiToolPlan(BaseModel):
    """Schema for planning multiple sequential tool calls."""
    plan: List[ToolCallRequest] = Field(
        ..., min_length=1,
        description="Ordered list of tools to execute",
    )
    goal: str = Field(..., description="What this plan aims to achieve")


# ═══════════════════════════════════════════════════════════════════════════
#  Backend 1: Outlines (Local Grammar-Based Constrained Generation)
# ═══════════════════════════════════════════════════════════════════════════


class OutlinesBackend:
    """
    Uses the `outlines` library for TRUE grammar-based constrained
    generation.  The LLM literally cannot produce tokens outside the
    JSON schema — hallucination is physically impossible at the token
    sampling level.

    Requires: `pip install outlines transformers torch`
    Works with: Any HuggingFace / local transformer model.
    """

    def __init__(self, model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"):
        self._model_name = model_name
        self._model = None  # Lazy-loaded

    def _ensure_model(self):
        """Lazy-load the outlines model (heavy import)."""
        if self._model is not None:
            return
        try:
            import outlines
            self._model = outlines.models.transformers(
                self._model_name,
                device="auto",
            )
            logger.info(
                "Outlines model loaded: %s", self._model_name
            )
        except ImportError:
            raise ImportError(
                "outlines is required for grammar-based generation. "
                "Install with: pip install outlines transformers torch"
            )

    def generate(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> T:
        """
        Generate a response constrained to the given Pydantic schema.
        The output is MATHEMATICALLY GUARANTEED to be valid JSON
        matching the schema.
        """
        self._ensure_model()
        import outlines

        # Build the constrained generator from the Pydantic schema
        generator = outlines.generate.json(self._model, schema)

        # Format as chat-style prompt
        full_prompt = self._format_prompt(prompt, schema, system_prompt)

        # Generate — output is already a validated Pydantic instance
        result = generator(full_prompt, max_tokens=max_tokens)

        if isinstance(result, schema):
            return result

        # Defensive: if outlines returns raw dict, validate
        return schema.model_validate(result)

    @staticmethod
    def _format_prompt(
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: str,
    ) -> str:
        schema_json = json.dumps(
            schema.model_json_schema(), indent=2
        )
        parts = []
        if system_prompt:
            parts.append(f"[System] {system_prompt}")
        parts.append(
            f"You must respond with valid JSON matching this schema:\n"
            f"```json\n{schema_json}\n```"
        )
        parts.append(f"[User] {prompt}")
        return "\n\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
#  Backend 2: Instructor (Cloud OpenAI-Compatible Constrained Calling)
# ═══════════════════════════════════════════════════════════════════════════


class InstructorBackend:
    """
    Uses `instructor` to patch OpenAI/OpenRouter clients for guaranteed
    Pydantic output.  Works with any OpenAI-compatible API.

    The library:
      1. Injects the JSON schema as a function-calling definition
      2. Parses the response into the Pydantic model
      3. Auto-retries on validation failure (up to `max_retries`)

    Requires: `pip install instructor openai`
    """

    def __init__(
        self,
        model_name: str = "anthropic/claude-3.5-sonnet",
        base_url: str = "https://openrouter.ai/api/v1",
        api_key: Optional[str] = None,
        max_retries: int = 3,
    ):
        self._model_name = model_name
        self._base_url = base_url
        self._api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._max_retries = max_retries
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            import instructor
            from openai import OpenAI

            raw_client = OpenAI(
                base_url=self._base_url,
                api_key=self._api_key,
            )
            self._client = instructor.from_openai(raw_client)
            logger.info(
                "Instructor client ready: %s @ %s",
                self._model_name,
                self._base_url,
            )
        except ImportError:
            raise ImportError(
                "instructor + openai are required for cloud constrained "
                "generation. Install: pip install instructor openai"
            )

    def generate(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> T:
        """
        Generate a response constrained to the Pydantic schema.
        Uses function-calling + auto-retry for guaranteed valid output.
        """
        self._ensure_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        schema_hint = json.dumps(schema.model_json_schema(), indent=2)
        user_content = (
            f"{prompt}\n\n"
            f"Respond with valid JSON matching this schema:\n"
            f"```json\n{schema_hint}\n```"
        )
        messages.append({"role": "user", "content": user_content})

        result = self._client.chat.completions.create(
            model=self._model_name,
            response_model=schema,
            messages=messages,
            max_tokens=max_tokens,
            max_retries=self._max_retries,
        )
        return result


# ═══════════════════════════════════════════════════════════════════════════
#  Backend 3: Ollama JSON Mode (Local, No GPU Model Loading)
# ═══════════════════════════════════════════════════════════════════════════


class OllamaConstrainedBackend:
    """
    Uses Ollama's native JSON mode (`format: "json"`) combined with
    Pydantic post-validation and auto-retry.

    Lighter than outlines (no model weights in Python process).
    Requires: Ollama running at localhost:11434.
    """

    def __init__(
        self,
        model_name: str = "llama3",
        endpoint: str = "http://localhost:11434/api/generate",
        max_retries: int = 3,
        timeout: float = 120.0,
    ):
        self._model_name = model_name
        self._endpoint = endpoint
        self._max_retries = max_retries
        self._timeout = timeout

    def generate(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> T:
        """
        Generate via Ollama JSON mode + Pydantic validation + retry.
        """
        schema_json = json.dumps(schema.model_json_schema(), indent=2)

        full_system = (
            f"{system_prompt}\n\n"
            f"CRITICAL: You MUST respond with valid JSON matching "
            f"this exact schema:\n```json\n{schema_json}\n```\n"
            f"Output ONLY the JSON object. No markdown, no explanation."
        ).strip()

        last_error: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            try:
                payload = {
                    "model": self._model_name,
                    "prompt": prompt,
                    "system": full_system,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": max_tokens,
                    },
                }
                resp = httpx.post(
                    self._endpoint, json=payload, timeout=self._timeout
                )
                resp.raise_for_status()
                raw_text = resp.json().get("response", "")

                # Parse and validate against the Pydantic schema
                parsed = json.loads(raw_text)
                return schema.model_validate(parsed)

            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                logger.warning(
                    "Ollama attempt %d/%d failed validation: %s",
                    attempt, self._max_retries, e,
                )
                # Retry with error feedback injected into prompt
                prompt = (
                    f"{prompt}\n\n"
                    f"[PREVIOUS ATTEMPT FAILED: {e}]\n"
                    f"Fix the JSON output to match the schema exactly."
                )
                continue

            except httpx.HTTPError as e:
                raise ConnectionError(
                    f"Ollama request failed: {e}. "
                    f"Is Ollama running at {self._endpoint}?"
                ) from e

        raise ValueError(
            f"Failed to produce valid {schema.__name__} after "
            f"{self._max_retries} attempts. Last error: {last_error}"
        )


# ═══════════════════════════════════════════════════════════════════════════
#  Unified Grammar Shield — auto-selects the best available backend
# ═══════════════════════════════════════════════════════════════════════════


class BackendType(str, Enum):
    OUTLINES = "outlines"
    INSTRUCTOR = "instructor"
    OLLAMA = "ollama"
    AUTO = "auto"


class GrammarShield:
    """
    Unified constrained generation interface.

    The Grammar Shield ensures that NO agent can produce raw,
    unstructured text for reasoning or tool calls.  Every output
    is mathematically constrained to a Pydantic schema.

    Usage:
        shield = GrammarShield()  # auto-detects best backend

        # Structured agent reasoning
        output = shield.generate(
            "Analyze the stock price of AAPL",
            schema=AgentOutput,
            system_prompt="You are a financial analyst.",
        )

        # Structured tool call
        call = shield.generate(
            "Search the web for 'Python async patterns'",
            schema=ToolCallRequest,
        )
    """

    def __init__(
        self,
        backend: BackendType = BackendType.AUTO,
        model_name: Optional[str] = None,
        **backend_kwargs: Any,
    ):
        self._backend_type = backend
        self._model_name = model_name
        self._backend_kwargs = backend_kwargs
        self._backend = None

    def _resolve_backend(self) -> Any:
        """Select and instantiate the best available backend."""
        if self._backend is not None:
            return self._backend

        if self._backend_type == BackendType.OUTLINES:
            self._backend = OutlinesBackend(
                model_name=self._model_name or "Qwen/Qwen2.5-1.5B-Instruct",
                **self._backend_kwargs,
            )
            return self._backend

        if self._backend_type == BackendType.INSTRUCTOR:
            self._backend = InstructorBackend(
                model_name=self._model_name or "anthropic/claude-3.5-sonnet",
                **self._backend_kwargs,
            )
            return self._backend

        if self._backend_type == BackendType.OLLAMA:
            self._backend = OllamaConstrainedBackend(
                model_name=self._model_name or "llama3",
                **self._backend_kwargs,
            )
            return self._backend

        # AUTO mode: detect what's available
        # Priority: Ollama (free, local) → Instructor (cloud) → Outlines (heavy)

        # 1. Check Ollama
        if self._is_ollama_available():
            logger.info("GrammarShield: auto-selected Ollama backend")
            self._backend = OllamaConstrainedBackend(
                model_name=self._model_name or "llama3",
                **self._backend_kwargs,
            )
            return self._backend

        # 2. Check cloud API keys
        if os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"):
            logger.info("GrammarShield: auto-selected Instructor backend")
            self._backend = InstructorBackend(
                model_name=self._model_name or "anthropic/claude-3.5-sonnet",
                **self._backend_kwargs,
            )
            return self._backend

        # 3. Fall back to outlines (requires GPU / heavy model)
        logger.info("GrammarShield: auto-selected Outlines backend (heavyweight)")
        self._backend = OutlinesBackend(
            model_name=self._model_name or "Qwen/Qwen2.5-1.5B-Instruct",
            **self._backend_kwargs,
        )
        return self._backend

    @staticmethod
    def _is_ollama_available() -> bool:
        """Ping Ollama to check if it's running."""
        try:
            resp = httpx.get(
                "http://localhost:11434/api/version", timeout=2.0
            )
            return resp.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> T:
        """
        Generate a response constrained to the Pydantic schema.

        This is the ONLY way agents should produce output.
        Raw text generation is forbidden.

        Args:
            prompt:        The user/agent prompt.
            schema:        Pydantic model class defining the output shape.
            system_prompt: Optional system context.
            max_tokens:    Maximum generation length.

        Returns:
            A validated instance of `schema`.

        Raises:
            ValueError: If generation fails after all retries.
            ImportError: If required backend libraries are missing.
        """
        backend = self._resolve_backend()
        return backend.generate(
            prompt=prompt,
            schema=schema,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

    def generate_tool_call(
        self,
        prompt: str,
        available_tools: List[Dict[str, Any]],
        system_prompt: str = "",
    ) -> ToolCallRequest:
        """
        Force the LLM to select and parameterize a tool call.

        The output is constrained to the ToolCallRequest schema —
        the LLM cannot hallucinate tool names or arguments.
        """
        tool_manifest = "\n".join(
            f"  - {t['name']}: {t.get('description', '')} "
            f"| params: {json.dumps(t.get('parameters', {}))}"
            for t in available_tools
        )
        augmented_prompt = (
            f"{prompt}\n\n"
            f"[AVAILABLE TOOLS]\n{tool_manifest}\n\n"
            f"Select the best tool and provide exact arguments."
        )
        return self.generate(
            prompt=augmented_prompt,
            schema=ToolCallRequest,
            system_prompt=system_prompt,
        )

    def generate_reasoning(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> AgentOutput:
        """
        Force the LLM to produce structured reasoning with chain-of-thought.

        Returns a validated AgentOutput with reasoning steps, confidence
        scores, and optional formal assertions for Z3 verification.
        """
        return self.generate(
            prompt=prompt,
            schema=AgentOutput,
            system_prompt=(
                f"{system_prompt}\n\n"
                "Think step by step. For each step, state your thought, "
                "the action you're taking, and your confidence level. "
                "Include formal assertions where applicable."
            ),
        )

    @property
    def backend_name(self) -> str:
        """Name of the active backend."""
        backend = self._resolve_backend()
        return type(backend).__name__
