# sinister-swarm

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Status:** v0.1.0 — stdlib-only multi-agent coordination layer over disk-first `_shared-memory/`
> **Parity:** jcode-swarm semantics — DM / broadcast / spawn / file-watch / mark-done + wait-for / hive-status

## What it is

The fleet's coordination plane. Every Sinister agent (Sanctum, Forge, Term, Panel, Kernel-APK, RKOJ, future Freeze) uses the same disk surface for cross-agent comms; this package wraps that surface into a clean Python API + a stdalone `sinister-swarm <op>` CLI + composes under the umbrella `sinister swarm <op>` from `tools/sinister-cli/`.

## Surface

```python
from sinister_swarm import (
    dm, broadcast, spawn_agent, list_active,
    watch_file, mark_done, wait_for, detect_my_slug,
)

dm("forge", "found a regression in app.py", subject="P1 regression")
broadcast("fleet pause in 5 min", tag="[PAUSE]")
spawn_agent("sinister-freeze", mode="resume", agent_name="freeze-bootstrap", headless=True)
active = list_active(stale_minutes=15)   # [{slug, mtime_utc, age_seconds, ...}, ...]
h = watch_file("projects/sinister-forge/source/forge/app.py", on_change=print, blocking=True)
mark_done("R7", result="shipped")
rec = wait_for("forge", "R8", timeout_s=300)   # blocks until forge marks R8 done
```

## CLI

```
sinister-swarm dm forge "found a regression"
sinister-swarm broadcast "fleet pause in 5 min"
sinister-swarm spawn --project sinister-freeze --mode resume --no-notepad
sinister-swarm list --stale-minutes 15
sinister-swarm watch --path projects/sinister-forge/source/forge/app.py --blocking
sinister-swarm mark-done R7 --result shipped
sinister-swarm wait-for forge R8 --timeout 300
sinister-swarm hive-status
sinister-swarm whoami
```

Or via the umbrella: `sinister swarm <op>`.

## Disk contracts

| Path | Purpose |
|---|---|
| `_shared-memory/inbox/<slug>/<ts>-*.json` | DM + broadcast drops |
| `_shared-memory/heartbeats/<slug>.{json,beat}` | liveness signal (mtime = lastBeat) |
| `_shared-memory/swarm-spawned/<ts>-<project>-by-<slug>.json` | spawn audit log |
| `_shared-memory/swarm-watch/<my-slug>/<hash>.json` | per-watcher file state |
| `_shared-memory/swarm-status/<ts>-<from>-<task>.json` | mark-done / wait-for ledger |
| `_shared-memory/swarm-mcp-cache.json` | optional MCP hive_id cache (Ruflo) |

## Identity resolution

`detect_my_slug()` reads `SINISTER_AGENT_SLUG` env var → `SINISTER_AGENT_NAME` (slugified) → fallback `"unknown-caller"`. Launcher (`automations/start-sinister-session.ps1`) sets these.

## Composes with

- `tools/sinister-cli/` — umbrella `sinister swarm <op>` dispatch
- `tools/forge-memory-bridge/` — orthogonal lane (`sinister memory <op>`)
- `projects/sinister-forge/source/forge/bridge/registry.py` — Forge's REST/SSE bridge already wraps `subprocess.Popen` per-agent; this package's `spawn_agent` is the launcher-driven counterpart (terminal sessions, not subprocess pumps)
- `automations/start-sinister-session.ps1` — `spawn_agent` shells out to this
- `_shared-memory/knowledge/multi-agent-branch-contention-isolation-pattern.md` — `watch_file` enriches each change event with `current_active_agents` to surface contention live
- Ruflo MCP hive-mind_* tools — `mcp_broadcast` / `mcp_hive_status` are stubs in v0.1.0; v0.2.0 wires the real MCP calls when available

## Non-goals (v0.1.0)

- No conflict auto-resolution (jcode's headless mode) — operator-decided per Sanctum doctrine
- No sub-swarm hierarchies (coordinator → workers) — Forge bridge handles subprocess-style; CLI version stays terminal-session-style
- No in-process MCP calls — relies on disk-first; MCP fast-path is opt-in via Ruflo when available
