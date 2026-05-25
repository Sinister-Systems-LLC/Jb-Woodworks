<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: RKOJ fleet-state — SSE consolidation of spawned/sessions/progress

**Slug:** rkoj-fleet-state-sse
**First discovered:** 2026-05-19 13:30 by Sinister Sanctum master agent
**Last updated:** 2026-05-19 13:30 by Sinister Sanctum master agent
**Status:** fixed
**Tags:** sse, eventsource, fleet-state, rkoj, frontend, consolidation, hr-b

## Problem

`web/app.js` had three independent polling loops rendering overlapping views of
the same fleet state:

1. `setInterval(refreshSpawnedWindows, 15000)` — polled `/api/spawned-windows` every 15s
2. `setInterval(refreshAgentsSessionsStrip, REFRESH_MS)` — polled `/api/sessions`
3. `setInterval(refreshActivityFeed, REFRESH_MS)` — polled `/api/progress` + `/api/operator-requests`

HR-B audit (PROGRESS 2026-05-19 11:17) recommendation #4: collapse to a single
SSE stream so views render coherently + the poll rate drops.

## Why it happens

Each pane (Spawned-Windows control bar, Sessions strip, Inbox view) was authored
independently. The fleet-state view they all needed was the same, but the
authors reached for `setInterval` because it's the obvious primitive. Result:
3× the network chatter, 3× the chances of view skew when one fetch lagged.

## Fix or workaround

**Tested 2026-05-19 (Phase 1.2 of complete-everything sweep).**

### Backend (`server.py`)

- `/api/fleet-stream` — SSE endpoint, emits `event: fleet-update` every
  `FLEET_TICK_INTERVAL_S` (5s) with consolidated snapshot.
- `/api/fleet-snapshot` — one-shot REST view of the same shape (for cold-start
  paint before SSE event 1 arrives).
- `_compute_fleet_snapshot()` — gathers `spawned`, `sessions`, `progress[]`,
  `operator_requests_pending`, `heartbeats{}`. Best-effort: any helper that
  throws contributes an empty slot, never kills the snapshot.
- `_fleet_state_loop()` — drives the per-client `asyncio.Queue` fan-out. Slow
  consumers (queue full) are dropped, never blocking the publisher.

### Frontend (`web/fleet-state.js`)

`window.FleetState.subscribe((snap) => { ... })` — one shared EventSource;
auto-reconnect with 1s→30s exponential backoff; stale-marking after 30s of
silence; cached snapshot returned to late subscribers via cb(_snapshot).

### Wire-up in `web/app.js`

```javascript
// 3 setIntervals retired:
// setInterval(refreshSpawnedWindows, 15000);                              // -> FleetState
// (sessions branch inside main REFRESH_MS setInterval removed)            // -> FleetState
// (refreshActivityFeed branch kept; snapshot doesn't carry op-requests rows)

window.FleetState.subscribe((snap) => {
    if (snap && Array.isArray(snap.spawned)) refreshSpawnedWindows(snap.spawned);
    if (state.activeTab === 'agents') {
        const pane = $('skel-agents');
        if (pane && Array.isArray(snap.sessions)) {
            refreshAgentsSessionsStrip(pane, snap.sessions);
        }
    }
});
```

The `refresh*` functions accept an optional override array — when given, they
render directly from the snapshot; when omitted, they fall back to a direct
fetch (for popouts, manual reload).

## Event semantics

- `event: fleet-update` — payload `{ts, spawned[], sessions[], progress[], operator_requests_pending, heartbeats{}}`. Both the connect-time `hello` and per-tick events use this name (one client listener handles both).
- Keepalive — server emits `: keepalive\n\n` SSE comment if the queue has been silent for 20s; defeats idle-proxy buffering (Edge WebView2, some corporate proxies).

## Snapshot shape

```json
{
  "ts": "2026-05-19T13:30:00+00:00",
  "spawned": [...],
  "sessions": [...],
  "progress": [{"ts": "...", "agent": "...", "title": "...", "status": "..."}, ...],
  "operator_requests_pending": 4,
  "heartbeats": {
    "rkoj": {"slug": "rkoj", "file": "rkoj-runtime.beat", "exists": true, "alive": true, "age_s": 12, "last_line": "..."},
    "sinister-vault": {...},
    "sanctum-console": {...}
  }
}
```

## Why SSE (not WebSocket)

- One-direction (server→client): SSE fits the shape exactly.
- HTTP/1.1 + plain text: trivial proxy traversal, no upgrade handshake.
- Built-in EventSource auto-reconnect (though we layer our own backoff for finer feedback).
- ~50 LOC backend vs ~200 LOC for a WebSocket equivalent.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 13:30 by Sinister Sanctum master agent
First landing. Aligned `snap.windows` vs `snap.spawned` field names (a prior
staging branch used `windows`; server now emits `spawned` to match the Python
helper `_read_spawned_windows()`).

## Related topics

- [runtime-liveness-heartbeats](./runtime-liveness-heartbeats.md) — the `heartbeats` field is sourced from these
- [rkoj-hot-reload-pattern](./rkoj-hot-reload-pattern.md) — parallel SSE channel for file-change events; same `_sse_subscribers` shape mirrored here
