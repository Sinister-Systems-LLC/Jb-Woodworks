#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""
sinister_swarm.py -- Python port of jcode's swarm fan-out primitive.

jcode source citation:
    C:\\Users\\Zonia\\Desktop\\jcode-0.12.4\\src\\server\\swarm.rs:1024-1038
    (run_swarm_message + try_join_all)
    + src\\tool\\task.rs:200-271 (SubagentTool::run forked provider isolation)

Mechanism summary (jcode):
    1. A coordinator forks its provider via `provider.fork()` so model/session
       mutations stay local to the child (tool/task.rs:208).
    2. A planner LLM decomposes the request into 2-4 SwarmTaskSpec entries
       (description / prompt / subagent_type) -- swarm.rs:998-1014.
    3. Each spec maps to a future that calls `run_swarm_task`, which builds an
       isolated `Agent` with the recursion-blocking allow-list ("subagent",
       "task", "todo*" removed -- swarm.rs:946) and runs to completion.
    4. `futures::future::try_join_all` (swarm.rs:1038) fans the N futures out
       concurrently with fail-fast semantics.
    5. The coordinator integrates outputs in a final synthesis prompt
       (swarm.rs:1040-1056).

Sanctum port reuses existing fleet primitives:
    - `automations/mesh-coordinator.ps1` -- mesh-lock check/register for each
      slice's `owned_paths` (prevents two agents touching the same file).
    - `automations/start-sinister-session.ps1` -- mintty spawn with full cold
      start + injected env (`SINISTER_SLICE_ID`, `SINISTER_SLICE_PROMPT`).
    - `_shared-memory/heartbeats/<slug>.json` -- liveness check post-spawn.
    - `_shared-memory/inbox/swarm-results/<prefix>/<slice_id>.json` -- each
      spawned sub-agent drops its final result-row here before exit; the
      coordinator polls until present (or timeout).

Public API:
    fanout(slug_prefix: str,
           slices: list[dict],
           timeout_s: int = 600,
           dry_run: bool = False) -> list[dict]

    Each slice is:
        {
            "id": "slice-01",
            "prompt": "Investigate <thing> and ship <artifact>",
            "owned_paths": ["projects/foo/src/bar.py"],
            "lane": "sinister-foo"
        }

    Returns: list of result dicts with shape:
        {
            "id": "slice-01",
            "status": "ok" | "timeout" | "spawn_failed" | "lock_conflict",
            "result_path": "<absolute path or None>",
            "result": <parsed JSON payload or None>,
            "elapsed_s": float,
            "spawn_pid": int | None
        }

CLI:
    python automations/sinister_swarm.py fanout \\
        --slug-prefix sanctum-swarm-2026-05-25 \\
        --slices-file /tmp/slices.json \\
        [--timeout-s 600] [--dry-run]

    python automations/sinister_swarm.py smoke         # built-in dry-run self-test
    python automations/sinister_swarm.py list-locks    # mesh-coord -Action List
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# -----------------------------------------------------------------------------
# Path layout (matches sanctum conventions)
# -----------------------------------------------------------------------------
SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
AUTOMATIONS = SANCTUM_ROOT / "automations"
MESH_COORD = AUTOMATIONS / "mesh-coordinator.ps1"
START_SESSION = AUTOMATIONS / "start-sinister-session.ps1"
HEARTBEATS = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
SWARM_RESULTS_ROOT = SANCTUM_ROOT / "_shared-memory" / "inbox" / "swarm-results"

POLL_INTERVAL_S = 3.0
HEARTBEAT_GRACE_S = 60.0  # how long to wait for first heartbeat after spawn


# -----------------------------------------------------------------------------
# Mesh-lock pre-flight (reuses mesh-coordinator.ps1 -Action Check)
# -----------------------------------------------------------------------------
def _mesh_check(slug: str, focus: str, dry_run: bool = False) -> bool:
    """Return True if `focus` is CLEAR for `slug` to take, False if LOCKED by peer."""
    if dry_run:
        return True
    if not MESH_COORD.exists():
        # mesh-coordinator absent -> treat as clear, log warning
        print(f"  [WARN] mesh-coordinator.ps1 not found at {MESH_COORD}; "
              "skipping lock check.", file=sys.stderr)
        return True
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(MESH_COORD),
        "-Action", "Check",
        "-Focus", focus,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        # mesh-coordinator emits "CLEAR" or "LOCKED" on stdout; exit 0 either way.
        return "LOCKED" not in proc.stdout.upper()
    except Exception as exc:
        print(f"  [WARN] mesh-check failed for {focus}: {exc}", file=sys.stderr)
        return True  # fail-open: don't block on coordinator hiccup


