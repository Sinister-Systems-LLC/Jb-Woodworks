<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 90
-->
# Session-start auto-update propagation doctrine

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Trigger:** Operator 2026-05-24 21:30Z verbatim — *"make sure as we update things that all session starts in the eve exe are auto updated and contain all things we add and change when where and if needed"*
> **Composes with:** `fleet-update-channel-doctrine-2026-05-24`, `sanctum-scope-discipline-2026-05-24`, `mesh-coordination-and-resource-lifecycle-2026-05-24`, `sinister-os-fleet-host-linkage-2026-05-24`

## The five propagation surfaces

When any sanctum-class agent ships a change, that change reaches spawned EVE sessions through ONE of these five mechanisms. Knowing which surface a change lives on tells you whether it auto-propagates or needs a step.

| # | Surface | Auto-propagates? | Trigger needed |
|---|---|---|---|
| 1 | `.ps1` scripts (start-sinister-session, claude-accounts, fleet-update, etc.) | **YES** — read live each spawn | None |
| 2 | `CLAUDE.md` hard-canonical blocks | **YES** — read fresh on every cold-start | None |
| 3 | `_shared-memory/knowledge/*.md` brain entries | **YES via fleet-update channel + cold-start grep** | Push to channel + `_INDEX.md` update |
| 4 | `eve.py` (EVE.exe launcher source) | **NO** — bundled into PyInstaller binary | Rebuild EVE.exe + sync mirror |
| 5 | JSON config (`projects.json`, `agent-prefs.json`, `claude-accounts.json`) | **YES** — read on each spawn | None |

## The five canonical paths and their freshness rules

### 1. Build-Phrase / spawn pipeline (`start-sinister-session.ps1`)
- Read **fresh** by `subprocess.call(["powershell.exe", ..., "-File", PS1_LAUNCHER, ...])` in `eve.py:dispatch_project`.
- Every spawn loads the current file from disk. Changes to `Build-Phrase`, account-lease logic, progress bar, fleet-updates poll, detect-similar wiring, etc. take effect on the **next spawn** with zero rebuild.
- **Test before ship**: parse-check via `[System.Management.Automation.Language.Parser]::ParseFile(...)`.

### 2. CLAUDE.md (root + per-project)
- Read by the spawned Claude session itself on cold-start (CLAUDE.md is part of Claude Code's standard context).
- New hard-canonical blocks are visible to the agent on the **next spawn** with zero rebuild.
- **Cold-start step 0** also invokes `understand-anything:understand-explain` which re-reads the project's CLAUDE.md.

### 3. Brain entries (`_shared-memory/knowledge/*.md`)
- Picked up via two mechanisms:
  - **Cold-start grep**: agents grep `_INDEX.md` for tags relevant to their lane.
  - **Fleet-update channel poll** (now wired in `Build-Phrase`): pre-fetches last 3 unacked rows visible to the lane and injects into cold-start phrase.
- **Ship protocol**: write the `.md` → add row to `_INDEX.md` → `fleet-update.ps1 -Action Push -Kind doctrine`.

### 4. eve.py (EVE.exe launcher Python source) — **THE GAP**
- Bundled into PyInstaller binary at `automations/eve-launcher/dist/EVE/EVE.exe` + mirror at `~/.eve/EVE.exe`.
- Source edits do **not** propagate until the binary is rebuilt.
- **Ship protocol** (post-2026-05-24): after any `eve.py` edit, run:
  ```
  powershell -File automations\verify-eve-features.ps1 -AutoRebuild -SyncMirror
  ```
- The script detects stale bundle (source mtime > exe mtime), runs `build-eve-exe.bat`, and copies dist → mirror.
- Operator must close + reopen running EVE.exe windows to see the new bundle (running instance holds old).

### 5. JSON configs
- `projects.json`: read by `eve_picker_lib.build_picker_state()` on every picker render.
- `agent-prefs.json`: read by `Confirm-AgentPrefs` + headless `-Project` path on every spawn.
- `claude-accounts.json`: read by `Get-NextAvailableAccount` + `Mark-AccountSpawned` per spawn (with mutex).
- All take effect on the **next spawn** with zero rebuild.

## Mandatory ship checklist (any sanctum-class agent editing fleet surface)

After editing any of these surfaces, verify the change reaches spawned sessions:

```
# .ps1 change                  → parse-check + smoke a -Project spawn
[Parser]::ParseFile(...); start-sinister-session.ps1 -NoLaunch -Project <key>

# CLAUDE.md change              → no action (read fresh next spawn)
# Brain entry change            → push to channel:
fleet-update.ps1 -Action Push -Kind doctrine -Priority high -Message "..."

# eve.py change                 → REBUILD:
verify-eve-features.ps1 -AutoRebuild -SyncMirror

# JSON config change            → no action (read fresh next spawn)
```

## Anti-patterns (don't ship these)

1. **Edit `eve.py` without rebuilding** — operator sees old bundle, blames the feature for "not working" when it's just stale (operator 21:08Z "i see no accounts panel" was this exact symptom).
2. **Push doctrine to fleet-update without writing the brain entry** — channel message points at nothing.
3. **Edit `start-sinister-session.ps1` without parse-check** — broken script kills every subsequent spawn.
4. **Skip `Build-Phrase` env-skip-flag** — new instructions can't be opted out for headless / scheduled-task runs.
5. **Hide critical announcements behind `low` priority** — operator misses, then blames the doctrine for "never being followed".
6. **Edit bundled `.pyc` directly** — never survives a rebuild.

## How operator sees an update reach them

A sanctum agent ships a feature in this order:

```
edit eve.py
    ↓
verify-eve-features.ps1 -AutoRebuild -SyncMirror      ← bundle now fresh
    ↓
fleet-update.ps1 -Action Push -Kind feature           ← channel announces
    ↓
brain entry written + _INDEX.md row added             ← knowledge captured
    ↓
operator closes + reopens EVE.exe                     ← sees new bundle
    ↓
operator's other lanes (sibling EVE sessions)
hit their next heartbeat poll cycle                    ← fleet-update inject
    ↓
sibling agents now see + ack the announcement         ← acks land in jsonl
```

Result: change reaches every surface that needs it within minutes.

## Tooling shipped

- `automations/eve-first-run-check.ps1` — first-run detector (11 checks; exit 1=first-run, exit 0=already-setup)
- `automations/eve-first-run-wizard.ps1` — interactive 4-step setup with auto-spawn of setup-helper agent
- `automations/verify-eve-features.ps1 -AutoRebuild -SyncMirror` — staleness probe + auto-rebuild
- `automations/fleet-update.ps1` — channel CLI for cross-lane announcements (Push/List/Acked/Stats)
- `start-sinister-session.ps1 Build-Phrase` — SETUP-HELPER mode (env-gated) + 6-stage `_SpawnProgress`

## Status

- **Created:** 2026-05-24 21:32Z
- **Bound in:** `_shared-memory/knowledge/_INDEX.md` (next iter row)
- **Distributed via:** `fleet-update.ps1 -Action Push -Kind doctrine -Priority high` (fleet-wide)
- **Validated:** 5 surfaces enumerated; 4 of 5 are auto-propagate; surface #4 (eve.py) now has `-AutoRebuild` path
