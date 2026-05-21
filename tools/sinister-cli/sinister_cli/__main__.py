# Sinister Sanctum :: sinister-cli :: umbrella dispatcher entry-point
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Top-level `sinister <subcommand> <rest...>` dispatcher.

Each subcommand resolves at runtime to an installed sibling tool's `main(argv)`
callable. Missing backends print a graceful install hint and exit 2 — they do
NOT crash with an ImportError stack.
"""
from __future__ import annotations
import importlib
import sys
from typing import Callable

from . import __version__

# slug → (display, backend module path, callable name, install hint)
SUBCOMMAND_MAP: dict[str, tuple[str, str, str, str]] = {
    "memory": (
        "Disk-first cross-session memory (jcode-memory parity)",
        "forge_memory_bridge.__main__", "main",
        "pip install -e \"D:/Sinister Sanctum/tools/forge-memory-bridge\"",
    ),
    "swarm": (
        "Multi-agent coordination (jcode-swarm parity)",
        "sinister_swarm.__main__", "main",
        "pip install -e \"D:/Sinister Sanctum/tools/sinister-swarm\"",
    ),
    "graph": (
        "Memory-graph -> mermaid -> PNG",
        "memory_graph_render.__main__", "main",
        "pip install -e \"D:/Sinister Sanctum/tools/memory-graph-render\"",
    ),
    "login": (
        "11-provider auth wallet (jcode-login parity)",
        "sinister_login.__main__", "main",
        "pip install -e \"D:/Sinister Sanctum/tools/sinister-login\"",
    ),
    "usage": (
        "Token-usage + quota inspector — local-state scan + 11-provider endpoint registry + chars/4 estimator (jcode-usage parity)",
        "sinister_usage.__main__", "main",
        "pip install -e \"D:/Sinister Sanctum/tools/sinister-usage\"",
    ),
    "freeze": (
        "Joe @ Ferrari of Winter Park lane (future project)",
        "sinister_freeze.__main__", "main",
        "projects/sinister-freeze/source/ not implemented yet.",
    ),
    "term": (
        "Sinister Term shell (Term agent's PH-CLI integration)",
        "term.__main__", "run",
        "pip install -e \"D:/Sinister Sanctum/projects/sinister-term/source\"",
    ),
    "forge": (
        "Sinister Forge TUI (Forge agent's PH17 integration)",
        "forge.__main__", "run",
        "pip install -e \"D:/Sinister Sanctum/projects/sinister-forge/source\"",
    ),
}

_AUTHOR = "RKOJ-ELENO :: 2026-05-21"


def _print_help(subcmd: str | None = None) -> int:
    if subcmd and subcmd in SUBCOMMAND_MAP:
        desc, mod, fn, hint = SUBCOMMAND_MAP[subcmd]
        print(f"sinister {subcmd} — {desc}")
        print(f"  backend module: {mod}:{fn}")
        print(f"  install hint:   {hint}")
        print(f"  run `sinister {subcmd} --help` to see backend flags.")
        return 0
    print(f"sinister v{__version__}  ({_AUTHOR})")
    print("Sinister Sanctum umbrella CLI — 'our commands will be sinister then the command'")
    print()
    print("Usage: sinister <subcommand> [args...]")
    print()
    print("Subcommands:")
    width = max(len(s) for s in SUBCOMMAND_MAP) + 2
    for slug, (desc, _m, _f, _h) in SUBCOMMAND_MAP.items():
        print(f"  {slug.ljust(width)}{desc}")
    print(f"  {'help'.ljust(width)}Print this help (or `sinister help <subcmd>`)")
    print(f"  {'version'.ljust(width)}Print version of every Sinister tool installed")
    return 0


def _print_version() -> int:
    print(f"sinister-cli         {__version__}")
    for slug, (_desc, mod, _fn, _hint) in SUBCOMMAND_MAP.items():
        pkg = mod.split(".", 1)[0]
        try:
            m = importlib.import_module(pkg)
            v = getattr(m, "__version__", "?")
            print(f"{('sinister ' + slug).ljust(22)} {v} ({pkg})")
        except Exception:
            print(f"{('sinister ' + slug).ljust(22)} not installed ({pkg})")
    return 0


def _resolve(subcmd: str) -> Callable[[list[str]], int] | None:
    if subcmd not in SUBCOMMAND_MAP:
        return None
    _desc, mod_path, fn_name, hint = SUBCOMMAND_MAP[subcmd]
    try:
        mod = importlib.import_module(mod_path)
    except ImportError:
        print(f"sinister: backend for `{subcmd}` is not installed.", file=sys.stderr)
        print(f"  install: {hint}", file=sys.stderr)
        return None
    fn = getattr(mod, fn_name, None)
    if not callable(fn):
        print(f"sinister: backend `{mod_path}` has no callable `{fn_name}`.", file=sys.stderr)
        return None
    return fn


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        return _print_help(argv[1] if len(argv) > 1 else None)
    if argv[0] in ("-V", "--version", "version"):
        return _print_version()
    subcmd = argv[0]
    rest = argv[1:]
    fn = _resolve(subcmd)
    if fn is None:
        if subcmd not in SUBCOMMAND_MAP:
            print(f"sinister: unknown subcommand `{subcmd}`. Try `sinister help`.", file=sys.stderr)
        return 2
    rv = fn(rest)
    return int(rv) if isinstance(rv, int) else 0


if __name__ == "__main__":
    sys.exit(main())
