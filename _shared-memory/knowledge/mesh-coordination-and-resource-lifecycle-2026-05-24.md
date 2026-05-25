<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

<!-- decay:
  category: fact
  confidence: 0.95
  reinforcements: 0
  half_life_days: 90
-->
# Mesh Coordination + Resource Lifecycle Doctrine

**Created:** 2026-05-24 (EVE on Sanctum, mesh-foundation iter)
**Scope:** Every EVE session, every spawned agent, every per-project lane.
**Authority:** Operator hard-canonical 2026-05-24:
- 19:14:39Z — *"i need you to make sure swarm and loop can be ran on multiplle different agents without them having issues with each other... a complete mesh network where no one steps on toes"*
- 19:17:18Z — *"when our agents are closed that everything that agent is using is closed aswell. UNLESS another agent is using something from that. then you wait until its done then close. do that with all things like our local agents have them sleep, turn off overall just be efficent and then seamless awaken when they are needed"*
- 19:45Z — *"have docker start on bootup so we can easily call our agents for use from that and make sure all skills, liocal aghents etc can auto start with no issues"*

---

## Why this exists

5+ concurrent EVE sessions running `swarm=on loop=on` can collide on the same files (e.g. two sessions editing `eve.py`), spawn duplicate local-bot processes (RAM bloat), or orphan resources when one session crashes (operator: "eve exe just crashed... cannot x it out"). This doctrine specifies the lock + refcount + cleanup pattern every lane must honor.

---

## Three primitives

### 1. `automations/mesh-coordinator.ps1` — file-lock + TTL

Lock files live under `_shared-memory/mesh-locks/<sanitized-focus>.json` with a TTL that auto-expires. Each lock carries `owner_slug`, `expires_utc`, `hint`, and `blast_radius (single|lane|fleet)`.

```powershell
# Claim before editing shared files / focus areas
powershell -File automations/mesh-coordinator.ps1 -Action Register `
    -Slug sanctum -Display "Sinister Sanctum" `
    -Focus "automations/eve-launcher/eve.py" `
    -Hint "crash hardening" -TtlSeconds 1800 -BlastRadius lane

# Other agents check before editing the same focus
powershell -File automations/mesh-coordinator.ps1 -Action Check -Focus "automations/eve-launcher/eve.py"
# exit 0 + CLEAR = safe to proceed; exit 1 + LOCKED = pick a different slice

# Extend lifetime during long work
powershell -File automations/mesh-coordinator.ps1 -Action Heartbeat -Slug sanctum -Focus "automations/eve-launcher/eve.py"

# Release on completion (always)
powershell -File automations/mesh-coordinator.ps1 -Action Release -Slug sanctum -Focus "automations/eve-launcher/eve.py"

# Periodic cleanup
powershell -File automations/mesh-coordinator.ps1 -Action Sweep
powershell -File automations/mesh-coordinator.ps1 -Action List
```

Exit codes: `0` ok / `1` conflict / `2` missing arg / `3` io fail. Smoke-tested 6/6 PASS 2026-05-24T19:31Z.

### 2. `automations/bot-lifecycle.ps1` — refcount sleep/wake

Per-bot state in `_shared-memory/bot-lifecycle.json`. Each local MCP bot tracks: `state (asleep|spawning|awake|terminating)`, `refcount`, `users[]`, `pid`, `idle_since_utc`, `wake_cmd`.

```powershell
# Acquire before calling the bot
powershell -File automations/bot-lifecycle.ps1 -Action Acquire `
    -Bot librarian -Slug sanctum -WakeCmd "py -m librarian.server" -SleepAfterIdleSec 300

# Release when done; if refcount=0 it starts idle clock
powershell -File automations/bot-lifecycle.ps1 -Action Release -Bot librarian -Slug sanctum

# Periodic sweep marks refcount=0 + idle>N as asleep (caller kills PID)
powershell -File automations/bot-lifecycle.ps1 -Action Sweep -MaxIdleSec 300
```

Smoke-tested 7/7 PASS 2026-05-24T19:40Z. Refcount honors "wait until others done" before kill.

### 3. `automations/heartbeat-sweep.ps1` — prune-as-add hygiene

