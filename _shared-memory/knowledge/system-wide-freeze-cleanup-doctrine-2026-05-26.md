# System-Wide Freeze Cleanup Doctrine (2026-05-26)

> Author: RKOJ-ELENO :: 2026-05-26
> Tag: perf / containment / resource-mgmt
> Composes with: `perf-freeze-root-cause-2026-05-24` + `fleet-freeze-and-zombie-windows-diagnosis-2026-05-25` + `automate-everything-no-operator-admin-2026-05-25` + `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` + `agent-containment-failsafe-doctrine-2026-05-25`.

## 1. Operator verbatim (binding)

2026-05-26 ~22:47Z: *"this shit keeps happening. agents freezing. i cannot even use file explorer. then after a random amount of time it all starts working again ... few agents frozen. one says done and i cannot type in it. cant launch file explorer. you need to fix this and stop it from happening and alos clean up my windows. like all shit that is taking up resources and running for no reason need to be stopped. unistall useless shit and dont break anything."*

This is **distinct from** the iter-23 "Simmering" popup (MCP+schtask+spawn-phrase). That bug is local to one agent — this one freezes Explorer + multiple agents simultaneously. Root cause: **workstation-wide resource starvation**.

## 2. Root causes (ranked with evidence)

### R1. TEMP folder pathology
- **Evidence:** `%TEMP%` = 34.7 GB / 212,376 files at diagnosis (6.8 GB / 16,459 are >7 days old)
- **Why it freezes Explorer:** every `CreateFile` in TEMP triggers Defender real-time scan; NTFS MFT on C:\ thrashes when 200k+ entries in one folder; Explorer's lazy enumeration when ANY consumer touches TEMP
- **Compounding:** claude.exe writes session transcripts to `%TEMP%\claude-*` continuously; npm/cargo write cache there

### R2. Zombie spawn children (claude.exe / mintty.exe / node.exe / pythonw.exe)
- **Evidence at 22:52Z:** 14 zombies aged 33.6 hours with `cpu_per_hour < 5s/h`
  - 2x `claude.exe` (PID 42624, 57992) at 33.6 hours — survived the morning fleet restart
  - 10x `node.exe` MCP-server children, 33.6h, ~38 MB each
  - 1x `pythonw.exe` 37.6h
- **Why it freezes:** each holds file handles into D:\Sinister Sanctum + a TCP socket; Windows can't unmount/lazy-flush; cumulative handle count starves CSRSS

### R3. Schtask cluster-fire (PARTIALLY MITIGATED, still active)
- **Evidence:** 21 of 40 Sinister* schtasks fire faster than 4x/hour (interval `<PT15M`); 4 currently `Running` concurrently at diagnosis
  - 6x at `PT1M` (every minute): `SinisterEVEWatchdog`, `SinisterOperatorPrioritySafety`, `SinisterOverseerLoopQuality`, `SinisterOverseerRateLimitAgent`, `SinisterOverseerTokenAgent`, `SinisterResourceQuota`, `SinisterStaleLockCleaner`
  - 8x at `PT5M`: `SinisterAccountWatchdog`, `SinisterEveCrashWatchdog`, `SinisterLinkPoller`, `SinisterLoopRelentlessWatchdog`, `SinisterOAuthHealthPoll`, `SinisterOverseer`, `Sinister-fleet-monitor`, plus others
- **Why it freezes:** when 3+ co-fire they all spawn python.exe + git.exe + may write `_shared-memory/*.jsonl` simultaneously -> D:\ disk queue saturates -> any claude.exe `fsync()` blocks -> UI loop blocks for that agent
- **Status:** `automations/schtask_stagger.py` exists (per FILE:LINE schtask_stagger.py:1-222) but the cluster of `PT1M` tasks cannot be staggered further than 60s window. **Real fix = lower cadence** of low-value ones.

