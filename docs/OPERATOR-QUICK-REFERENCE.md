<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Sanctum :: Operator Quick Reference

**One-pager.** Every operator-runnable script in the Sanctum, with one-line description + invocation. Distilled from /loop iters 1-16 (2026-05-23 → 2026-05-24).

For deeper context: each script has its own docstring header at the top.

---

## Fleet Health (run first, run often)

### Fleet-Tour (the demo bat)
```
automations\Fleet-Tour.bat       (double-click)
```
5-step READ-ONLY tour: sinister-doctor → HTML report → opens browser → per-project autofix preview → brain-orphans preview. Closes with copy-paste apply commands. **Start here.**

### sinister-doctor (one-command fleet health)
```
automations\sinister-doctor.ps1                       # console summary (~0.6s quick mode)
automations\sinister-doctor.ps1 -Quick                # same
automations\sinister-doctor.ps1 -Html                 # writes _shared-memory/sinister-doctor-<UTC>.html
automations\sinister-doctor.ps1 -Json                 # machine-readable
automations\sinister-doctor.ps1 -Watch                # live monitor; refresh 60s; Ctrl+C exits
automations\sinister-doctor.ps1 -Watch -WatchInterval 30   # custom refresh
```
Exit codes: 0=GREEN, 1=YELLOW, 2=RED (CI-friendly).

### Install nightly cron (operator-gated)
```
automations\install-sinister-doctor-task.ps1          # registers daily 03:30 task
automations\install-sinister-doctor-task.ps1 -DryRun  # preview
schtasks /Delete /TN SinisterDoctorTask /F            # uninstall
```

---

## Per-project protections (PP1-PP5)

### Check (current status)
```
automations\per-project-protections-check.ps1            # all 22 lanes table
automations\per-project-protections-check.ps1 -Lane sanctum
automations\per-project-protections-check.ps1 -Json      # machine-readable
```

### Autofix (operator-gated; creates stub CLAUDE.md / settings.json / heartbeat / PROGRESS files)
```
automations\per-project-protections-autofix.ps1 -DryRun     # preview (default)
automations\per-project-protections-autofix.ps1 -Yes        # apply, skip prompt
automations\per-project-protections-autofix.ps1 -Lane jkor  # one lane only
```
Conservative: never overwrites; PP5 (brain entry) is flagged for operator/lane to author themselves.

---

## Brain (Rule 7.5 ceiling = 150)

### Check (orphans + ceiling status)
```
automations\brain-index-orphan-check.ps1
automations\brain-index-orphan-check.ps1 -Json
```

### Archive orphans (operator-gated; moves to knowledge/_archive/)
```
automations\brain-archive-orphans.ps1 -DryRun    # preview (default)
automations\brain-archive-orphans.ps1 -Yes       # apply
```
Reversible via `git mv` back + add row to `_INDEX.md`.

---

## Other operator tools

### clone-missing-sources (for Leo + new operators)
```
automations\clone-missing-sources.ps1                    # auto-clone missing project sources
automations\clone-missing-sources.ps1 -DryRun
automations\clone-missing-sources.ps1 -Only kernel-apk   # one project
automations\Clone-Missing-Sources.bat                    # double-click wrapper
```
See `docs/LEO-MISSING-SOURCES.md` for full guide.

### EVE.exe (launcher, --onedir build)
```
automations\eve-launcher\dist\EVE\EVE.exe                # launch picker (52ms boot)
automations\eve-launcher\dist\EVE\EVE.exe --version      # probe
automations\eve-launcher\build-eve-exe.bat               # rebuild from source
```
Boot: ~52 ms median warm-cache (v0.3.0 --onedir; cold-cache trial 1 ~370 ms; doctrine target <300 ms, PASS by 5x). Falls through to PS1 if missing.

### cross-lane-impact-diff (post-commit hook)
```
.git\hooks\post-commit                                   # auto-fires after every commit
automations\cross-lane-impact-diff.ps1 -DryRun           # manual preview
```
Emits broadcast to `_shared-memory/cross-agent/` when canonical files change.

### index-resume-search (rebuild search index)
```
automations\index-resume-search.ps1                      # writes _shared-memory/resume-search-index.json
```
970+ entries: resume-points + PROGRESS sections + commits + brain rows. Feeds launcher Pick-ResumeRow.

