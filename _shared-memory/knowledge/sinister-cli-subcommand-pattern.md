<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# sinister-cli subcommand pattern

> **Author:** RKOJ-ELENO :: 2026-05-21
> **First instance:** `tools/sinister-cli/` umbrella (2026-05-21T12:28Z, commit `f3bba4b`)
> **Reinforced by:** `tools/sinister-login/` v0.1.0 (commit `be1a821`)

## TL;DR

Every `sinister <subcommand>` tool follows the same 5-file Python layout + 1 dispatcher row. The umbrella resolves at runtime; no static link required. New tools install with `pip install -e` and immediately become callable through both the direct entry-point (`sinister-X`) and the umbrella (`sinister X ...`).

## The contract

A backing package `sinister_<slug>` (or any module name) exposes:

```python
# sinister_<slug>/__main__.py
def main(argv: list[str] | None = None) -> int:
    ...
```

That single `main(argv) -> int` callable is what the dispatcher resolves. Everything else (argparse, JSON output, --version) is internal to the package.

## The 5-file layout

```
tools/sinister-<slug>/
├── pyproject.toml              # setuptools build, AGPL-3.0-or-later, entry-point sinister-<slug>
├── README.md                   # surface + install + CLI examples + design constraints
├── sinister_<slug>/
│   ├── __init__.py             # __version__ + re-export API surface
│   ├── __main__.py             # CLI dispatch (argparse subparsers) + main(argv) -> int
│   ├── api.py                  # programmatic API (importable from other tools)
│   └── <domain>.py             # one or more domain modules (providers.py, schedulers.py, etc)
└── tests/
    └── test_<slug>.py          # stdlib unittest only (no pytest dep); 15-25 tests
```

## The dispatcher row

In `tools/sinister-cli/sinister_cli/__main__.py` `SUBCOMMAND_MAP`:

```python
"<slug>": (
    "<one-line description shown in `sinister help`>",
    "sinister_<slug>.__main__", "main",
    "pip install -e \"D:/Sinister Sanctum/tools/sinister-<slug>\"",
),
```

Then `sinister <slug> [args]` works. `sinister version` enumerates it. `sinister help <slug>` shows the install hint.

## Why this works

1. **Zero static link** — the umbrella `importlib.import_module()`s the backing module at call time. Adding a new tool doesn't touch the umbrella's wheel; just edit the dict + ship.
2. **Graceful missing-backend** — uninstalled tools print the install hint and exit 2 instead of crashing. `sinister-cli version` reports `not installed (sinister_X)` for the unmounted ones.
3. **Stdlib-first** — every tool can be stdlib-only. No transitive deps creep into the umbrella.
4. **Test isolation** — each tool runs its own `unittest discover`; the umbrella has no test responsibility.
5. **Branding consistency** — `sinister <command>` is the operator's verbatim 2026-05-21 directive. Each subcommand inherits the convention without re-deciding.

## Concrete examples shipped

| Tool | Package | Install path | API surface | Tests |
|---|---|---|---|---|
| `sinister memory` | `forge_memory_bridge` | `tools/forge-memory-bridge/` v0.1.1 | `write/recall/list/consolidate` | smoke |
| `sinister swarm` | `sinister_swarm` | `tools/sinister-swarm/` v0.1.0 | `dm/broadcast/spawn/list/watch/done/wait` | 7 |
| `sinister graph` | `memory_graph_render` | `tools/memory-graph-render/` v0.1.0 | `render(graph_json) -> PNG` | smoke |
| `sinister login` | `sinister_login` | `tools/sinister-login/` v0.1.0 | `list_providers/status_all/resolve_active/doctor/print_env_for/add_to_envfile` | 21 |

## Anti-patterns

- ❌ **In-umbrella implementation** — never put a subcommand's domain logic inside `sinister-cli/`. The umbrella is a dispatcher, not a tool.
- ❌ **Cross-tool imports without explicit dependency** — if `sinister X` calls `sinister Y` internally, declare it in `pyproject.toml` `dependencies = [...]`. Never assume.
- ❌ **Adding heavy deps to a single tool** — keep stdlib-first. If you NEED a third-party dep (e.g. `requests` for OAuth flows), make it an `[project.optional-dependencies]` extra so the umbrella's `import_module` lazy-load doesn't fail when the extra is missing.
- ❌ **Hidden side effects on import** — `__init__.py` re-exports + `__version__` only. NEVER spawn threads, open sockets, or write files at import time.
- ❌ **Skipping the README** — every tool's README is the contract. The umbrella's `help <slug>` shows the install hint; the README owns the surface.

## Composes-with

- `automations/agent-host-routing.md` — which provider serves which task class (sinister-login extends row 1b)
- `_shared-memory/knowledge/jcode-feature-matrix.md` — capability inventory; every shipped tool flips a row
- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md` — the meta-doctrine; this pattern is its CLI specialization
- `_shared-memory/knowledge/sinister-swarm-jcode-parity-pattern.md` — sibling pattern for `sinister swarm`
- `_shared-memory/knowledge/sinister-cli-naming-convention.md` — naming rule "sinister then the command"

## Update protocol

When you ship a new sinister-X tool:

1. Follow the 5-file layout above.
2. Add a row to `tools/sinister-cli/sinister_cli/__main__.py` `SUBCOMMAND_MAP`.
3. Run `pip install -e` from the new tool's directory.
4. Verify with: `sinister version` (your tool appears), `sinister help <slug>` (hint correct), `sinister <slug> --help` (your argparse shows).
5. Flip the row in `_shared-memory/knowledge/jcode-feature-matrix.md` to ✅ shipped + commit hash.
6. (Optional) extend `automations/agent-host-routing.md` if your tool affects routing decisions.

## Next planned tools (operator-implicit jcode parity gaps)

- `sinister usage` — token quota check (`jcode usage --json` parity); small lift
- `sinister serve` — background daemon (`jcode serve`); medium lift
- `sinister connect` — daemon client (`jcode connect`); paired with serve
- `sinister replay` — session replay incl. video (`jcode replay <session>`); heavy lift
- `sinister model list` — list available models per configured provider; small lift
- `sinister ambient {status,log,trigger,stop}` — background loop control; small lift each
- `sinister setup-hotkey` — global hotkey (Alt+;) install; Windows-side; small lift
