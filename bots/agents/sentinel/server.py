"""
Sentinel agent — date-based alarms (Yurikey expiry, deadlines, recurring reminders).

Pure Python — no LLM. Tier 1 in the escalation ladder. Zero token cost.

Exposes MCP tools:
  sentinel.list_alarms()              -> [{name, due, days_until, severity, message}]
  sentinel.add(name, due_iso, ...)    -> {ok: true, id}
  sentinel.remove(name)               -> {ok: true}
  sentinel.check_urgent()             -> [{name, days_until}] for items <= 7 days
  sentinel.snooze(name, until_iso)    -> {ok: true}
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
    print("[sentinel] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# ===== Paths =====
HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "sentinel"
ALARMS_PATH = AGENT_DIR / "alarms.json"
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

# ===== Default alarms (loaded on first run) =====
DEFAULT_ALARMS = [
    {
        "id": "yurikey51-root-expiry",
        "name": "Yurikey51 root cert expires",
        "due": "2026-05-24T00:00:00Z",
        "severity": "critical",
        "message": "Source Yurikey52 from yuriservice (TG t.me/yuriservice) by 2026-05-23. Without it, phone-stack + pure-API attestation breaks server-side on May 24.",
        "tags": ["yurikey", "rka", "phone-stack", "operator-action"],
    },
    {
        "id": "yurikey-warn-7day",
        "name": "Yurikey rotation reminder (1 week before)",
        "due": "2026-05-17T00:00:00Z",  # passed; will surface as "stale" not urgent
        "severity": "warning",
        "message": "1 week until Yurikey51 root cert expiry. Operator should be sourcing replacement.",
        "tags": ["yurikey", "reminder"],
    },
    {
        "id": "phone-pi-reauth",
        "name": "PI 0/3 on phones P1 + P2 — interactive re-auth",
        "due": "2026-05-19T00:00:00Z",  # ASAP — within 24h
        "severity": "high",
        "message": "Open Settings -> Passwords & accounts -> Google -> Account sync -> 'Sync now' -> re-enter password. Both phones (2A061JEGR09301 + 26031JEGR17598).",
        "tags": ["phone", "pi", "operator-action"],
    },
    {
        "id": "hetzner-state-check-stale",
        "name": "Hetzner state check: run weekly",
        "due": "2026-05-25T00:00:00Z",
        "severity": "warning",
        "message": "Run C:\\Users\\Zonia\\Desktop\\Check-Hetzner-State.bat weekly to confirm panel + RKA daemon are up + in sync. Auto-closes when everything is healthy; otherwise shows what's drifted. Scribe's daily digest also surfaces the latest result.",
        "tags": ["hetzner", "operations", "recurring"],
    },
    # NOTE: pending-deploy alarms are NOT hardcoded. The check-hetzner-state script
    # detects pending commits at run-time and writes them to PENDING-NEXT-ACTIONS.md
    # which scribe + sinister-bus surface to the operator. Avoids stale hand-coded alarms.
    {
        "id": "sinister-llc-migration-ready",
        "name": "Sinister LLC monorepo: ready when operator is",
        "due": "2026-05-22T00:00:00Z",
        "severity": "normal",
        "message": "D:\\Sinister LLC\\ skeleton in place. Before first git push: (1) copy stubs from 01_MEMORY/<proj>/_to-copy-to-source/ into source projects, (2) run D:\\Sinister LLC\\automations\\migrate-projects.ps1, (3) run secret-scrub.ps1 (MUST PASS; TT capsolver.key flagged), (4) pick LICENSE.",
        "tags": ["sinister-llc", "migration", "operator-decision"],
    },
    {
        "id": "memory-vault-passphrase-set",
        "name": "Memory vault passphrase: set when you want at-rest encryption",
        "due": "2026-05-25T00:00:00Z",
        "severity": "normal",
        "message": "At-rest vault available (Fernet AES). Set SINISTER_VAULT_PASSPHRASE env (User scope) OR drop the passphrase into ~/.sinister/vault-key. Then bus.vault_lock / bus.vault_unlock work. See 12_LLM_ORCHESTRATION/MEMORY-CODEC-AND-CRYPTO.md.",
        "tags": ["vault", "privacy", "operator-decision"],
    },
]


def atomic_write(path: Path, content: str) -> None:
    """Crash-safe write — temp file + rename."""
    tmp = path.with_suffix(path.suffix + f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def load_alarms() -> list[dict[str, Any]]:
    if not ALARMS_PATH.exists():
        AGENT_DIR.mkdir(parents=True, exist_ok=True)
        atomic_write(ALARMS_PATH, json.dumps(DEFAULT_ALARMS, indent=2))
        return list(DEFAULT_ALARMS)
    try:
        return json.loads(ALARMS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # corrupted — restore defaults but back up the bad file
        backup = ALARMS_PATH.with_suffix(f".corrupt.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json")
        ALARMS_PATH.rename(backup)
        atomic_write(ALARMS_PATH, json.dumps(DEFAULT_ALARMS, indent=2))
        return list(DEFAULT_ALARMS)


def save_alarms(alarms: list[dict[str, Any]]) -> None:
    atomic_write(ALARMS_PATH, json.dumps(alarms, indent=2))


def log_call(tool: str, **extra: Any) -> None:
    """Append-only usage log."""
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "sentinel",
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")
        f.flush()


def days_until(due_iso: str) -> int:
    due = datetime.fromisoformat(due_iso.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (due - now).days


# ===== MCP server =====
mcp = FastMCP("sentinel")


@mcp.tool()
def list_alarms(include_past: bool = False) -> list[dict[str, Any]]:
    """List all sentinel alarms with computed days_until. Skips snoozed."""
    log_call("list_alarms", include_past=include_past)
    alarms = load_alarms()
    out = []
    for a in alarms:
        snooze = a.get("snooze_until")
        if snooze:
            try:
                if datetime.fromisoformat(snooze.replace("Z", "+00:00")) > datetime.now(timezone.utc):
                    continue
            except ValueError:
                pass
        du = days_until(a["due"])
        if du < 0 and not include_past:
            continue
        out.append({
            **a,
            "days_until": du,
            "is_urgent": du <= 7 and du >= 0,
            "is_critical": du <= 1 and du >= 0 and a.get("severity") == "critical",
        })
    out.sort(key=lambda x: x["days_until"])
    return out


@mcp.tool()
def check_urgent(window_days: int = 7) -> list[dict[str, Any]]:
    """Return alarms due within window_days days."""
    log_call("check_urgent", window=window_days)
    all_alarms = list_alarms(include_past=False)
    return [a for a in all_alarms if 0 <= a["days_until"] <= window_days]


@mcp.tool()
def add(name: str, due_iso: str, severity: str = "normal", message: str = "", tags: list[str] | None = None) -> dict[str, Any]:
    """Add a new alarm. severity in {critical, high, warning, normal}."""
    if severity not in ("critical", "high", "warning", "normal"):
        return {"ok": False, "error": f"invalid severity: {severity}"}
    try:
        datetime.fromisoformat(due_iso.replace("Z", "+00:00"))
    except ValueError as e:
        return {"ok": False, "error": f"invalid due_iso: {e}"}
    alarms = load_alarms()
    alarm_id = f"{name.lower().replace(' ', '-')}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    new_alarm = {
        "id": alarm_id,
        "name": name,
        "due": due_iso,
        "severity": severity,
        "message": message,
        "tags": tags or [],
        "created": datetime.now(timezone.utc).isoformat(),
    }
    alarms.append(new_alarm)
    save_alarms(alarms)
    log_call("add", id=alarm_id)
    return {"ok": True, "id": alarm_id}


@mcp.tool()
def remove(alarm_id: str) -> dict[str, Any]:
    """Remove an alarm by id."""
    alarms = load_alarms()
    before = len(alarms)
    alarms = [a for a in alarms if a.get("id") != alarm_id]
    if len(alarms) == before:
        return {"ok": False, "error": f"alarm_id not found: {alarm_id}"}
    save_alarms(alarms)
    log_call("remove", id=alarm_id)
    return {"ok": True}


@mcp.tool()
def snooze(alarm_id: str, until_iso: str) -> dict[str, Any]:
    """Snooze an alarm until until_iso. Won't appear in list_alarms while snoozed."""
    try:
        datetime.fromisoformat(until_iso.replace("Z", "+00:00"))
    except ValueError as e:
        return {"ok": False, "error": f"invalid until_iso: {e}"}
    alarms = load_alarms()
    for a in alarms:
        if a.get("id") == alarm_id:
            a["snooze_until"] = until_iso
            save_alarms(alarms)
            log_call("snooze", id=alarm_id, until=until_iso)
            return {"ok": True}
    return {"ok": False, "error": f"alarm_id not found: {alarm_id}"}


