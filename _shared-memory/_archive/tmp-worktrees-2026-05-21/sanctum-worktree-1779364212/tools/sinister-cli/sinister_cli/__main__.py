# Sinister Sanctum :: sinister-cli :: umbrella dispatcher entry-point
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
`sinister <subcommand> <args...>` umbrella CLI. Mirrors jcode's `jcode <cmd>`
pattern per operator directive 2026-05-21: "our commands will be sinister then
the command".

Subcommands resolve at runtime to per-tool packages. Graceful-degrade if a
backend tool isn't installed — prints install hint and exits 2.
"""

from __future__ import annotations

import importlib
import sys
from typing import Callable

__version__ = "0.1.0"

# (subcommand, module_path, callable_name, install_hint)
SUBCOMMAND_MAP: dict[str, tuple[str, str, str]] = {
    "memory": ("forge_memory_bridge.__main__", "main", "pip install -e tools/forge-memory-bridge"),
    "swarm": ("sinister_swarm.__main__", "main", "pip install -e tools/sinister-swarm"),
    "graph": ("memory_graph_render.__main__", "main", "pip install -e tools/memory-graph-render"),
    # Stubs for forthcoming tools (graceful-error until they exist):
    "login": ("sinister_login.__main__", "main", "pip install -e tools/sinister-login (planned v0.2.0)"),
    "freeze": ("sinister_freeze.__main__", "main", "Sinister Freeze backend not yet shipped (operator-gated; see projects/sinister-freeze/PLAN.md)"),
    "term": ("term.__main__", "main", "pip install -e projects/sinister-term/source"),
    "forge": ("forge.__main__", "main", "pip install -e projects/sinister-forge/source"),
}


def _print_help() -> int:
    print(f"sinister-cli v{__version__} — umbrella dispatcher")
    print("Usage: sinister <subcommand> <args...>")
    print()
    print("Subcommands:")
    for cmd, (mod, _fn, hint) in SUBCOMMAND_MAP.items():
        installed = "✓" if _can_import(mod) else "✗"
        print(f"  {installed} sinister {cmd:<10} → {mod}")
        if installed == "✗":
            print(f"      install: {hint}")
    print()
    print("Special:")
    print("  sinister help [subcommand]    Print this help (or subcommand's help)")
    print("  sinister version              Print version of every Sinister tool installed")
    print()
    print("Operator directive 2026-05-21: 'our commands will be sinister then the command'.")
    print("Author: RKOJ-ELENO :: 2026-05-21 :: AGPL-3.0-or-later")
    return 0


def _can_import(module_path: str) -> bool:
    try:
        importlib.import_module(module_path)
        return True
    except (ImportError, ModuleNotFoundError):
        return False


def _print_version() -> int:
    print(f"sinister-cli  {__version__}")
    for cmd, (mod, _fn, _hint) in SUBCOMMAND_MAP.items():
        # Try the parent package for __version__
        parent_pkg = mod.split(".")[0]
        try:
            m = importlib.import_module(parent_pkg)
            v = getattr(m, "__version__", "?")
            print(f"  sinister-{cmd:<10}  {v}")
        except (ImportError, ModuleNotFoundError):
            print(f"  sinister-{cmd:<10}  (not installed)")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        if len(argv) > 1 and argv[1] in SUBCOMMAND_MAP:
            return _dispatch(argv[1], ["--help"])
        return _print_help()
    if argv[0] in ("--version", "version"):
        return _print_version()

    cmd = argv[0]
    if cmd not in SUBCOMMAND_MAP:
        print(f"sinister: unknown subcommand '{cmd}'", file=sys.stderr)
        print(f"Try: sinister help", file=sys.stderr)
        return 2

    return _dispatch(cmd, argv[1:])


def _dispatch(cmd: str, sub_argv: list[str]) -> int:
    module_path, fn_name, install_hint = SUBCOMMAND_MAP[cmd]
    try:
        mod = importlib.import_module(module_path)
    except (ImportError, ModuleNotFoundError) as e:
        print(f"sinister: backend tool for '{cmd}' not installed: {e}", file=sys.stderr)
        print(f"  install: {install_hint}", file=sys.stderr)
        return 2

    fn: Callable[[list[str]], int] | None = getattr(mod, fn_name, None)
    if fn is None:
        print(f"sinister: backend '{module_path}' has no callable '{fn_name}'", file=sys.stderr)
        return 2

    return fn(sub_argv) or 0


if __name__ == "__main__":
    sys.exit(main())
