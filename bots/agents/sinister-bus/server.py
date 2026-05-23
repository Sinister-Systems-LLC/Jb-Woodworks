"""
sinister-bus — orchestrator for the agent fleet.

Routes operator's "delegate to X" requests to the right agent.
Records every handoff at 01_MEMORY/_bus/<context_id>.json for replay.

Tier 1 (pure Python). Tools:
  bus.dispatch(target, args, context_id=None) -> {target_result, handoff_id}
  bus.replay(context_id)                       -> chronological list of all calls
  bus.list_recent(n=20)                        -> recent contexts
  bus.health()                                 -> fleet status
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[bus] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Shared runlog reader (sees manifests produced by operator-run scripts)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from _shared import runlog as _runlog  # type: ignore
    HAS_RUNLOG = True
except Exception:
    HAS_RUNLOG = False

try:
    from _shared import codec as _codec  # type: ignore
    HAS_CODEC = True
except Exception:
    HAS_CODEC = False

try:
    from _shared import crypto as _crypto  # type: ignore
    HAS_CRYPTO_MOD = True
except Exception:
    HAS_CRYPTO_MOD = False

try:
    from _shared import bot_memory as _botmem  # type: ignore
    HAS_BOTMEM = True
except Exception:
    HAS_BOTMEM = False

try:
    from _shared import inbox as _inbox  # type: ignore
    HAS_INBOX = True
except Exception:
    HAS_INBOX = False

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
BUS_DIR = HUB_ROOT / "01_MEMORY" / "_bus"
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"

BUS_DIR.mkdir(parents=True, exist_ok=True)
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

# Known MCP endpoints. Two classes:
#   - "bot" (under our control, under 12_LLM_ORCHESTRATION/agents/<name>/server.py)
#   - "base" (operator's pre-existing MCP servers; not our code, but bus knows
#     about them so dispatch() can route operator handoffs to ANY of the 19)
KNOWN_AGENTS = {
    # ===== Sinister Bots (our fleet) =====
    "sentinel":         {"class": "bot", "path": "agents/sentinel",         "kind": "alarms"},
    "translator":       {"class": "bot", "path": "agents/translator",       "kind": "mcp-catalog-search"},
    "librarian":        {"class": "bot", "path": "agents/librarian",        "kind": "rag-archive"},
    "watcher":          {"class": "bot", "path": "agents/watcher",          "kind": "drift-detection"},
    "auditor":          {"class": "bot", "path": "agents/auditor",          "kind": "secrets-dedup-freshness"},
    "triage":           {"class": "bot", "path": "agents/triage",           "kind": "file-classifier"},
    "scribe":           {"class": "bot", "path": "agents/scribe",           "kind": "daily-digest"},
    "curator":          {"class": "bot", "path": "agents/curator",          "kind": "code-library-scout"},
    "custodian":        {"class": "bot", "path": "agents/custodian",        "kind": "active-backup"},
    "stealth-browser":  {"class": "bot", "path": "agents/stealth-browser",  "kind": "browser-automation scrape stealth nodriver"},
    "researcher":       {"class": "bot", "path": "agents/researcher",       "kind": "web-research scrape lookup summarize"},
    "sinister-bus":     {"class": "bot", "path": "agents/sinister-bus",     "kind": "orchestrator handoff network-discovery"},
    # ===== Base MCP servers (operator's pre-existing) =====
    "eve":              {"class": "base", "kind": "memory-schedule-notify-search", "tool_count": 51},
    "sinister-panel":   {"class": "base", "kind": "panel-control", "tool_count": 13},
    "sinister-snap":    {"class": "base", "kind": "snap-automation", "tool_count": 12},
    "sinister-tiktok":  {"class": "base", "kind": "tiktok-automation", "tool_count": 12},
    "sinister-apk":     {"class": "base", "kind": "apk-signing", "tool_count": 12},
    "letstext":         {"class": "base", "kind": "messaging-ui", "tool_count": 27},
    "letstext-admin":   {"class": "base", "kind": "messaging-admin", "tool_count": 44},
}


def log_call(tool: str, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "sinister-bus",
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def persist_handoff(context_id: str, entry: dict[str, Any]) -> None:
    """Append-only entries per context."""
    path = BUS_DIR / f"{context_id}.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"context_id": context_id, "created": datetime.now(timezone.utc).isoformat(), "entries": []}
    data["entries"].append(entry)
    tmp = path.with_suffix(f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


mcp = FastMCP("sinister-bus")


@mcp.tool()
def dispatch(target: str, args: dict[str, Any] | None = None, context_id: str | None = None) -> dict[str, Any]:
    """Route a request to an agent.

    NOTE: This is a metadata-recording wrapper. Actual MCP-to-MCP calls require
    operator's Claude session to invoke the target agent directly. This bus
    PERSISTS the intent so it can be reconstructed even after a crash.

    args:
        target: 'sentinel', 'translator', 'librarian', etc. + tool e.g. 'sentinel.list_alarms'
        args: parameters to pass to the tool
        context_id: optional — group multiple handoffs in one context
    """
    log_call("dispatch", target=target, context_id=context_id)
    if context_id is None:
        context_id = f"ctx-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6]}"
    parts = target.split(".", 1)
    if len(parts) != 2:
        return {"ok": False, "error": "target must be 'agent.tool'"}
    agent, tool = parts
    if agent not in KNOWN_AGENTS:
        return {"ok": False, "error": f"unknown agent: {agent}. Known: {list(KNOWN_AGENTS)}"}
    meta = KNOWN_AGENTS[agent]
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "from": "operator",
        "to": agent,
        "to_class": meta.get("class"),
        "to_kind": meta.get("kind"),
        "tool": tool,
        "args": args or {},
        "status": "dispatched",
        "note": "Operator's Claude session should now call the target tool directly via MCP. This bus entry is the handoff record.",
    }
    persist_handoff(context_id, entry)
    return {
        "ok": True,
        "context_id": context_id,
        "target_agent": agent,
        "target_tool": tool,
        "args": args,
        "instructions": f"Operator: call {target}({args}) via MCP. Result will appear in operator's session.",
    }


@mcp.tool()
def replay(context_id: str) -> dict[str, Any]:
    """Get the full handoff chain for a context."""
    log_call("replay", context_id=context_id)
    path = BUS_DIR / f"{context_id}.json"
    if not path.exists():
        return {"ok": False, "error": f"context not found: {context_id}"}
    return json.loads(path.read_text(encoding="utf-8"))


@mcp.tool()
def list_recent(n: int = 20) -> list[dict[str, Any]]:
    """List recent handoff contexts."""
    log_call("list_recent")
    contexts = sorted(BUS_DIR.glob("ctx-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:n]
    out = []
    for c in contexts:
        try:
            data = json.loads(c.read_text(encoding="utf-8"))
            out.append({
                "context_id": data["context_id"],
                "created": data.get("created"),
                "entries_count": len(data.get("entries", [])),
                "last_entry": data["entries"][-1] if data.get("entries") else None,
            })
        except Exception:
            continue
    return out


@mcp.tool()
def record_response(context_id: str, agent: str, tool: str, result: Any) -> dict[str, Any]:
    """Record an agent's response back to the bus log (called by operator after MCP call)."""
    log_call("record_response", agent=agent, tool=tool)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "from": agent,
        "to": "operator",
        "tool": tool,
        "result": result,
        "status": "completed",
    }
    persist_handoff(context_id, entry)
    return {"ok": True}


