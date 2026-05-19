> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: RKOJ fleet-state.js — single SSE source replaces 3 setInterval pollers

**Slug:** fleet-state-single-source
**First discovered:** 2026-05-19 13:30 by Sinister Sanctum master (agent D wave 2)
**Last updated:** 2026-05-19 13:30 by Sinister Sanctum master (agent D wave 2)
**Status:** fixed
**Tags:** rkoj, sse, fleet-state, polling, eventsource, single-source-of-truth, app.js, performance, ui, real-time, websockets-alternative

## Problem

RKOJ's web UI had three independent pollers each hitting different endpoints and re-rendering the same fleet data three different ways:

- `refreshSpawnedWindows` (app.js ~line 1659) — `setInterval` polling `/api/spawned-windows`
- Sessions strip refresher — separate `setInterval` polling `/api/sessions`
- Inbox view agent-list — separate `setInterval` polling `/api/inbox/<agent>`

Symptoms:
- 3 separate `setInterval` timers firing on different intervals
- Cross-pane state drift (Sessions strip showed agent X up; Inbox showed X down for 5-10s)
- Wasted bandwidth on the same data shape returned 3 ways
- Inconsistent stale-detection (each timer had its own debounce)

Plus: no real-time push channel for daemon-liveness heartbeats. The new `_shared-memory/heartbeats/*.beat` files (sanctum-console / sinister-vault / rkoj) had no UI surface.

## Why it happens

Organic UI growth. Each pane was built in isolation by a different sprint; each one introduced its own poller because that was the path of least resistance. The HR-B audit at PROGRESS log 2026-05-19 11:17 ("Redundancies to consolidate" section) explicitly flagged this as item #1.

## Fix or workaround

Three-part fix shipped 2026-05-19 13:30:

1. **Server side — new SSE endpoint `GET /api/fleet-stream`** in `automations/window-manager/server.py`. Aggregates:
   - Heartbeats from `_shared-memory/heartbeats/*.beat` (alive = mtime < 120s)
   - Spawned-windows list (from `_shared-memory/spawned-windows.jsonl`)
   - Sessions snapshot (via `_compute_sessions_snapshot()` — also used by REST `/api/sessions`)
   - Inbox cursors (last 5 messages per online agent from `_shared-memory/_inbox/<agent>/messages.jsonl`)
   - 5-second cadence + immediate first paint + 15-second keep-alive `: ping\n\n` comments
   - Token auth via the existing middleware (token in query string since EventSource can't send Authorization headers)

2. **Server side — new endpoint `GET /api/fleet/heartbeats`** in `server.py`. Single-shot read of the heartbeat files for REST clients (curl, scripted probes). Returns JSON with per-daemon `mtime_iso`, `age_s`, `alive`, `last_line`. Used by the daemon-liveness dot row in the UI.

3. **Client side — new `web/fleet-state.js`** (189 LOC, IIFE module). Public surface:
   ```js
   window.FleetState = {
     subscribe(cb)   // returns unsubscribe fn; cb gets every snapshot update
     onStatus(cb)    // fires on connect/disconnect/stale events
     getSnapshot()   // current cached snapshot (synchronous)
     connect()       // idempotent; starts EventSource
     disconnect()    // closes EventSource cleanly
   };
   ```
   - Single shared `EventSource('/api/fleet-stream?t=<token>')` across all subscribers
   - Exponential backoff on disconnect: 1s → 2s → 4s → 8s → max 30s
   - Stale guard: if no event received in 30s, snapshot flagged `{stale: true}` + reconnect
   - Auto-connect on `DOMContentLoaded`
   - Token sourced from `localStorage.getItem('sinister_token')`

4. **Client side — app.js refactor.** The 3 `setInterval` calls were REPLACED (not commented out) with `FleetState.subscribe` callbacks. Legacy `fetch` fallback retained for the case where `window.FleetState` is undefined (defensive). The refresh functions (`refreshSpawnedWindows`, `refreshAgentsSessionsStrip`, `PaneRegistry.inbox.refresh`) now accept an optional snapshot-override argument and fall back to fetch only when not pre-populated.

5. **New daemon-liveness panel.** Three colored dots in the windows bar (sanctum-console / sinister-vault / rkoj). Green if `alive`, red if stale. Click a dot → toast with the last `.beat` line content. Sourced from FleetState snapshot — no separate poll.

```bash
# Smoke verify:
curl -N "http://127.0.0.1:5077/api/fleet-stream?t=<token>" | head -20
# -> event: fleet-update
# -> data: {"heartbeats": {...}, "windows": [...], "sessions": [...], "inbox_cursors": {...}}
# -> (5s pause)
# -> event: fleet-update
# -> ...
```

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 13:30 by Sinister Sanctum master (agent D wave 2)
Shipped. Verification: `python -c "import ast; ast.parse(open('server.py').read())"` OK; `node --check web/app.js` OK; `node --check web/fleet-state.js` OK. Heartbeats helper smoke-tested standalone against `sinister-vault.beat` — returned `alive=false, age_s=916, last_line="2026-05-19T13:13:19+00:00 pid=58024 port=5079 uptime=97"` (vault daemon not currently running on canonical 5078 because scheduled-task registration was blocked by sandbox; will go green once operator runs `wire-everything.ps1`).

The `// WINDOW_TOOLS / AGENT_VIEWS (old)` comment cluster flagged in the audit was already absent — agent E's codex refactor likely removed it earlier in the day.

## Related topics

- [rkoj-workbench-architecture](./rkoj-workbench-architecture.md)
- [rkoj-hot-reload-pattern](./rkoj-hot-reload-pattern.md)
- [daemon-liveness-heartbeats](./daemon-liveness-heartbeats.md)
- [cross-agent-coordination](./cross-agent-coordination.md)
