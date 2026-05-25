# Sinister Term :: cli.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Top-level `sinister <subcommand>` dispatcher. Mirrors the jcode CLI surface
# at https://github.com/1jehuang/jcode for compatibility familiarity, with
# attribution per canonical-20.

from __future__ import annotations

import argparse
import sys
from typing import Optional


PROG = "sinister"
DESCRIPTION = "Sinister Term — Sinister-branded terminal + AI CLI front-end."

PROVIDERS = [
    "claude", "openai", "copilot", "gemini", "azure",
    "alibaba-coding-plan", "openrouter", "openai-compatible",
    "opencode", "opencode-go", "zai", "kimi",
    "302ai", "baseten", "cortecs", "deepseek", "firmware",
    "huggingface", "moonshotai", "nebius", "scaleway", "stackit",
    "groq", "mistral", "perplexity", "togetherai", "deepinfra",
    "fireworks", "minimax", "xai", "lmstudio", "ollama",
    "chutes", "cerebras", "cursor", "antigravity", "google",
]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=PROG, description=DESCRIPTION)
    p.add_argument("--version", action="store_true", help="Show version and exit")
    p.add_argument("--resume", metavar="NAME", help="Resume a previous session by name (alias for `resume <NAME>`)")
    sub = p.add_subparsers(dest="cmd", metavar="<command>")

    sub.add_parser("start", help="Launch the interactive Sinister Term shell (default)")

    p_run = sub.add_parser("run", help="Run a single shell line or slash-command non-interactively")
    p_run.add_argument("line", nargs=argparse.REMAINDER, help="Slash command or shell line")

    p_resume = sub.add_parser("resume", help="Resume from latest resume-point (or by name)")
    p_resume.add_argument("name", nargs="?", help="Resume-point UTC name (optional; default = latest)")

    p_ctl = sub.add_parser("ctl", help="IPC client for a running sterm (handterm @ parity)")
    p_ctl.add_argument("ipc_cmd", help="health|state|dispatch|send-text|get-prompt|get-toolbar|get-history|set-title|ls|close|swarm-spawn|swarm-broadcast")
    p_ctl.add_argument("args", nargs=argparse.REMAINDER)
    p_ctl.add_argument("--port", type=int, default=5081, help="IPC port (default 5081)")

    p_swarm = sub.add_parser("swarm", help="Multi-agent same-repo coordination (jcode swarm parity)")
    p_swarm.add_argument("swarm_cmd", help="spawn|list|dm|broadcast|watch")
    p_swarm.add_argument("args", nargs=argparse.REMAINDER)

    p_login = sub.add_parser("login", help="Per-provider auth flow (OPERATOR-ONLY stub)")
    p_login.add_argument("--provider", required=True, choices=PROVIDERS, metavar="NAME")
    p_login.add_argument("--no-browser", action="store_true")
    p_login.add_argument("--headless", action="store_true", help="alias of --no-browser")
    p_login.add_argument("--print-auth-url", action="store_true")
    p_login.add_argument("--json", action="store_true", dest="json_out")
    p_login.add_argument("--callback-url")
    p_login.add_argument("--auth-code")
    p_login.add_argument("--complete", action="store_true")

    sub.add_parser("auth-test", help="Verify provider auth (OPERATOR-ONLY stub)")

    p_prov = sub.add_parser("provider", help="Provider management (OPERATOR-ONLY stub)")
    p_prov.add_argument("provider_cmd", choices=["list", "add"])
    p_prov.add_argument("args", nargs=argparse.REMAINDER)

    p_br = sub.add_parser("browser", help="Browser automation (delegated to Sanctum agent-browser-bridge)")
    p_br.add_argument("browser_cmd", help="status|setup|open|snapshot|get_content|interactables|click|type|fill_form|select|wait|screenshot|eval|scroll|upload|press")
    p_br.add_argument("args", nargs=argparse.REMAINDER)

    sub.add_parser("serve", help="(future PH-SERVE) Persistent background server")
    sub.add_parser("connect", help="(future PH-SERVE) Attach to running server")
    sub.add_parser("dictate", help="(future PH-DICTATE) Voice input")
    sub.add_parser("version", help="Show version")
    sub.add_parser("help", help="Show help")

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from term import __version__
        print(f"sinister-term {__version__}")
        return 0

    if args.resume and not args.cmd:
        return _cmd_resume(args.resume)

    cmd = args.cmd or "start"

    if cmd == "start":
        from term.app import run as run_shell
        run_shell()
        return 0
    if cmd == "run":
        return _cmd_run(args.line)
    if cmd == "resume":
        return _cmd_resume(args.name)
    if cmd == "ctl":
        return _cmd_ctl(args.ipc_cmd, args.args, port=args.port)
    if cmd == "swarm":
        return _cmd_swarm(args.swarm_cmd, args.args)
    if cmd == "login":
        return _cmd_login(args)
    if cmd == "auth-test":
        return _cmd_auth_test()
    if cmd == "provider":
        return _cmd_provider(args.provider_cmd, args.args)
    if cmd == "browser":
        return _cmd_browser(args.browser_cmd, args.args)
    if cmd in {"serve", "connect"}:
        print(f"sinister {cmd}: not yet implemented (PH-SERVE — future session). Use `sinister start` + `sinister ctl` for now.")
        return 1
    if cmd == "dictate":
        print("sinister dictate: not yet implemented (needs operator's STT command — future session).")
        return 1
    if cmd == "version":
        from term import __version__
        print(f"sinister-term {__version__}")
        return 0
    if cmd == "help":
        parser.print_help()
        return 0

    parser.print_help()
    return 1


