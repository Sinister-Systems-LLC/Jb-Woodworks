# RKOJ Workstation API

> Author: RKOJ-ELENO :: 2026-05-23
> Shipped: v1.6.82 (`api_server.py` module)

Local HTTP API agents call to interact with the workstation — phones,
claims, shell, screencap, APK install — without going through brittle
shell pipelines. **Loopback only** (`127.0.0.1:5077`), no external
network exposure, no auth (trusted-local model).

## Quick start

```bash
# Health check
curl http://127.0.0.1:5077/api/health

# List connected phones + who owns each
curl http://127.0.0.1:5077/api/phones

# Claim a phone for your agent (exclusive lock)
curl -X POST http://127.0.0.1:5077/api/phones/26031JEGR17598/claim \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"my-agent","agent_display":"My Agent"}'

# Run a shell command on the claimed phone
curl -X POST http://127.0.0.1:5077/api/phones/26031JEGR17598/shell \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"my-agent","cmd":"pm list packages | head -5"}'

# Release when done
curl -X POST http://127.0.0.1:5077/api/phones/26031JEGR17598/release \
  -d '{"agent_id":"my-agent"}'
```

## Endpoints

### `GET /api/health`
Returns `{ok, service, version, uptime_s}`. Never gated.

### `GET /api/version`
Returns `{sinister_rkoj_qt: "x.y.z"}`.

### `GET /api/phones`
Returns `{devices: [...], count: N}` where each device has
`{serial, model, state, transport, owner}`. `owner` is the claim record
or `null` if free.

### `POST /api/phones/<serial>/claim`
Body: `{agent_id, agent_display?}`. Returns 200 + claim record if
granted, 409 + current owner if already claimed by a different agent.
Idempotent for the same `agent_id`.

### `POST /api/phones/<serial>/release`
Body: `{agent_id?}`. If `agent_id` provided, only releases if that agent
currently holds the claim (safe-release).

### `POST /api/phones/<serial>/screenshot`
Body: `{agent_id}`. Owner-checked. Runs `adb exec-out screencap -p`,
saves PNG to `~/Desktop/eve-<serial>-<timestamp>.png`. Returns `{path}`.
Returns 403 if `agent_id` doesn't match the current claim.

### `POST /api/phones/<serial>/shell`
Body: `{agent_id, cmd}`. Owner-checked. 30s timeout. Returns
`{stdout, stderr, returncode}`.

### `POST /api/phones/<serial>/install-apk`
Body: `{agent_id, apk_path, replace?: bool}`. Owner-checked. APK file
must exist on disk where RKOJ.exe can read it. 120s timeout. Returns
`{stdout, stderr, returncode}`.

### `GET /api/agents`
Returns `{agents: [...], total_claimed_phones: N}`. Each agent entry:
`{agent_id, owned_phones: [serial,...], phone_count}`.

## Phone-claim guarantees (why it matters)

Agents working on phone A **cannot** accidentally drive phone B. The
shell + screenshot + install-apk endpoints all check the claim record
and 403 if the caller isn't the owner. This prevents:

- Frida injection on phone A leaking to phone B
- Two agents simultaneously running `am force-stop` on the same phone
- Screencap timing collisions
- APK install from wrong agent's queue landing on wrong phone

The claim registry persists to `_shared-memory/phone-claims.json` so it
survives RKOJ restart.

## Status surface

- Bottom-of-window status bar pill: `api: http://127.0.0.1:5077` (green = live)
- `/api` slash command inside any agent card prints this endpoint list
- `python -m unittest tests.test_agents_tab.TestApiServerV182` verifies import surface
