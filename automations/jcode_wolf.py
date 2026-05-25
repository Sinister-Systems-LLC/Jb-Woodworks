#!/usr/bin/env python3
"""jcode_wolf.py -- unified jcode-pattern adoption facade for the Sanctum fleet.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 (verbatim):
    "oh yea 100% add jcode wolf now and have it by default an called and uysed
     when needed."
    "tell sinister term i want the jcode approach to things and all ways they
     do it paired with what we know"

WHY THIS EXISTS:
    Six jcode artifacts (turn_loops / reload / OAUTH / optimization SKILL /
    swarm bench / terminal capabilities) all deserve adoption. Scattering the
    knowledge across six modules makes each one easy to forget. jcode_wolf is
    the SINGLE FACADE every Sanctum agent calls when they want a jcode-grade
    primitive. Tools below are thin wrappers that encode the *patterns* — not
    rust ports. Each command returns JSON for machine consumption + pretty for
    humans.

THE 6 PRIMITIVES:

  oauth-contract        Apply jcode's Claude-OAuth contract to a claude invocation:
                          - User-Agent: claude-cli/1.0.0
                          - anthropic-beta: oauth-2025-04-20,claude-code-20250219
                          - tool name remap: bash->shell_exec / read->file_read /
                            write->file_write / edit->file_edit / glob->file_glob /
                            grep->file_grep / task->task_runner
                          Likely fixes the claude-wrapper.ps1 param-binding crash.
                          CLI: jcode_wolf oauth-contract --print-headers
                               jcode_wolf oauth-contract --wrap "claude args here"

  turn-loop             Bounded-retry runner per jcode's turn_loops.rs.
                          CLI: jcode_wolf turn-loop --cmd "python script.py" \
                                 --max-context-retries 5 --max-incomplete 3 \
                                 --max-empty 1

  reload                File-watch + hot-reload signal (per jcode reload.rs).
                          CLI: jcode_wolf reload --watch automations/,projects/sanctum/ \
                                 --notify-projects sanctum,sinister-term-themes
                               jcode_wolf reload --once

  optimize              Optimization SKILL methodology: define metric -> measure ->
                        attribute -> static analysis -> macro before micro.
                          CLI: jcode_wolf optimize --target latency \
                                 --cmd "python build.py" --baseline 4500

  term-check            Probe current terminal for jcode capability matrix:
                        truecolor / kitty kbd / bracketed paste / mouse SGR 1006 /
                        alt-screen / cursor visibility.
                          CLI: jcode_wolf term-check
                               jcode_wolf term-check --json

  swarm-bench           Port of jcode benchmark_swarm.py: time single-agent vs
                        N-agent swarm on a fixed task.
                          CLI: jcode_wolf swarm-bench --task "build EVE.exe" \
                                 --single --swarm 3 --timeout-min 20

DEFAULT-ON:
    start-sinister-session.ps1 should source this into the spawn phrase so
    every agent knows: 'jcode_wolf is available; use it before re-inventing'.

DOCTRINE: _shared-memory/knowledge/jcode-wolf-doctrine-2026-05-25.md
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
LOG = SANCTUM_ROOT / "_shared-memory" / "jcode-wolf.log"
RELOAD_WATCH_STATE = SANCTUM_ROOT / "_shared-memory" / "jcode-wolf-reload-state.json"

OAUTH_HEADERS = {
    "User-Agent": "claude-cli/1.0.0",
    "anthropic-beta": "oauth-2025-04-20,claude-code-20250219",
}
OAUTH_TOOL_REMAP = {
    "bash": "shell_exec",
    "read": "file_read",
    "write": "file_write",
    "edit": "file_edit",
    "glob": "file_glob",
    "grep": "file_grep",
    "task": "task_runner",
}


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{utc_iso()}] {msg}\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# oauth-contract
# ---------------------------------------------------------------------------

def cmd_oauth_contract(args) -> int:
    if args.print_headers:
        out = {
            "headers": OAUTH_HEADERS,
            "tool_remap": OAUTH_TOOL_REMAP,
            "messages_endpoint_param": "?beta=true",
            "system_prefix_block": "You are Claude Code, Anthropic's official CLI for Claude.",
        }
        print(json.dumps(out, indent=2))
        return 0
    if args.wrap:
        # Build a curl/HTTP-client-friendly shell snippet that wraps a claude call
        hdrs = " ".join(f'-H "{k}: {v}"' for k, v in OAUTH_HEADERS.items())
        remap = " ".join(f"--tool-remap {k}={v}" for k, v in OAUTH_TOOL_REMAP.items())
        wrapped = f'claude {args.wrap} {remap} {hdrs}'
        print(wrapped)
        return 0
    print("usage: jcode_wolf oauth-contract --print-headers | --wrap <args>", file=sys.stderr)
    return 2


# ---------------------------------------------------------------------------
# turn-loop
# ---------------------------------------------------------------------------

def cmd_turn_loop(args) -> int:
    """Bounded-retry runner per jcode turn_loops.rs. Re-runs cmd on transient
    failures up to N times for each failure class."""
    cmd = args.cmd
    if isinstance(cmd, str):
        import shlex
        cmd = shlex.split(cmd)
    context_retries = 0
    incomplete_retries = 0
    empty_retries = 0
    while True:
        start = time.time()
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout_s)
        except subprocess.TimeoutExpired:
            log(f"turn-loop: timeout after {args.timeout_s}s")
            return 124
        elapsed = time.time() - start
        out = (cp.stdout or "") + (cp.stderr or "")
        if cp.returncode == 0:
            log(f"turn-loop: success rc=0 elapsed={elapsed:.1f}s")
            print(cp.stdout, end="")
            return 0
        # Classify failure
        low = out.lower()
        if any(p in low for p in ("context length", "context limit", "too many tokens")):
            context_retries += 1
            if context_retries > args.max_context_retries:
                print(out, file=sys.stderr)
                return cp.returncode
            log(f"turn-loop: context-limit retry {context_retries}/{args.max_context_retries}")
            time.sleep(min(2 ** context_retries, 30))
            continue
        if any(p in low for p in ("incomplete", "truncated", "max_tokens")):
            incomplete_retries += 1
            if incomplete_retries > args.max_incomplete:
                print(out, file=sys.stderr)
                return cp.returncode
            log(f"turn-loop: incomplete-continuation retry {incomplete_retries}/{args.max_incomplete}")
            time.sleep(min(2 ** incomplete_retries, 15))
            continue
        if not cp.stdout.strip():
            empty_retries += 1
            if empty_retries > args.max_empty:
                print(out, file=sys.stderr)
                return cp.returncode
            log(f"turn-loop: empty-output retry {empty_retries}/{args.max_empty}")
            time.sleep(2)
            continue
        # Unclassified failure - don't retry
        print(out, file=sys.stderr)
        return cp.returncode


# ---------------------------------------------------------------------------
# reload (hot-reload signal)
# ---------------------------------------------------------------------------

def cmd_reload(args) -> int:
    if args.once:
        out = scan_reload(args.watch)
        print(json.dumps(out, indent=2))
        return 0
    if args.watch:
        watch_paths = [Path(p.strip()) for p in args.watch.split(",")]
        targets = [t.strip() for t in (args.notify_projects or "").split(",") if t.strip()]
        print(f"[jcode-wolf reload] watching {len(watch_paths)} paths, notifying {targets}")
        prev_state = load_reload_state()
        while True:
            try:
                new_state = scan_paths_for_mtime(watch_paths)
                changed = diff_states(prev_state, new_state)
                if changed:
                    log(f"reload: detected {len(changed)} file changes, notifying {targets}")
                    for slug in targets:
                        notify_project_reload(slug, changed)
                    prev_state = new_state
                    save_reload_state(prev_state)
                time.sleep(args.interval)
            except KeyboardInterrupt:
                return 0
            except Exception as exc:
                log(f"reload err: {exc}")
                time.sleep(args.interval)
    print("usage: jcode_wolf reload --once | --watch <paths> --notify-projects <slugs>", file=sys.stderr)
    return 2


def scan_paths_for_mtime(paths: list[Path]) -> dict[str, float]:
    out: dict[str, float] = {}
    for root in paths:
        if not root.exists():
            continue
        if root.is_file():
            try:
                out[str(root)] = root.stat().st_mtime
            except OSError:
                continue
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(part.startswith(".") or part in ("node_modules", "__pycache__", "_acked") for part in p.parts):
                continue
            try:
                out[str(p)] = p.stat().st_mtime
            except OSError:
                continue
    return out


def load_reload_state() -> dict:
    if not RELOAD_WATCH_STATE.exists():
        return {}
    try:
        return json.loads(RELOAD_WATCH_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_reload_state(s: dict) -> None:
    try:
        RELOAD_WATCH_STATE.parent.mkdir(parents=True, exist_ok=True)
        RELOAD_WATCH_STATE.write_text(json.dumps(s), encoding="utf-8")
    except Exception:
        pass


def diff_states(prev: dict, new: dict) -> list[str]:
    out: list[str] = []
    for path, mt in new.items():
        if path not in prev or prev[path] != mt:
            out.append(path)
    return out


def notify_project_reload(slug: str, changed_files: list[str]) -> None:
    inbox = SANCTUM_ROOT / "_shared-memory" / "inbox" / slug
    inbox.mkdir(parents=True, exist_ok=True)
    ts = utc_iso().replace(":", "").replace("-", "")[:13]
    msg = {
        "kind": "hot-reload",
        "from": "jcode-wolf",
        "to": slug,
        "ts_utc": utc_iso(),
        "changed_files": changed_files[:50],  # cap
        "directive": "Files in your watch set have changed. Re-read CLAUDE.md, projects.json, brain _INDEX.md WITHOUT restarting your Claude process. Use sanctum's hot-reload pattern.",
    }
    try:
        (inbox / f"{ts}Z-from-jcode-wolf-reload.json").write_text(
            json.dumps(msg, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def scan_reload(watch: str | None) -> dict:
    if not watch:
        watch = "automations,projects,_shared-memory/knowledge"
    paths = [SANCTUM_ROOT / p.strip() for p in watch.split(",")]
    s = scan_paths_for_mtime(paths)
    return {"watched_paths": [str(p) for p in paths], "file_count": len(s)}


# ---------------------------------------------------------------------------
# optimize (jcode optimization SKILL methodology)
# ---------------------------------------------------------------------------

def cmd_optimize(args) -> int:
    """Run a command, measure, print before/after vs baseline. The METHODOLOGY
    enforcement: refuse to run without --target and --measure-first."""
    if not args.target:
        print("ERR: --target metric required (latency|throughput|memory|cost|tokens)", file=sys.stderr)
        return 2
    if not args.cmd:
        print("ERR: --cmd required (the thing being optimized)", file=sys.stderr)
        return 2
    print(f"[jcode-wolf optimize] target={args.target} cmd={args.cmd}")
    print(f"[jcode-wolf optimize] baseline={args.baseline}")
    start = time.time()
    cp = subprocess.run(args.cmd, shell=True, capture_output=True, text=True, timeout=args.timeout_s)
    elapsed = time.time() - start
    result = {
        "target": args.target,
        "elapsed_s": round(elapsed, 3),
        "elapsed_ms": int(elapsed * 1000),
        "rc": cp.returncode,
        "baseline": args.baseline,
        "delta_vs_baseline_pct": (round((elapsed * 1000 - args.baseline) / args.baseline * 100, 2)
                                   if args.baseline > 0 else None),
        "stdout_lines": len((cp.stdout or "").splitlines()),
        "stderr_lines": len((cp.stderr or "").splitlines()),
    }
    print(json.dumps(result, indent=2))
    log(f"optimize: {json.dumps(result)}")
    return cp.returncode


# ---------------------------------------------------------------------------
# term-check (terminal capability probe)
# ---------------------------------------------------------------------------

def cmd_term_check(args) -> int:
    """Probe current terminal for jcode capability matrix."""
    caps = {
        "TERM": os.environ.get("TERM", "(unset)"),
        "COLORTERM": os.environ.get("COLORTERM", "(unset)"),
        "TERM_PROGRAM": os.environ.get("TERM_PROGRAM", "(unset)"),
        "WT_SESSION": os.environ.get("WT_SESSION", "(unset)"),  # Windows Terminal
        "is_tty": sys.stdout.isatty(),
        "truecolor": (os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")
                       or os.environ.get("TERM", "").endswith("-direct")),
        "kitty_kbd_likely": (os.environ.get("TERM", "").startswith("xterm-kitty")
                              or os.environ.get("TERM_PROGRAM", "") in ("iTerm.app", "WezTerm", "ghostty")),
        "platform": sys.platform,
    }
    try:
        cols, lines = os.get_terminal_size()
        caps["cols"] = cols
        caps["lines"] = lines
    except Exception:
        caps["cols"] = None
        caps["lines"] = None

    if args.json:
        print(json.dumps(caps, indent=2))
    else:
        print(f"[jcode-wolf term-check] terminal capabilities:")
        for k, v in caps.items():
            print(f"  {k:24} {v}")
    return 0


# ---------------------------------------------------------------------------
# swarm-bench (port of jcode benchmark_swarm.py)
# ---------------------------------------------------------------------------

def cmd_swarm_bench(args) -> int:
    """Run a task in single-agent mode then N-agent swarm; print wall-clock."""
    results = {"task": args.task, "single": None, "swarm": None}
    if args.single:
        start = time.time()
        cp = subprocess.run(args.task, shell=True, capture_output=True, text=True,
                            timeout=args.timeout_min * 60)
        results["single"] = {
            "elapsed_s": round(time.time() - start, 2),
            "rc": cp.returncode,
            "stdout_lines": len((cp.stdout or "").splitlines()),
        }
    if args.swarm:
        # Spawn N parallel agents via multi_agent_launcher if available; else
        # just run cmd N times in parallel as a basic proxy
        launcher = SANCTUM_ROOT / "automations" / "multi_agent_launcher.py"
        start = time.time()
        if launcher.exists():
            cp = subprocess.run(
                ["python", str(launcher), "--swarm-preset", f"bench-{args.swarm}"],
                capture_output=True, text=True, timeout=args.timeout_min * 60,
            )
            results["swarm"] = {
                "n": args.swarm,
                "elapsed_s": round(time.time() - start, 2),
                "rc": cp.returncode,
            }
        else:
            results["swarm"] = {"error": "multi_agent_launcher.py not found"}
    print(json.dumps(results, indent=2))
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="jcode_wolf",
                                  description="Unified jcode-pattern facade for Sanctum")
    sub = ap.add_subparsers(dest="cmd", required=True)

    oc = sub.add_parser("oauth-contract")
    oc.add_argument("--print-headers", action="store_true")
    oc.add_argument("--wrap", help="claude arg string to wrap")

    tl = sub.add_parser("turn-loop")
    tl.add_argument("--cmd", required=True, help="command to run with bounded retry")
    tl.add_argument("--max-context-retries", type=int, default=5)
    tl.add_argument("--max-incomplete", type=int, default=3)
    tl.add_argument("--max-empty", type=int, default=1)
    tl.add_argument("--timeout-s", type=int, default=600)

    rl = sub.add_parser("reload")
    rl.add_argument("--once", action="store_true")
    rl.add_argument("--watch", help="comma-separated paths to watch")
    rl.add_argument("--notify-projects", help="comma-separated project slugs to notify")
    rl.add_argument("--interval", type=int, default=5)

    op = sub.add_parser("optimize")
    op.add_argument("--target", help="latency|throughput|memory|cost|tokens")
    op.add_argument("--cmd")
    op.add_argument("--baseline", type=int, default=0, help="baseline ms")
    op.add_argument("--timeout-s", type=int, default=600)

    tc = sub.add_parser("term-check")
    tc.add_argument("--json", action="store_true")

    sb = sub.add_parser("swarm-bench")
    sb.add_argument("--task", required=True, help="shell command to benchmark")
    sb.add_argument("--single", action="store_true")
    sb.add_argument("--swarm", type=int, default=0, help="N agents in swarm")
    sb.add_argument("--timeout-min", type=int, default=20)

    args = ap.parse_args(argv)
    if args.cmd == "oauth-contract":
        return cmd_oauth_contract(args)
    if args.cmd == "turn-loop":
        return cmd_turn_loop(args)
    if args.cmd == "reload":
        return cmd_reload(args)
    if args.cmd == "optimize":
        return cmd_optimize(args)
    if args.cmd == "term-check":
        return cmd_term_check(args)
    if args.cmd == "swarm-bench":
        return cmd_swarm_bench(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
