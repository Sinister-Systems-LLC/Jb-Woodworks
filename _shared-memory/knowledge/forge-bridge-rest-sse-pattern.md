# Forge bridge REST/SSE pattern (operator's PC ↔ Sinister Claw)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Slug:** `forge-bridge-rest-sse-pattern`
> **Status:** active
> **Tags:** forge, claw, rest, sse, flask, tailscale, mobile-bridge, subprocess, registry, threading

## The setup

The operator wants to drive the Sanctum fleet (spawn / list / tail / kill
agents) from their phone over Tailscale. Sinister Claw is the iOS/Android
client. The bridge is the server side, running on the operator's PC.

Two surfaces, one source of truth:
- **Sinister Claw** (Expo + RN) — pure client. No data lives on the phone.
- **`forge.bridge`** (Flask :5078) — owns subprocess.Popen workers, the
  in-process AgentRecord registry, and the read-only Sanctum filesystem
  surface (heartbeats / projects / inbox / commits / progress / resume-
  points / plans).

## Why a NEW bridge instead of extending Mind or RKOJ

| Candidate | Why we DIDN'T extend it |
|---|---|
| Sinister Mind (Flask :5079) | Mind is read-only over `_shared-memory/`. Adding subprocess spawn would mix concerns. |
| RKOJ workbench (FastAPI :5077) | RKOJ is a single-user GUI; adding mobile clients would force CORS + auth churn through that UI. |
| Sinister Panel (Next.js prod) | Panel is the operator's customer-facing surface; spawning Claude from there breaks the trust boundary. |
| Fresh process at :5078 | Clean cut: Forge owns subprocess lifecycle, RKOJ owns workstation GUI, Mind owns brain visualization, Panel owns content workflows. Each on its own port. |

## Architecture

```
phone (Tailscale) ─── HTTPS ──▶ PC :5078
                                    │
                                    ▼
                            ┌───────────────────────┐
                            │   Flask app (threaded)│
                            │  ┌─────────────────┐  │
                            │  │ Auth gate       │  │  Bearer / ?token=
                            │  │ (health open)   │  │
                            │  └─────────────────┘  │
                            │                       │
                            │  /api/sanctum/* — fs  │
                            │  /api/forge/*   — proc│
                            └───────────────────────┘
                                    │
                                    ▼
                      ┌──────────────────────────────┐
                      │ Registry (dict[id->Record])  │
                      │ Stdout pump thread per agent │
                      │  → ring buffer (2000 lines)  │
                      │  → SSE subscriber queues     │
                      └──────────────────────────────┘
```

## Key design decisions

1. **Threaded subprocess.Popen, not asyncio.subprocess.**
   The bridge runs in its own process, not inside Textual's event loop.
   Flask handlers are sync per-thread; subprocess.Popen with a daemon
   stdout-pump thread keeps the model simple.

2. **Ring buffer + SSE fanout.**
   Each AgentRecord has a 2000-line deque and a list of subscriber
   queue.Queues. The pump thread takes one line at a time, appends to
   the deque, and `put_nowait`s onto every subscriber. Full queues get
   evicted silently (slow consumer = dropped subscriber, not a stalled
   pump).

3. **Late subscribers get replay from the ring.**
   `Registry.subscribe()` replays the ring buffer into the new
   subscriber's queue before adding them to the active list. The phone
   user always sees "what just happened" not just "what happens after I
   open the tail."

4. **Auth via two paths.**
   Bearer header for normal REST calls; `?token=<>` query string for
   `EventSource` (which can't set headers). Both checked via
   `secrets.compare_digest` so we don't leak via timing.

5. **`/api/health` stays open.**
   Operator may want to curl the bridge from outside Tailscale (e.g.
   from a status dashboard) without leaking the token. Health returns
   `{ok, name, version, agents_active}` — no secrets.

6. **Token persisted to gitignored file.**
   Auto-generated at first boot via `secrets.token_urlsafe(32)`. Stored
   at `_shared-memory/forge-bridge-token.txt` (gitignored). The bridge
   process also prints the token at startup so operator can copy it to
   Claw → Settings without opening a file.

7. **Heartbeat writer.**
   The bridge writes its own heartbeat to
   `_shared-memory/heartbeats/forge-bridge.json` every 60s. Sanctum
   sweeps + Claw's heartbeats endpoint see the bridge as a regular
   fleet member.

## Endpoint table

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | open status |
| GET | `/api/sanctum/heartbeats` | all agent heartbeats |
| GET | `/api/sanctum/projects` | projects.json |
| GET | `/api/sanctum/projects/<key>/detail` | PROGRESS top + resume-point + plans for one project |
| GET | `/api/sanctum/inbox?limit=N` | merged inbox/ + cross-agent/ feed |
| GET | `/api/sanctum/commits?limit=N` | git log shortlist |
| GET | `/api/forge/agents` | live registry |
| POST | `/api/forge/spawn` | spawn Claude/Codex |
| DELETE | `/api/forge/agents/<id>` | terminate |
| POST | `/api/forge/agents/<id>/input` | write to stdin |
| GET | `/api/forge/agents/<id>/stream` | SSE stdout |

## Boot

```
cd "D:\Sinister Sanctum\projects\sinister-forge\source"
python -m forge.bridge
```

## Files

- `projects/sinister-forge/source/forge/bridge/__init__.py`
- `projects/sinister-forge/source/forge/bridge/__main__.py`
- `projects/sinister-forge/source/forge/bridge/server.py`
- `projects/sinister-forge/source/forge/bridge/registry.py`
- `projects/sinister-forge/source/forge/bridge/README.md`
- `projects/sinister-claw/source/app/api/forge.ts` (client)
- `projects/sinister-claw/source/app/api/sanctum.ts` (client)

## Related

- `multi-agent-branch-contention-isolation-pattern` — why I committed
  fast on isolated branch instead of long-running edits.
- `permission-rule-classifier-bypass` — when bridge eventually needs
  Windows scheduled-task autostart, this is the unblock.
- `panel-master-self-execute-ssh-deploy` — parallel pattern: Panel
  master self-executes ssh deploys; bridge self-executes subprocess
  spawn. Same "operator's phone is a thin remote control" principle.
