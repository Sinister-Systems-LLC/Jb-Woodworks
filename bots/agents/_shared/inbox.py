"""
inbox - file-based message bus + presence + ephemeral-spawn fallback for
operator's parallel Claude sessions ("agents").

Mental model:
  - An "agent" here = ONE Claude session (NOT an MCP bot). The operator runs
    multiple sessions in parallel, one per project. Naming: 'master',
    'snap-signer', 'sinister-tiktok-emu', 'sinister-panel', 'sinister-bumble-emu',
    'kernel-su-setup', etc.
  - Each session "checks in" via heartbeat() each turn → its online flag is fresh.
  - Sessions message each other via inbox files. Recipient polls.
  - If recipient is offline AND caller allows ephemeral, an ephemeral
    `claude --print` subprocess is spawned, given context + the prompt, and its
    output captured. Ephemeral sessions exit when done. Operator-started
    sessions persist until the operator closes them.

File layout:
  01_MEMORY/_inbox/<agent>/
    online.flag           mtime = last heartbeat. Fresh if < 5 min old.
    messages.jsonl        append-only inbound queue
    sent.jsonl            audit of sent messages
    consumed.jsonl        audit of poll() calls

Concurrency:
  - Multiple sessions can write to the same target inbox; use append + atomic
    rename for the online flag.
  - poll() reads + truncates atomically.

Cost:
  - File-based messaging: $0 (just disk I/O).
  - Ephemeral spawn via `claude --print`: each invocation = 1 Claude turn at
    whatever model is configured for the operator's CLI. Logged to audit.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
INBOX_ROOT = HUB_ROOT / "01_MEMORY" / "_inbox"
INBOX_ROOT.mkdir(parents=True, exist_ok=True)
PRESENCE_TTL_SECONDS = 5 * 60  # 5 min - fresh heartbeat = online

DELEGATE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "delegate-log.jsonl"
DELEGATE_LOG.parent.mkdir(parents=True, exist_ok=True)


def _agent_dir(name: str) -> Path:
    safe = "".join(c for c in name if c.isalnum() or c in "-_")
    d = INBOX_ROOT / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


def _atomic_write_text(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def heartbeat(agent_name: str) -> dict[str, Any]:
    """Mark this agent as online. Call each turn (cheap; touches one file)."""
    d = _agent_dir(agent_name)
    flag = d / "online.flag"
    now = datetime.now(timezone.utc).isoformat()
    _atomic_write_text(flag, now)
    return {"ok": True, "agent": agent_name, "ts": now, "path": str(flag)}


def is_online(agent_name: str) -> bool:
    flag = _agent_dir(agent_name) / "online.flag"
    if not flag.exists():
        return False
    try:
        mtime = flag.stat().st_mtime
        age = time.time() - mtime
        return age < PRESENCE_TTL_SECONDS
    except Exception:
        return False


def who_is_online() -> list[dict[str, Any]]:
    """List every agent dir + its online state + last-seen timestamp."""
    out = []
    if not INBOX_ROOT.exists():
        return out
    now = time.time()
    for d in sorted(INBOX_ROOT.iterdir()):
        if not d.is_dir():
            continue
        flag = d / "online.flag"
        if flag.exists():
            try:
                age = now - flag.stat().st_mtime
                out.append({
                    "agent": d.name,
                    "online": age < PRESENCE_TTL_SECONDS,
                    "last_seen_age_seconds": int(age),
                    "last_seen": datetime.fromtimestamp(flag.stat().st_mtime, timezone.utc).isoformat(),
                })
            except Exception:
                continue
        else:
            out.append({"agent": d.name, "online": False, "last_seen_age_seconds": None, "last_seen": None})
    return out


def inbox_send(to_agent: str, message: str, from_agent: str = "unknown",
               urgent: bool = False, tags: list[str] | None = None) -> dict[str, Any]:
    """Enqueue a message for recipient. Returns immediately; recipient polls.

    If recipient is OFFLINE, message still lands - they'll see it when they come back.
    Use delegate_to() for blocking ask-and-wait pattern with ephemeral fallback.
    """
    if not isinstance(message, str) or not message.strip():
        return {"ok": False, "error": "message must be non-empty string"}
    d = _agent_dir(to_agent)
    msg_path = d / "messages.jsonl"
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "from": from_agent,
        "to": to_agent,
        "urgent": urgent,
        "tags": tags or [],
        "message": message,
        "msg_id": f"m-{int(time.time()*1000)}-{os.urandom(2).hex()}",
    }
    with msg_path.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(entry) + "\n")

    # Audit: from-agent's sent log
    sent_path = _agent_dir(from_agent) / "sent.jsonl"
    with sent_path.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(entry) + "\n")

    return {"ok": True, "msg_id": entry["msg_id"], "delivered_to": to_agent, "recipient_online": is_online(to_agent)}


def inbox_poll(my_agent: str, mark_consumed: bool = True, limit: int = 50) -> dict[str, Any]:
    """Read my inbox. If mark_consumed=True, atomically clears the queue after read."""
    d = _agent_dir(my_agent)
    msg_path = d / "messages.jsonl"
    if not msg_path.exists():
        return {"ok": True, "messages": [], "consumed": 0}
    try:
        text = msg_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": str(e)}
    messages = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            messages.append(json.loads(line))
        except Exception:
            continue
    if mark_consumed and messages:
        # Atomic truncate
        _atomic_write_text(msg_path, "")
        consumed_path = d / "consumed.jsonl"
        with consumed_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                                "count": len(messages),
                                "msg_ids": [m["msg_id"] for m in messages]}) + "\n")
    return {"ok": True, "messages": messages[:limit], "consumed": len(messages) if mark_consumed else 0}


def _log_delegate(entry: dict[str, Any]) -> None:
    with DELEGATE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def delegate_to(agent_name: str, prompt: str, timeout_sec: int = 60,
                allow_ephemeral: bool = True, context_hint: str = "") -> dict[str, Any]:
    """Ask another agent for an answer. Three behaviors:

      1. If recipient is ONLINE: send via inbox + poll for response in `outbox`. Time-bounded.
      2. If recipient OFFLINE and allow_ephemeral=False: return {ok:false, error:"offline"}.
      3. If recipient OFFLINE and allow_ephemeral=True: spawn `claude --print <prompt>`
         as a one-shot subprocess. Captures stdout. Ephemeral process exits after answering.
         The OPERATOR's persistent sessions are NEVER auto-closed by this - we only
         spawn NEW subprocesses.

    Audit log at runtime-state/delegate-log.jsonl.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return {"ok": False, "error": "prompt must be non-empty"}
    ts = datetime.now(timezone.utc).isoformat()

    if is_online(agent_name):
        # Path 1: inbox + wait-for-response pattern
        msg = inbox_send(agent_name, prompt, from_agent="delegate-to", tags=["delegate", "ask"])
        # Poll the recipient's "outbox" (their own sent.jsonl) for a reply tied to this msg_id
        # Simplistic: wait up to timeout_sec for a sent message with reply_to == our msg_id
        deadline = time.time() + timeout_sec
        msg_id = msg.get("msg_id")
        their_sent = _agent_dir(agent_name) / "sent.jsonl"
        while time.time() < deadline:
            if their_sent.exists():
                for line in their_sent.read_text(encoding="utf-8").splitlines()[-200:]:
                    try:
                        e = json.loads(line)
                        if e.get("reply_to") == msg_id:
                            _log_delegate({"ts": ts, "to": agent_name, "mode": "inbox", "ok": True, "msg_id": msg_id})
                            return {"ok": True, "mode": "inbox", "response": e.get("message"), "answered_by": agent_name}
                    except Exception:
                        continue
            time.sleep(1)
        _log_delegate({"ts": ts, "to": agent_name, "mode": "inbox", "ok": False, "error": "timeout"})
        return {"ok": False, "mode": "inbox", "error": f"recipient online but didn't reply within {timeout_sec}s",
                "msg_id": msg_id, "hint": "recipient may have seen but not acked"}

    if not allow_ephemeral:
        _log_delegate({"ts": ts, "to": agent_name, "mode": "denied", "ok": False, "error": "offline"})
        return {"ok": False, "mode": "offline", "error": f"{agent_name} is offline and allow_ephemeral=False"}

    # Path 3: ephemeral claude subprocess
    claude_exe = shutil.which("claude")
    if not claude_exe:
        _log_delegate({"ts": ts, "to": agent_name, "mode": "ephemeral", "ok": False, "error": "claude CLI not on PATH"})
        return {"ok": False, "mode": "ephemeral", "error": "claude CLI not on PATH"}

    # Compose contextual prompt: tell ephemeral session who it is + where context lives
    full_prompt = (
        f"You are an EPHEMERAL session impersonating the '{agent_name}' agent. "
        f"Your task is one-shot: answer the prompt below + exit. Don't try to start long-running work.\n\n"
        f"Hub context: D:\\Sinister\\Sinister Skills\\01_MEMORY\\{agent_name}\\ has that project's memory.\n"
        f"If you need broader hub state: D:\\Sinister\\Sinister Skills\\.claude\\memory\\NEXT-SESSION-READ-FIRST.md\n\n"
        + (f"Additional context: {context_hint}\n\n" if context_hint else "")
        + f"PROMPT:\n{prompt}"
    )

    try:
        p = subprocess.run(
            [claude_exe, "--print", full_prompt],
            capture_output=True, text=True, timeout=timeout_sec,
        )
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        ok = (p.returncode == 0 and bool(out))
        _log_delegate({"ts": ts, "to": agent_name, "mode": "ephemeral", "ok": ok,
                       "exit": p.returncode, "out_chars": len(out)})
        return {
            "ok": ok,
            "mode": "ephemeral",
            "response": out,
            "answered_by": f"ephemeral-{agent_name}",
            "stderr_tail": err[-500:] if err else None,
            "exit_code": p.returncode,
        }
    except subprocess.TimeoutExpired:
        _log_delegate({"ts": ts, "to": agent_name, "mode": "ephemeral", "ok": False, "error": "timeout"})
        return {"ok": False, "mode": "ephemeral", "error": f"ephemeral claude timed out after {timeout_sec}s"}
    except Exception as e:
        _log_delegate({"ts": ts, "to": agent_name, "mode": "ephemeral", "ok": False, "error": str(e)})
        return {"ok": False, "mode": "ephemeral", "error": str(e)}


