# HANERMA CUA — How to Run

## Prerequisites

```bash
pip install anthropic playwright openai python-dotenv
playwright install chromium
```

## Configuration

`.env` in the project root:

```
OPENROUTER_API_KEY=sk-or-...    # free at openrouter.ai — required
ANTHROPIC_API_KEY=sk-ant-...    # optional, only if you want to use Claude
```

The system auto-selects the model based on which key is present.
If both are set, OpenRouter (free Nemotron VL) is used by default.

---

## Run the CUA

```bash
cd /Users/macbook/Documents/HANERMA
python demo.py
```

A Chromium browser opens. The agent navigates autonomously.
The terminal streams a live cognitive trace each cycle:
- Current URL
- LLM chain-of-thought reasoning
- Action chosen + target element
- Z3 formal verification proof time
- Cumulative token consumption

Press `Ctrl+C` at any time to stop.

---

## Change the target site or goal

Edit the `CONFIG` block at the top of `demo.py`:

```python
URL  = "https://news.ycombinator.com"   # any URL
GOAL = "Find 3 posts about AI and click into each one."
MAX_CYCLES  = 35     # hard stop after N cycles
DELAY_SECS  = 2.5    # seconds between perception cycles
```

---

## Output files (generated per run)

| File | Contents |
|---|---|
| `cua_audit.jsonl` | Immutable per-cycle audit trail (screen hash, LLM I/O, Z3 verdict, latency) |
| `enterprise_readiness_report.json` | Post-session production readiness scorecard (9 dimensions) |

---

## Run headless (no visible browser)

In `demo.py`, change:
```python
headless=False   →   headless=True
```

---

## Architecture overview

```
PERCEIVE  →  screenshot of browser viewport
REASON    →  vision LLM (Nemotron VL / Claude) decides next action
VERIFY    →  Z3 theorem prover checks action safety before execution
ACT       →  Playwright executes the action in the browser
AUDIT     →  AuditRecord written to cua_audit.jsonl
REPEAT
```

Every 10 cycles: DriftMonitor uses Z3 to verify the agent is still
aligned with the original goal. If not, it hard-resets.