def main_compat() -> int:
    """Entry-point for the legacy `sterm` alias. Defaults to `start` if no
    args, otherwise forwards to main()."""
    if len(sys.argv) <= 1:
        from term.app import run as run_shell
        run_shell()
        return 0
    return main()


def _cmd_run(line_parts: list[str]) -> int:
    """Non-interactive single dispatch. jcode parity: `jcode run <cmd>`."""
    if not line_parts:
        print("usage: sinister run <slash-command or shell line>")
        return 2
    line = " ".join(line_parts)
    from term.commands import dispatch
    result = dispatch(line)
    if not result.handled:
        # Not a slash command — pass to underlying shell
        import platform
        import subprocess
        if platform.system() == "Windows":
            cmd = ["powershell.exe", "-NoProfile", "-Command", line]
        else:
            cmd = ["/bin/sh", "-c", line]
        rc = subprocess.run(cmd, check=False).returncode
        return rc
    if result.output:
        print(result.output)
    return 0


def _cmd_resume(name: Optional[str]) -> int:
    """Read the latest resume-point (or by-name) and print a one-screen warm-start summary."""
    from pathlib import Path
    import json
    import os
    sanctum_root = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
    rp_dir = sanctum_root / "_shared-memory" / "resume-points" / "Sinister Term"
    if not rp_dir.exists():
        print(f"(no resume-points dir at {rp_dir})")
        return 1
    candidates = sorted(rp_dir.glob("*.json"))
    if not candidates:
        print(f"(no resume-points found in {rp_dir})")
        return 1
    if name:
        match = [p for p in candidates if name in p.name]
        if not match:
            print(f"no resume-point matching '{name}'. Available: {[p.name for p in candidates]}")
            return 1
        target = match[-1]
    else:
        target = candidates[-1]
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"failed to read {target}: {e}")
        return 1
    print(f"Resume-point: {target.name}")
    print(f"  branch:     {data.get('git', {}).get('branch', '?')}")
    print(f"  head:       {data.get('git', {}).get('head', '?')[:10]} {data.get('git', {}).get('head_msg', '')}")
    print(f"  progress:")
    for p in data.get("progress_top3", []):
        print(f"    · {p}")
    print(f"  inbox unread: {data.get('inbox_unread_count', 0)}")
    print(f"  pre-warm reads:")
    for r in data.get("pre_warm_reads", []):
        print(f"    · {r}")
    return 0


