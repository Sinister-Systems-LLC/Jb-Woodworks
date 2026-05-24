"""Send a single iMessage via AppleScript through the operator's Mac farm.

RKOJ-ELENO :: 2026-05-24 :: phase P2

Three guards the AppleScript layer can't enforce:
  1. operator_ok=True required (the per-thread OK rule during P1-P3)
  2. recipient in p2_allowed allowlist (parsed from memory/contact-policy.md)
  3. rate-limit (>=5s between sends per recipient)

The send subprocess can be patched in tests; see tests/test_send.py.
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Literal

POLICY_PATH = Path(__file__).resolve().parents[2] / "memory" / "contact-policy.md"
APPLESCRIPT_LOCAL = Path(__file__).resolve().parent / "send.applescript"
APPLESCRIPT_FARM = "/Users/imessage-bridge/send.applescript"  # placeholder; real path lands at P2 unlock
RATE_GAP_SEC = 5.0
SUBPROCESS_TIMEOUT = 30

_last_send: dict[str, float] = {}


def send(
    service: Literal["iMessage", "SMS"],
    recipient: str,
    body: str,
    *,
    operator_ok: bool = False,
    dry_run: bool = False,
    ssh_target: str | None = None,
) -> dict:
    """Send body to recipient via service. Returns a status dict.

    status values:
      "blocked"  — guard failed (reason in `.reason`)
      "dry_run"  — dry_run=True path; no subprocess invoked
      "ok"       — AppleScript returned OK
      "error"    — subprocess ran but returned non-OK
    """
    if not operator_ok and not dry_run:
        return {"status": "blocked", "reason": "operator_ok=False"}
    allowed = _load_allowed()
    if recipient not in allowed:
        return {
            "status": "blocked",
            "reason": "recipient not in p2_allowed",
            "allowed_count": len(allowed),
        }
    if time.monotonic() - _last_send.get(recipient, float("-inf")) < RATE_GAP_SEC:
        return {"status": "blocked", "reason": "rate_limit"}
    if dry_run:
        return {
            "status": "dry_run",
            "service": service,
            "recipient": recipient,
            "body_len": len(body),
        }
    _last_send[recipient] = time.monotonic()
    if ssh_target:
        cmd = [
            "ssh", ssh_target,
            "osascript", APPLESCRIPT_FARM,
            service, recipient, _shquote(body),
        ]
    else:
        cmd = ["osascript", str(APPLESCRIPT_LOCAL), service, recipient, body]
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "reason": "timeout", "cmd": cmd[:2]}
    is_ok = out.stdout.strip().startswith("OK")
    return {
        "status": "ok" if is_ok else "error",
        "stdout": out.stdout.strip(),
        "stderr": out.stderr.strip(),
        "exit": out.returncode,
    }


def _load_allowed() -> set[str]:
    """Parse `memory/contact-policy.md` for the `p2_allowed` markdown table.

    Table format (in contact-policy.md):
        ## p2_allowed
        | handle | added_ts | operator_signed |
        |---|---|---|
        | +15551234567 | 2026-05-24 | yes |
    """
    if not POLICY_PATH.exists():
        return set()
    txt = POLICY_PATH.read_text(encoding="utf-8")
    m = re.search(r"##\s*p2_allowed\s*\n(.*?)(?=\n##|\Z)", txt, re.DOTALL)
    if not m:
        return set()
    out: set[str] = set()
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        handle, _added, signed = cells[0], cells[1], cells[2]
        if handle == "handle":  # header row
            continue
        if signed.lower() != "yes":
            continue
        out.add(handle)
    return out


def _shquote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"


def reset_rate_limiter() -> None:
    """Test helper — clears the per-recipient rate-limit memory."""
    _last_send.clear()
