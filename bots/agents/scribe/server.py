"""
Scribe agent — daily-digest writer.

Tier 3 (Anthropic Claude Haiku). Format-faithful drafting from Sentinel + Watcher +
Auditor + token-usage outputs. Uses prompt caching on the system prompt + category
catalog so repeated invocations cost ~1/10th of input tokens.

Cost: ~$0.02 per digest at qty ~5k input / 800 output tokens.

Tools:
  scribe.generate_digest(preview=False, model=None)   -> {ok, path, preview, tokens, cost_usd}
  scribe.weekly_summary(preview=False, model=None)    -> {ok, path, preview, tokens, cost_usd}
  scribe.list_inputs()                                -> {sentinel, watcher, auditor, usage}
  scribe.health()                                     -> {ok, api_key_present, model}
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[scribe] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Bot memory loader (see 12_LLM_ORCHESTRATION/BOT-MEMORY-PROTOCOL.md)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from _shared import bot_memory  # type: ignore
    HAS_BOT_MEMORY = True
except Exception:
    HAS_BOT_MEMORY = False

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "scribe"
AGENT_DIR.mkdir(parents=True, exist_ok=True)
DIGEST_PATH = HUB_ROOT / "07_DASHBOARD" / "daily-digest.md"
WEEKLY_DIR = HUB_ROOT / "07_DASHBOARD" / "weekly"
WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
HISTORY_DIR = AGENT_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# Inputs (peer-agent state files)
SENTINEL_ALARMS = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "sentinel" / "alarms.json"
WATCHER_QUEUE = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "watcher" / "queue.jsonl"
AUDITOR_FINDINGS = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "auditor" / "findings"
FOLLOWUPS = HUB_ROOT / "01_MEMORY" / "_consolidated" / "ALL-FOLLOWUPS.md"
WHERE_I_STOPPED = HUB_ROOT / "01_MEMORY" / "_consolidated" / "ALL-WHERE-I-STOPPED.md"

DEFAULT_MODEL = os.environ.get("SCRIBE_MODEL", "claude-haiku-4-5-20251001")
# Haiku 4.5 pricing per 1k tokens
COST_INPUT = 0.00080
COST_OUTPUT = 0.00400
COST_CACHE_WRITE = 0.00100
COST_CACHE_READ = 0.00008

# Cached system prompt — stable across runs, prompt-cache eligible.
SYSTEM_PROMPT = """You are Scribe, the Sinister Skills hub daily-digest writer.

Your single job: turn the operator's raw agent-state inputs into a tight, scannable
markdown digest they can read in 60 seconds every morning.

Hard rules:
- Markdown only. No code fences around the whole output. Render H1 + H2 + bullet lists.
- NEVER invent items not present in the inputs. If an input section is empty, say so briefly.
- Preserve operator-action phrasing verbatim from Sentinel's "message" field — those are exact instructions.
- Severity ordering: critical -> high -> warning -> normal. Sort within each section by days_until ascending.
- Be terse. Each bullet ~1 line. No filler ("Today is a great day to ship!" -> NO).
- Never quote API keys, tokens, or secrets even if they appear in inputs — write "[REDACTED]" instead.

Output shape (exactly these H2 sections, in order):

# Daily digest - <ISO date>

## Urgent (operator action this week)
<bullets from sentinel.check_urgent + ALL-FOLLOWUPS active blockers>

## What changed
<bullets from watcher.queue (recent file drift)>

## Audit findings
<one-line summary of auditor findings: secrets / duplicates / stale counts>

## Cost
<one line: yesterday's token spend by agent, total USD>

