# sinister-swarm

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Status:** v0.1.0 — disk-first swarm primitives; jcode-swarm feature parity
> **Operator directives:**
> - *"i want all systems in jcode features in our system like swarm"* (2026-05-21 with jcode swarm screenshot)
> - *"our commands will be sinister then the command"* (2026-05-21 with jcode login-flows screenshot)
> - *"everything is going to connect to everything im a forver expanding modular approach"* (2026-05-21T11:15Z)

## What it is

**jcode-swarm feature parity** for the Sinister fleet. Wraps the existing primitives (Ruflo MCP `hive-mind_*`, Sanctum disk-inbox at `_shared-memory/inbox/<slug>/`, Forge bridge SSE at `:5078`, `start-sinister-session.ps1` spawn) into a single Python API + CLI that any agent in the fleet can use.

jcode swarm features (per the screenshot) → our equivalents:

| jcode swarm capability | sinister-swarm equivalent | Backend |
|---|---|---|
| Spawn 2+ agents in same repo | `spawn_agent(project, mode='resume', ...)` | shells `start-sinister-session.ps1 -Project X -Headless` |
| Server-managed native collab | `_shared-memory/swarm-spawned/<UTC>.json` ledger + Ruflo hive-mind | disk + MCP |
| Code-shifting-under-its-feet detection | `watch_file(path, on_change=callback)` | mtime + content-hash poll; agent-id from author-line |
| DM single agent | `dm(to_slug, message, tag='[MSG]')` | `_shared-memory/inbox/<to_slug>/<UTC>-msg-from-<from-slug>.json` |
| Broadcast to all agents | `broadcast(message, tag='[BROADCAST]')` | drops in every active-heartbeat inbox + Ruflo `hive-mind_broadcast` |
| Spawn-your-own-swarm tool | `spawn_agent(...)` callable from inside any agent | shells launcher |
| Coordinator/worker pattern | use `mark_done(task)` from worker, `wait_for(slug, task)` from coordinator | disk-status |
| Auto-managed groups + completion | `_shared-memory/swarm-status/<UTC>-<from>-<task>.json` append-only | disk |
| Headless OR headed | `spawn_agent(headless=True)` adds `-NoNotepad` flag | disk |

## Quickstart

```bash
cd "D:/Sinister Sanctum/tools/sinister-swarm"
pip install -e .

# CLI (via direct entry-point OR via umbrella `sinister swarm ...`)
sinister-swarm dm forge "found a bug in panes/picker.py line 47"
sinister-swarm broadcast "moving session-contracts.md in 2 min — pause shared edits"
sinister-swarm spawn --project sinister-freeze --mode resume --headless
sinister-swarm list --stale-minutes 15
sinister-swarm watch --path automations/start-sinister-session.ps1
sinister-swarm mark-done R8 --result "mermaid render parity shipped"

# Python (any sibling agent imports)
from sinister_swarm import dm, broadcast, spawn_agent, list_active, watch_file, mark_done, wait_for

dm("forge", "PH16 memory is broken, see _shared-memory/inbox/sanctum/...")
broadcast("Sinister Sanctum auto-push in 5 min; commit your work")
who = list_active(stale_minutes=15)
spawn_agent("sinister-freeze", mode="resume", headless=True, focus="MVP-PH1-daily-brief")
watch_file("automations/start-sinister-session.ps1", on_change=lambda diff: print(f"sibling edited: {diff[:120]}"))
mark_done("R10-multi-provider-routing", result="agent-host-routing.md shipped")
hits = wait_for(slug="forge", task="R8", timeout_s=300)
```

## Public API (`sinister_swarm`)

| Function | Signature | Returns |
|---|---|---|
| `dm` | `dm(to_slug: str, message: str \| dict, *, tag: str = '[MSG]', subject: str \| None = None, from_slug: str \| None = None) -> dict` | the dropped inbox record |
| `broadcast` | `broadcast(message: str \| dict, *, tag: str = '[BROADCAST]', subject: str \| None = None, exclude: list[str] = [], use_mcp: bool = True) -> list[dict]` | one record per recipient |
| `spawn_agent` | `spawn_agent(project: str, *, mode: str = 'resume', agent_name: str \| None = None, accent: str = 'purple', headless: bool = True, focus: str \| None = None) -> dict` | spawn record (pid, cwd, project, mode, ts_utc) |
| `list_active` | `list_active(stale_minutes: int = 15) -> list[dict]` | one entry per heartbeat with mtime < stale_minutes |
| `watch_file` | `watch_file(path: str \| Path, *, on_change: Callable \| None = None, poll_seconds: float = 2.0, blocking: bool = False) -> WatchHandle` | watcher handle (call `.stop()`); when blocking=True, runs forever |
| `mark_done` | `mark_done(task_label: str, *, result: str \| dict \| None = None, from_slug: str \| None = None) -> dict` | the status record |
| `wait_for` | `wait_for(slug: str, task: str, *, timeout_s: float = 300, poll_seconds: float = 2.0) -> dict \| None` | the status record when it lands, or None on timeout |
| `mcp_broadcast` | `mcp_broadcast(message: str, *, priority: str = 'normal') -> dict` | Ruflo hive-mind_broadcast result if MCP loaded, else stub |
| `mcp_hive_status` | `mcp_hive_status() -> dict` | hive id + topology + queen + peer count |