@mcp.tool()
def add_from_runlog(manifest_id_or_path: str, severity: str = "warning") -> dict[str, Any]:
    """Auto-create an alarm from a runlog manifest's next_actions list.

    Reads `runtime-state/script-runs/<id>.json`. For each next_actions entry,
    creates a sentinel alarm due in 3 days. So when operator runs Check-Hetzner-State
    and it produces a "deploy panel" next-action, sentinel tracks it as an alarm
    until the operator does it (or snoozes / removes).
    """
    p = Path(manifest_id_or_path)
    if not p.is_absolute():
        p = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "script-runs" / f"{manifest_id_or_path}.json"
    if not p.exists():
        return {"ok": False, "error": f"manifest not found: {p}"}
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"manifest unreadable: {e}"}
    next_actions = m.get("next_actions", []) or []
    if not next_actions:
        return {"ok": True, "added": 0, "note": "no next_actions in manifest"}
    if severity not in ("critical", "high", "warning", "normal"):
        severity = "warning"
    alarms = load_alarms()
    added = []
    due_iso = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    script_name = m.get("script", "runlog")
    for i, action in enumerate(next_actions):
        alarm_id = f"runlog-{script_name}-{i}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        if any(a.get("id") == alarm_id for a in alarms):
            continue
        alarms.append({
            "id": alarm_id,
            "name": f"From {script_name}: {action[:80]}",
            "due": due_iso,
            "severity": severity,
            "message": action,
            "tags": ["runlog", "auto-generated", script_name],
            "created": datetime.now(timezone.utc).isoformat(),
            "from_manifest": str(p),
        })
        added.append(alarm_id)
    save_alarms(alarms)
    log_call("add_from_runlog", manifest=manifest_id_or_path[:200], added=len(added))
    return {"ok": True, "added": len(added), "alarm_ids": added}


@mcp.tool()
def health() -> dict[str, Any]:
    """Health check — confirms agent is up + can read/write its state."""
    log_call("health")
    alarms = load_alarms()
    return {
        "ok": True,
        "agent": "sentinel",
        "alarms_file": str(ALARMS_PATH),
        "alarm_count": len(alarms),
        "next_due": min((a["due"] for a in alarms), default=None),
    }


if __name__ == "__main__":
    mcp.run()