## What to work on next
<2-4 bullets ranked by urgency, drawn ONLY from above sections>
"""


def log_call(tool: str, model: str | None = None, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "scribe",
        "model": model,
        "input_tokens": extra.pop("input_tokens", 0),
        "output_tokens": extra.pop("output_tokens", 0),
        "cache_read_tokens": extra.pop("cache_read_tokens", 0),
        "cache_write_tokens": extra.pop("cache_write_tokens", 0),
        "cost_usd": extra.pop("cost_usd", 0.0),
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


# ===== Input gathering =====

def load_sentinel_alarms() -> list[dict[str, Any]]:
    if not SENTINEL_ALARMS.exists():
        return []
    try:
        alarms = json.loads(SENTINEL_ALARMS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    out = []
    now = datetime.now(timezone.utc)
    for a in alarms:
        try:
            due = datetime.fromisoformat(a["due"].replace("Z", "+00:00"))
            days = (due - now).days
        except Exception:
            days = None
        out.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "severity": a.get("severity"),
            "due": a.get("due"),
            "days_until": days,
            "message": a.get("message", ""),
            "tags": a.get("tags", []),
        })
    out.sort(key=lambda x: (x.get("days_until") if x.get("days_until") is not None else 9999))
    return out


def load_watcher_queue(limit: int = 30) -> list[dict[str, Any]]:
    if not WATCHER_QUEUE.exists():
        return []
    lines = WATCHER_QUEUE.read_text(encoding="utf-8").splitlines()
    out = []
    for l in lines[-limit:]:
        if not l.strip():
            continue
        try:
            out.append(json.loads(l))
        except json.JSONDecodeError:
            continue
    return out


def load_auditor_findings() -> dict[str, Any]:
    """Pull the freshest findings file from auditor/findings/."""
    if not AUDITOR_FINDINGS.exists():
        return {}
    candidates = sorted(AUDITOR_FINDINGS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return {}
    try:
        return json.loads(candidates[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_usage_summary(window_hours: int = 24) -> dict[str, Any]:
    """Sum token-usage.jsonl entries within window."""
    if not USAGE_LOG.exists():
        return {"by_agent": {}, "total_cost_usd": 0.0, "calls": 0}
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    by_agent: dict[str, dict[str, float]] = {}
    total_cost = 0.0
    calls = 0
    for line in USAGE_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            ts = datetime.fromisoformat(r["ts"].replace("Z", "+00:00"))
        except Exception:
            continue
        if ts < cutoff:
            continue
        agent = r.get("agent", "unknown")
        slot = by_agent.setdefault(agent, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        slot["calls"] += 1
        slot["input_tokens"] += r.get("input_tokens", 0) or 0
        slot["output_tokens"] += r.get("output_tokens", 0) or 0
        slot["cost_usd"] += r.get("cost_usd", 0.0) or 0.0
        total_cost += r.get("cost_usd", 0.0) or 0.0
        calls += 1
    return {"by_agent": by_agent, "total_cost_usd": round(total_cost, 4), "calls": calls, "window_hours": window_hours}


def load_followups_excerpt(max_lines: int = 30) -> str:
    if not FOLLOWUPS.exists():
        return ""
    try:
        lines = FOLLOWUPS.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(lines[:max_lines])
    except Exception:
        return ""


def load_latest_runlog(script_name: str) -> dict[str, Any] | None:
    """Pull the most-recent runlog manifest for a script name. Used to surface
    Hetzner state / activation results in the daily digest."""
    runlog_dir = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "script-runs"
    if not runlog_dir.exists():
        return None
    candidates = [p for p in runlog_dir.glob("*.json") if p.stem.lower().startswith(script_name.lower())]
    if not candidates:
        return None
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_pending_actions() -> str:
    """Read runtime-state/PENDING-NEXT-ACTIONS.md if present."""
    p = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "PENDING-NEXT-ACTIONS.md"
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def load_memory_garden() -> dict[str, Any] | None:
    """Per-bot aliveness snapshot. Mirrors sinister-bus.memory_garden."""
    try:
        scribe_dir = Path(__file__).resolve().parent
        agents_dir = scribe_dir.parent
        if str(agents_dir) not in sys.path:
            sys.path.insert(0, str(agents_dir))
        from _shared import bot_memory as _bm  # type: ignore
    except Exception:
        return None
    garden = []
    for name in ("sentinel", "translator", "librarian", "watcher", "auditor", "sinister-bus",
                 "triage", "scribe", "curator", "custodian", "stealth-browser", "researcher"):
        try:
            s = _bm.memory_stats(name)
            garden.append({"bot": name, "facts": s.get("fact_count", 0),
                           "calls": s.get("lifetime_calls", 0),
                           "last_absorbed": s.get("last_absorbed"),
                           "smart_retrieval": s.get("smart_retrieval_active", False)})
        except Exception:
            pass
    garden.sort(key=lambda r: -(r.get("facts") or 0))
    return {"garden": garden, "total_facts": sum(r.get("facts", 0) for r in garden)}


def gather_inputs(window_hours: int = 24) -> dict[str, Any]:
    return {
        "today": datetime.now(timezone.utc).date().isoformat(),
        "sentinel_alarms": load_sentinel_alarms(),
        "watcher_recent": load_watcher_queue(limit=30),
        "auditor_findings": load_auditor_findings(),
        "usage_24h": load_usage_summary(window_hours=window_hours),
        "followups_excerpt": load_followups_excerpt(max_lines=40),
        "hetzner_state_latest": load_latest_runlog("check-hetzner-state"),
        "activate_everything_latest": load_latest_runlog("activate-everything"),
        "deploy_hetzner_latest": load_latest_runlog("deploy-all-to-hetzner"),
        "pending_next_actions": load_pending_actions(),
        "memory_garden": load_memory_garden(),
    }


# ===== Anthropic call (with prompt caching) =====

def get_system_prompt() -> str:
    """Prefer the SYSTEM-PROMPT.md + gotchas + learned facts chain. Fall back to hard-coded."""
    if HAS_BOT_MEMORY:
        loaded = bot_memory.load_memory("scribe")
        if loaded and "[no SYSTEM-PROMPT.md found" not in loaded:
            return loaded
    return SYSTEM_PROMPT


def call_haiku(user_payload: str, model: str, system_prompt: str | None = None) -> dict[str, Any]:
    if system_prompt is None:
        system_prompt = get_system_prompt()
    """Call Anthropic Haiku with prompt caching on the system prompt.

    Returns {ok, text, input_tokens, output_tokens, cache_read, cache_write, cost_usd}.
    """
    if not HAS_ANTHROPIC:
        return {"ok": False, "error": "anthropic SDK not installed (pip install anthropic)"}
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"ok": False, "error": "ANTHROPIC_API_KEY env var not set"}
    client = Anthropic(api_key=api_key)
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=1500,
            system=[{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_payload}],
        )
    except Exception as e:
        return {"ok": False, "error": f"Anthropic API error: {e}"}
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    usage = resp.usage
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cost = (
        (input_tokens / 1000) * COST_INPUT
        + (output_tokens / 1000) * COST_OUTPUT
        + (cache_write / 1000) * COST_CACHE_WRITE
        + (cache_read / 1000) * COST_CACHE_READ
    )
    return {
        "ok": True,
        "text": text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read,
        "cache_write_tokens": cache_write,
        "cost_usd": round(cost, 6),
    }


# ===== MCP server =====
mcp = FastMCP("scribe")


@mcp.tool()
def generate_digest(preview: bool = False, model: str | None = None) -> dict[str, Any]:
    """Generate today's daily digest. By default writes to 07_DASHBOARD/daily-digest.md.

    preview=True returns the generated text without writing.
    """
    chosen_model = model or DEFAULT_MODEL
    inputs = gather_inputs(window_hours=24)
    user_payload = (
        "Generate today's daily digest from these inputs. Follow the system prompt's output shape exactly.\n\n"
        f"```json\n{json.dumps(inputs, indent=2, default=str)}\n```"
    )
    result = call_haiku(user_payload, model=chosen_model)
    if not result.get("ok"):
        log_call("generate_digest", model=chosen_model, error=result.get("error"))
        return result
    body = result["text"]
    log_call(
        "generate_digest",
        model=chosen_model,
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        cache_read_tokens=result["cache_read_tokens"],
        cache_write_tokens=result["cache_write_tokens"],
        cost_usd=result["cost_usd"],
        preview=preview,
    )
    if preview:
        return {"ok": True, "preview": body, "tokens": {
            "input": result["input_tokens"], "output": result["output_tokens"],
            "cache_read": result["cache_read_tokens"], "cache_write": result["cache_write_tokens"],
        }, "cost_usd": result["cost_usd"], "model": chosen_model}
    # Archive previous + write new
    if DIGEST_PATH.exists():
        prev = DIGEST_PATH.read_text(encoding="utf-8")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        (HISTORY_DIR / f"daily-digest-{stamp}.md").write_text(prev, encoding="utf-8")
    atomic_write(DIGEST_PATH, body)
    return {
        "ok": True,
        "path": str(DIGEST_PATH.relative_to(HUB_ROOT)),
        "tokens": {"input": result["input_tokens"], "output": result["output_tokens"],
                   "cache_read": result["cache_read_tokens"], "cache_write": result["cache_write_tokens"]},
        "cost_usd": result["cost_usd"],
        "model": chosen_model,
    }


@mcp.tool()
def weekly_summary(preview: bool = False, model: str | None = None) -> dict[str, Any]:
    """Generate a 7-day rollup. Writes to 07_DASHBOARD/weekly/<iso-week>.md."""
    chosen_model = model or DEFAULT_MODEL
    inputs = gather_inputs(window_hours=24 * 7)
    week_label = datetime.now(timezone.utc).strftime("%G-W%V")
    user_payload = (
        f"Generate the weekly rollup for {week_label}. Same H2 sections as daily, "
        f"but aggregate across 7 days and add a '## Week-over-week' section "
        f"comparing total cost vs the prior week.\n\n"
        f"```json\n{json.dumps(inputs, indent=2, default=str)}\n```"
    )
    result = call_haiku(user_payload, model=chosen_model)
    if not result.get("ok"):
        log_call("weekly_summary", model=chosen_model, error=result.get("error"))
        return result
    body = result["text"]
    log_call("weekly_summary", model=chosen_model,
             input_tokens=result["input_tokens"], output_tokens=result["output_tokens"],
             cache_read_tokens=result["cache_read_tokens"], cache_write_tokens=result["cache_write_tokens"],
             cost_usd=result["cost_usd"], preview=preview)
    if preview:
        return {"ok": True, "preview": body, "cost_usd": result["cost_usd"], "model": chosen_model}
    out_path = WEEKLY_DIR / f"{week_label}.md"
    atomic_write(out_path, body)
    return {
        "ok": True,
        "path": str(out_path.relative_to(HUB_ROOT)),
        "tokens": {"input": result["input_tokens"], "output": result["output_tokens"],
                   "cache_read": result["cache_read_tokens"], "cache_write": result["cache_write_tokens"]},
        "cost_usd": result["cost_usd"],
        "model": chosen_model,
    }


@mcp.tool()
def list_inputs() -> dict[str, Any]:
    """Show the raw inputs Scribe would feed to Haiku. Useful for debugging without spending tokens."""
    log_call("list_inputs")
    return gather_inputs(window_hours=24)


@mcp.tool()
def absorb(fact: str, source: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Persist a fact into scribe's memory. Audit-logged. See BOT-MEMORY-PROTOCOL.md."""
    if not HAS_BOT_MEMORY:
        return {"ok": False, "error": "bot_memory module not loadable"}
    return bot_memory.absorb_fact("scribe", fact, source, tags or [])


