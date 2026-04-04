"""
Predictive Failure & Intelligence Router.

Analyzes prompt complexity using token-entropy and structural ambiguity
to generate a Risk Score (0.0–1.0).

If Risk > 0.8, autonomously injects a CriticAgent into the DAG.

Routes requests to optimal LLM backends:
  - Low risk / short prompts → localhost Ollama (fast, free)
  - Code-heavy / high risk   → cloud APIs (frontier reasoning)
"""

import logging
import math
import re
import time
from collections import Counter, deque
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("hanerma.model_router")


# ═══════════════════════════════════════════════════════════════════════════
#  Prompt Complexity Analyzer
# ═══════════════════════════════════════════════════════════════════════════

_CODE_INDICATORS = [
    re.compile(r"^\s*(def |class |import |from |return |if |for |while |try:|except)"),
    re.compile(r"[=!<>]="),
    re.compile(r"\w+\(.*\)"),
    re.compile(r"```"),
    re.compile(r"^\s*#"),
    re.compile(r"\{.*\}"),
    re.compile(r"\[.*\]"),
]


def analyze_prompt_complexity(prompt: str) -> Dict[str, Any]:
    """
    Analyze structural ambiguity and complexity of a prompt.

    Returns a dict with:
      - risk_score: float 0.0–1.0
      - token_count: int
      - entropy: float (Shannon entropy of token distribution)
      - nested_depth: int (max nesting of clauses)
      - code_ratio: float (fraction of content that looks like code)
      - signals: list of triggered risk signals
    """
    tokens = prompt.split()
    token_count = len(tokens)
    signals: List[str] = []

    # 1. Shannon Entropy of token distribution
    entropy = _token_entropy(tokens)

    # 2. Nested clause depth (parentheses, brackets, conditional depth)
    nested_depth = _nesting_depth(prompt)

    # 3. Code density ratio
    code_ratio = _code_ratio(prompt)

    # 4. Ambiguity indicators
    ambiguity_score = _ambiguity_score(prompt, tokens)

    # 5. Compute composite risk score
    risk = 0.0

    # Token count factor (long prompts = more risk)
    if token_count > 2000:
        risk += 0.2
        signals.append("long_prompt")
    elif token_count > 500:
        risk += 0.1
        signals.append("medium_prompt")

    # Entropy factor (high entropy = diverse/complex vocabulary)
    if entropy > 5.0:
        risk += 0.15
        signals.append("high_entropy")
    elif entropy > 4.0:
        risk += 0.08

    # Nesting depth (deeply nested logic = complex reasoning)
    if nested_depth >= 5:
        risk += 0.2
        signals.append("deep_nesting")
    elif nested_depth >= 3:
        risk += 0.1
        signals.append("moderate_nesting")

    # Code density (code-heavy = needs strong model)
    if code_ratio > 0.4:
        risk += 0.2
        signals.append("code_heavy")
    elif code_ratio > 0.15:
        risk += 0.1
        signals.append("code_present")

    # Ambiguity (vague/unclear language)
    if ambiguity_score > 0.3:
        risk += 0.15
        signals.append("high_ambiguity")

    # Multi-step reasoning indicators
    multi_step_keywords = [
        "then", "after that", "next", "finally", "first",
        "step 1", "step 2", "phase", "stage",
    ]
    multi_step_hits = sum(1 for kw in multi_step_keywords if kw in prompt.lower())
    if multi_step_hits >= 3:
        risk += 0.1
        signals.append("multi_step")

    # Clamp to [0, 1]
    risk = max(0.0, min(1.0, risk))

    return {
        "risk_score": round(risk, 3),
        "token_count": token_count,
        "entropy": round(entropy, 3),
        "nested_depth": nested_depth,
        "code_ratio": round(code_ratio, 3),
        "ambiguity_score": round(ambiguity_score, 3),
        "signals": signals,
    }


