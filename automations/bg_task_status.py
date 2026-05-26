#!/usr/bin/env python3
"""bg_task_status.py -- pure-Python background-task status tracker.

Author: RKOJ-ELENO :: 2026-05-26
License: AGPL-3.0-or-later

Mirrors jcode's background-task model (src/background/model.rs:21-73) so any
Sinister fleet surface (sterm, EVE.exe, mesh-coord, swarm slices) can register
a long-running task, push progress events, and read status from one shared
JSON store.

Sinister gap-audit iter-94 (Rank #4): jcode tracks every background spawn with
status/exit_code/progress/event_history. Our fleet's background commands had
no canonical surface -- swarm slices were polled by heartbeat-mtime alone and
pytest runs lost their "342 of 1000" progress on disconnect. This daemon-less
CLI fixes that.

Schema (per _shared-memory/bg-tasks/<task_id>.json):
    {
        "task_id": "bgt-<utc>-<6hex>",
        "tool_name": "bash" | "pytest" | "swarm" | ...,
        "session_slug": "sinister-term",
        "status": "running" | "completed" | "failed" | "superseded",
        "exit_code": int | None,
        "started_at_utc": iso8601-Z,
        "completed_at_utc": iso8601-Z | None,
        "duration_secs": float | None,
        "pid": int | None,
        "cwd": str,
        "command_preview": str (<=80 chars),
        "progress_current": int | None,
        "progress_total": int | None,
        "progress_unit": str | None,
        "event_history": [
            {"ts_utc": iso8601-Z, "kind": str, "message": str,
             "progress": {"cur": int, "total": int} | None}
        ]  # ring-buffer cap 50 (oldest dropped)
    }

CLI:
    register <tool> <command-preview> [--session SLUG] [--pid PID]
        -> stdout: task_id
    progress <task_id> <current> <total> [--unit UNIT] [--message MSG]
    event <task_id> <kind> <message>
    complete <task_id> <exit_code> [--message MSG]
    fail <task_id> <reason>
    list [--session SLUG] [--status STATUS] [--limit N]
        -> stdout: TSV (task_id, status, age, session, command_preview)
    get <task_id>
        -> stdout: full JSON
    cleanup --older-than-hours N

Atomicity:
    Every mutation writes <task_id>.json.tmp then os.replace() onto the live
    path -> multi-writer safe on Windows + POSIX. Updates are read-modify-write
    so concurrent writers may lose the loser's event; acceptable for an
    audit-log surface (callers append, never edit).

Tolerance:
    - Missing _shared-memory/bg-tasks/ -> auto-created.
    - Corrupt JSON files in list/cleanup -> skipped + WARN to stderr.
    - Unknown task_id in update/get -> exit 2 + clear msg on stderr.

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- constants ---------------------------------------------------------------

EVENT_HISTORY_CAP = 50
COMMAND_PREVIEW_CAP = 80
TASK_ID_PREFIX = "bgt"
VALID_STATUSES = {"running", "completed", "failed", "superseded"}
VALID_EVENT_KINDS = {
    "spawned",
    "progress",
    "checkpoint",
    "completed",
    "failed",
    "superseded",
}

# --- paths -------------------------------------------------------------------


def _repo_root() -> Path:
    """Sanctum root = parent of automations/."""
    return Path(__file__).resolve().parent.parent


def _tasks_dir() -> Path:
    d = _repo_root() / "_shared-memory" / "bg-tasks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _task_path(task_id: str) -> Path:
    return _tasks_dir() / f"{task_id}.json"


# --- time / id ---------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _parse_utc(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def _new_task_id() -> str:
    return f"{TASK_ID_PREFIX}-{_utc_now_compact()}-{secrets.token_hex(3)}"


def _age_str(started_iso: str) -> str:
    dt = _parse_utc(started_iso)
    if dt is None:
        return "?"
    delta = datetime.now(timezone.utc) - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m{secs % 60}s"
    if secs < 86400:
        return f"{secs // 3600}h{(secs % 3600) // 60}m"
    return f"{secs // 86400}d{(secs % 86400) // 3600}h"


# --- io ----------------------------------------------------------------------


def _read_task(task_id: str) -> dict[str, Any]:
    p = _task_path(task_id)
    if not p.exists():
        print(f"bg_task_status: task not found: {task_id}", file=sys.stderr)
        sys.exit(2)
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(
            f"bg_task_status: corrupt JSON for {task_id}: {e}", file=sys.stderr
        )
        sys.exit(2)


def _write_task(task: dict[str, Any]) -> None:
    """Atomic write: tmp + os.replace."""
    task_id = task["task_id"]
    final = _task_path(task_id)
    # unique tmp suffix to avoid collisions between writers
    tmp = final.with_suffix(
        f".json.tmp.{os.getpid()}.{secrets.token_hex(2)}"
    )
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(task, f, indent=2, sort_keys=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, final)


def _append_event(
    task: dict[str, Any],
    kind: str,
    message: str,
    progress: dict[str, int] | None = None,
) -> None:
    """Append to event_history with ring-buffer cap."""
    if kind not in VALID_EVENT_KINDS:
        print(
            f"bg_task_status: WARN unknown event kind '{kind}'",
            file=sys.stderr,
        )
    entry: dict[str, Any] = {
        "ts_utc": _utc_now_iso(),
        "kind": kind,
        "message": message,
        "progress": progress,
    }
    history = task.setdefault("event_history", [])
    history.append(entry)
    # ring buffer: drop oldest when over cap
    if len(history) > EVENT_HISTORY_CAP:
        del history[: len(history) - EVENT_HISTORY_CAP]


# --- commands ----------------------------------------------------------------


def cmd_register(args: argparse.Namespace) -> int:
    tool_name = args.tool
    preview = (args.command_preview or "")[:COMMAND_PREVIEW_CAP]
    session = args.session or ""
    pid = args.pid
    cwd = os.getcwd().replace("\\", "/")

    task_id = _new_task_id()
    now = _utc_now_iso()
    task: dict[str, Any] = {
        "task_id": task_id,
        "tool_name": tool_name,
        "session_slug": session,
        "status": "running",
        "exit_code": None,
        "started_at_utc": now,
        "completed_at_utc": None,
        "duration_secs": None,
        "pid": pid,
        "cwd": cwd,
        "command_preview": preview,
        "progress_current": None,
        "progress_total": None,
        "progress_unit": None,
        "event_history": [],
    }
    _append_event(task, "spawned", "process started", progress=None)
    _write_task(task)
    print(task_id)
    return 0


def cmd_progress(args: argparse.Namespace) -> int:
    task = _read_task(args.task_id)
    if task.get("status") != "running":
        print(
            f"bg_task_status: WARN task {args.task_id} status="
            f"{task.get('status')}, progress recorded anyway",
            file=sys.stderr,
        )
    current = int(args.current)
    total = int(args.total)
    task["progress_current"] = current
    task["progress_total"] = total
    if args.unit:
        task["progress_unit"] = args.unit
    unit = task.get("progress_unit") or "items"
    msg = args.message or f"{current} of {total} {unit}"
    _append_event(task, "progress", msg, progress={"cur": current, "total": total})
    _write_task(task)
    return 0


def cmd_event(args: argparse.Namespace) -> int:
    task = _read_task(args.task_id)
    _append_event(task, args.kind, args.message, progress=None)
    _write_task(task)
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    task = _read_task(args.task_id)
    exit_code = int(args.exit_code)
    now = _utc_now_iso()
    task["status"] = "completed" if exit_code == 0 else "failed"
    task["exit_code"] = exit_code
    task["completed_at_utc"] = now
    started = _parse_utc(task.get("started_at_utc", ""))
    if started is not None:
        task["duration_secs"] = round(
            (datetime.now(timezone.utc) - started).total_seconds(), 3
        )
    kind = "completed" if exit_code == 0 else "failed"
    msg = args.message or f"exit_code={exit_code}"
    _append_event(task, kind, msg, progress=None)
    _write_task(task)
    return 0


def cmd_fail(args: argparse.Namespace) -> int:
    task = _read_task(args.task_id)
    now = _utc_now_iso()
    task["status"] = "failed"
    if task.get("exit_code") is None:
        task["exit_code"] = 1
    task["completed_at_utc"] = now
    started = _parse_utc(task.get("started_at_utc", ""))
    if started is not None:
        task["duration_secs"] = round(
            (datetime.now(timezone.utc) - started).total_seconds(), 3
        )
    _append_event(task, "failed", args.reason, progress=None)
    _write_task(task)
    return 0


def _iter_tasks() -> list[dict[str, Any]]:
    """Read all tasks, skipping corrupt files (logged to stderr)."""
    out: list[dict[str, Any]] = []
    for p in _tasks_dir().glob("*.json"):
        try:
            with p.open("r", encoding="utf-8") as f:
                out.append(json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            print(
                f"bg_task_status: WARN skipping corrupt {p.name}: {e}",
                file=sys.stderr,
            )
    return out


def cmd_list(args: argparse.Namespace) -> int:
    tasks = _iter_tasks()
    if args.session:
        tasks = [t for t in tasks if t.get("session_slug") == args.session]
    if args.status:
        tasks = [t for t in tasks if t.get("status") == args.status]
    # newest first
    tasks.sort(key=lambda t: t.get("started_at_utc", ""), reverse=True)
    if args.limit and args.limit > 0:
        tasks = tasks[: args.limit]
    for t in tasks:
        row = "\t".join(
            [
                t.get("task_id", "?"),
                t.get("status", "?"),
                _age_str(t.get("started_at_utc", "")),
                t.get("session_slug", "") or "-",
                (t.get("command_preview", "") or "").replace("\t", " "),
            ]
        )
        print(row)
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    task = _read_task(args.task_id)
    print(json.dumps(task, indent=2, sort_keys=False))
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    cutoff = time.time() - (args.older_than_hours * 3600)
    cutoff_dt = datetime.fromtimestamp(cutoff, tz=timezone.utc)
    removed = 0
    kept = 0
    for t in _iter_tasks():
        status = t.get("status", "running")
        if status not in {"completed", "failed", "superseded"}:
            kept += 1
            continue
        # prefer completed_at_utc, fall back to started_at_utc
        ts = t.get("completed_at_utc") or t.get("started_at_utc")
        dt = _parse_utc(ts) if ts else None
        if dt is None:
            kept += 1
            continue
        if dt < cutoff_dt:
            try:
                _task_path(t["task_id"]).unlink()
                removed += 1
            except OSError as e:
                print(
                    f"bg_task_status: WARN failed to remove {t['task_id']}: {e}",
                    file=sys.stderr,
                )
                kept += 1
        else:
            kept += 1
    print(f"removed={removed} kept={kept}")
    return 0


# --- argparse ----------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bg_task_status",
        description=(
            "Sinister background-task status tracker (jcode-gap audit "
            "iter-94). Per-task JSON in _shared-memory/bg-tasks/."
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    sp = sub.add_parser("register", help="register a new background task")
    sp.add_argument("tool", help="tool name (bash, pytest, swarm, ...)")
    sp.add_argument(
        "command_preview", help="first 80 chars of the command being run"
    )
    sp.add_argument("--session", help="session slug (e.g. sinister-term)")
    sp.add_argument("--pid", type=int, help="OS pid of the spawned process")

    sp = sub.add_parser("progress", help="record progress (cur/total)")
    sp.add_argument("task_id")
    sp.add_argument("current", type=int)
    sp.add_argument("total", type=int)
    sp.add_argument("--unit", help="progress unit (tests, files, bytes, ...)")
    sp.add_argument("--message", help="human-readable progress note")

    sp = sub.add_parser("event", help="append a generic event")
    sp.add_argument("task_id")
    sp.add_argument(
        "kind",
        help="event kind: spawned, progress, checkpoint, completed, failed, superseded",
    )
    sp.add_argument("message")

    sp = sub.add_parser("complete", help="mark task completed with exit_code")
    sp.add_argument("task_id")
    sp.add_argument("exit_code", type=int)
    sp.add_argument("--message", help="completion note")

    sp = sub.add_parser("fail", help="mark task failed")
    sp.add_argument("task_id")
    sp.add_argument("reason")

    sp = sub.add_parser("list", help="list tasks (newest first, TSV)")
    sp.add_argument("--session", help="filter by session slug")
    sp.add_argument(
        "--status",
        help="filter by status: running / completed / failed / superseded",
    )
    sp.add_argument(
        "--limit", type=int, default=0, help="max rows (0 = unlimited)"
    )

    sp = sub.add_parser("get", help="print full JSON for a task_id")
    sp.add_argument("task_id")

    sp = sub.add_parser(
        "cleanup", help="delete completed/failed tasks older than N hours"
    )
    sp.add_argument("--older-than-hours", type=float, required=True)

    return p


HANDLERS = {
    "register": cmd_register,
    "progress": cmd_progress,
    "event": cmd_event,
    "complete": cmd_complete,
    "fail": cmd_fail,
    "list": cmd_list,
    "get": cmd_get,
    "cleanup": cmd_cleanup,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "list" and getattr(args, "status", None):
        if args.status not in VALID_STATUSES:
            print(
                f"bg_task_status: WARN unknown status filter '{args.status}', "
                f"valid: {sorted(VALID_STATUSES)}",
                file=sys.stderr,
            )
    return HANDLERS[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
