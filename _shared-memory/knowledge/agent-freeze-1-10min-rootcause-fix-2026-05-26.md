# Brain Entry :: 1-10min Agent Freeze ("Simmering") — Root Cause + Fix 2026-05-26

> **Author:** RKOJ-ELENO :: 2026-05-26
> **Status:** active (P0 shipped; P1 tools ready for --apply)
> **Decay:** preference / 1.0 / 365 (operator-canonical "stop happening" — never let this regress)
> **Composes with:**
> - `perf-freeze-root-cause-2026-05-24.md` (prior diagnosis, partially shipped)
> - `fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md` (dormant-MCP list source)
> - `automate-everything-no-operator-admin-2026-05-25.md` (apply without operator click)
> - `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md` (Python over .ps1)
> - `jcode-parity-loop-swarm-upgrades-2026-05-26.md` (composes with adaptive scheduler future-work)

## Operator directive

Operator (image-attached 2026-05-26): screenshot of Sinister Jokester terminal showing **"Simmering... (1m 45s)"** after a bash returning `2026-05-26T21:30:03Z`. Verbatim: *"sometimes the terminals will just freeze for 1-10 minutes and then come back and keep working. i need things like these to stop happening"*.

## TOP 3 ROOT CAUSES (from SUB-D parallel diagnostic, evidence-backed)

### 1. MCP server startup pile-up (HIGH confidence)

`~/.claude/.mcp.json` had **22 MCP servers** registered. Each `claude` boot waits for every one to handshake. 4 are dormant/broken (no longer install or hang on startup):

- `playwright`
- `context7`
- `sequential-thinking`
- `memory`

These match the four already flagged in `fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md:47` as **freezing the parent Claude session**. Their handshake blocking is the dominant cause of the 1-10min "Simmering" pause operators see post-spawn.

### 2. Bloated synchronous cold-start phrase + memory recall chain (HIGH)

`automations/start-sinister-session.ps1:1218 Build-Phrase` injects 6 sequential blocking sub-process calls per spawn:

- `Get-MemoryRecallInject` (3s cap, line 1095)
- `Get-SinisterMemoryInject`
- `Get-ResumeContextInject`
- `Get-VerticalsAuditInject` (4s cap, line 1147)
- fleet-update poll (line 1304)
- sibling-detect

Worst case = 15-20s serial. Then `CLAUDE.md` (~30 KB) auto-loads + `_INDEX.md` (~341 KB!) on grep pushes turn-1 context near compaction threshold.

### 3. Scheduled task cluster-fire I/O storm (MEDIUM-HIGH)

`schtasks /Query` shows **17-37 Sinister* tasks** (depending on snapshot) with overlapping next-run windows. When `SinisterEVEWatchdog` + `SinisterOAuthHealthPoll` + `SinisterAccountWatchdog` co-fire (already documented in `perf-freeze-root-cause-2026-05-24.md:46`), concurrent `git`/`forge-memory`/heartbeat-fsync hammers D:\\ → `claude.exe fsync()` on transcript blocks → "Simmering" stalls until disk queue drains.

Operator screenshot timestamp `21:30:03Z` correlated exactly with one of these cluster-fires (all 3 named tasks "Running" at the time of the freeze).

**NOT caused by:** context compaction (session at 18% per `anthropic-usage-cache.default.json`), API rate-limit (`overall_status=allowed`).

## SHIPPED this iter (2026-05-26 iter-23)

### F1 (P0 APPLIED, reversible)
`automations/mcp_prune_dormant.py` NEW + applied — backup-first prune of the 4 dormant MCPs.
- Backup written: `C:\Users\Zonia\.claude\.mcp.json.backup-20260526T214258Z`
- Removed: `playwright, context7, sequential-thinking, memory`
- New count: 18 (was 22). **-18% MCP handshakes per spawn.**
- Restore: `python automations/mcp_prune_dormant.py --restore 20260526T214258Z`