@mcp.tool()
def list_network() -> dict[str, Any]:
    """Return the full MCP network: 12 Sinister Bots + 7 base servers + their kinds + tool counts."""
    log_call("list_network")
    bots = {k: v for k, v in KNOWN_AGENTS.items() if v.get("class") == "bot"}
    base = {k: v for k, v in KNOWN_AGENTS.items() if v.get("class") == "base"}
    return {
        "ok": True,
        "summary": {
            "bots": len(bots),
            "base_mcps": len(base),
            "total": len(KNOWN_AGENTS),
            "total_base_tools": sum(v.get("tool_count", 0) for v in base.values()),
        },
        "bots": bots,
        "base_mcps": base,
    }


@mcp.tool()
def find(query: str) -> list[dict[str, Any]]:
    """Substring-match against agent names + kinds. Returns matching network entries."""
    log_call("find", query=query[:100])
    q = query.lower()
    matches = []
    for name, meta in KNOWN_AGENTS.items():
        hay = (name + " " + (meta.get("kind") or "")).lower()
        if q in hay:
            matches.append({"name": name, **meta})
    return matches


@mcp.tool()
def runlog_list(limit: int = 20) -> list[dict[str, Any]]:
    """List recent operator-run script manifests (most recent first). Pure read."""
    log_call("runlog_list", limit=limit)
    if not HAS_RUNLOG:
        return []
    return _runlog.list_recent(limit=limit)