@mcp.tool()
def list_facts(limit: int = 50) -> list[dict[str, Any]]:
    """List scribe's persisted absorbed facts."""
    if not HAS_BOT_MEMORY:
        return []
    return bot_memory.list_facts("scribe", limit=limit)


@mcp.tool()
def forget(fact_substring: str) -> dict[str, Any]:
    """Remove absorbed facts containing this substring. Audit-logged."""
    if not HAS_BOT_MEMORY:
        return {"ok": False, "error": "bot_memory module not loadable"}
    return bot_memory.forget_fact("scribe", fact_substring)


@mcp.tool()
def health() -> dict[str, Any]:
    """Health check - Anthropic SDK + API key + peer agents + bot memory."""
    log_call("health")
    mem_stats = bot_memory.memory_stats("scribe") if HAS_BOT_MEMORY else {}
    return {
        "ok": True,
        "agent": "scribe",
        "has_anthropic_sdk": HAS_ANTHROPIC,
        "api_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "model": DEFAULT_MODEL,
        "digest_path": str(DIGEST_PATH.relative_to(HUB_ROOT)),
        "sentinel_input_exists": SENTINEL_ALARMS.exists(),
        "watcher_input_exists": WATCHER_QUEUE.exists(),
        "auditor_input_exists": AUDITOR_FINDINGS.exists(),
        "bot_memory": {"loaded": HAS_BOT_MEMORY, **mem_stats},
    }


if __name__ == "__main__":
    mcp.run()
