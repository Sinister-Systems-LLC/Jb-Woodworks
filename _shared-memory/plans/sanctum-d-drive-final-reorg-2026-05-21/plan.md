# Author: RKOJ-ELENO :: 2026-05-21

# Sanctum :: D-drive final reorg + RKOJ workstation completion + test plan

> Generated in response to operator directive 2026-05-21 ~18:00 (verbatim):
>
> *"i want to organize d drive. clean sinister folder of sinister projects and call it Personal now. add sinister term and sinister vault to sinister sanctum. Sinister sanctum is main working file you need to clean that up and make it all efficent with the jcode addtions. we should ahve one backups folder in the d drive not two. make sure its oragnized to owith a readme and backup sanctum every 24 hours. make sure we have exe RKOJ start and a back up bat file in the sanctum main directory. make sure everything in the sanctum is pushed to github and get to work to complete the entire rkoj workstation. eevrything for that should be in one folder. clean up things we dont need in the sanctum as well. create a plan to complete and test all this and what iasked for on rkoj"*

## Headline state (pre-flight survey)

- **Branch ahead 59 commits** vs origin (auto-push skips non-main branches — see auto-push.log "skipped | not-on-target-branch"). Pushing the agent branch is master-actionable + safe (operator-canonical only blocks `main` pushes).
- **D:/Sinister/01_Projects/** still hosts residual Sinister projects: `JOKR/` (JOKR-Global + Library-of-JOKR + Logo-Options + _vault), `Sinister/` (Kernel-SU-Setup, Library-of-Alexandria, Sinister-APK, Sinister-Bumble-EMU, Sinister-Emulator-Bundle), `RKOJ/` (Sinister-Drone + Sinister-Mobile + CLAUDE.md). Some are dupes of already-migrated projects/sinister-* dirs; some are NEW that need moving.
- **D:/_backups/** still has `_logs/`, `_manifest.jsonl` (16.7 MB), `snapshots/` because custodian daemon held locks during Phase 2. Gated on operator stopping the daemon.
- **D:/Sinister-Term-WT@** + **D:/sinister-vault@** are both junctions pointing inside Sanctum — Sinister Term + Sinister Vault are already integrated; no move needed. Only the junction-source paths can be removed once the operator confirms no live process binds them.
- **Sanctum root has 7 stale artifacts**: `test-out.log`, `test-personal-out.log`, `test-runner-stderr.log`, `test-runner-stdout.log`, `test-stderr2.log`, `test-stdout2.log`, `tmp-recover-sanctum-2026-05-21-batch8/` — cleanup targets.
- **No RKOJ-Start.bat or Backup-Sanctum.bat in Sanctum root** — operator-facing entry points missing.
- **No D:/Backups/README.md** (a MANIFEST.md does exist; needs README equivalent).
- **No 24h scheduled task for Sanctum backup** — sanctum-backup tool exists (`tools/sanctum-backup/`, 47/47 tests per commit `178fbcf`) but not scheduled.

## Phase index

| Phase | Goal | Master-actionable? | Risk |
|---|---|---|---|
| **PUSH** | Push 59 ahead commits to origin | Yes | Low |
| **CLEAN** | Delete 7 stale artifacts in Sanctum root | Yes | Low |
| **BATS** | RKOJ-Start.bat + Backup-Sanctum.bat in Sanctum root | Yes | Low |
| **README** | D:/Backups/README.md | Yes | Low |
| **TASK** | Install 24h SinisterSanctumDailyBackup scheduled task | Operator-gated (UAC) | Medium |
| **CUSTODIAN** | Stop custodian daemon + drain _backups → Backups + remove _backups | Operator-gated | Medium |
| **PROJECTS** | Move residual D:/Sinister/01_Projects Sinister-themed dirs into Sanctum/projects/* | Yes (per-project) | Medium |
| **RENAME** | Rename D:/Sinister → D:/Personal | Operator-gated (high-impact) | High |
| **RKOJ-VERIFY** | Verify every MANIFEST component works | Yes | Low |
| **TEST** | RKOJ.exe v1.3.0 end-to-end smoke test | Operator-driven UI | Low |

## PHASE PUSH — Push 59 commits to origin (master-actionable, low risk)

**Gap.** Auto-push log shows steady `skipped | not-on-target-branch current=agent/sinister-sanctum/cli-dispatcher-2026-05-21 target=main` because the daemon only pushes when on `main`. Branch is 59 commits ahead. Operator's "make sure everything in the sanctum is pushed to github" is the ask.

- **EXACT-INSTRUCTIONS:** `git push origin agent/sinister-sanctum/cli-dispatcher-2026-05-21`. Push the agent branch (not main — main pushes are still operator-gated per canonical-3).
- **EXPECTED-OUTPUT:** `Total NN (delta NN), reused NN (delta NN)` + `To https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git`.
- **VERIFICATION:** `git status -sb` shows `[ahead 0]` or no ahead marker.
- **RISK:** Branch is public on GitHub. Sinister-Systems-LLC is operator's own org so secret-leak risk is operator-acknowledged. The 59 commits are RKOJ docs + brain entries + cross-agent messages — no secrets known.
- **COMMIT-MESSAGE:** N/A (push only).
- **Status:** ready, master-actionable.

## PHASE CLEAN — Remove 7 stale artifacts in Sanctum root

**Gap.** Sanctum root has accumulated test logs + a recovery tmp dir. Operator's "clean up things we dont need in the sanctum" applies.

Targets:
1. `test-out.log`
2. `test-personal-out.log`
3. `test-runner-stderr.log`
4. `test-runner-stdout.log`
5. `test-stderr2.log`
6. `test-stdout2.log`
7. `tmp-recover-sanctum-2026-05-21-batch8/`

- **EXACT-INSTRUCTIONS:** For each test-*.log: verify size + last-mtime (anything mtime >7d old is safe; anything mtime <1h is a live run — defer). For tmp-recover-* dir: list contents, archive if non-empty into `_archive/recovery-2026-05-21/`, otherwise `rmdir`. Then `rm -f` each log.
- **EXPECTED-OUTPUT:** D:/Sinister Sanctum/ root reduced by ~6-7 entries; nothing breaks.
- **VERIFICATION:** `ls "D:/Sinister Sanctum/" | grep -E "(test-|tmp-recover-)"` returns empty.
- **RISK:** Low if mtime check skips live runs.
- **COMMIT-MESSAGE:** `chore(sanctum): root cleanup — remove stale test-*.log + tmp-recover-* artifacts`
- **Status:** ready, master-actionable.

## PHASE BATS — One-click entry points at Sanctum root

**Gap.** Operator wants `RKOJ-Start.bat` (launch the RKOJ.exe) + `Backup-Sanctum.bat` (trigger a manual Sanctum backup) at `D:/Sinister Sanctum/` root for one-click access.

### BATS-1 — `RKOJ-Start.bat`

- **EXACT-INSTRUCTIONS:** Write `D:/Sinister Sanctum/RKOJ-Start.bat`:
  ```bat
  @echo off
  REM Author: RKOJ-ELENO :: 2026-05-21
  REM One-click launcher for RKOJ.exe (Forge TUI default).
  set EXE_DESKTOP=%USERPROFILE%\Desktop\RKOJ.exe
  set EXE_BUILD=%~dp0automations\build\forge-exe\dist\RKOJ.exe
  if exist "%EXE_DESKTOP%" ( start "" "%EXE_DESKTOP%" & exit /b 0 )
  if exist "%EXE_BUILD%"   ( start "" "%EXE_BUILD%"   & exit /b 0 )
  echo [RKOJ-Start] RKOJ.exe not found on Desktop or in build/dist.
  echo Run: pwsh automations\build\forge-exe\build.ps1 to build, OR re-run the RKOJ-Setup wizard.
  pause
  ```
- **EXPECTED-OUTPUT:** double-click launches RKOJ.exe v1.3.0 (Forge TUI default).
- **VERIFICATION:** `cmd /c "D:\Sinister Sanctum\RKOJ-Start.bat"` launches a window; close it cleanly.
- **COMMIT-MESSAGE:** `feat(sanctum): RKOJ-Start.bat + Backup-Sanctum.bat one-click entry points at root`

### BATS-2 — `Backup-Sanctum.bat`

- **EXACT-INSTRUCTIONS:** Write `D:/Sinister Sanctum/Backup-Sanctum.bat`:
  ```bat
  @echo off
  REM Author: RKOJ-ELENO :: 2026-05-21
  REM Manual Sanctum backup → D:/Backups/sanctum-daily/<YYYY-MM-DD>/
  REM Calls the sanctum-backup tool (commit 178fbcf, 47/47 tests).
  set DATE_STAMP=%date:~10,4%-%date:~4,2%-%date:~7,2%
  set DEST=D:\Backups\sanctum-daily\%DATE_STAMP%
  if not exist "%DEST%" mkdir "%DEST%"
  pushd "%~dp0"
  python -m tools.sanctum-backup.run --dest "%DEST%" --retention-days 7
  popd
  echo [Backup-Sanctum] Done. Dest: %DEST%
  pause
  ```
- **EXPECTED-OUTPUT:** runs the sanctum-backup tool, writes to `D:/Backups/sanctum-daily/<today>/`.
- **VERIFICATION:** ls `D:/Backups/sanctum-daily/<today>/` after run shows snapshot files.
- **NOTE:** Calls `tools/sanctum-backup/run.py` — verify the exact entry-point matches the tool's actual CLI; adjust if needed.

## PHASE README — D:/Backups/README.md

**Gap.** `D:/Backups/MANIFEST.md` exists (Phase 1) but no README. Operator wants a README.

- **EXACT-INSTRUCTIONS:** Write `D:/Backups/README.md`. Sections: (1) Purpose — single backup root for the Sinister Sanctum workstation. (2) Layout — `sanctum-daily/<YYYY-MM-DD>/` (24h scheduled), `custodian/` (live mirror from custodian daemon), `_logs/` (daemon + manual run logs), `_config/` (retention configs), `_manifest.jsonl` (append-only event log). (3) Retention — 7d for sanctum-daily, custodian retains rolling-30d, _logs retains 90d. (4) Restore — point at the snapshot dir + run sanctum-backup --restore. (5) Sources tracked. (6) Pointer to MANIFEST.md for full Phase 1/2 history.
- **EXPECTED-OUTPUT:** `D:/Backups/README.md` ~80 lines.
- **VERIFICATION:** file exists; opens cleanly.
- **COMMIT-MESSAGE:** `docs(backups): D:/Backups/README.md — purpose + layout + retention + restore steps`
- **NOTE:** This file lives OUTSIDE the Sanctum git repo (`D:/Backups/` is not tracked). Either commit a copy in `_shared-memory/operator-docs/D-Backups-README.md` for version history OR leave as on-disk-only. The plan picks the former (track a copy under `_shared-memory/operator-docs/`).

## PHASE TASK — Install 24h SinisterSanctumDailyBackup scheduled task

**Gap.** Operator wants automatic Sanctum backup every 24h. Tool exists (`tools/sanctum-backup/`); scheduled task does not.

- **EXACT-INSTRUCTIONS:** Operator (elevated UAC) runs `automations/install-sanctum-daily-task.ps1` (NEW file to be created — registers `SinisterSanctumDailyBackup` schtask, daily at 03:00, action = `D:/Sinister Sanctum/Backup-Sanctum.bat`).
- **EXPECTED-OUTPUT:** `schtasks /Query /TN SinisterSanctumDailyBackup` returns the task with `Next Run Time` set + `Status: Ready`.
- **VERIFICATION:** Within 24h of install, `D:/Backups/sanctum-daily/<tomorrow>/` exists.
- **GATING:** Operator-gated because schtask install needs UAC elevation.
- **COMMIT-MESSAGE:** `feat(automations): install-sanctum-daily-task.ps1 — 24h scheduled Sanctum backup`

## PHASE CUSTODIAN — Drain D:/_backups → D:/Backups + remove _backups

**Gap.** D:/_backups/ leftover from Phase 2: `_logs/`, `_manifest.jsonl` (16.7 MB), `snapshots/`. Custodian daemon held locks at Phase 2 time. Operator: "we should have one backups folder in the d drive not two".

- **EXACT-INSTRUCTIONS:**
  1. Operator stops custodian daemon: `Stop-Process -Name 'custodian*' -Force` OR via Task Manager → end "custodian" task.
  2. Master moves: `Move-Item D:/_backups/_logs D:/Backups/_logs-custodian -Force` (if name collides, suffix `-custodian`); `Move-Item D:/_backups/_manifest.jsonl D:/Backups/_manifest-custodian.jsonl -Force`; `Move-Item D:/_backups/snapshots D:/Backups/custodian/snapshots -Force` (merge into existing `custodian/`).
  3. `Remove-Item D:/_backups -Recurse -Force`.
  4. Operator restarts custodian with config pointed at `D:/Backups/custodian/` instead of `D:/_backups/`.
- **EXPECTED-OUTPUT:** `D:/_backups` no longer exists. `D:/Backups` is the only backup root.
- **VERIFICATION:** `ls D:/ | grep -i backup` returns only `Backups`.
- **GATING:** Operator stops + restarts the daemon (master can't end an operator process safely).
- **COMMIT-MESSAGE:** `chore(sanctum): custodian _backups final consolidation into D:/Backups`

## PHASE PROJECTS — Move residual Sinister-themed dirs from D:/Sinister/01_Projects/ into Sanctum/projects/*

**Gap.** D:/Sinister/01_Projects/ still has Sinister-themed content. Some is duplicate (already migrated to Sanctum/projects/sinister-*), some is unique.

### Mapping table

| Source path | Status | Action |
|---|---|---|
| `D:/Sinister/01_Projects/JOKR/JOKR-Global/` | Already migrated to `projects/sinister-jokr/JOKR-Global/` per `55f7c7f`. | Verify dest, then remove src. |
| `D:/Sinister/01_Projects/JOKR/Library-of-JOKR/` | NEW (not yet migrated). | Move to `projects/sinister-jokr/Library-of-JOKR/`. |
| `D:/Sinister/01_Projects/JOKR/Logo-Options/` | NEW. | Move to `projects/sinister-jokr/Logo-Options/`. |
| `D:/Sinister/01_Projects/JOKR/_vault/` | Project-scoped vault. | Move to `projects/sinister-jokr/_vault/` (gitignore). |
| `D:/Sinister/01_Projects/Sinister/Kernel-SU-Setup/` | Sinister-themed Android root setup. | Move to `projects/sinister-kernel-su-setup/`. New MANIFEST row. |
| `D:/Sinister/01_Projects/Sinister/Library-of-Alexandria/` | Sinister-themed knowledge base. | Move to `projects/sinister-library-of-alexandria/`. New MANIFEST row. |
| `D:/Sinister/01_Projects/Sinister/Sinister-APK/` | DUPE of `projects/sinister-kernel-apk/`? | Compare contents; if dupe → remove src; if not → archive src to `_archive/`. |
| `D:/Sinister/01_Projects/Sinister/Sinister-Bumble-EMU/` | DUPE of `projects/sinister-bumble-emu/`? | Compare; remove or archive src. |
| `D:/Sinister/01_Projects/Sinister/Sinister-Emulator-Bundle/` | DUPE of `projects/sinister-emulator-bundle/`? | Compare; remove or archive src. |
| `D:/Sinister/01_Projects/RKOJ/Sinister-Drone/` | NEW Sinister-themed sub. | Move to `projects/sinister-drone/`. New MANIFEST row. |
| `D:/Sinister/01_Projects/RKOJ/Sinister-Mobile/` | NEW Sinister-themed sub. | Move to `projects/sinister-mobile/`. New MANIFEST row. |
| `D:/Sinister/01_Projects/Inventions/` | Has CLAUDE.md + SESSION-START.md only — pointer dir, not an active project. | Compare to `D:/Sinister Sanctum/inventions/`; if pointer-only → leave or remove src. |
| `D:/Sinister/01_Projects/_vault/_index.md` | Cross-project vault index. | Merge into `_vault-personal/_index.md` or archive. |

- **EXACT-INSTRUCTIONS:** For each row, perform: (a) `diff -r` between src + intended dest (if dest exists) — if identical, rm src; (b) if dest doesn't exist, `mv src projects/sinister-<slug>/`; (c) update `projects/rkoj/MANIFEST.json` with new components for the 4 NEW ones (kernel-su-setup, library-of-alexandria, drone, mobile).
- **EXPECTED-OUTPUT:** D:/Sinister/01_Projects/ contains only non-Sinister content (or empty).
- **VERIFICATION:** `ls "D:/Sinister/01_Projects/"` returns only `Inventions/` (if kept) + `_README.md`. Sanctum projects/ grows by 4 new entries. MANIFEST.json count goes 26 → 30.
- **GATING:** None (master-actionable but high effort — best done as a single batch turn after the BATS + PUSH + CLEAN trio).
- **COMMIT-MESSAGE:** `chore(sanctum): D-drive PROJECTS phase — 4 new + 3 dupe-cleanup migrations from D:/Sinister/01_Projects/`

## PHASE RENAME — D:/Sinister → D:/Personal

**Gap.** Operator wants `D:/Sinister/` cleaned of Sinister projects then renamed to `D:/Personal/`.

- **EXACT-INSTRUCTIONS:**
  1. PHASE PROJECTS must complete first (no more Sinister content under D:/Sinister/).
  2. Verify junctions: `D:/Sinister Sanctum/Sinister Skills` is a junction that points to `_sinister-skills/` (inside Sanctum); `D:/Sinister/Sinister Skills` is ALSO a junction (legacy). Renaming `D:/Sinister/` will break the legacy junction's source path — but since both junctions point to the same target inside Sanctum, removing the legacy junction first is the fix.
  3. Remove legacy junctions inside `D:/Sinister/` before rename: `(Get-Item 'D:/Sinister/Sanctum').Delete()` and `(Get-Item 'D:/Sinister/Sinister Skills').Delete()` (junctions, not real dirs).
  4. Grep for fleet refs to `D:\Sinister\` (excluding `Sinister Sanctum`): `Grep -rn '\\Sinister\\\\' /d/Sinister\ Sanctum/` — surface anything that still resolves to the old root.
  5. Operator confirms intent → `Rename-Item D:/Sinister D:/Personal`.
  6. Re-create junctions if anything broke (e.g., a fleet bot still expects `D:/Sinister/Sinister Skills` — repoint to `D:/Personal/Sinister Skills` or directly to `D:/Sinister Sanctum/_sinister-skills`).
- **EXPECTED-OUTPUT:** `D:/Sinister/` no longer exists; `D:/Personal/` contains the operator's personal (non-Sinister) content.
- **VERIFICATION:** `ls D:/ | grep -i sinister` returns only `Sinister Sanctum/` + `sinister-vault@`.
- **GATING:** **High-impact — operator-confirms before execution.** Surface the grep results for refs that still point at the old path; operator green-lights or operator says "leave Sinister name alone".
- **COMMIT-MESSAGE:** `chore(sanctum): D:/Sinister → D:/Personal rename (post-projects extraction)`
- **RISK:** Until verified, ~1300 fleet refs to `D:/Sinister/Sinister Skills` exist; many resolve through the junction `D:/Sinister Sanctum/Sinister Skills` which IS internal to Sanctum, so most should survive. The legacy `D:/Sinister/Sinister Skills` junction is the one at risk — if removed cleanly first, the rename is safe.

## PHASE RKOJ-VERIFY — Every MANIFEST component verified

**Gap.** Operator: "get to work to complete the entire rkoj workstation. everything for that should be in one folder". The MANIFEST has 26 components (post-docs-catchup) — confirm each works end-to-end.

- **EXACT-INSTRUCTIONS:** Parse `projects/rkoj/MANIFEST.json`. For each component:
  - `path` exists on disk: `test -e <path>`
  - For `kind=tool`: run `python -m <tool> --version` or `--help` (CLI must respond).
  - For `kind=forge` / `forge-pane` / `forge-theme`: import the module (`python -c "import forge.panes.sidebar"`).
  - For `kind=project` (the 5 newly migrated): `ls <path>` returns non-empty.
  - For `kind=build`: `automations/build/forge-exe/build.ps1` exists.
- **EXPECTED-OUTPUT:** 26/26 GREEN. Any RED component gets a separate gap-fix task.
- **VERIFICATION:** Verdict log at `_shared-memory/plans/sanctum-d-drive-final-reorg-2026-05-21/rkoj-verify.md`.
- **COMMIT-MESSAGE:** `docs(rkoj): MANIFEST 26-component verification — N/N GREEN`

## PHASE TEST — RKOJ.exe v1.3.0 end-to-end smoke

**Gap.** No record of an operator-driven UI smoke test for v1.3.0 (the operator's "phone all in one" image-28 reference). Source-level audit is GREEN; binary-level click-test is needed.

### Test matrix

| # | Step | Expected | Owner |
|---|---|---|---|
| 1 | Double-click `D:/Sinister Sanctum/RKOJ-Start.bat` (or Desktop RKOJ.exe) | Forge TUI launches, no crash, mascot renders | Operator |
| 2 | Sidebar visible with mascot + "EVE" label | Mascot block purple-bg, EVE label centered | Operator |
| 3 | Sidebar shows Agents `[●]` + Phones `[#]` tabs | Agents `-active` (purple wash), Phones inactive | Operator |
| 4 | Sidebar STATUS section: agents N live / inbox N / brain N | All 3 counters non-zero | Operator |
| 5 | Click Phones tab | AdbPanel mounts, scans devices in <4s | Operator |
| 6 | If phone connected: device card shows model + state + transport | Pixel-6a P1/P2 listed | Operator |
| 7 | Click Agents tab | AgentsDashboard with sub-tabs strip + status row | Operator |
| 8 | Sub-tab strip shows: All N + per-project chips (Sanctum, Forge, Panel, Term, Kernel APK, RKOJ, ...) | One chip per session-templates/projects.json entry | Operator |
| 9 | Click a project sub-tab (e.g. "Sanctum") | Grid filters to Sanctum panes only | Operator |
| 10 | Click "All N" | All workspaces re-visible | Operator |
| 11 | Type `/help` | Help overlay opens with command list | Operator |
| 12 | Type `/git` | Real impl (not stub) — shows current git state | Operator |
| 13 | Type `/todo` | Real impl — opens TaskList | Operator |
| 14 | Type `/save smoke-2026-05-21` | Saves journal to `~/.sinister/sessions/smoke-2026-05-21.jsonl` | Operator |
| 15 | Type `/resume smoke-2026-05-21` | Restores the saved session | Operator |
| 16 | Type `/effort fast` | Switches model to fast tier | Operator |
| 17 | Type `/mermaid` | Renders mermaid graph in pane | Operator |
| 18 | Bottom statusbar shows: agents · inbox · memory · tokens X/200K | Live counters refresh every 5s | Operator |
| 19 | Quit via `Ctrl+Q` or X | Clean exit, no zombie processes | Operator |
| 20 | RKOJ.exe info | Prints MANIFEST 26-component summary | Operator |

- **EXACT-INSTRUCTIONS:** Operator runs the matrix above; any FAIL → surface as a gap. Master archives screenshots into `_shared-memory/plans/sanctum-d-drive-final-reorg-2026-05-21/test-screenshots/` once captured.
- **EXPECTED-OUTPUT:** 20/20 GREEN, no zombie processes after quit.
- **VERIFICATION:** Verdict appended to `_shared-memory/PROGRESS/Sinister Sanctum.md`.
- **GATING:** Operator-driven (master can't simulate clicks reliably).

## Sequencing (recommended execution order)

1. **PUSH** + **CLEAN** + **BATS** + **README** + **RKOJ-VERIFY** — parallel, master-actionable, single commit per phase. Estimated 1-2 turns.
2. **PROJECTS** — single batch turn, ~5 file moves + 4 MANIFEST rows. Estimated 1 turn.
3. **TASK** — surface to operator for UAC-elevated install.
4. **CUSTODIAN** — surface to operator for daemon-stop + master finishes the move on operator's signal.
5. **RENAME** — surface to operator for green-light AFTER PROJECTS phase done.
6. **TEST** — operator-driven UI smoke.

## What stays operator-gated (surface only, never silent-execute)

- PHASE TASK (UAC elevation)
- PHASE CUSTODIAN (daemon stop)
- PHASE RENAME (high-impact rename of D:/Sinister)
- PHASE TEST (UI clicks)

All other phases are master-actionable and start now.

## Risk register

| Risk | Mitigation |
|---|---|
| 59-commit push reveals a secret | Pre-push grep for `sk-ant-`, `[Aa][Ww][Ss]_`, `BEGIN PRIVATE KEY`, etc. across the 59 diffs |
| Custodian daemon won't stop cleanly | If `Stop-Process` fails, operator restarts the OS — daemon is just a backup pipe, no live transactional state |
| D:/Sinister rename breaks ~/.claude/.mcp.json paths | Operator never lets master touch .mcp.json (canonical-3); operator must verify the file after rename |
| Sanctum cleanup deletes a file someone needs | Each delete preceded by mtime check; old (>7d) only |
| 4 new projects added to MANIFEST break the v1.3.0 EXE | EXE doesn't read MANIFEST at runtime for routing — info display only |

---

**End of plan.** Plan-doc lives at this path; execution starts immediately on the four parallel phases (PUSH, CLEAN, BATS, README, RKOJ-VERIFY).
