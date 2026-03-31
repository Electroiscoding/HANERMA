"""
HANERMA CUA — Autonomous Execution Runner

Executes a live Computer Use Agent session with real-time observability output.

Every perception-cognition-action cycle emits:
  - Current page URL (spatial context)
  - LLM chain-of-thought reasoning (cognitive trace)
  - Chosen action + target (execution intent)
  - Z3 formal verification proof time (safety audit)
  - Cumulative token consumption

Run:
    python demo.py
"""

import asyncio
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent / "src"))

from hanerma.cua.browser_runtime import BrowserRuntime
from hanerma.cua.cua_agent import CUAAgent
from hanerma.cua.audit_trail import CUAAuditTrail, AuditedCUAAgent, EnterpriseReadinessAuditor
import os

# ── CONFIG ────────────────────────────────────────────────────────
URL  = "https://news.ycombinator.com"
GOAL = (
    "You are an autonomous browser agent. Start on Hacker News. "
    "Find 3 posts about AI, LLMs, or machine learning. "
    "For each post: click its title link to open the article in the browser, "
    "scroll down to read some of the content, then navigate back to "
    "https://news.ycombinator.com to find the next post. "
    "You must open each article yourself by clicking or navigating to its URL — "
    "do not just list them. After visiting all 3 articles, set goal_progress to 1.0 and stop."
)
MAX_CYCLES  = 35   # well under the 50-request limit
DELAY_SECS  = 2.0

# ── MODEL SELECTION ──────────────────────────────────────────────
# USE_CLAUDE = True  → Claude vision (paid, ~7s/cycle, most reliable)
# USE_CLAUDE = False → Text mode via OpenRouter (free, fast, zero parse errors)
USE_CLAUDE = False

# Pick one:
MODEL = "meta-llama/llama-3.1-8b-instruct"            # fast, reliable JSON
# MODEL = "nvidia/llama-3.1-nemotron-nano-8b-v1"      # Nemotron Nano 8B
# MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"    # Nemotron Super 49B (larger)
# MODEL = "google/gemma-3-12b-it:free"                # Gemma 3 12B free

_runtime_ref = None   # shared so callback can read page text

if USE_CLAUDE:
    from hanerma.cua.claude_vision_callback import make_claude_vision_callback as _make_cb
    MODEL = "claude-opus-4-6"
    async def _get_callback(): return await _make_cb(goal=GOAL, model=MODEL)
else:
    from hanerma.cua.text_callback import make_text_callback
    async def _get_callback():
        return await make_text_callback(goal=GOAL, model=MODEL, runtime=_runtime_ref)
# ─────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────


def banner(text, char="═", width=62):
    print(f"\n  ╔{char*width}╗")
    for line in text.strip().split("\n"):
        print(f"  ║  {line:<{width-2}}║")
    print(f"  ╚{char*width}╝")


async def main():
    banner(
        f"HANERMA CUA — Autonomous Browser Agent\n"
        f"Model : {MODEL}\n"
        f"Goal  : {GOAL[:55]}...\n"
        f"Cycles: {MAX_CYCLES}   Delay: {DELAY_SECS}s"
    )
    print()
    print("  ⚡ Starting browser... (you will see it open)")
    print("  ⚡ AI takes a screenshot every cycle — NO human input")
    print("  ⚡ Every action is Z3-verified before execution")
    print()

    runtime = BrowserRuntime(
        headless=False,          # headed mode — browser viewport is visible
        viewport_width=1280,
        viewport_height=900,
        slow_mo=80,              # slight slow-mo so actions are visible
    )
    await runtime.start()
    await runtime.navigat®e(URL)
    print(f"  Browser open at: {URL}\n")

    global _runtime_ref
    _runtime_ref = runtime
    llm_callback = await _get_callback()






    agent   = CUAAgent("cua-session-01", runtime, llm_callback, role="web_researcher")
    audit   = CUAAuditTrail("cua-session-01", export_path="cua_audit.jsonl")
    audited = AuditedCUAAgent(agent, audit, MODEL)
    agent.drift_monitor.set_goal("cua-session-01", GOAL)

    total_tokens = 0
    posts_visited = 0
    cycle_num = 0
    MAX_RETRIES = 3   # retry a failed cycle up to 3 times before advancing

    try:
        while cycle_num < MAX_CYCLES:
            cycle_num += 1

            # Retry loop — cycle must pass before we advance
            result = None
            for attempt in range(1, MAX_RETRIES + 1):
                result = await audited.run_once()
                if result.get("status") in ("success", "goal_complete"):
                    break
                if attempt < MAX_RETRIES:
                    print(f"  ⚠ Cycle {cycle_num} attempt {attempt} failed ({result.get('status')}) — retrying...")
                    await asyncio.sleep(1.0)

            # Pull the audit record for this cycle
            rec = audit.get_records()[-1]
            total_tokens += rec.llm_input_tokens + rec.llm_output_tokens

            try:
                resp   = json.loads(rec.llm_response_raw)
                reason = resp.get("reasoning", "")
                prog   = resp.get("goal_progress", 0)
            except Exception:
                reason = ""
                prog   = 0

            action  = result.get("action", result.get("status", "?"))
            target  = str(result.get("target", ""))[:45]
            status  = result.get("status", "?")
            z3_ms   = result.get("z3_proof_time_ms", 0)
            url     = rec.screen_url[:50] if rec.screen_url else ""

            # Structured per-cycle observability output
            print(f"  ┌─ Cycle {cycle_num:02d}/{MAX_CYCLES} {'─'*46}┐")
            print(f"  │  📍 URL     : {url:<46}│")
            print(f"  │  🧠 Thinking: {reason[:46]:<46}│")
            print(f"  │  ⚡ Action  : {action:<12} → {target:<30}│")
            print(f"  │  🔒 Z3 proof: {z3_ms:.1f}ms   tokens: {total_tokens:,}   progress: {prog*100:.0f}%  │")
            print(f"  │  {'✅ OK' if status=='success' else '❌ '+status:<58}│")
            print(f"  └{'─'*60}┘")

            if action == "click" and ("ycombinator.com/item" in url or prog > 0.3):
                posts_visited += 1

            if isinstance(prog, (int, float)) and prog >= 1.0:
                print()
                print("  🎯 AI reports goal COMPLETE — stopping.")
                break

            await asyncio.sleep(DELAY_SECS)

    except KeyboardInterrupt:
        print("\n  Stopped by user (Ctrl+C)")
    finally:
        await runtime.stop()

    # Final report
    print()
    # SLA: 90s for free OpenRouter reasoning models, 15s for paid (Claude)
    sla_ms = 15_000 if MODEL.startswith("claude") else 90_000
    report = EnterpriseReadinessAuditor(audit, latency_sla_ms=sla_ms).run()
    print(report.summary())
    print(f"  📄 Audit trail saved    → cua_audit.jsonl")
    print(f"  📊 Readiness report    → enterprise_readiness_report.json")
    with open("enterprise_readiness_report.json", "w") as f:
        import json as _j
        _j.dump(report.to_dict(), f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
