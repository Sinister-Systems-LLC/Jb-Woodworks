<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Auto-Brain-Propagation doctrine

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Created:** 2026-05-24
> **Status:** active
> **Tags:** brain, fleet-update, cold-start, doctrine-propagation, auto-update, sanctum-scope

## Operator verbatim (2026-05-24T23:58Z)

*"make sure all agents have the memory updates as we grow on it daily and it auto updates."*

The brain (`_shared-memory/knowledge/`) grows daily. Operator wants every spawned agent to automatically know about new updates rather than manually re-read the brain on each spawn. This doctrine closes that loop end-to-end.

## State diagram

```
1. NEW DOCTRINE LANDS                  2. BRAIN-BROADCAST SCAN+PUSH                3. LIVE AGENTS POLL
   agent writes/edits           ->     SinisterBrainBroadcast schtask              ->  per-CLAUDE.md cold-start step 11
   _shared-memory/knowledge/           ticks every 10 min, runs                       fleet-update.ps1 -Action List
   <slug>.md                            brain-broadcast.ps1 -Action Broadcast          tails 3 unacked rows visible
                                       which diffs mtime vs                             to this slug; doctrine_update
                                       _shared-memory/.brain-broadcast-state.json       rows surface in inbox
                                       and pushes fleet-update row                      (already wired iter-1)
                                       kind=doctrine_update priority=normal
                                       message="BRAIN new|updated: <slug> - <summary>"

                                                                                    4. LIVE AGENT READS + ACKS
                                                                                       agent opens the doctrine,
                                                                                       acts on it, then
                                                                                       fleet-update.ps1 -Action Acked
                                                                                       -Id <fu-id> -Slug <agent>

5. NEW AGENT SPAWNS                    6. BUILD-PHRASE INJECTS                      7. CHILD READS + APPLIES
   operator clicks EVE.exe       ->    Build-Phrase scans                           ->  child Claude session reads
   or picker spawns new lane           _shared-memory/knowledge/ for                    the inject + opens the listed
                                       *.md mtime >= now-24h, picks                     doctrine paths during its
                                       top 3, builds 'RECENT BRAIN UPDATES'              REVIEW step on cold-start
                                       inject + appends to phrase
                                       (alongside fleet-updates inject)
```

## Components

| Component | Path | Purpose |
|---|---|---|
| `brain-broadcast.ps1` | `automations/brain-broadcast.ps1` | Scan/Broadcast/Watch/Status actions. Diffs `_shared-memory/knowledge/*.md` mtime vs persisted state, pushes fleet-update row per new/updated doctrine. |
| `register-brain-broadcast-task.ps1` | `automations/register-brain-broadcast-task.ps1` | Idempotent schtask registration; `SinisterBrainBroadcast` runs every 10 min. |
| State file | `_shared-memory/.brain-broadcast-state.json` | `{ files: { slug: mtime_iso }, last_sweep: iso }`. Same mtime never re-broadcasts. |
| Build-Phrase inject | `automations/start-sinister-session.ps1` (Build-Phrase, RESUME mode) | "RECENT BRAIN UPDATES (last 24h, top 3 ...)" appended to cold-start phrase. Skippable via `SINISTER_SKIP_RECENT_BRAIN=1`. |
| Fleet-update transport | `automations/fleet-update.ps1` + `_shared-memory/fleet-updates.jsonl` | Already-built broadcast channel; this doctrine just adds a producer (brain-broadcast) and consumer (Build-Phrase). |
| Cold-start step 11 | `CLAUDE.md` cold-start section | Per-agent fleet-update poll on each spawn + periodic heartbeat re-poll. Already wired. |

## Idempotency rules

1. `brain-broadcast.ps1 -Action Broadcast` re-run with no doctrine changes is a no-op (writes `state.last_sweep`, pushes zero rows).
2. Same doctrine same mtime = no re-push. Touch a doctrine without editing it -> no broadcast (mtime unchanged after Save).
3. Update a doctrine's content -> mtime bumps -> next sweep broadcasts as `BRAIN updated:`.
4. `_INDEX.md`, `_TEMPLATE.md`, `_archive/**` excluded (housekeeping files, not doctrine).
5. `-Force` flag re-broadcasts all in-window files (use sparingly; floods the channel).

## Composes with

- `fleet-update-channel-doctrine-2026-05-24.md` - the transport this rides on
- `sanctum-scope-discipline-2026-05-24.md` - this is a fleet-wide / high-level mechanism, fits Sanctum mandate
- `forever-improve-review-doctrine-2026-05-24.md` - composes; brain-broadcast surfaces new doctrines so forever-improve agents see what to audit
- `agent-continuity-no-long-naps-2026-05-24.md` - 10-min cadence matches the awake-cadence expectation
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` rule 8 - this doctrine respects consolidation: only top 3 doctrines injected, summary capped at 220 chars

## Pass criterion

A new doctrine added to `_shared-memory/knowledge/` MUST:
1. Show up in EVERY agent's next spawn cold-start phrase (within 24h window) via Build-Phrase RECENT BRAIN UPDATES inject.
2. Show up in any live agent's fleet-update poll within 10 min (next SinisterBrainBroadcast tick).
3. Be acknowledgeable per-agent via `fleet-update.ps1 -Action Acked -Id <id> -Slug <agent>`.

## Smoke tests

```powershell
# 1. Scan only (no push)
powershell -File "D:\Sinister Sanctum\automations\brain-broadcast.ps1" -Action Scan

# 2. Broadcast (pushes 1 row per in-window doctrine, persists state)
powershell -File "D:\Sinister Sanctum\automations\brain-broadcast.ps1" -Action Broadcast

# 3. Verify fleet-updates row landed
Get-Content "D:\Sinister Sanctum\_shared-memory\fleet-updates.jsonl" | Select-Object -Last 5

# 4. State check
powershell -File "D:\Sinister Sanctum\automations\brain-broadcast.ps1" -Action Status

# 5. Register schtask
powershell -File "D:\Sinister Sanctum\automations\register-brain-broadcast-task.ps1"
Get-ScheduledTask -TaskName SinisterBrainBroadcast | Get-ScheduledTaskInfo
```

## Tuning knobs

- `-WindowHours N` (default 24) - only consider doctrine files modified in the last N hours
- `-IntervalSec N` (default 600) - Watch action loop interval
- `-Force` - re-broadcast all in-window files regardless of state
- Env `SINISTER_SKIP_RECENT_BRAIN=1` - disable Build-Phrase inject (useful for tests / reduced-noise spawns)
- Schtask `-IntervalMinutes 10` - matches the operator "random check on a time basis" cadence from fleet-update-channel doctrine