## On-disk surfaces

```
_shared-memory/
├── inbox/<slug>/                       # DM destination (per-slug folder)
│   └── <UTC>-msg-from-<from-slug>.json
├── swarm-spawned/                      # spawn ledger (every spawn_agent call)
│   └── <UTC>-<project>-by-<from-slug>.json
├── swarm-status/                       # mark_done log (append-only per task)
│   └── <UTC>-<from-slug>-<task>.json
├── swarm-watch/                        # watch_file callback state
│   └── <slug>/<file-hash>.json         # last-seen mtime + content_hash per watcher
└── heartbeats/                         # presence (existing)
    └── <slug>.json
```

## "Code-shifting-under-its-feet" semantics

`watch_file(path)` records the file's `(mtime, sha256, last_seen_utc, my_slug)` in `_shared-memory/swarm-watch/<my_slug>/<file-hash>.json`. Every `poll_seconds`:

1. Read current file mtime + sha256
2. If unchanged → continue
3. If changed → look up the latest commit touching this file (`git log -1 --format='%an %ae %s' -- <path>`)
4. Look up the heartbeat of the author-slug (if author is another sibling)
5. Fire `on_change(diff_summary)` callback with:
   - `path`, `old_hash`, `new_hash`, `mtime_delta_s`
   - `last_commit_author`, `last_commit_subject`
   - `current_active_agents` (from `list_active`)
6. Update the stored state to the new hash

That's the "agent B notified when agent A edits a file B has read" loop — jcode does it server-side; we do it disk-poll-side per modular doctrine (no server required; works without MCP).

## Composes with

- **Ruflo MCP** `hive-mind_init` / `hive-mind_broadcast` / `swarm_status` / `coordination_*` — MCP fast-path for live cross-process pub-sub
- **`tools/forge-memory-bridge/`** — swarm decisions + completion-statuses can also be written to `forge-memory` for semantic recall
- **`automations/start-sinister-session.ps1`** — `spawn_agent()` shells out to it (`-Project` + `-Mode` + `-NoNotepad` for headless)
- **`projects/sinister-forge/source/forge/bridge/`** — Forge bridge SSE at `:5078` can push swarm events to mobile/Claw
- **`_shared-memory/inbox/<slug>/`** — disk DM channel (canonical existing pattern)
- **`_shared-memory/cross-agent/`** — broadcast threads (canonical existing pattern)
- **`_shared-memory/heartbeats/<slug>.json`** — presence (canonical existing pattern)
- **`_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md`** — disk-first MCP-optional bound by this doctrine
- **`_shared-memory/knowledge/sibling-active-launch-coordination-pattern.md`** — the doctrine this implements
- **`_shared-memory/knowledge/verify-head-before-commit-multi-agent.md`** (Term-authored) — watch_file() can detect the wayward-checkout pattern as a special case

## Umbrella CLI

The umbrella `sinister` command (from `tools/sinister-cli/`) wraps this tool's `sinister-swarm` entry-point as:

```bash
sinister swarm dm forge "found a bug"
sinister swarm broadcast "fleet pause incoming"
sinister swarm spawn --project sinister-freeze
sinister swarm watch --path foo.py
```

Per operator: *"our commands will be sinister then the command"*.

## What we deliberately did NOT do

- **No central server** (jcode does server-mediated swarm; we do disk-mediated for sovereignty + no-single-point-of-failure)
- **No telemetry** (per canonical doctrine)
- **No auto-conflict-resolution** (we surface the conflict; agent decides; canonical-11 reversibility)
- **No agent-impersonation** (every dm/broadcast carries `from_slug` derived from heartbeat — agent can't forge a DM "from" another agent without write access to that agent's heartbeat file)

## Status

🚧 v0.1.0 ships disk-first surfaces + Python API + sinister-swarm CLI + sinister-cli umbrella subcommand. MCP fast-path detected at runtime when Ruflo loaded. Forge-bridge SSE push deferred to v0.2.0 (waits for Forge bridge stability).
