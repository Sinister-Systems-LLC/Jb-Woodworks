> **Author:** RKOJ-ELENO :: 2026-05-21
> **Project:** D:\ drive reorg — operator-mandated consolidation
> **Branch:** `agent/sinister-sanctum/cli-dispatcher-2026-05-21`
> **Risk level:** 🔴 HIGH — 1300+ path references at stake

# D:\ drive reorganization plan

## Operator directive (verbatim 2026-05-21)

> "there should only be these folders: Let'sText, Research, change Sinister to Personal and remove all sinister projects from there. Sinister LLC needs to become Sinister Sanctum. no dupe files. Sinister Sanctum will include all sinister projects and everything we need in there like the rkoj etc etc. have one backups folder with all backups we need in it organized and place in their respective places. sinister term-WT and sinister vault need to be in sinister sanctum. full audit the sanctum and clean somethings up. make it all efficient and organized and review how jcode memory and all the shit we have been working on can help things and what we need to do. place the tmp file where it needs to go. add text file to backups Sinister Sanctum folder. complete everything else and create a full plan to complete all this in parallel."

## Section A — current state inventory

### D:\ root (as of 2026-05-21 16:15 UTC)

| Path | Type | Size | Notes |
|---|---|---|---|
| `D:\LetsText\` | dir | small | KEEP — operator's app |
| `D:\Research\` | dir | small | KEEP — research bin |
| `D:\Seagate\` | dir | varies | External drive ref, keep |
| `D:\Sinister\` | dir | large | → rename to `D:\Personal\` |
| `D:\Sinister LLC` | symlink → `D:\Sinister Sanctum` | — | REMOVE (redundant alias) |
| `D:\Sinister Sanctum\` | dir | large | KEEP — main project hub |
| `D:\Sinister-Term-WT\` | dir | ~80 MB | → move into Sanctum |
| `D:\sinister-vault\` | dir | varies | → move into Sanctum (HIGH RISK — 728 refs) |
| `D:\_backups\` | dir | 30+ MB | → rename to `D:\Backups\` + absorb dated backup |
| `D:\sinister-sanctum-backup-2026-05-21\` | dir | 4.4 GB | → move into `D:\Backups\sanctum\daily\` |
| `D:\sinister-sanctum-backup-2026-05-21-robocopy.log` | file | 605 KB | → move into `D:\Backups\_logs\` |
| `D:\tmp\` | dir | small | → triage worktrees, delete or move to Sanctum |
| `D:\$RECYCLE.BIN\` | system | — | leave |
| `D:\System Volume Information\` | system | — | leave |
| `D:\.VolumeIcon.*`, `D:\Autorun.inf` | system | — | leave |

### Sub-inventory of `D:\Sinister\` (needs split)

- `01_Projects/` — has REAL project dirs: Cell-Network, Dashboard-Skeleton, EVE, Inventions, JOKR, LetsText, RKOJ, Sinister, _vault, _README.md — **these are the "sinister projects" operator wants moved**
- `02_Personal/` — Family, Finances, Health, Notes, _vault — **stays in Personal**
- `03_Games/` — operator stuff, stays in Personal
- `04_Reference/` — stays in Personal
- `05_Media/` — stays in Personal
- `06_Tools/` — has junctions (Apps@, Coding@, Tools-Desktop@, _tools@, platform-tools@, usb_driver@) + Sinister-Bats subdir — **the Sinister-Bats may be relevant to Sanctum**
- `07_Archive/` — stays in Personal
- `Sanctum@` — junction → likely to `D:\Sinister Sanctum\` — **remove (redundant)**
- `Sinister Skills/` — heavyweight skills hub, **566 refs from Sanctum tree** — HIGH RISK to move
- `_vault/` — stays in Personal (separate from sinister-vault)
- `local-secrets/`, `old/` — Personal junk

### Reference impact count (from grep against Sanctum tree)

| Pattern | Count | Notes |
|---|---|---|
| `D:\Sinister\` (excluding "Sinister Sanctum") | 0 | direct refs all qualified — surprisingly low |
| `Sinister Skills` (anywhere) | **566** | path refs to D:\Sinister\Sinister Skills\... |
| `sinister-vault` (anywhere) | **728** | refs to D:\sinister-vault\... |
| `Sinister-Term-WT` | **10** | low impact |

**Net assessment**: Moving `Sinister Skills` and `sinister-vault` breaks ~1300 references. Renaming `D:\Sinister` → `D:\Personal` is feasible (0 direct refs) IF we move `Sinister Skills` and `_vault` OUT first.

## Section B — desired end state

```
D:\
├── LetsText\
├── Research\
├── Personal\                            (was D:\Sinister\)
│   ├── 02_Personal\
│   ├── 03_Games\
│   ├── 04_Reference\
│   ├── 05_Media\
│   ├── 07_Archive\
│   ├── _vault\                          (personal vault, NOT the sinister-vault)
│   ├── local-secrets\
│   └── old\
├── Sinister Sanctum\
│   ├── (existing tree)
│   ├── _sinister-skills\                (← MOVED from D:\Sinister\Sinister Skills\, OR keep as junction in old location for compat)
│   ├── _vault\                          (← MOVED from D:\sinister-vault\)
│   ├── projects\
│   │   ├── rkoj\                        (existing umbrella)
│   │   ├── sinister-cell-network\       (← MOVED from D:\Sinister\01_Projects\Cell-Network\)
│   │   ├── sinister-dashboard\          (← MOVED from D:\Sinister\01_Projects\Dashboard-Skeleton\)
│   │   ├── sinister-eve\                (← MOVED from D:\Sinister\01_Projects\EVE\)
│   │   ├── sinister-inventions\         (← MOVED from D:\Sinister\01_Projects\Inventions\)
│   │   ├── sinister-jokr\               (← MOVED from D:\Sinister\01_Projects\JOKR\)
│   │   ├── sinister-letstext\           (← MOVED from D:\Sinister\01_Projects\LetsText\)
│   │   ├── sinister-rkoj-personal\      (← MOVED from D:\Sinister\01_Projects\RKOJ\)
│   │   └── (existing sinister-* projects already in Sanctum)
│   ├── worktrees\
│   │   ├── sinister-term-wt\            (← MOVED from D:\Sinister-Term-WT\)
│   │   └── sanctum-worktrees\           (← MOVED from D:\tmp\sanctum-worktree-*\)
│   └── (rest of Sanctum tree)
└── Backups\                              (renamed from _backups, absorbs dated backup)
    ├── README.md
    ├── MANIFEST.md                      (NEW — operator-requested text file)
    ├── _config\                         (existing custodian config)
    ├── _logs\                           (existing + robocopy log moved here)
    ├── _manifest.jsonl                  (existing custodian ledger)
    ├── snapshots\                       (existing custodian sources)
    │   ├── sinister-skills-hub\
    │   ├── sinister-sanctum-llc\
    │   ├── sinister-panel-source-canonical\
    │   └── sinister-panel-source-legacy\
    └── sanctum-daily\                   (NEW — dated robocopy backups)
        └── 2026-05-21\                  (← MOVED from D:\sinister-sanctum-backup-2026-05-21\)