@mcp.tool()
def runlog_latest(script_name: str) -> dict[str, Any]:
    """Read the most recent manifest for a script name (e.g. 'activate-everything')."""
    log_call("runlog_latest", script=script_name)
    if not HAS_RUNLOG:
        return {"ok": False, "error": "runlog module not loadable"}
    return _runlog.read_latest(script_name)


@mcp.tool()
def runlog_summary(id_or_path: str) -> dict[str, Any]:
    """One-paragraph plain-text rollup of a manifest (no LLM cost)."""
    log_call("runlog_summary", id=id_or_path[:200])
    if not HAS_RUNLOG:
        return {"ok": False, "error": "runlog module not loadable"}
    r = _runlog.read(id_or_path)
    if not r.get("ok"):
        return r
    return {"ok": True, "summary": _runlog.summary_text(r["manifest"]), "manifest": r["manifest"]}


@mcp.tool()
def pending_actions() -> dict[str, Any]:
    """Aggregated operator next-actions across all unconsumed script runs.

    Reads runtime-state/PENDING-NEXT-ACTIONS.md (curated by every Save-Runlog call).
    Call consume_pending() after the operator confirms they did them.
    """
    log_call("pending_actions")
    if not HAS_RUNLOG:
        return {"ok": False, "error": "runlog module not loadable"}
    return _runlog.pending_actions()


@mcp.tool()
def consume_pending(mark_checked: bool = True, archive: bool = True) -> dict[str, Any]:
    """Mark every unchecked next-action in PENDING-NEXT-ACTIONS.md as done.

    With archive=True (default), fully-consumed blocks move to
    runtime-state/_archive/PENDING-<date>.md so the live file stays clean.
    """
    log_call("consume_pending", mark_checked=mark_checked, archive=archive)
    if not HAS_RUNLOG:
        return {"ok": False, "error": "runlog module not loadable"}
    return _runlog.consume_pending(mark_checked=mark_checked, archive=archive)


@mcp.tool()
def encode(text: str) -> dict[str, Any]:
    """Compact a string via the Sinister memory codec. Lossless; reversible via decode().
    NOT classifier evasion; the dictionary is open + the result reads cleanly when decoded.
    """
    log_call("encode", chars=len(text or ""))
    if not HAS_CODEC:
        return {"ok": False, "error": "codec module not loadable"}
    enc = _codec.encode(text)
    s = _codec.stats(text)
    return {"ok": True, "encoded": enc, "stats": s}


@mcp.tool()
def decode(text: str) -> dict[str, Any]:
    """Expand a codec-encoded string back to canonical phrase form."""
    log_call("decode", chars=len(text or ""))
    if not HAS_CODEC:
        return {"ok": False, "error": "codec module not loadable"}
    return {"ok": True, "decoded": _codec.decode(text)}


@mcp.tool()
def codec_status() -> dict[str, Any]:
    """Codec dictionary stats + sample roundtrip."""
    log_call("codec_status")
    if not HAS_CODEC:
        return {"ok": False, "error": "codec module not loadable"}
    d = _codec.get_dictionary()
    sample = "operator action by Yurikey51 root cert expires; green path: pure-API"
    rt = _codec.roundtrip(sample)
    return {"ok": True, "phrase_count": len(d), "sample": sample, "roundtrip": rt}


