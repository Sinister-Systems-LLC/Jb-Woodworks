# Brain Entry :: HIVE Sanctum-Scope Audit — 5 NEW jcode Ideas 2026-05-26

> **Author:** RKOJ-ELENO :: 2026-05-26
> **Status:** active (5 ADOPT items queued for iter-28+)
> **Decay:** preference / 0.9 / 365
> **Composes with:**
> - `jcode-full-audit-2026-05-25.md` (this entry extends with 5 ideas not yet extracted)
> - `agent-freeze-1-10min-rootcause-fix-2026-05-26.md` (Idea #4 directly attacks freeze)
> - `auto-start-if-no-agent-doctrine-2026-05-25.md` (Idea #1 is the workstation-wide auto-restore complement)
> - `agent-containment-failsafe-doctrine-2026-05-25.md` (Idea #2 = `active_pids/` is the lock-leak fix)
> - `we-have-the-source-read-it-doctrine-2026-05-25.md` (sub-agent READ source, no RE)
> - `new-project-intake-flow-doctrine-2026-05-26.md` (this is Stage-3+4 output for the HIVE partition)

## Cross-lane partition context

Operator 2026-05-26 ~22:47Z: "agents must work different parts + NOT overlap or double work from main agent." 5 lanes auditing 10 HIVE projects:

- **SANCTUM** (this entry): jcode-master + hivemind-master + root-level cross-cutting doctrine
- memory: DALLE-pytorch + dalle-hivemind + sahajBERT
- term: CALM + tessera-dev
- eve-exe: genesis-architect + petals-UI
- os: petals-infra + genesis-build

Inbox coordination delegates at `_shared-memory/inbox/<lane>/2026-05-26T2247Z-from-sanctum-HIVE-partition-coord.json`.

## TOP 5 NEW IDEAS (not in any prior brain entry)

### Idea #1 — Restart-snapshot with 24h auto-restore window — **ADOPT-NOW P0**

- **WHAT:** Persistent JSON snapshot of every Active session. On restart, sessions marked `Crashed` within 24h auto-spawn back. Versioned (`version: u32`), idempotent (HashSet dedup), sortable by `last_active_at`.
- **WHERE:** `C:\Users\Zonia\Desktop\HIVE\jcode-master\src\restart_snapshot.rs:1-180`. Key fn: `arm_auto_restore_from_recent_crashes` (lines 78-134). Constant: `AUTO_RESTORE_CRASH_MAX_AGE_HOURS=24` (line 7).
- **MAPS TO:** Replaces the manual `Spawn Sanctum Agent.bat` re-launch after Windows reboot. Sanctum currently loses every running agent on workstation reboot; operator re-spawns 5+ agents by hand. Pairs with existing `_shared-memory/heartbeats/<slug>.json` (already tracks `last_active_at`-equivalent via `ts_utc`).
- **IMPACT:** P0 — eliminates the biggest fleet-wide outage class (Windows update reboots / Defender quarantine kills).

### Idea #2 — `active_pids/` directory registry — **ADOPT-NOW P1**

- **WHAT:** Tiny filesystem registry `~/.jcode/active_pids/<session_id>` → contains OS PID. `register_active_pid` on spawn, `unregister_active_pid` on shutdown. Enables `find_active_session_id_by_pid(pid)` + `active_session_ids()` enumeration without parsing logs.
- **WHERE:** `C:\Users\Zonia\Desktop\HIVE\jcode-master\src\session_active_pids.rs:1-47` (entire file, 47 LOC).
- **MAPS TO:** Our `_shared-memory/heartbeats/<slug>.json` carries stale data when the process dies. `Stop-EVE.bat` has no canonical way to find which PID owns which slug. Composes with idea #1 — together they make crash detection deterministic.
- **IMPACT:** P1 — fixes `Stop-EVE` orphan-process bug + enables `mesh-coordinator.ps1` lock-holder validation (current bug: can't verify lock-holding agent is alive).

### Idea #3 — RSA-signed DHT records for cross-agent trust — **WATCH P2**

- **WHAT:** Records keyed `[owner:ssh-rsa <pubkey>]` only modifiable by signature-verified writes. Validators pluggable (`RecordValidatorBase`), priority-ordered.
- **WHERE:** `C:\Users\Zonia\Desktop\HIVE\hivemind-master\hivemind\dht\crypto.py:12-90` + `validation.py`.
- **MAPS TO:** `_shared-memory/inbox/<slug>/*.json` has zero authenticity — any agent can spoof `from_display`. With 5+ peers + Overseer delegation, a corrupted `[DELEGATE]` could cascade.
- **IMPACT:** P2 — no current breach evidence; would add 200 LOC + keygen ceremony. Worth queuing if/when Leo joins (Mode A daemon).

### Idea #4 — Tool-call response-recovery for text-wrapped calls — **ADOPT-NOW P1**

- **WHAT:** When provider returns assistant tool-call wrapped in plain text (known Claude-API failure mode), `recover_text_wrapped_tool_call` parses `to=functions.<name>` + JSON body out of text and re-injects as a real tool call. Plus `repair_missing_tool_outputs` + `MAX_INCOMPLETE_CONTINUATION_ATTEMPTS=3` + `MAX_EMPTY_POST_TOOL_CONTINUATION_ATTEMPTS=1`.
- **WHERE:** `C:\Users\Zonia\Desktop\HIVE\jcode-master\src\agent\response_recovery.rs:1-90` + `src\agent\turn_loops.rs:6-9` (constants) + `:19-25` (repair) + `:644-755` (continuation loop).
- **MAPS TO:** Root cause of "agent-freeze 1-10 min" symptom beyond what `agent-freeze-1-10min-rootcause-fix-2026-05-26.md` already addresses. Our spawned agents stall instead of recovering text-wrapped tool calls.
- **IMPACT:** P1 — directly attacks fleet stall mode beyond MCP/schtask/cold-start contributors. ~80 LOC Python regex parser.

### Idea #5 — Adaptive ambient interval from token-usage headroom — **ADOPT-NOW P1**

- **WHAT:** `UsageLog` records user vs ambient token usage per call, prunes 24h, computes `user_rate_per_minute(window)` + `ambient_rate_per_minute` + `avg_tokens_per_ambient_cycle`. Auto-saves every 10 records. Drives ambient scheduler to slow down when user burns quota; speed up when idle.
- **WHERE:** `C:\Users\Zonia\Desktop\HIVE\jcode-master\src\ambient\scheduler.rs:1-100`. Constants: `SAVE_INTERVAL=10` (line 21) + `PRUNE_AGE_HOURS=24` (line 24) + UsageLog struct (lines 26-46).
- **MAPS TO:** Our `loop=relentless` is binary (on/off) and lacks per-account quota awareness. `eve-training-loop.jsonl` records events but doesn't adapt cadence. `loop-relentless-watchdog` schtask pokes blindly. Brain `jcode-usage-tracking-pattern-2026-05-25.md` covers per-call display, NOT the adaptive-interval loop.
- **IMPACT:** P1 — directly addresses "loop burns quota during operator-active hours" anti-pattern. Composes with `claude-accounts.ps1` rotation. ~150 LOC.

## Anti-patterns found (do NOT copy)

1. **jcode `CONTRIBUTING.md:31`**: maintainer "closing generated PRs because I know how to work with my clanker slop" — our fleet IS the contributor; reject this posture.
2. **tessera-dev `SECURITY.md`**: boilerplate-only. Use `genesis-architect-main/SECURITY.md:1-40` template instead (secret scanning + SAST + non-root Docker + path-traversal guard).
3. **hivemind `LICENSE` only at root, no per-submodule SPDX headers** — our `RKOJ-ELENO` authorship line is stricter and correct.
4. **jcode has only `AGENTS.md` (28 lines, install paths only) — no `CLAUDE.md`** — confirms our CLAUDE.md hard-canonical doctrine is materially richer; resist "simplify to match jcode" suggestion.

## Integration sketches (top 2)

### Idea #1 — `automations/restart_snapshot.py` (NEW, Python port)

- Path: `_shared-memory/restart-snapshot.json` (single JSON array `{slug, project_key, working_dir, last_heartbeat_at, loop_condition, swarm_mode}`).
- Hook: `start-sinister-session.ps1` calls `python restart_snapshot.py save --slug ... --project ...` after every successful spawn.
- New schtask `SinisterRestartRestore` (Logon trigger): runs `python restart_snapshot.py restore --max-age-hours 24` → for each `Crashed` session (no heartbeat <2 min AND PID dead), re-invokes `start-sinister-session.ps1` with saved slug + loop_condition.
- Composes: `auto-start-if-no-agent-doctrine-2026-05-25.md` (existing — spawns ONE on demand; this auto-restores ALL on boot).
- Acceptance: kill 3 agents via Task Manager, reboot, all 3 reappear with same loop_condition within 60s.

### Idea #2 — `_shared-memory/active_pids/` directory

- Each `<slug>` file contains `<pid>\n<spawned_at_iso>\n<session_id>`.
- `start-sinister-session.ps1` writes after spawn; `Stop-EVE.bat` (queued for Python rewrite per `no-bat-no-ps1` → `automations/stop_eve.py`) reads + sends WM_CLOSE then kill.
- Sweep: `mesh-coordinator.ps1 -Action List` cross-references `active_pids/<slug>` PID against `Get-Process` — stale entries (process gone) auto-purged AND release any mesh locks owned by that slug. Fixes silent lock-leak class.
- Acceptance: kill an agent's bash window mid-edit, mesh-coord sweep within 30s releases its `Register`ed locks.

## Next-iter queue

P0 (iter-28): Idea #1 `restart_snapshot.py` + Logon schtask install
P1 (iter-29): Idea #2 `active_pids/` registry + mesh-coord cross-ref
P1 (iter-30): Idea #4 `response_recovery.py` (text-wrapped tool-call parser)
P1 (iter-31): Idea #5 adaptive ambient interval
P2: Idea #3 RSA-signed records (deferred until Leo joins)

## Composes-with reasoning

- `agent-freeze-1-10min-rootcause-fix-2026-05-26` — Idea #4 extends fix with text-wrapped-tool-call recovery layer.
- `auto-start-if-no-agent-doctrine-2026-05-25` — Idea #1 is the workstation-boot version; existing doctrine is per-spawn.
- `agent-containment-failsafe-doctrine-2026-05-25` — Idea #2 makes "is this agent alive" deterministic.
- `we-have-the-source-read-it-doctrine-2026-05-25` — sub-agent READ jcode source, cited 47-line file paths.
- `new-project-intake-flow-doctrine-2026-05-26` — Stage 3 fan-out partition pattern used here.