def _token_entropy(tokens: List[str]) -> float:
    """Shannon entropy of the token frequency distribution."""
    if not tokens:
        return 0.0
    counts = Counter(t.lower() for t in tokens)
    total = len(tokens)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _nesting_depth(text: str) -> int:
    """Max nesting depth of brackets/parens/braces + conditional keywords."""
    max_depth = 0
    current = 0
    openers = set("([{")
    closers = set(")]}")
    for ch in text:
        if ch in openers:
            current += 1
            max_depth = max(max_depth, current)
        elif ch in closers:
            current = max(0, current - 1)

    # Also count conditional/logical keyword nesting
    conditional_kws = ["if", "else", "elif", "while", "for", "try", "except"]
    lines = text.split("\n")
    indent_depth = 0
    for line in lines:
        stripped = line.lstrip()
        if any(stripped.startswith(kw) for kw in conditional_kws):
            indent_level = len(line) - len(stripped)
            indent_depth = max(indent_depth, indent_level // 4)

    return max(max_depth, indent_depth)


def _code_ratio(text: str) -> float:
    """Fraction of lines that look like code."""
    if not text.strip():
        return 0.0
    lines = text.strip().split("\n")
    code_lines = 0
    for line in lines:
        for prog in _CODE_INDICATORS:
            if prog.search(line):
                code_lines += 1
                break
    return code_lines / len(lines)


def _ambiguity_score(text: str, tokens: List[str]) -> float:
    """Score vague/unclear language."""
    ambiguous_words = {
        "maybe", "perhaps", "possibly", "might", "could",
        "somehow", "something", "whatever", "stuff", "things",
        "etc", "various", "some", "any", "kind of", "sort of",
    }
    if not tokens:
        return 0.0
    hits = sum(1 for t in tokens if t.lower().strip(".,!?") in ambiguous_words)
    return hits / len(tokens)


# ═══════════════════════════════════════════════════════════════════════════
#  Latency Monitor — tracks response times per model
# ═══════════════════════════════════════════════════════════════════════════


class LatencyMonitor:
    """Rolling window latency tracker."""

    def __init__(self, window_size: int = 20):
        self._windows: Dict[str, deque] = {}
        self._window_size = window_size

    def record(self, model: str, latency_ms: float) -> None:
        if model not in self._windows:
            self._windows[model] = deque(maxlen=self._window_size)
        self._windows[model].append(latency_ms)

    def avg_latency(self, model: str) -> float:
        if model not in self._windows or not self._windows[model]:
            return float("inf")
        return sum(self._windows[model]) / len(self._windows[model])

    def is_slow(self, model: str, threshold_ms: float = 5000.0) -> bool:
        """Only flag slowness if we have actual recorded data."""
        if model not in self._windows or not self._windows[model]:
            return False  # No data → don't flag as slow
        return self.avg_latency(model) > threshold_ms


# ═══════════════════════════════════════════════════════════════════════════
#  Best Model Router
# ═══════════════════════════════════════════════════════════════════════════


class BestModelRouter:
    """
    Routes prompts to the optimal LLM backend based on complexity analysis.

      < 1000 tokens + low risk  → localhost:11434 (Ollama)
      Code-heavy / high risk    → Cloud API (frontier reasoning)
      Very long context         → Cheap long-context cloud model
    """

    # Backend targets
    OLLAMA_LOCAL = "http://localhost:11434"
    CLOUD_FRONTIER = "openrouter/anthropic/claude-sonnet-4"
    CLOUD_LONG_CTX = "openrouter/google/gemini-2.5-pro"

    def __init__(self):
        self.latency = LatencyMonitor()
        self._route_history: List[Dict[str, Any]] = []

    def route(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze prompt and return the optimal routing decision.

        Returns:
            {
                "model": str,
                "endpoint": str,
                "risk_analysis": {...},
                "inject_critic": bool,
                "reason": str,
            }
        """
        analysis = analyze_prompt_complexity(prompt)
        risk = analysis["risk_score"]
        token_count = analysis["token_count"]
        code_ratio = analysis["code_ratio"]
        signals = analysis["signals"]

        inject_critic = risk > 0.8
        model = self.OLLAMA_LOCAL
        reason = "default_local"

        # Decision tree
        if risk > 0.7 or "code_heavy" in signals:
            model = self.CLOUD_FRONTIER
            reason = "high_risk_or_code"
        elif token_count > 5000:
            model = self.CLOUD_LONG_CTX
            reason = "long_context"
        elif token_count < 1000 and risk < 0.4:
            model = self.OLLAMA_LOCAL
            reason = "short_low_risk"
        elif code_ratio > 0.15:
            model = self.CLOUD_FRONTIER
            reason = "code_present"
        else:
            model = self.OLLAMA_LOCAL
            reason = "medium_complexity_local"

        # Latency override: if cloud is slow, fall back to local
        if model != self.OLLAMA_LOCAL and self.latency.is_slow(model):
            logger.warning(
                "Model %s is slow (avg %.0fms), falling back to local",
                model, self.latency.avg_latency(model),
            )
            model = self.OLLAMA_LOCAL
            reason = "latency_fallback"

        decision = {
            "model": model,
            "endpoint": self.OLLAMA_LOCAL if model == self.OLLAMA_LOCAL else "https://openrouter.ai/api/v1",
            "risk_analysis": analysis,
            "inject_critic": inject_critic,
            "reason": reason,
        }

        self._route_history.append({
            "timestamp": time.time(),
            "model": model,
            "risk": risk,
            "tokens": token_count,
            "reason": reason,
        })

        return decision

    async def speculative_decode_request(self, prompt: str, memory_manager=None) -> Dict[str, Any]:
        """
        Latency Shield: Generate speculative tokens using tiny model while primary model warms up.
        """
        if not memory_manager:
            return {"speculative_tokens": "", "cache_hit": False, "latency_ms": 0}
        
        try:
            return await memory_manager.speculative_decode(prompt, max_tokens=20)
        except Exception as e:
            logger.warning(f"Speculative decode failed: {e}")
            return {"speculative_tokens": "", "cache_hit": False, "latency_ms": 0, "error": str(e)}

    def inject_style_into_request(self, prompt: str, memory_manager=None) -> str:
        """
        Inject user style into the request prompt.
        """
        if not memory_manager:
            return prompt
        
        try:
            return memory_manager.inject_user_style_into_prompt(prompt)
        except Exception as e:
            logger.warning(f"Style injection failed: {e}")
            return prompt

    def record_response(self, model: str, latency_ms: float) -> None:
        """Record response time for adaptive routing."""
        self.latency.record(model, latency_ms)

    def inject_critic_node(self, dag_spec) -> None:
        """
        Autonomously inject a CriticAgent into the DAG when risk > 0.8.
        The Critic validates outputs before they reach downstream agents.
        """
        from hanerma.orchestrator.nlp_compiler import AgentSpec

        critic = AgentSpec(
            agent_id="critic_auto",
            name="Auto-Critic",
            role="Validates reasoning and catches potential failures before they propagate",
            system_prompt=(
                "You are a strict validator. Review the output of the previous agent. "
                "Check for logical inconsistencies, missing edge cases, and potential "
                "errors. If the output is sound, approve it. If not, explain the issues."
            ),
            tools=[],
            model="llama3",
            dependencies=[],
        )

        # Insert critic before the last agent in the pipeline
        if len(dag_spec.agents) > 1:
            last_agent = dag_spec.agents[-1]
            critic.dependencies = [dag_spec.agents[-2].agent_id]
            last_agent.dependencies = ["critic_auto"]
            dag_spec.agents.insert(-1, critic)
            dag_spec.edges.append([dag_spec.agents[-3].agent_id, "critic_auto"])
            dag_spec.edges.append(["critic_auto", last_agent.agent_id])
        else:
            # Single agent: add critic after it
            critic.dependencies = [dag_spec.agents[0].agent_id]
            dag_spec.agents.append(critic)
            dag_spec.edges.append([dag_spec.agents[0].agent_id, "critic_auto"])

        logger.info("[ROUTER] Injected Auto-Critic agent (risk > 0.8)")

    @property
    def stats(self) -> Dict[str, Any]:
        """Routing statistics."""
        if not self._route_history:
            return {"total_routes": 0}

        models_used = Counter(r["model"] for r in self._route_history)
        avg_risk = sum(r["risk"] for r in self._route_history) / len(self._route_history)

        return {
            "total_routes": len(self._route_history),
            "models_used": dict(models_used),
            "avg_risk": round(avg_risk, 3),
            "local_ratio": round(
                models_used.get(self.OLLAMA_LOCAL, 0) / len(self._route_history), 3
            ),
        }