# -----------------------------------------------------------------------------
# Slice runner -- the per-slice worker thread
# -----------------------------------------------------------------------------
def _run_slice(slug_prefix: str,
               slice_def: dict,
               timeout_s: int,
               dry_run: bool) -> dict:
    sid = slice_def["id"]
    slug = f"{slug_prefix}-{sid}"
    prompt = slice_def.get("prompt", "")
    owned = slice_def.get("owned_paths", [])
    lane = slice_def.get("lane", "")

    started = time.time()
    result_dir = SWARM_RESULTS_ROOT / slug_prefix
    result_path = result_dir / f"{sid}.json"

    # 1. Mesh pre-flight for each owned_path
    for path in owned:
        if not _mesh_check(slug, path, dry_run=dry_run):
            return {
                "id": sid,
                "status": "lock_conflict",
                "result_path": None,
                "result": None,
                "elapsed_s": time.time() - started,
                "spawn_pid": None,
                "locked_path": path,
            }

    # 2. Spawn sub-agent (skipped in dry-run)
    spawn_pid: int | None = None
    if not dry_run:
        result_dir.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["SINISTER_SLICE_ID"] = sid
        env["SINISTER_SLICE_PROMPT"] = prompt
        env["SINISTER_SLICE_RESULT_PATH"] = str(result_path)
        env["SINISTER_LOOP_CONDITION"] = (
            f"Write final result JSON to {result_path} then exit."
        )
        spawn_cmd = [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(START_SESSION),
        ]
        if lane:
            spawn_cmd += ["-Project", lane]
        spawn_cmd += ["-AgentName", slug]
        try:
            proc = subprocess.Popen(
                spawn_cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            spawn_pid = proc.pid
        except Exception as exc:
            return {
                "id": sid,
                "status": "spawn_failed",
                "result_path": None,
                "result": None,
                "elapsed_s": time.time() - started,
                "spawn_pid": None,
                "error": str(exc),
            }

        # 3. Wait for heartbeat to confirm liveness
        hb_path = HEARTBEATS / f"{slug}.json"
        hb_deadline = time.time() + HEARTBEAT_GRACE_S
        while time.time() < hb_deadline and not hb_path.exists():
            time.sleep(POLL_INTERVAL_S)
    else:
        # dry-run: synthesize a fake result so the polling path works
        result_dir.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps({
                "id": sid,
                "dry_run": True,
                "received_prompt_chars": len(prompt),
                "owned_paths": owned,
            }, indent=2),
            encoding="utf-8",
        )

    # 4. Poll inbox/swarm-results/<prefix>/<sid>.json until present or timeout
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if result_path.exists():
            try:
                payload = json.loads(result_path.read_text(encoding="utf-8"))
            except Exception as exc:
                payload = {"_parse_error": str(exc)}
            return {
                "id": sid,
                "status": "ok",
                "result_path": str(result_path),
                "result": payload,
                "elapsed_s": time.time() - started,
                "spawn_pid": spawn_pid,
            }
        time.sleep(POLL_INTERVAL_S)

    return {
        "id": sid,
        "status": "timeout",
        "result_path": str(result_path) if result_path.exists() else None,
        "result": None,
        "elapsed_s": time.time() - started,
        "spawn_pid": spawn_pid,
    }


