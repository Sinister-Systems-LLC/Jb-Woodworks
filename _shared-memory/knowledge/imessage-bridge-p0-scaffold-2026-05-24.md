# imessage-bridge-p0-scaffold-2026-05-24

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Updated:** 2026-05-24
> **Tags:** sinister-imessage-bridge, p0, scaffold, plans, source, dashboard
> **Composes with:** sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24, no-bullshit-tested-before-claimed-doctrine-2026-05-23, sanctioned-bypasses-doctrine-2026-05-21

## Status

Updated: 2026-05-24. **Active.** P0 surface shipped + smoke-tested. Lane is fully prepared for P1 unlock the moment operator connects the Mac farm; P2/P3/P4 plans are already pre-written so each subsequent unlock is single-step.

## TL;DR

First resume on the lane delivered the entire P0 surface in one autonomous /loop iteration: 4 phase plans, Python source skeleton (21/21 pytest + 5/5 daemon curl), 6 docs/memory baselines, Next.js dashboard scaffold inheriting `dashboard-skeleton` with LetsText iOS-blue branding (per operator 16:08Z), brain entry + cross-lane brief. The only blockers remaining are operator actions (connect farm, run `npm install`).

## What landed (verified)

The `sinister-imessage-bridge` lane completed its full P0 surface in one autonomous /loop run (no operator interaction beyond the initial RESUME + /loop prompt):

| Deliverable | Path | Verb |
|---|---|---|
| 4 phase plans (P1/P2/P3/P4 acceptance criteria) | `projects/sinister-imessage-bridge/plans/*.md` | shipped |
| Python source skeleton (bridge_daemon + send_worker + recv_worker + cli + fixtures) | `projects/sinister-imessage-bridge/source/` | acceptance-tested (21/21 pytest + 5/5 daemon endpoints) |
| Canned chat.db fixture builder (real Sonoma schema + 10 sample messages across 3 handles) | `source/fixtures/make_canned_chatdb.py` | smoke-tested |
| 6 docs/memory baseline files (architecture / applescript-surface / chat-db-schema / decisions / gotchas / farm-inventory / contact-policy) | `projects/sinister-imessage-bridge/docs/` + `memory/` | shipped |
| Next.js dashboard scaffold (LetsText branding — iOS-blue iMessage-bubble accent; inheritance of dashboard-skeleton with NO accent override; 4 routes; HTTP-proxied to bridge_daemon) | `projects/sinister-imessage-bridge/dashboard/` | scaffolded (needs `npm install` + browser smoke at operator time) |
| Heartbeat + PROGRESS + 1 resume-point | `_shared-memory/heartbeats/`, `PROGRESS/`, `resume-points/Sinister iMessage Bridge/` | shipped |
| resume-point-write.ps1 mapping for the lane | `automations/resume-point-write.ps1:71-73` | shipped |

## Architecture in one paragraph

bridge_daemon (Python, on operator Windows) supervises an SSH tunnel to the farm Mac. recv_worker/tail.py (lives on the farm) uses `fswatch -1 chat.db-wal` to wake on new messages, re-polls chat.db read-only, emits JSON-per-line over SSH back to bridge_daemon. bridge_daemon ring-buffers the last 500 messages, exposes HTTP 127.0.0.1:8731 (`/status` / `/threads` / `/threads/{id}/messages` / `POST /send` / `GET /events` SSE), and posts `iMessageReceived` to sinister-bus (DBus on OS lane, cross-agent inbox fallback). send_worker/send.py wraps `osascript send.applescript` with three guards (operator_ok / per-thread allowlist / 5-second per-recipient rate-limit). Dashboard is Next.js + Tailwind 4, inheriting `tokens/globals.css` + `.lg-*` Liquid Glass classes from `projects/sinister-dashboard-skeleton/dashboard-skeleton/` via `@import` and TS path alias `@skeleton/*`; per-lane brand-lock overrides ONLY `--accent` to Sinister fleet purple `#c084fc`.

## Why this matters

P0 is normally a thin scaffold phase that just creates a folder; this run shipped P0 + every pre-farm deliverable in one go. When the operator says "farm is online", the lane needs ONLY:
1. SSH key handoff via `_vault/farm-ssh/<host>.meta.json`
2. P1 acceptance plan run (`plans/p1-readonly-acceptance.md` §0-§6)

…then P1 closes. P2-P4 plans are pre-written so each subsequent unlock is "open the matching plan, follow §2-§6, land PROGRESS row".

## Key decisions (full log at memory/decisions.md)

1. AppleScript as canonical send path (defer IMCore.framework SPI to P4+ if needed)
2. Per-thread operator OK for every send P1-P3; auto-respond is P4 + operator-curated per-rule
3. Farm-only execution (zero Apple-ID surface ever runs on operator's daily-driver or any cloud Mac)
4. SQLite URI `mode=ro` always (never take chat.db write locks)
5. bridge_daemon binds 127.0.0.1 only; Bearer-token gate on `/send` for P4 cross-host
6. Mock-friendly architecture — every Python module runs on Windows with canned chat.db; tests monkeypatch `subprocess.run` for AppleScript

## Gotchas already documented (memory/gotchas.md)

1. Rate-limit `_last_send.get(recipient, 0)` defaulted to 0 → blocked first send when `time.monotonic` is monkeypatched to 0.0. Fix: default to `float("-inf")`.
2. `from send_worker import send` shadowed the submodule via `__init__.py` re-export. Fix: drop re-exports, use explicit submodule imports.
3. `python bridge_daemon/bridge.py` can't import sibling packages. Fix: run as module — `python -m bridge_daemon.bridge`.

## Tests + smoke evidence

- `python -m pytest tests/` from `source/` → **21 passed in 1.47s**
- `python -m bridge_daemon.bridge --port 8731 --chatdb fixtures/canned-chat.db` → boots clean
- `curl /status` → 200 + correct JSON (`phase: P0-scaffold`, `chatdb_exists: true`, `farm_ssh: not_connected`)
- `curl /threads` → 200, 3 threads, 10 total messages across them
- `curl /threads/1/messages?limit=3` → 200, 3 messages
- `curl -X POST /send (no allowlist)` → 200, `{"status":"blocked","reason":"recipient not in p2_allowed","allowed_count":0}` (correct)

## What's still in-flight / queued for operator

| Item | Why blocked |
|---|---|
| P1 unlock (real farm) | operator hasn't connected the farm yet — that's THE P1 trigger |
| Dashboard browser smoke | needs `cd dashboard && npm install` (~600MB node_modules); operator-action |
| Branch discipline | working tree currently on `agent/sinister-os/m1-hardening-2026-05-24` with ~211 uncommitted files; didn't switch to `agent/sinister-imessage-bridge/p0-scaffold-2026-05-24` to avoid clobbering sibling lane work |

## Pre-existing lane signals to watch

Per Sanctum no-bullshit doctrine (rule 8): brain entry count hit 155 with this addition (signal threshold = 150). **Consolidation needed at the sanctum-master level** — flagging via inbox to sanctum.

## Related plans / docs

- `projects/sinister-imessage-bridge/plans/p1-readonly-acceptance.md` (P1 unlock walkthrough)
- `projects/sinister-imessage-bridge/plans/p2-send-acceptance.md`
- `projects/sinister-imessage-bridge/plans/p3-bridge-daemon-acceptance.md`
- `projects/sinister-imessage-bridge/plans/p4-cross-lane-acceptance.md`
- `projects/sinister-imessage-bridge/docs/architecture.md`
- `projects/sinister-imessage-bridge/docs/applescript-surface.md`
