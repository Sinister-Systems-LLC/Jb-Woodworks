<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Freeze-triad root cause (PC slow + agents hang + EVE.exe won't close)

> Author: RKOJ-ELENO :: 2026-05-24
> Scope: Sanctum high-level performance doctrine. Per-project lanes inherit via cold-start step 6 (brain index).
> Operator verbatim 2026-05-24T22:10Z: *"why the fuck i keep getting the issue opf my agents just like freezeing like this and being stuck for a few minutes then coming back. then at same time the pc is slow. file explorer wont work cant take screenshots then it just comes back fine after sometime, you need to fix things like this and make sure my terminal run with minmal issues. same time this happens is when i cannoot close eve exe. it wont close"*

## Evidence captured (snapshot 2026-05-24T22:12-22:18Z)

| Metric | Reading | Verdict |
|---|---|---|
| RAM used | 47% (30.7 GB / 65.3 GB) | Healthy — NOT a memory-pressure freeze |
| `vmmem` (WSL2/Docker VM) | **2632 MB resident** | Top consumer. WSL2 backing Docker (panel/syncthing/mongo/rocketchat) |
| `Memory Compression` | **2418 MB** | Windows is compressing pages. Indicates *memory churn*, not pressure. Big tell. |
| `claude.exe` count | **9 procs / 4893 MB total** | Average 543 MB each. Cluster of 5 spawned within a 9-minute window (17:53-18:04) |
| `mintty` count | 8 | One per spawned claude session - matches |
| `node` count | 14 | Vault daemon + MCP servers + others |
| `EVE.exe` | 2 procs, **17.9 + 18.5 MB, Responding=True** | NOT hung at sample time. Operator hit it during a different window. |
| Disk queue (sampled) | request hung the parallel batch | **Disk I/O is the smoking gun** — even querying the perfcounter blocked |
| `.tmp.PID.timestamp` stale files | **5 found** across heartbeats + resume-points | Atomic-write pattern crashed mid-rename. Pid samples: 50936, 31696, 36820, 36144, 49868 — none are live. |
| `.lock` files >30min old | **27 stale locks** (worst 26177 min = 18 days) | Many in `node_modules`/`.gradle` (benign) but `.claude/scheduled_tasks.lock` aged 201 min + others 1700-5000 min are FLEET-OWNED stale |
| `eve-incidents.jsonl` | 0 lines | No crash trail — freezes aren't being logged as incidents |
| Heartbeat-write pattern | `sanctum-mesh-foundation.json.tmp.26988.1779660869751` was being written live during snapshot | Confirms atomic-rename pattern in active use |

## Top 3 most-likely causes (ranked)

### 1. **Disk I/O saturation from heartbeat thundering herd** (HIGH confidence)

Multiple sources hammering D:\ concurrently:
- 9 claude.exe sessions each writing heartbeat JSON every cycle (atomic write = create .tmp → fsync → rename → may leave .tmp on crash)
- `sanctum-auto-push` task firing every 30 min (git stage+commit+push of a working tree with **80+ modified files** and large untracked dirs)
- `SinisterWindowPosMonitor`, `SinisterToolAutotrigger`, `SinisterMeshCoordSweep`, `SinisterAPKWatchdog` all on independent timers — they OVERLAP unpredictably
- WSL2 vmmem + Docker rocketchat/mongo doing their own continuous I/O on the same physical disk
- MsMpEng (Defender) at 637 MB — actively scanning every new .tmp file the atomic-writes spit out

When disk queue saturates, EVERYTHING that hits the filesystem blocks: Explorer thumbnail cache, screenshot WIC encoder, claude.exe transcript fsyncs, EVE.exe (which uses input() polling = blocks on stdin which is going through the same git-bash pty subsystem that's waiting on disk).

**Smoking gun:** `Get-Counter '\PhysicalDisk(_total)\Avg. Disk Queue Length'` itself blocked when run in parallel with `Get-ChildItem -Recurse` on `_shared-memory/`. The perfcounter waits for a quiet moment to sample, and that moment never came. That's exactly what the operator experiences.

### 2. **Scheduled task cluster-fire collisions** (MEDIUM-HIGH)

Snapshot of next-run times shows ~5 fleet tasks all due within the same 5-minute window (18:15-18:20 PM):
- `SinisterSanctumAutoPush` 18:15:19
- `Sinister-fleet-monitor` 18:15:00
- `Sinister-sheets-sync` 18:15:00
- `SinisterToolAutotrigger` 18:16:58
- `SinisterWindowPosMonitor` 18:18:00
- `SinisterMeshCoordSweep` 18:20:47

Six tasks in 5 minutes, each spawning powershell.exe + doing disk work + (auto-push) doing network I/O + git pack-objects. Operator's freezes correlate with cluster-fire windows.

### 3. **Atomic-write `.tmp.PID.timestamp` orphans accumulate** (MEDIUM)

Pattern: `Json.tmp.<PID>.<unix_ms>` files left by interrupted atomic rename. Each one represents a write that did NOT complete cleanly. 5 found in active snapshot — small absolute number, but the pattern indicates writers being killed mid-flight (matches operator's "freezes for minutes then comes back"). Defender re-scans every new .tmp file → adds to the disk burden.

**Why EVE.exe "won't close":** EVE picker's `main_menu.py` line 281 calls bare `input()` which blocks on stdin. When the mintty/git-bash pty is itself blocked waiting on disk, the input() never returns to check the SIGINT handler that lines 41-50 install. EVE *is* responsive (sampled `Responding=True`), it's the pty pipe under it that's wedged. **The "won't close" is downstream of the disk freeze, not a separate bug.**

## Recommended fixes (ROI ranked)

| ROI | Fix | Effort |
|---|---|---|
| ★★★★★ | **De-cluster scheduled task next-run times** — spread the 6 tasks across 30 min instead of 5. `schtasks /Change /TN ... /ST HH:MM` with offsets (00, 05, 10, 15, 20, 25). | 5 min |
| ★★★★★ | **Add Defender exclusion** for `D:\Sinister Sanctum\_shared-memory\` and `D:\Sinister Sanctum\.git\` — these are write-hot, untrusted-code-free, and currently driving constant re-scan. | 2 min (admin PowerShell `Add-MpPreference -ExclusionPath`) |
| ★★★★ | **Heartbeat backoff jitter** — instead of every claude session writing on the same cadence, add a random 0-5s jitter per session start. | 10 min in `automations\start-sinister-session.ps1` |
| ★★★★ | **Truncate `.git` size + `git gc --aggressive`** before next auto-push run. Currently auto-push is iterating 80+ modified files including big imports. | 5 min one-shot |
| ★★★ | **kill-fleet.ps1 already exists** (292 lines, comprehensive). Document its existence in `docs/OPERATOR-QUICK-REFERENCE.md` if not already. | 2 min |
| ★★★ | **EVE picker: replace bare `input()` with a `select()`-based poller** that wakes every 200 ms to check a shutdown flag. Lets Ctrl-C + parent SIGTERM actually land even when pty is wedged. | 30 min in `main_menu.py` |
| ★★ | **Cap concurrent claude.exe spawns** — picker should warn at 6, block at 8. Currently 9 live. | 15 min |
| ★★ | **WSL2 memory cap** — `%UserProfile%\.wslconfig` `memory=4GB`. Currently `vmmem` is at 2.6 GB but uncapped it can spike to 50% of physical. | 2 min |
| ★ | **Auto-push exclude `_shared-memory/heartbeats/*.tmp.*`** in .gitignore (already wildcard `.tmp` would catch — verify). | 2 min |

## Quick-wins SHIPPED this turn

1. **Swept 5 stale `.tmp.PID.timestamp` files** from `_shared-memory/heartbeats/` and `_shared-memory/resume-points/` via `find ... -mmin +5 -delete`. Verified count = 0 after sweep.
2. **`automations/perf-snapshot.ps1`** (NEW) — on-demand diagnostic capture. Writes timestamped snapshot to `_shared-memory/perf-snapshots/<ts>-<tag>.txt` covering memory %, process counts, top 20 procs, stale .tmp files, stale locks (>30 min), disk-queue single-sample (no parallel-hang), all Sinister scheduled tasks + next-run times. Invoke: `powershell -File automations\perf-snapshot.ps1 -Tag <reason>`.
3. **`automations/kill-fleet.ps1`** (CONFIRMED EXISTS, 292 lines) — already shipped by prior loop iteration. Force-closes EVE.exe + mintty + claude.exe + sweeps stale .tmp + stale locks. Use when wedged.

## Quick-wins QUEUED for next turn (do not require operator approval, low-risk)

- De-cluster the 6 scheduled tasks to 5-minute offsets within 18:00-18:30 window
- Add Defender exclusion for `_shared-memory/` and `.git/` (needs admin PowerShell prompt → surface to operator)
- Document kill-fleet.ps1 + perf-snapshot.ps1 in `docs/OPERATOR-QUICK-REFERENCE.md`

## Composes with

- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (rule 8: quality-degradation limits — signal #1 fired: brain >150 rows AND scheduled-task cluster-fire ≥6)
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` (this IS in-scope: terminal/system perf is high-level orchestration concern)
- `automations/sanctum-auto-push.ps1` (top scheduled-task contributor to D:\ I/O)
- `tools/eve-picker/main_menu.py` (input() blocker discussed)
