#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""
auto_snapshot_on_milestone.py — auto-create version snapshot when a milestone is detected.

Milestone triggers (any one fires):
  (a) HEAD commit message starts with "MILESTONE:"
  (b) HEAD commit message matches /iter-N CLOSE/i
  (c) HEAD commit touched deploy/ or _internal/

On trigger, bumps patch + creates tag + pushes + appends manifest. Idempotent:
re-running on the same SHA is a no-op (HEAD-SHA cached in state file).

Invocation (one-line, after the push step inside sanctum-auto-push.ps1):
    python automations/auto_snapshot_on_milestone.py

Log: _shared-memory/auto-snapshot-log.jsonl (one JSON line per run).
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG = REPO / "_shared-memory" / "auto-snapshot-log.jsonl"
STATE = REPO / "_shared-memory" / ".auto-snapshot-state.json"
VS = REPO / "automations" / "version_snapshot.py"

ITER_CLOSE_RE = re.compile(r"iter-\d+\s+close", re.I)


def _run(cmd: list[str]) -> str:
    return subprocess.run(cmd, cwd=str(REPO), capture_output=True,
                          text=True, check=False).stdout


def _utc() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _head_sha() -> str:
    return _run(["git", "rev-parse", "HEAD"]).strip()


def _head_msg() -> str:
    return _run(["git", "log", "-1", "--format=%B"]).strip()


def _head_files() -> list[str]:
    return [f.strip() for f in _run(["git", "show", "--name-only",
                                     "--format=", "HEAD"]).splitlines() if f.strip()]


def _last_sha_cached() -> str:
    if not STATE.exists():
        return ""
    try:
        return json.loads(STATE.read_text(encoding="utf-8")).get("last_sha", "")
    except Exception:
        return ""


def _save_state(sha: str, version: str, reason: str) -> None:
    STATE.write_text(json.dumps({"last_sha": sha, "version": version,
                                 "reason": reason, "utc": _utc()}, indent=2),
                     encoding="utf-8")


def _log(entry: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def _detect_milestone(msg: str, files: list[str]) -> tuple[bool, str]:
    if msg.startswith("MILESTONE:"):
        return True, "commit-prefix-MILESTONE"
    if ITER_CLOSE_RE.search(msg):
        return True, "iter-N-CLOSE"
    if any(f.startswith("deploy/") or f.startswith("_internal/") for f in files):
        return True, "deploy-or-internal-touched"
    return False, ""


def _label_from_msg(msg: str) -> str:
    first = msg.splitlines()[0] if msg else "milestone"
    slug = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")[:30] or "milestone"
    return slug


def main(argv: list[str] | None = None) -> int:
    sha = _head_sha()
    if not sha:
        _log({"utc": _utc(), "result": "skip", "reason": "no-head"})
        return 0
    if sha == _last_sha_cached():
        _log({"utc": _utc(), "sha": sha, "result": "skip", "reason": "already-processed"})
        return 0
    msg = _head_msg()
    files = _head_files()
    fire, reason = _detect_milestone(msg, files)
    if not fire:
        _log({"utc": _utc(), "sha": sha, "result": "skip", "reason": "no-milestone"})
        _save_state(sha, "", "no-milestone")
        return 0
    label = _label_from_msg(msg)
    cmd = [sys.executable, str(VS), "--create", label, "--bump", "patch", "--push"]
    out = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, check=False)
    _log({"utc": _utc(), "sha": sha, "result": "fired", "reason": reason,
          "label": label, "stdout": out.stdout.strip(), "rc": out.returncode})
    _save_state(sha, label, reason)
    return out.returncode


if __name__ == "__main__":
    raise SystemExit(main())