# -----------------------------------------------------------------------------
# Public API: fanout (jcode's try_join_all analogue via ThreadPoolExecutor)
# -----------------------------------------------------------------------------
def fanout(slug_prefix: str,
           slices: list[dict],
           timeout_s: int = 600,
           dry_run: bool = False) -> list[dict]:
    """Spawn N parallel sub-agents and aggregate their results.

    Mirrors jcode's `run_swarm_message` (server/swarm.rs:982-1066). Whereas jcode
    uses Tokio + `futures::future::try_join_all` for in-process concurrency, the
    Sanctum port uses subprocess.Popen + a ThreadPoolExecutor so each sub-agent
    is a real OS process (a fresh Claude CLI session via start-sinister-session).
    """
    if not slices:
        return []

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, len(slices))) as pool:
        futures = {
            pool.submit(_run_slice, slug_prefix, sl, timeout_s, dry_run): sl
            for sl in slices
        }
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as exc:
                sl = futures[fut]
                results.append({
                    "id": sl.get("id", "?"),
                    "status": "exception",
                    "error": str(exc),
                    "result": None,
                    "result_path": None,
                    "elapsed_s": 0.0,
                    "spawn_pid": None,
                })
    # Stable order = original slice order
    order = {sl["id"]: i for i, sl in enumerate(slices)}
    results.sort(key=lambda r: order.get(r["id"], 999))
    return results


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def _cmd_fanout(args: argparse.Namespace) -> int:
    # accept --slices-file (canonical) or --slices-json (legacy alias)
    raw = getattr(args, "slices_file", None) or getattr(args, "slices_json", None)
    if not raw:
        print("[FAIL] --slices-file is required", file=sys.stderr)
        return 2
    slices_path = Path(raw)
    if not slices_path.exists():
        print(f"[FAIL] slices file not found: {slices_path}", file=sys.stderr)
        return 2
    slices = json.loads(slices_path.read_text(encoding="utf-8"))
    if not isinstance(slices, list):
        print("[FAIL] slices-json must be a JSON array", file=sys.stderr)
        return 2
    results = fanout(
        slug_prefix=args.slug_prefix,
        slices=slices,
        timeout_s=args.timeout_s,
        dry_run=args.dry_run,
    )
    print(json.dumps(results, indent=2))
    bad = [r for r in results if r["status"] != "ok"]
    return 0 if not bad else 1


def _cmd_smoke(_: argparse.Namespace) -> int:
    """Built-in dry-run that proves the API shape without spawning real agents."""
    print("[smoke] sinister_swarm.py :: dry-run fanout (3 slices)")
    slices = [
        {"id": "slice-a", "prompt": "ALPHA work",
         "owned_paths": ["projects/demo/a.py"], "lane": "demo"},
        {"id": "slice-b", "prompt": "BRAVO work",
         "owned_paths": ["projects/demo/b.py"], "lane": "demo"},
        {"id": "slice-c", "prompt": "CHARLIE work",
         "owned_paths": ["projects/demo/c.py"], "lane": "demo"},
    ]
    results = fanout(
        slug_prefix="smoke-2026-05-25",
        slices=slices,
        timeout_s=15,
        dry_run=True,
    )
    print(json.dumps(results, indent=2))
    ok = all(r["status"] == "ok" for r in results)
    print(f"[smoke] PASS={ok} ({len(results)} slices)")
    # Clean up the synthetic result files we just dropped
    try:
        for r in results:
            rp = r.get("result_path")
            if rp and Path(rp).exists():
                Path(rp).unlink()
        smoke_dir = SWARM_RESULTS_ROOT / "smoke-2026-05-25"
        if smoke_dir.exists() and not any(smoke_dir.iterdir()):
            smoke_dir.rmdir()
    except Exception:
        pass
    return 0 if ok else 1


def _cmd_list_locks(args: argparse.Namespace) -> int:
    """Forward to mesh-coordinator.ps1 -Action List (read-through)."""
    if not MESH_COORD.exists():
        print(f"[FAIL] mesh-coordinator.ps1 not found at {MESH_COORD}",
              file=sys.stderr)
        return 2
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(MESH_COORD),
        "-Action", "List",
    ]
    if getattr(args, "slug", None):
        cmd += ["-Slug", args.slug]
    proc = subprocess.run(cmd, capture_output=False, text=True)
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sinister_swarm")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fan = sub.add_parser("fanout", help="Fan out N parallel sub-agents")
    p_fan.add_argument("--slug-prefix", required=True)
    p_fan.add_argument("--slices-file", dest="slices_file",
                       help="Path to JSON array of slice defs (canonical)")
    p_fan.add_argument("--slices-json", dest="slices_json",
                       help="Legacy alias for --slices-file")
    p_fan.add_argument("--timeout-s", type=int, default=600)
    p_fan.add_argument("--dry-run", action="store_true")
    p_fan.set_defaults(func=_cmd_fanout)

    p_smoke = sub.add_parser("smoke", help="Built-in dry-run self-test")
    p_smoke.set_defaults(func=_cmd_smoke)

    p_list = sub.add_parser("list-locks",
                            help="Call mesh-coordinator.ps1 -Action List")
    p_list.add_argument("--slug", default=None,
                        help="Filter locks by owner slug (optional)")
    p_list.set_defaults(func=_cmd_list_locks)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    # No args -> run the built-in dry-run smoke (manifest + input shape validation).
    if len(sys.argv) == 1:
        sys.exit(main(["smoke"]))
    sys.exit(main())