def _cmd_ctl(ipc_cmd: str, args: list[str], port: int = 5081) -> int:
    from term.ipc_client import call as ipc_call
    payload: dict = {}
    if ipc_cmd in {"dispatch", "send-text", "set-title", "swarm-broadcast"}:
        payload = {"text": " ".join(args)} if args else {}
    elif ipc_cmd in {"get-history"}:
        payload = {"limit": int(args[0])} if args else {}
    elif ipc_cmd in {"swarm-spawn"}:
        payload = {"project": args[0]} if args else {}
    try:
        resp = ipc_call(ipc_cmd, payload, port=port)
    except Exception as e:
        print(f"IPC call failed: {e}")
        return 1
    import json
    print(json.dumps(resp, indent=2, default=str))
    return 0 if resp.get("ok") else 1


def _cmd_swarm(swarm_cmd: str, args: list[str]) -> int:
    from term import swarm
    if swarm_cmd == "spawn":
        if not args:
            print("usage: sinister swarm spawn <project-key>")
            return 2
        return swarm.spawn(args[0])
    if swarm_cmd == "list":
        rows = swarm.list_agents()
        if not rows:
            print("(no live agents)")
            return 0
        for r in rows:
            print(f"  {r['marker']} {r['agent']:<32} {r['age_min']}m ago  cwd={r.get('cwd', '?')}")
        return 0
    if swarm_cmd == "dm":
        if len(args) < 2:
            print("usage: sinister swarm dm <agent-slug> <message...>")
            return 2
        target = args[0]
        msg = " ".join(args[1:])
        path = swarm.dm(target, msg)
        if path is None:
            print(f"unknown agent inbox: {target}")
            return 1
        print(f"[DM] -> {path}")
        return 0
    if swarm_cmd == "broadcast":
        if not args:
            print("usage: sinister swarm broadcast <message...>")
            return 2
        msg = " ".join(args)
        path = swarm.broadcast(msg)
        print(f"[BROADCAST] -> {path}")
        return 0
    if swarm_cmd == "watch":
        print("sinister swarm watch: not yet implemented (PH-SWARM-WATCH future).")
        print("For now, sibling file-edit detection is provided by:")
        print("  · _shared-memory/knowledge/multi-agent-branch-contention-isolation-pattern.md")
        print("  · _shared-memory/knowledge/verify-head-before-commit-multi-agent.md")
        return 1
    print(f"unknown swarm subcommand: {swarm_cmd}")
    return 2


def _cmd_login(args) -> int:
    from term import login_stub
    return login_stub.run(args)


def _cmd_auth_test() -> int:
    from term import login_stub
    return login_stub.auth_test()


def _cmd_provider(provider_cmd: str, args: list[str]) -> int:
    from term import login_stub
    if provider_cmd == "list":
        for p in PROVIDERS:
            print(f"  {p}")
        return 0
    if provider_cmd == "add":
        return login_stub.provider_add(args)
    print(f"unknown provider subcommand: {provider_cmd}")
    return 2


def _cmd_browser(browser_cmd: str, args: list[str]) -> int:
    print(f"sinister browser {browser_cmd}: delegated to Sanctum agent-browser-bridge.")
    print("See: _shared-memory/knowledge/agent-browser-bridge-pattern.md")
    print("Status: doc-only this session; the actual Firefox Agent Bridge integration")
    print("is operator-gated (touches browser extension install + per-domain allowlist).")
    if browser_cmd in {"status"}:
        print()
        print("Quick local check: looking for firefox-agent-bridge clone...")
        from pathlib import Path
        import os
        # RKOJ-ELENO :: 2026-05-25 :: env-var first to avoid hardcoded operator-machine paths
        # (overseer-audit finding 2026-05-25 — cli.py:303 hardcoded C:\Users\Zonia\...).
        # Falls back to the operator default for backwards-compat, but any other workstation
        # can set SINISTER_FIREFOX_BRIDGE_PATH instead.
        local_str = os.environ.get(
            "SINISTER_FIREFOX_BRIDGE_PATH",
            r"C:\Users\Zonia\Desktop\Github Research\firefox-agent-bridge-0.9.9",
        )
        local = Path(local_str)
        print(f"  clone present: {local.exists()}  ({local})")
        print(f"  (override with SINISTER_FIREFOX_BRIDGE_PATH env var)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