@mcp.tool()
def vault_lock(path: str) -> dict[str, Any]:
    """At-rest encrypt a single file. Requires passphrase via env or key file.
    Writes `<path>.locked` + removes the plaintext. See vault_status() first.
    """
    log_call("vault_lock", path=path[:200])
    if not HAS_CRYPTO_MOD:
        return {"ok": False, "error": "crypto module not loadable (pip install cryptography)"}
    return _crypto.lock_path(path)


@mcp.tool()
def vault_unlock(path: str, keep_locked: bool = False) -> dict[str, Any]:
    """Decrypt a `.locked` file back to its plaintext path."""
    log_call("vault_unlock", path=path[:200], keep=keep_locked)
    if not HAS_CRYPTO_MOD:
        return {"ok": False, "error": "crypto module not loadable"}
    return _crypto.unlock_path(path, keep_locked=keep_locked)


@mcp.tool()
def vault_status() -> dict[str, Any]:
    """Report cryptography lib + passphrase availability + salt path."""
    log_call("vault_status")
    if not HAS_CRYPTO_MOD:
        return {"ok": False, "error": "crypto module not loadable"}
    return _crypto.status()


# ===== Bot-callable script runner (Phase 8s) =====
# Whitelist of safe scripts. Each entry: {name -> (kind, path, default_args)}.
# kind = "ps1" or "python". Destructive scripts are NOT in this list.
_SCRIPT_WHITELIST: dict[str, dict[str, Any]] = {
    "check-hetzner-state": {
        "kind": "ps1",
        "path": HUB_ROOT / "08_AUTOMATIONS" / "check-hetzner-state.ps1",
        "args": ["-Quiet"],
    },
    "verify-backups": {
        "kind": "ps1",
        "path": HUB_ROOT / "08_AUTOMATIONS" / "verify-backups.ps1",
        "args": ["-Quiet"],
    },
    "memory-garden": {
        "kind": "python",
        "path": HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "_shared" / "garden_cli.py",
        "args": [],
    },
    "aggregate-gotchas": {
        "kind": "ps1",
        "path": HUB_ROOT / "08_AUTOMATIONS" / "aggregate-gotchas.ps1",
        "args": [],
    },
    "prepare-for-migration-dryrun": {
        "kind": "ps1",
        "path": HUB_ROOT / "08_AUTOMATIONS" / "prepare-for-migration.ps1",
        "args": ["-DryRun", "-Quiet"],
    },
}

_SCRIPT_RUNNER_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "script-runner-log.jsonl"


@mcp.tool()
def list_scripts() -> dict[str, Any]:
    """Return the whitelist of scripts the operator (or a bot) can invoke via run_script."""
    log_call("list_scripts")
    return {
        "ok": True,
        "scripts": [
            {"name": n, "kind": v["kind"], "path": str(v["path"]),
             "default_args": v["args"], "exists": v["path"].exists()}
            for n, v in _SCRIPT_WHITELIST.items()
        ],
    }


