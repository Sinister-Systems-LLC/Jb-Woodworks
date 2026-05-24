# Architecture — Sinister iMessage Bridge

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** P0 (scaffold). Diagrams reflect the target end-state; P0 ships only the stub layer.

## Topology

```
                      operator's Windows / Linux                            farm Mac
                      ──────────────────────────                            ─────────
   ┌──────────────────┐   ┌─────────────────────┐    SSH     ┌──────────────────────────┐
   │  dashboard UI    │──▶│  bridge_daemon       │───────────│  recv_worker/tail.py     │
   │  (Next.js)       │   │  HTTP 127.0.0.1:8731 │           │  (fswatch chat.db-wal)   │
   │  port 3000       │   │  + send_queue +      │           │  emits JSON-per-line     │
   └──────────────────┘   │  policy enforcement  │   SSH     └──────────────────────────┘
        │                  │                      │───────────┐
        │ SSE /events      │                      │           │
        ▼                  │                      │           ▼
   ┌──────────────────┐   │                      │           ┌──────────────────────────┐
   │  operator        │   │                      │           │  send.applescript        │
   │  attention       │   │                      │           │  (osascript per-send)    │
   └──────────────────┘   └─────┬────────────────┘           └──────────────────────────┘
                                │
                                ▼
                          ┌──────────────────────┐
                          │  sinister-bus        │
                          │  org.sinister.Bus.*  │
                          │  (DBus on OS lane;   │
                          │   inbox fallback)    │
                          └──────────────────────┘
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
              vault         mind          forge
              backup        graph         suggestions
```

## Process inventory

| Process | Host | Lifecycle | Lifetime |
|---|---|---|---|
| `dashboard UI` (Next.js dev server) | operator Win/Linux | one per operator session | until tab closes |
| `bridge_daemon` (Python) | operator Win/Linux | always-on (systemd / NSSM / task scheduler) | weeks |
| `recv_worker/tail.py` | farm Mac | spawned by bridge_daemon via SSH | until SSH drops; bridge_daemon restarts |
| `send.applescript` | farm Mac | one-shot per send | <2s |

Only `dashboard UI` and `bridge_daemon` live on the operator's side. Everything iMessage-touching lives ON the farm. This is binding (per lane CLAUDE.md hard rule §1: "Farm-only execution").

## Data flow (inbound)

1. iPhone delivers iMessage → `chat.db-wal` modified on the farm.
2. `fswatch -1` on farm wakes up `tail.py`.
3. `tail.py` runs the P3 §1 SQL against `chat.db` (read-only), emits JSON for any ROWID > last seen.
4. JSON travels back to operator Win/Linux over the existing SSH pipe.
5. `bridge_daemon.dispatch_inbound` runs three things in order:
   - Appends to `state.recent` (in-memory ring, cap 500)
   - Emits to all dashboard SSE subscribers
   - Posts `iMessageReceived` to sinister-bus (DBus on OS lane / inbox fallback)
6. Subscribers (vault / mind / forge / showmasters / sanctum) each get their own copy via bus.

## Data flow (outbound)

1. Operator clicks "Send" in dashboard (or `imessage send` CLI invoked locally).
2. POST /send hits `bridge_daemon` with `{service, recipient, body, operator_ok: true}`.
3. `bridge_daemon` calls `send_worker.send.send(...)`.
4. `send.py` runs three guards (operator_ok / allowlist / rate-limit) BEFORE invoking AppleScript.
5. On pass, `subprocess.run(["ssh", farm, "osascript", APPLESCRIPT_FARM, ...])`.
6. AppleScript returns `OK` or `ERR <num> <msg>`.
7. `bridge_daemon` returns the result to caller.
8. Within ~3s, the inbound tail picks up the new `is_from_me=1` row and emits the corresponding `iMessageReceived` SSE event — confirming the round-trip.

## Storage

| Store | Path | Content |
|---|---|---|
| chat.db (live) | farm `~/Library/Messages/chat.db` | source of truth, owned by Messages.app |
| chat.db (backup) | Vault `imessage/farm/<host>/chat-YYYYMMDD.db` | nightly snapshot (P4.1) |
| in-memory recent | `bridge_daemon.state.recent` | ring buffer of last 500 messages |
| contact policy | `memory/contact-policy.md` | per-contact allowlists + auto-respond rules |
| farm inventory | `memory/farm-inventory.md` | registered farms + their parameters |
| schema observations | `memory/chat-db-schema.md` | observed schema per macOS version |
| brain entries | `_shared-memory/knowledge/imessage-bridge-*.md` | cross-session learnings |

## Security boundaries

| Boundary | Enforced by |
|---|---|
| Operator's primary Apple ID is read-only forever | `is_primary` flag in `memory/farm-inventory.md`; bridge_daemon refuses send if matched |
| Send only to allowlisted contacts | `send.py` `_load_allowed()` returns set from `contact-policy.md`; non-members blocked |
| Auto-respond rules require explicit operator signature | `operator_signed: yes` column in contact-policy.md; unsigned rows ignored at boot |
| HTTP API never exposed beyond localhost | `bind="127.0.0.1"`; vault token gate on /send (P4) |
| chat.db reads never take write locks | SQLite URI `mode=ro` + `timeout=5` |
| Message bodies never logged at INFO | logging gates body strings to DEBUG only |

## Phase mapping

| Phase | Adds | Removes |
|---|---|---|
| P0 | scaffold + plans + source skeleton + dashboard UI shell + canned chat.db fixture | — |
| P1 | SSH to farm; live chat.db read; schema fingerprint persisted | mock chat.db (still present for tests) |
| P2 | AppleScript send via wrapper; per-thread operator OK; contact policy populated | — |
| P3 | bridge_daemon supervisor; fswatch tail; SSE events; bus posting | poll-based receive |
| P4 | vault backup / mind / forge / auto-respond rules | per-thread OK on signed rules only |

## What's deliberately NOT in this architecture

- No third-party message broker (Kafka / RabbitMQ etc) — sinister-bus is the bus.
- No alternate send paths (no `osascript -e` inline strings; no `imessage` CLI tool dependency; no private framework calls before P3+).
- No client-side message persistence in the dashboard (single source of truth = chat.db; UI is a view).
- No mobile companion app — the dashboard is the only operator surface (the iPhone itself is the inbound surface).