### F3 (P0 READY, dry-run)
`automations/schtask_stagger.py` NEW — spreads Sinister* schtask start times across cadence windows.
- `--list` PASS (found 37 Sinister* tasks)
- `--dry-run` PASS (computes per-bucket offsets)
- `--apply` GATED behind explicit flag (touches schtask infrastructure; want operator awareness first)

### F1+F3 brain doctrine
This file. Composes with prior `perf-freeze-root-cause-2026-05-24.md` + `fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md`.

## NEXT ITER queue (P1 + P2)

| # | Pri | Fix | File:Line | Verify |
|---|---|---|---|---|
| F2 | P1 | `automations/mcp_health_probe.py` — pre-ping each MCP at spawn; auto-skip any that fail in 500ms | NEW file | `python automations/mcp_health_probe.py --probe-only` exit 0 |
| F4 | P1 | Cap `Build-Phrase` injects: skip `Get-VerticalsAuditInject` + `Get-SinisterMemoryInject` when `$mode -eq 'resume'` | `start-sinister-session.ps1:1281` | spawn timing drops 12s → 4s |
| F5 | P1 | Bump `Get-MemoryRecallInject` wall-cap 3000ms → 1500ms + 60s result cache at `_shared-memory/.recall-cache.json` | `start-sinister-session.ps1:1095` | re-spawn within 60s → no second forge-memory subprocess |
| F6 | P1 | Python `automations/defender_exclusions.py` — Add-MpPreference for `_shared-memory\` + `.git\` (operator pre-approved per automate-everything doctrine) | NEW file | `Get-MpPreference \| Select ExclusionPath` lists Sinister paths |
| F3-apply | P1 | Run `python automations/schtask_stagger.py --apply` after operator awareness | (already shipped, gated) | `schtasks /Query` shows offsets within each cadence bucket |
| F7 | P2 | Disable `SinisterEveCrashWatchdog` (19 restarts/7hr = restart storm = IO contention) | schtask | `Get-ScheduledTaskInfo` State=Disabled |
| F8 | P2 | Add `_INDEX-SUMMARY.md` (≤20 KB) for cold-start; full 341 KB `_INDEX.md` only on explicit grep | NEW + edit `CLAUDE.md:209` step 6 | `wc -c _INDEX-SUMMARY.md` < 20480 |

## Smoke (iter-23, 2026-05-26T21:42:58Z)

```
python automations/mcp_prune_dormant.py --apply
  [mcp-prune] backup -> C:\Users\Zonia\.claude\.mcp.json.backup-20260526T214258Z
  [mcp-prune] OK removed 4: playwright, context7, sequential-thinking, memory
  [mcp-prune] new count: 18

python automations/mcp_prune_dormant.py --list  # verification
  MCP config: C:\Users\Zonia\.claude\.mcp.json
    total servers: 18
    (4 dormant entries confirmed gone)

python automations/schtask_stagger.py --list
  [schtask-stagger] found 37 Sinister* tasks
  (list mode PASS; --apply gated)
```

## Key file paths

- `D:\Sinister Sanctum\automations\mcp_prune_dormant.py` NEW (this iter)
- `D:\Sinister Sanctum\automations\schtask_stagger.py` NEW (this iter)
- `D:\Sinister Sanctum\automations\start-sinister-session.ps1:1042-1310` (cold-start spawn-phrase; F4/F5 targets)
- `C:\Users\Zonia\.claude\.mcp.json` (now 18 servers; backup retained)
- `D:\Sinister Sanctum\_shared-memory\knowledge\perf-freeze-root-cause-2026-05-24.md` (prior; this entry extends)
- `D:\Sinister Sanctum\_shared-memory\knowledge\fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md` (companion)

## Verification post-fix

Operator can confirm freeze elimination by:
1. Close all running EVE/Claude windows.
2. Re-spawn any lane (e.g., `cmd /c "D:\Sinister Sanctum\Spawn Sanctum Agent.bat" -SoloSanctum`).
3. Time from spawn to first interactive prompt should be < 30 seconds (was 1-10 minutes).
4. If still slow: run F2 + F4 + F5 + F6 from next-iter queue.