@mcp.tool()
def run_script(name: str, timeout_sec: int = 120, extra_args: list[str] | None = None) -> dict[str, Any]:
    """Execute a whitelisted operator-script from inside Claude. Returns exit + stdout tail + manifest path.

    Use this so the operator doesn't have to leave the chat to double-click a bat.
    Whitelisted scripts (call list_scripts to see):
      check-hetzner-state, verify-backups, memory-garden, aggregate-gotchas, prepare-for-migration-dryrun

    Destructive scripts (Deploy-Hetzner, install-task, migrate-projects, secret-scrub) are NOT whitelisted -
    the operator runs those manually.

    Returns {ok, exit_code, stdout_tail, stderr_tail, manifest_path}.
    The fresh manifest is also readable via runlog_latest(name).
    """
    import subprocess
    log_call("run_script", script=name, timeout_sec=timeout_sec)
    if name not in _SCRIPT_WHITELIST:
        return {"ok": False, "error": f"not in whitelist: {name}. Known: {list(_SCRIPT_WHITELIST)}"}
    spec = _SCRIPT_WHITELIST[name]
    if not spec["path"].exists():
        return {"ok": False, "error": f"script not found on disk: {spec['path']}"}
    args = list(spec["args"]) + list(extra_args or [])
    if spec["kind"] == "ps1":
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(spec["path"])] + args
    elif spec["kind"] == "python":
        cmd = ["python", str(spec["path"])] + args
    else:
        return {"ok": False, "error": f"unsupported kind: {spec['kind']}"}

    started = datetime.now(timezone.utc).isoformat()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        exit_code = p.returncode
        stdout, stderr = p.stdout or "", p.stderr or ""
        timed_out = False
    except subprocess.TimeoutExpired as e:
        exit_code = -1
        stdout = (e.stdout or b"").decode("utf-8", errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = f"TIMEOUT after {timeout_sec}s"
        timed_out = True
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Audit log
    _SCRIPT_RUNNER_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _SCRIPT_RUNNER_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": started, "script": name, "exit_code": exit_code,
            "timed_out": timed_out, "stdout_chars": len(stdout), "stderr_chars": len(stderr),
        }) + "\n")

    # Try to surface the latest matching manifest (script may have written one via _runlog)
    manifest_path = None
    if HAS_RUNLOG:
        try:
            r = _runlog.read_latest(name)
            if r.get("ok"):
                manifest_path = r.get("manifest", {}).get("script") and f"runtime-state/script-runs/{r.get('id')}.json"
        except Exception:
            pass

    return {
        "ok": (exit_code == 0),
        "script": name,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-500:],
        "manifest_path": manifest_path,
        "hint": f"call runlog_latest({name!r}) for the structured manifest",
    }


# ===== Agent-to-agent messaging (Phase 8w) =====

@mcp.tool()
def heartbeat(my_agent: str) -> dict[str, Any]:
    """Mark THIS session as online. Each Claude session calls this once per turn so
    other sessions know it's reachable. Cheap (touches one file)."""
    log_call("heartbeat", agent=my_agent)
    if not HAS_INBOX:
        return {"ok": False, "error": "inbox module not loadable"}
    return _inbox.heartbeat(my_agent)


@mcp.tool()
def who_is_online() -> dict[str, Any]:
    """List every known agent + whether they have a fresh heartbeat (< 5 min old)."""
    log_call("who_is_online")
    if not HAS_INBOX:
        return {"ok": False, "error": "inbox module not loadable"}
    return {"ok": True, "agents": _inbox.who_is_online()}


@mcp.tool()
def inbox_send(to_agent: str, message: str, from_agent: str = "unknown",
               urgent: bool = False, tags: list[str] | None = None) -> dict[str, Any]:
    """Send a message to another agent's inbox. Returns immediately; recipient polls.
    Use delegate_to for ask-and-wait pattern with offline fallback."""
    log_call("inbox_send", to=to_agent, from_a=from_agent)
    if not HAS_INBOX:
        return {"ok": False, "error": "inbox module not loadable"}
    return _inbox.inbox_send(to_agent, message, from_agent=from_agent, urgent=urgent, tags=tags or [])


@mcp.tool()
def inbox_poll(my_agent: str, mark_consumed: bool = True, limit: int = 50) -> dict[str, Any]:
    """Read my inbox. mark_consumed=True atomically clears the queue after read."""
    log_call("inbox_poll", agent=my_agent, mark_consumed=mark_consumed)
    if not HAS_INBOX:
        return {"ok": False, "error": "inbox module not loadable"}
    return _inbox.inbox_poll(my_agent, mark_consumed=mark_consumed, limit=limit)


@mcp.tool()
def inbox_reply(msg_id: str, my_agent: str, response: str) -> dict[str, Any]:
    """Reply to a delegate_to request. The original caller polls our sent.jsonl for reply_to == msg_id."""
    log_call("inbox_reply", agent=my_agent, msg_id=msg_id[:30])
    if not HAS_INBOX:
        return {"ok": False, "error": "inbox module not loadable"}
    return _inbox.reply_to(msg_id, my_agent, response)