Archives heartbeats older than `-MaxAgeHours` (default 24) into `_shared-memory/heartbeats/_archive/<yyyymmdd>/`. Default mode is `-DryRun`; pass `-Apply` to actually move. First production run 2026-05-24T19:43Z archived 25 stale files.

---

## Cold-start protocol additions

Every EVE session must — early in its turn:

1. **Register its current focus** with mesh-coordinator (if work touches shared files / focus areas) before editing.
2. **Acquire bots** via bot-lifecycle.ps1 before calling them; release when done.
3. **Honor existing locks** — if `Check` returns `LOCKED`, pick a different slice rather than `-Force`-seizing.
4. **Sweep on session-end** — release all locks owned by this slug; release all bots.

Locks are **advisory** (not OS-enforced); a stubborn agent CAN force, but the conflict log will surface it.

---

## Composition with existing systems

- **`_shared-memory/agent-modes/<slug>.json`** — already tracks per-slug `swarm` + `loop` flags. Mesh-coordinator does NOT replace it; the two layers complement (modes = *what mode* this lane runs in; locks = *what work* this lane currently owns).
- **`_shared-memory/fleet-updates.jsonl`** + `automations/fleet-update.ps1` — fleet-wide announcements; orthogonal to per-focus locks. Use fleet-update for new doctrine / fix announcements; use mesh-locks for short-lived work claims.
- **`_shared-memory/inbox/<slug>/`** — peer-to-peer messages. Use locks alongside inbox handoffs so the receiving lane knows whether the sender still owns the focus.
- **Docker Desktop AutoStart=true** (operator 19:45Z) — set in `%APPDATA%\Docker\settings-store.json`. After Docker is up, `bot-lifecycle.ps1` is the canonical entry-point for spawning local agents on demand (no need to bring up the whole fleet at boot — refcount-based wake handles it).

---

## EVE.exe crash-hardening (same operator-canonical, shipped this turn)

Operator 19:17Z's "eve exe just crashed... cannot x it out" was root-caused (sub-agent 2026-05-24T19:34Z): `subprocess.call()` in `eve.py:dispatch_project/dispatch_interactive` had no timeout + no try/except; a hung PS1 launcher (forge-memory recall, vault lock, etc.) blocked the UI thread.

**Fix shipped same turn:**
- `eve.py:808-845` — dispatch wrapped with `timeout=DISPATCH_TIMEOUT_SEC (180)` + try/except for `TimeoutExpired` + generic `Exception`. Returns 124 on timeout instead of hanging.
- `eve.py:1302-1340` — every dispatch call-site in the main loop wrapped in try/except with `time.sleep(2) + continue` so the picker survives.

Parse-clean PASS (`python -m py_compile`). Composes with v0.4.4 EVE.exe rebuild (owned by test-modes lane) — pulled into next build.

---

## Anti-patterns

1. **Don't `-Force`-seize without inbox-acking the prior owner first.** The lock TTL exists to let the owner finish or expire naturally.
2. **Don't acquire a bot without releasing.** Refcount leaks accumulate; `bot-lifecycle.ps1 -Action List` should never show users a slug doesn't actually have.
3. **Don't skip Register on "small" edits.** If two agents both edit eve.py simultaneously, last write wins → silent regression.
4. **Don't run heartbeat-sweep -Apply blindly.** Always `-DryRun` first; verify the archive list looks sane.

---

## Composes with

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 8: prune-as-add — heartbeat-sweep enforces it)
- `wake-on-demand-bot-dispatcher-2026-05-23` (this doctrine implements that doctrine)
- `agent-autonomy-push-and-completion-2026-05-23` (per-agent branches still auto-push; mesh just prevents simultaneous edits)
- `fleet-update-channel-doctrine-2026-05-24` (fleet-wide announcements complement per-focus locks)
- `agent-identity-eve.md` (every EVE session honors mesh; identity is EVE, lane is slug)

---

## Verification commands (re-run any time)

```powershell
# Lock + refcount end-to-end smoke
powershell -File automations/mesh-coordinator.ps1 -Action List
powershell -File automations/bot-lifecycle.ps1 -Action List

# Hygiene check
powershell -File automations/heartbeat-sweep.ps1 -MaxAgeHours 24   # dry-run first

# Docker autostart check
Get-Content "$env:APPDATA\Docker\settings-store.json" | Select-String 'AutoStart'
```