```

## Section C — phased execution plan

### 🟢 Phase 1 — SAFE (no destructive ops, can run autonomously)

| # | Step | Risk | Reversible |
|---|---|---|---|
| 1 | Write reference-audit script: scan ALL files in Sanctum + scripts for `D:\Sinister\`, `D:\sinister-vault\`, `D:\Sinister-Term-WT\`, `Sinister Skills` paths → produce `_shared-memory/audits/d-drive-path-refs-2026-05-21.json` | low | yes |
| 2 | Create `D:\Backups\` (new dir) + `MANIFEST.md` text file inside it | low | yes |
| 3 | Triage `D:\tmp\sanctum-worktree-*` — these are stale agent worktrees; check git status, then remove if clean | medium | reversible (just delete empty) |
| 4 | Move `D:\sinister-sanctum-backup-2026-05-21-robocopy.log` → `D:\Backups\_logs\sanctum-daily-2026-05-21.log` | low | yes |
| 5 | Write a compat-shim plan: for every `Sinister Skills` ref and `sinister-vault` ref, list the file:line, the current value, the proposed value | low | yes |
| 6 | Sweep `_shared-memory/audits/dedupe-2026-05-21.md` (already shipped by agent I) — apply more aggressive removals after operator review | low | yes |

### 🟡 Phase 2 — MEDIUM RISK (operator-gated, reversible with symlinks)

| # | Step | Risk | Reversible |
|---|---|---|---|
| 7 | Move `D:\sinister-sanctum-backup-2026-05-21\` → `D:\Backups\sanctum-daily\2026-05-21\` | medium | yes (move back) |
| 8 | Rename `D:\_backups\` → `D:\Backups\` (merge with the new dir from Phase 1 step 2) | medium | yes |
| 9 | Remove `D:\Sinister LLC` symlink (already redundant — points to Sinister Sanctum) | low | yes (recreate symlink) |
| 10 | Move `D:\Sinister-Term-WT\` → `D:\Sinister Sanctum\worktrees\sinister-term-wt\` + create junction `D:\Sinister-Term-WT` → new path (backward compat) | medium | yes |

### 🔴 Phase 3 — HIGH RISK (operator-gated, requires careful execution)

| # | Step | Risk | Reversible |
|---|---|---|---|
| 11 | Move `D:\sinister-vault\` → `D:\Sinister Sanctum\_vault\` + create junction `D:\sinister-vault` → new path (preserves 728 refs) | **HIGH** | yes (move back, recreate junction) |
| 12 | Move `D:\Sinister\Sinister Skills\` → `D:\Sinister Sanctum\_sinister-skills\` + create junction `D:\Sinister\Sinister Skills` → new path (preserves 566 refs) | **HIGH** | yes (move back, recreate junction) |
| 13 | Move project dirs from `D:\Sinister\01_Projects\` → `D:\Sinister Sanctum\projects\sinister-*\` for: Cell-Network, Dashboard-Skeleton, EVE, Inventions, JOKR, LetsText, RKOJ, Sinister. Add MANIFEST.json entries to `projects/rkoj/MANIFEST.json` | **HIGH** | yes (move back) |
| 14 | Rename `D:\Sinister\` → `D:\Personal\` (after steps 11-13 leave only Personal content) | **HIGH** | yes (rename back) |
| 15 | Update CLAUDE.md + all docs to reference new paths (use new junctions for backward compat in scripts) | medium | yes (git revert) |

## Section D — parallel execution (Phase 1 only, autonomous)

Spawn 5 parallel sub-agents:

| Agent | Mission |
|---|---|
| **D1-A** | Run reference-audit script + produce JSON with every refs across Sanctum tree |
| **D1-B** | Create `D:\Backups\` + add `MANIFEST.md` (operator-requested text file) with current state |
| **D1-C** | Triage `D:\tmp\sanctum-worktree-*\` — check git linkage, archive stale ones |
| **D1-D** | Move `D:\sinister-sanctum-backup-2026-05-21-robocopy.log` to `D:\Backups\_logs\` |
| **D1-E** | Audit `D:\Sinister\01_Projects\` subdirs — are they git repos? have remotes? what's their state? |

After all 5 return, present consolidated report. ASK OPERATOR before proceeding to Phase 2/3.

## Section E — what jcode memory can do for this reorg

The brain entry `_shared-memory/knowledge/jcode-agentic-loop-patterns-port-to-python.md` covers session_search + BM25. Applied here:

- After Phase 1 audit completes, the JSON output gets indexed by `forge_memory_bridge.write()` so future agents can grep "Sinister Skills" via BM25-scored recall
- The dated backup at `D:\Backups\sanctum-daily\2026-05-21\` is queryable as a historical session snapshot via `session_search` if we extend its scope
- The MANIFEST.md text file is the human-readable index; the JSON sidecar (next to it) is the machine-readable

## Section F — cleanup audit findings (efficiency)

From agent I's dedupe sweep (`789ab3c`):
- 5,084 files / 1.68 GB scanned
- 120 hash-duplicate groups (67 over 1 KB)
- 381 same-name different-content groups
- 106 groups flagged for operator review (`.md`/`.py`/`.json`/`.png`)
- 15 already-safe removed (caches, logs > 7 days)

Recommended additional dedupe targets (operator approves first):
- Old `.log` files in `automations/build/forge-exe/` (already gitignored, can purge anything > 7 days)
- `_shared-memory/forge-memory/_archive/` (if exists)
- `.claude/worktrees/*` (ephemeral, can delete on session end)
- Duplicate resume-points where mtime difference > 1 hour

## Section G — DO / DON'T checklist for operator

### ✅ DO right now (Phase 1, autonomous)
- [ ] Spawn the 5 parallel D1-A through D1-E agents
- [ ] Write the consolidated Phase 1 report
- [ ] Drop a broadcast about the in-flight Phase 1 work

### ⚠️ ASK OPERATOR before doing (Phase 2/3)
- [ ] Move `D:\sinister-vault\` (728 refs at stake — use junction shim)
- [ ] Move `D:\Sinister\Sinister Skills\` (566 refs — use junction shim)
- [ ] Rename `D:\Sinister\` → `D:\Personal\`
- [ ] Move 8 project dirs from D:\Sinister\01_Projects\

### 🛑 NEVER do without operator confirmation
- Delete any file in `D:\Sinister\` without backup
- Delete `D:\sinister-vault\` (auth keys, accounts data)
- Push any changes to GitHub
- Modify `~/.claude/.mcp.json` (operator territory)

## Section H — rollback plan

If anything goes wrong after Phase 2/3 execution:
1. `git -C "D:\Sinister Sanctum" reset --hard HEAD@{1}` (only affects Sanctum repo)
2. Move directories back: `mv "D:\Sinister Sanctum\_vault" "D:\sinister-vault"` etc.
3. Re-create junctions if removed: `mklink /J "D:\sinister-vault" "D:\Sinister Sanctum\_vault"`
4. Verify with `python -c "import sinister_login; print(sinister_login.wallet())"` — should still work via junction

---

## Verdict

**Phase 1 is SAFE — autonomous execution starts now.**
**Phases 2-3 are OPERATOR-GATED — explicit "go" required before execution.**

Junctions + symlinks are the safety net. They let us move physical files while preserving all 1300+ path references via transparent redirects. No source code edits needed for the moves themselves.
