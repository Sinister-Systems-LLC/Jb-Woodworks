# Sinister Swarm — jcode-swarm Feature Parity Pattern

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Operator directive (verbatim 2026-05-21):** *"i want all systems in jcode features in our system like swarm"* (with jcode "Swarm" feature screenshot — code-shifting detection, DM, broadcast, spawn-your-own-swarm)
> **Implements:** jcode-feature-matrix.md row 16 + new rows
> **Status:** doctrine, implemented (v0.1.0 ships this turn)

## The jcode swarm features (per screenshot)

1. Spawn 2+ agents in same repo; server manages native collab
2. **Code-shifting-under-its-feet detection** — agent B notified when agent A edits a file B has read; B can ignore or check diff
3. DM single agent, OR broadcast to all-in-repo
4. Spawn-your-own-swarm — agents spawn workers; coordinator/worker pattern
5. Groups + messaging channels + completion-statuses auto-managed
6. Headless OR headed

## How we re-implement (AGPL-3.0; no jcode code copied; design pattern only)

### Architectural delta

| jcode | sinister-swarm |
|---|---|
| Central server mediates | Disk-first surfaces (`_shared-memory/...`) + optional Ruflo MCP fast-path |
| Native pub/sub | Inbox-poll + Ruflo `hive-mind_broadcast` when present |
| Multi-process Rust harness | Python `subprocess.Popen` shelling `start-sinister-session.ps1` |
| MIT license | AGPL-3.0-or-later + attribution in NOTICES |
| Telemetry-by-default | Local-first; zero telemetry per data-sovereignty doctrine |

### The 7 public API surfaces

| Function | jcode equivalent | Backend |
|---|---|---|
| `dm(to_slug, msg)` | swarm DM | `_shared-memory/inbox/<slug>/<UTC>-msg-from-<from>.json` |
| `broadcast(msg)` | swarm broadcast | drop into every active heartbeat's inbox + Ruflo `hive-mind_broadcast` |
| `spawn_agent(project, ...)` | swarm spawn | `subprocess.Popen` on `start-sinister-session.ps1 -Project X -NoNotepad` |
| `list_active(stale_minutes=15)` | swarm members | scan `_shared-memory/heartbeats/*.json` |
| `watch_file(path, on_change=cb)` | code-shifting-under-its-feet | sha256 + mtime poll, augmented with `git log` author lookup |
| `mark_done(task, result)` | completion status | `_shared-memory/swarm-status/<UTC>-<from>-<task>.json` append-only |
| `wait_for(slug, task, timeout)` | coordinator wait-for-worker | poll status dir until matching record lands or timeout |

### "Code-shifting-under-its-feet" — disk-poll architecture

jcode does this server-side (server holds the watched-file set and pushes via WebSocket). Our disk-poll re-implementation:

1. `watch_file(path)` records baseline `(sha256, mtime, my_slug, ts_utc)` to `_shared-memory/swarm-watch/<my_slug>/<file-hash>.json`
2. Every `poll_seconds`, watcher re-reads file, compares hash + mtime
3. On change: looks up last commit touching that file (`git log -1 --format='%an|%s' -- <path>`)
4. Augments event with `current_active_agents` (from `list_active()`)
5. Fires `on_change(event)` callback with full context
6. Updates baseline so subsequent polls only fire on NEW changes

Trade-off: 2-second polling lag vs jcode's server-push instant. But no server required; works without MCP; survives across process restarts (state persists on disk).

### Coordinator/worker pattern walkthrough

```python
# Coordinator agent
from sinister_swarm import spawn_agent, wait_for

# Spawn 3 worker agents in parallel
for proj in ["snap-emulator-api", "tiktok-emulator-api", "bumble-emulator-api"]:
    spawn_agent(proj, mode="audit", focus="ship per-project AUP report", headless=True)

# Wait for all 3 to finish their task
for proj in ["snap-emulator-api", "tiktok-emulator-api", "bumble-emulator-api"]:
    slug = proj.replace("-emulator-api", "-emu")  # naming convention
    result = wait_for(slug, "audit-shipped", timeout_s=900)
    print(f"{slug}: {result['result'] if result else 'TIMEOUT'}")

# Worker agent (inside each spawned session)
from sinister_swarm import mark_done
# ...do the audit work...
mark_done("audit-shipped", result={"findings": 7, "operator_actions_open": 2})
```

## Composes with

- **Ruflo MCP** `hive-mind_init` / `hive-mind_broadcast` / `swarm_status` — when loaded, fast-path
- **`tools/forge-memory-bridge/`** — store swarm decisions + completion-statuses as recallable memories
- **`automations/start-sinister-session.ps1`** — `spawn_agent()` shells out (`-NoNotepad` for headless v0.1.0; full headless flag is v0.2.0 launcher work)
- **`projects/sinister-forge/source/forge/bridge/`** — Forge bridge SSE at `:5078` can push swarm events to Claw mobile (v0.2.0)
- **`_shared-memory/inbox/<slug>/`** — canonical disk DM channel
- **`_shared-memory/cross-agent/`** — canonical thread store
- **`_shared-memory/heartbeats/<slug>.json`** — presence
- **`_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md`** — disk-first + MCP-optional binding
- **`_shared-memory/knowledge/sibling-active-launch-coordination-pattern.md`** — coordination doctrine this implements
- **`_shared-memory/knowledge/verify-head-before-commit-multi-agent.md`** (Term-authored) — `watch_file()` can detect the wayward-checkout pattern as a special case (git index changes → file mtime updates)
- **`_shared-memory/knowledge/sinister-cli-naming-convention.md`** (this session) — `sinister swarm <subcmd>` is the operator UX
- **`_shared-memory/knowledge/jcode-feature-matrix.md`** rows 16 (swarm-mode), 27 (scrollable-tiling/niri), 28 (sinister-mermaid-render fork)

## What we deliberately did NOT do

- **No central server** — disk-first; sovereignty over performance trade-off
- **No auto-conflict-resolution** — surface conflict, agent decides (canonical-11 reversibility)
- **No agent-impersonation** — `from_slug` derives from heartbeat; agent can't forge a DM "from" another agent without writing that agent's heartbeat
- **No telemetry / no phone-home** — local only

## When to revisit

- Disk-poll lag (2s) becomes a real bottleneck → move to `watchdog` inotify/ReadDirectoryChangesW (still local, no server)
- Multi-host fleet → swap disk root to Sinister Vault sync layer
- Ruflo MCP federation lands → wire `mcp_broadcast` to the federated path
- Operator authorizes spawn-without-headless → add full UI surface in launcher

## Status

🚧 v0.1.0 (this turn): disk-first API + 7 tests + sinister-swarm CLI + sinister-cli umbrella subcommand. MCP fast-path stubbed (Ruflo hive-mind detection at runtime).
