# Sinister Forge — REST/SSE Bridge

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later

Flask app on port `:5078` that exposes the operator's Sanctum fleet over
Tailscale so Sinister Claw (mobile) — and any other Sanctum surface —
can drive Forge agents, browse the brain, and ack inbox messages
without an SSH/RDP session.

## Boot

```
cd "D:\Sinister Sanctum\projects\sinister-forge\source"
python -m forge.bridge
```

On first boot the bridge generates a random auth token, prints it, and
persists it to `_shared-memory/forge-bridge-token.txt` (gitignored).
Paste the token into Sinister Claw → Settings tab.

## Architecture

```
phone (Tailscale) ─── HTTPS ──▶ operator's PC :5078
                                    │
                                    ▼
                            ┌───────────────────────┐
                            │   Flask app (server)  │
                            │  ┌─────────────────┐  │
                            │  │ Auth gate       │  │  Bearer / ?token=
                            │  └─────────────────┘  │
                            │  ┌─────────────────┐  │
                            │  │ Sanctum reads   │  │  /api/sanctum/*
                            │  │ (heartbeats,    │  │  reads _shared-memory
                            │  │  projects, ...) │  │  + git log
                            │  └─────────────────┘  │
                            │  ┌─────────────────┐  │
                            │  │ Forge registry  │  │  /api/forge/*
                            │  │ (spawn / list / │  │  in-process dict of
                            │  │  tail / kill)   │  │  AgentRecord
                            │  └─────────────────┘  │
                            └───────────────────────┘
                                    │
                                    ▼
                      ┌──────────────────────────────┐
                      │ subprocess.Popen workers     │
                      │  • claude --dangerously-...  │
                      │  • codex exec                │
                      │  • stdout pump → SSE fanout  │
                      └──────────────────────────────┘
```

## Auth

Every endpoint EXCEPT `/api/health` requires a token via:
- `Authorization: Bearer <token>` header, OR
- `?token=<token>` query string (for `EventSource` which can't set headers)

`/api/health` is intentionally open so operator can `curl` the bridge
unauthenticated to verify it's up.

## Endpoints

| Method | Path | What |
|---|---|---|
| GET | `/api/health` | open; returns `{ok, name, version, agents_active}` |
| GET | `/api/sanctum/heartbeats` | live agents from `_shared-memory/heartbeats/` |
| GET | `/api/sanctum/projects` | `automations/session-templates/projects.json` |
| GET | `/api/sanctum/projects/<key>/detail` | metadata + PROGRESS top 5 + resume-point + plans |
| GET | `/api/sanctum/inbox?limit=N` | aggregates inbox/ + cross-agent/ newest-first |
| GET | `/api/sanctum/commits?limit=N` | last N commits from Sanctum repo |
| GET | `/api/forge/agents` | live agent registry |
| POST | `/api/forge/spawn` | spawn Claude/Codex subprocess |
| DELETE | `/api/forge/agents/<id>` | SIGTERM (5s) → SIGKILL |
| POST | `/api/forge/agents/<id>/input` | write a line to stdin |
| GET | `/api/forge/agents/<id>/stream` | SSE stdout (event name = `line`) |

## Files

- `__main__.py` — `python -m forge.bridge` entry
- `server.py` — Flask app + endpoint handlers + auth gate + heartbeat writer
- `registry.py` — threaded `subprocess.Popen` registry + stdout pump + SSE fanout

## Heartbeat

The bridge writes its own heartbeat to
`_shared-memory/heartbeats/forge-bridge.json` every 60 seconds while
running. Sanctum-level sweeps + the Claw `/api/sanctum/heartbeats`
endpoint will show it as alive.

## Tailscale setup

Standard Tailscale install on operator's PC + on phone. Once both are
on the same tailnet, the phone reaches the bridge at
`http://<pc-machine-name>:5078` (no port-forwarding, no public IP, no
DNS — Tailscale handles all of it).

## Lane discipline

- Bridge runs in its OWN process — does NOT share Textual's event loop.
- Subprocesses use blocking `subprocess.Popen` (not asyncio).
- Stdout pump runs in a daemon thread per agent.
- SSE subscriber queues are bounded (4000 lines); slow consumers get
  dropped from the list silently.
- Ring buffer is bounded (2000 lines); late subscribers see the most
  recent context but not the full history.

## What the bridge does NOT do

- Run the Textual TUI — that's `python -m forge` (different entry).
- Manage Forge plugins / hot-reload — that's PH8.
- Embed RKOJ — that's PH7.
- Implement `:host claude` / `:host codex` switching — that's PH10.
- Replace the operator's PC for compute — agents still spawn LOCALLY on
  operator's PC. Phone is a remote control, not the runner.