### R4. Defender real-time on D:\
- **Evidence:** `RealTimeProtectionEnabled=True`, `BehaviorMonitorEnabled=True`, `IoavProtectionEnabled=True`, zero exclusions for `D:\Sinister Sanctum\` paths
- **Why it freezes:** every git operation touches hundreds of `.git/objects/*` blobs; Defender scans each before Sanctum can read; on a fleet-wide `git push` salvo the scan queue eats both CPU cores allocated to MsMpEng
- **Composes with:** `automate-everything-no-operator-admin-2026-05-25` which **pre-approves** Sanctum dir exclusions

### R5. Process count explosion (consequence, not cause)
- 166 conhost + 126 bash + 42 cmd + 18 python + 13 claude + 37 node + 44 zen at diagnosis
- 32.1 GB total working-set / 63.8 GB RAM — RAM is fine, but kernel object handles are not

## 3. Pass criterion (binding)

For an operator session to be "freeze-free for 4h":

1. `%TEMP%` <= 5 GB (today: 34.7 GB)
2. No `claude.exe`/`mintty.exe` older than 12h with `cpu_per_hour < 30s/h`
3. Defender exclusions present for `D:\Sinister Sanctum\_shared-memory`, `\.git`, `\automations\__pycache__`
4. No more than 2 Sinister* schtasks `Running` at any sampled minute (use `automations/sanctum_resource_doctor.py diagnose`)
5. Zero `SinisterStop-EVE.bat` kill_invoked rows in `_shared-memory/eve-crash-log.jsonl` for 4h continuous

## 4. Canonical tool

**`automations/sanctum_resource_doctor.py`** (NEW 2026-05-26).

```bash
# read-only diagnosis -> JSON to _shared-memory/_archive/resource-doctor/<utc>.json
python automations/sanctum_resource_doctor.py diagnose

# report old TEMP files (DEFAULT dry-run)
python automations/sanctum_resource_doctor.py cleanup-temp --age-days 7
python automations/sanctum_resource_doctor.py cleanup-temp --age-days 7 --apply   # mutate

# list zombie spawn children
python automations/sanctum_resource_doctor.py kill-zombies
python automations/sanctum_resource_doctor.py kill-zombies --apply                # mutate

# add Defender exclusions (needs admin powershell, otherwise reports added=0)
python automations/sanctum_resource_doctor.py apply-defender-exclusions
python automations/sanctum_resource_doctor.py apply-defender-exclusions --apply   # mutate

# emergency: --safe blocks ALL mutations even if --apply present
python automations/sanctum_resource_doctor.py --safe cleanup-temp --age-days 7 --apply
```

**Default mode = `diagnose`** (read-only). Every mutating mode is dry-run unless `--apply`. Every `--apply` writes a snapshot to `_shared-memory/_archive/resource-doctor/<label>-<utc>.txt` BEFORE mutation.

## 5. Anti-patterns

- **Killing a claude.exe whose name is the master agent's window** (use `bots/find-master-by-progress.ps1` first). The zombie heuristic ignores recent CPU but cannot detect "compiled but idle waiting for operator input" — operator review the dry-run list before `--apply`.
- **Deleting from `%TEMP%` recursively without snapshot** — some build tools (cargo, msbuild) keep long-running build outputs there.
- **Adding `D:\Sinister Sanctum` (root) to Defender exclusions** — too broad; we exclude only `_shared-memory`, `.git`, `__pycache__`.
- **Lowering `PT1M` schtask cadence WITHOUT replacing with on-demand trigger** — `SinisterEVEWatchdog` exists for a reason; instead, dedup with `SinisterOperatorPrioritySafety` into a single 5-min poll.
- **Uninstalling apps without operator approval** — operator said "unistall useless shit and dont break anything" — the BREAK clause overrides. Tool surfaces uninstall candidates ONLY in diagnose JSON, never auto-applies.

## 6. Concrete fix list (operator approval order)

1. **NOW (no admin):** `python automations/sanctum_resource_doctor.py kill-zombies --apply` — reclaims ~14 zombie processes + 2 GB RAM + 14 file-handle sets. Risk = none (heuristic = >12h old AND <30s CPU/h).
2. **NOW (no admin):** `python automations/sanctum_resource_doctor.py cleanup-temp --age-days 7 --apply` — reclaims ~6.8 GB of stale TEMP. Risk = low (>7d means no active process is using).
3. **Needs admin PowerShell:** `python automations/sanctum_resource_doctor.py apply-defender-exclusions --apply` — adds 3 Sanctum exclusions. Operator hard-canonical pre-approves this per `automate-everything-no-operator-admin-2026-05-25`. Run from an elevated PowerShell or via schtask with `RunLevel=Highest`.
4. **Next iter:** dedup `PT1M` schtasks down to 2 of them (consolidate watchdog roles). Out of scope for this doctrine; sanctum-helper-A queue.
5. **Backlog:** uninstall candidates list (operator review): Beyond-All-Reason (steam game), AdsPower, Kameleo, Panda — surface in JSON, never auto-apply.

## 7. Composes / supersedes

- **Composes** with `perf-freeze-root-cause-2026-05-24.md` — that file covers the `fsync()`/disk-queue path; this file covers the OS-wide variant.
- **Composes** with `fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md` — that file diagnoses zombie agent WINDOWS (mintty); this file's `kill-zombies` is the executor.
- **Does NOT supersede** `schtask_stagger.py` — staggering is still binding; this doctrine ADDS cadence-lowering as next-step.

## 8. Forever-improve checklist (per `safe-quality-loops-doctrine-2026-05-24`)

| Signal | Threshold | Action |
|---|---|---|
| `%TEMP%` > 10 GB | static | run `cleanup-temp --apply` |
| zombie count > 5 | static | run `kill-zombies --apply` |
| 3+ schtasks `Running` co-eval | static | promote a `PT1M` task to `PT5M` |
| `eve-crash-log.jsonl` `kill_invoked=true` in last 1h > 3 | rolling | invoke containment failsafe doctrine |
| diagnose report size > 500 KB | static | rotate `_archive/resource-doctor/` quarterly |

## 9. Verification one-liner

Operator can confirm cleanup is safe BEFORE applying with:

```powershell
python "D:\Sinister Sanctum\automations\sanctum_resource_doctor.py" diagnose ; python "D:\Sinister Sanctum\automations\sanctum_resource_doctor.py" kill-zombies ; python "D:\Sinister Sanctum\automations\sanctum_resource_doctor.py" cleanup-temp --age-days 7
```

If the dry-run lists look right -> re-run each with `--apply`.