def reply_to(msg_id: str, my_agent: str, response: str) -> dict[str, Any]:
    """Reply to a delegate_to request. The original caller polls our sent.jsonl looking for reply_to == msg_id."""
    if not msg_id or not response:
        return {"ok": False, "error": "msg_id and response required"}
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "from": my_agent,
        "reply_to": msg_id,
        "message": response,
    }
    sent_path = _agent_dir(my_agent) / "sent.jsonl"
    with sent_path.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(entry) + "\n")
    return {"ok": True, "replied_to": msg_id}


def stats() -> dict[str, Any]:
    """Summary across all agent inboxes."""
    if not INBOX_ROOT.exists():
        return {"ok": True, "agents": 0, "online": 0}
    agents = []
    for d in INBOX_ROOT.iterdir():
        if not d.is_dir():
            continue
        msg_path = d / "messages.jsonl"
        queue = 0
        if msg_path.exists():
            queue = sum(1 for line in msg_path.read_text(encoding="utf-8").splitlines() if line.strip())
        agents.append({"name": d.name, "online": is_online(d.name), "queue_size": queue})
    return {
        "ok": True,
        "agents": len(agents),
        "online_count": sum(1 for a in agents if a["online"]),
        "queued_messages_total": sum(a["queue_size"] for a in agents),
        "by_agent": agents,
    }