### telemetry-rollup (daily metrics)
```
automations\telemetry-rollup.ps1                         # writes _shared-memory/telemetry/daily-<UTC>.json + _latest.json
```
Dashboard at `_shared-memory/status/index.html` reads `_latest.json`.

### Voice prompting POC (Path A; opt-in)
```
python tools\sinister-voice\voice_recorder.py --selftest
python tools\sinister-voice\voice_recorder.py --record-once
python tools\sinister-voice\voice_recorder.py --daemon   # needs SINISTER_VOICE_ENABLED=1
```
Spec: `_shared-memory/plans/voice-prompting-poc-2026-05-23/spec.md`. Deps: `keyboard sounddevice soundfile` (pip install when ready).

### Wake-on-demand bot dispatcher (standalone; bus-lane integrates when ready)
```
python tools\sinister-wake\wake_dispatcher.py            # peek-state of 13 bots
python tools\sinister-wake\test_smoke.py                 # 15-test smoke suite
```
Standalone WakeDispatcher class; bus lane wires in via `tools/sinister-wake/README.md` integration path.

---

## Status surfaces (read these)

| Path | What |
|---|---|
| `_shared-memory/status/index.html` | live dashboard (P1-P9 + per-project + brain + inbox + recent ships + PP scoreboard) |
| `_shared-memory/sinister-doctor-<UTC>.html` | timestamped daily health report |
| `_shared-memory/telemetry/_latest.json` | machine-readable rollup |
| `_shared-memory/OPERATOR-ACTION-QUEUE.md` | open operator-clicked items |
| `_shared-memory/PROGRESS/Sinister Sanctum.md` | sanctum-lane append-only ship log |
| `_shared-memory/knowledge/_INDEX.md` | brain doctrine catalog |
| `_shared-memory/cross-agent/` | cross-lane broadcast messages |

---

## Common workflows

### "Is the fleet healthy?"
```
automations\Fleet-Tour.bat
```

### "Bring all lanes up to baseline protections"
```
automations\per-project-protections-autofix.ps1 -DryRun         # preview
automations\per-project-protections-autofix.ps1 -Yes            # apply
```

### "Clean brain orphans"
```
automations\brain-archive-orphans.ps1 -Yes
```

### "I'm Leo / new operator, set me up"
1. `git clone https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git`
2. `cd Sinister-Sanctum`
3. `powershell -ExecutionPolicy Bypass -File automations\clone-missing-sources.ps1`
4. `powershell -ExecutionPolicy Bypass -File automations\sinister-doctor.ps1`
5. See `docs/LEO-SETUP.md` for full onboarding

### "Daily fleet health email/notification"
```
powershell -ExecutionPolicy Bypass -File automations\install-sinister-doctor-task.ps1
```
Runs `sinister-doctor -Html` daily at 03:30. Operator reviews HTML reports.

---

## Composes-with

This page covers operator-facing tooling shipped by sanctum lane /loop iters 1-16. For:
- **Bot fleet** (13 MCP bots) → `_shared-memory/knowledge/bot-fleet-quick-reference.md`
- **Per-project bot adoption** → `_shared-memory/knowledge/per-project-bot-adoption-playbook-2026-05-23.md`
- **EVE launcher walkthrough** → `docs/EVE-PICKER-OPERATOR-WALKTHROUGH.md`
- **Doctrines / Rule 7.5 / no-bullshit** → `_shared-memory/knowledge/_INDEX.md`
- **Master plan** → `_shared-memory/plans/sanctum-complete-and-expand-2026-05-23T1145Z/master-plan.md`

---

## What I don't do (operator-gated)

- C.3 PreToolUse Edit guard (L3 doctrine layer)
- C.7 Browser bridge Layer B (needs XPI install + registry write)
- C.8 Memory-graph mermaid-rs renderer (needs Rust toolchain)
- C.12 Context-cleaner v2 implementation (needs spec answers Q1-Q5)
- Voice prompting (needs Q1-Q5: provider / hotkey / dispatch / retention / Path B?)

---

**Author:** RKOJ-ELENO :: 2026-05-24
**Coverage:** /loop iters 1-16 (master plan B + C rows shipped: 19/24 ≈ 79%)