@mcp.tool()
def delegate_to(agent_name: str, prompt: str, timeout_sec: int = 60,
                allow_ephemeral: bool = True, context_hint: str = "") -> dict[str, Any]:
    """Ask another agent for an answer. If agent is online, sends to inbox + waits for reply.
    If offline AND allow_ephemeral=True, spawns ephemeral `claude --print` subprocess that
    answers + exits. Operator's persistent sessions are NEVER auto-closed — we only spawn
    NEW subprocesses. Audit log at runtime-state/delegate-log.jsonl."""
    log_call("delegate_to", agent=agent_name, ephemeral=allow_ephemeral, timeout=timeout_sec)
    if not HAS_INBOX:
        return {"ok": False, "error": "inbox module not loadable"}
    return _inbox.delegate_to(agent_name, prompt, timeout_sec=timeout_sec,
                              allow_ephemeral=allow_ephemeral, context_hint=context_hint)


@mcp.tool()
def inbox_stats() -> dict[str, Any]:
    """Summary across all agent inboxes (count online, queued message totals)."""
    log_call("inbox_stats")
    if not HAS_INBOX:
        return {"ok": False, "error": "inbox module not loadable"}
    return _inbox.stats()


@mcp.tool()
def memory_garden() -> dict[str, Any]:
    """Per-bot aliveness snapshot. For Scribe daily-digest + operator dashboard.

    Returns each bot's fact_count, lifetime_calls, last_called, last_absorbed,
    smart_retrieval_active. Lets operator see who's growing + who's idle.
    """
    log_call("memory_garden")
    if not HAS_BOTMEM:
        return {"ok": False, "error": "bot_memory module not loadable"}
    bot_names = [k for k, v in KNOWN_AGENTS.items() if v.get("class") == "bot"]
    garden = []
    for name in bot_names:
        try:
            stats = _botmem.memory_stats(name)
            garden.append({
                "bot": name,
                "facts": stats.get("fact_count", 0),
                "embedded": stats.get("embedded_fact_count", 0),
                "lifetime_calls": stats.get("lifetime_calls", 0),
                "last_called": stats.get("last_called"),
                "last_absorbed": stats.get("last_absorbed"),
                "smart_retrieval": stats.get("smart_retrieval_active", False),
            })
        except Exception as e:
            garden.append({"bot": name, "error": str(e)[:200]})
    garden.sort(key=lambda r: -(r.get("facts") or 0))
    return {
        "ok": True,
        "garden": garden,
        "summary": {
            "total_facts": sum(r.get("facts", 0) or 0 for r in garden),
            "total_calls": sum(r.get("lifetime_calls", 0) or 0 for r in garden),
            "bots_with_facts": sum(1 for r in garden if r.get("facts", 0)),
            "bots_with_smart_retrieval": sum(1 for r in garden if r.get("smart_retrieval")),
        },
    }


@mcp.tool()
def health() -> dict[str, Any]:
    log_call("health")
    bots = [k for k, v in KNOWN_AGENTS.items() if v.get("class") == "bot"]
    base = [k for k, v in KNOWN_AGENTS.items() if v.get("class") == "base"]
    runlog_stats = _runlog.stats() if HAS_RUNLOG else {"ok": False}
    pending = _runlog.pending_actions() if HAS_RUNLOG else {"unchecked_bullets": 0}
    codec_info = {"loaded": HAS_CODEC, "phrase_count": len(_codec.get_dictionary())} if HAS_CODEC else {"loaded": False}
    vault_info = _crypto.status() if HAS_CRYPTO_MOD else {"has_cryptography": False}
    return {
        "ok": True,
        "agent": "sinister-bus",
        "known_bots": bots,
        "known_base_mcps": base,
        "total_endpoints": len(KNOWN_AGENTS),
        "bus_log_dir": str(BUS_DIR.relative_to(HUB_ROOT)),
        "contexts_total": len(list(BUS_DIR.glob("ctx-*.json"))),
        "runlog": {
            "loaded": HAS_RUNLOG,
            "manifest_count": runlog_stats.get("manifest_count", 0),
            "pending_unchecked": pending.get("unchecked_bullets", 0),
        },
        "codec": codec_info,
        "vault": {
            "available": vault_info.get("has_cryptography", False),
            "passphrase_set": vault_info.get("env_passphrase_set", False) or vault_info.get("key_file_exists", False),
        },
    }


if __name__ == "__main__":
    mcp.run()
