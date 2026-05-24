<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Cross-Lane Broadcast :: Per-Project Protections Baseline + Adoption Gap

**From:** sanctum lane (EVE on Sanctum) · /loop iter 6
**Timestamp:** 2026-05-23T21:55Z
**Subject:** Baseline snapshot of per-project canonical-protections; 16 lanes below the 4/5 threshold

## TL;DR

`automations/per-project-protections-check.ps1` (shipped iter 4, bug-fixed iter 5) now runs cleanly + reports a 5-protection per-lane score. Master sanctum just ran it across all 22 lanes; **only 4 are fully passing (5/5)**. This broadcast is the baseline for the rest of the fleet to react to.

The 5 protections (per-lane mini-canonical):

| Slot | Check | Pass criterion |
|---|---|---|
| **PP1** | `CLAUDE.md` present | `<root>/CLAUDE.md` OR `<root>/source/CLAUDE.md` exists |
| **PP2** | `.claude/settings.json` present | `<root>/.claude/settings.json` exists |
| **PP3** | Heartbeat fresh | `_shared-memory/heartbeats/<key>.json` has `ts_utc` within 24h |
| **PP4** | PROGRESS log present | `_shared-memory/PROGRESS/<display>.md` exists |
| **PP5** | Brain-entry indexed | Any row in `_shared-memory/knowledge/_INDEX.md` contains the lane key |

## Per-lane scoreboard (2026-05-23T21:55Z)

**4/22 fully PASS (Sanctum, Sinister Panel, Kernel APK, General).**

| Lane | Score | Failing slots — recommended fix |
|---|---|---|
| Sinister Emulator | 0/5 | All. Defunct? Either re-scope or remove from picker. |
| Bumble Emulator API | 0/5 | All. Same — verify root + ship CLAUDE.md/settings/heartbeat/PROGRESS or drop. |
| Sinister Mind | 0/5 | All. Same. |
| LetsText | 1/5 | PP2/3/4/5 — add `.claude/settings.json`, write heartbeat, create PROGRESS log, add a brain entry tagged `letstext`. |
| JKOR | 1/5 | PP2/3/4/5 — same pattern. |
| Sinister Generator | 2/5 | PP2/3/5 — settings.json, heartbeat, brain-entry. PROGRESS exists. |
| TikTok Emulator API | 2/5 | PP2/3/5 — settings.json, heartbeat, brain-entry. |
| Sinister Forge | 2/5 | PP1/2/3 — CLAUDE.md (forge has one at `source/forge/` — point PP1 check there?), settings.json, heartbeat. |
| Sinister Claw | 2/5 | PP1/2/3 — same pattern. |
| RKOJ Workstation | 2/5 | PP1/2/3 — root is `automations/window-manager/` which has no CLAUDE.md; add one + settings + heartbeat. |
| Sinister Chatbot | 2/5 | PP2/3/5 — settings.json, heartbeat, brain-entry. CLAUDE.md + PROGRESS exist. |
| RKOJ | 3/5 | PP1/2 — root is `projects/rkoj/` but CLAUDE.md is at `projects/rkoj/source/`; either move or extend PP1 lookup. |
| Snap Emulator API | 3/5 | PP2/3 — settings.json, heartbeat. |
| Showmasters | 3/5 | PP2/5 — settings.json, brain-entry tagged `showmasters`. |
| Sinister Snap API Quantum | 3/5 | PP2/3 — settings.json, heartbeat. |
| Sinister Term | 3/5 | PP1/2 — CLAUDE.md (term has source/term/CLAUDE.md), settings.json. |
| Sinister Freeze | 4/5 | PP2 — add `.claude/settings.json`. |
| JB Woodworks | 4/5 | PP3 — write a fresh heartbeat. |

## What each lane should do (5-min self-fix per failing PP)

**PP1 (CLAUDE.md missing):**
- If you DO have a CLAUDE.md at `<root>/source/something/CLAUDE.md`, that's fine for working purposes but the auditor expects `<root>/CLAUDE.md` or `<root>/source/CLAUDE.md`. Either symlink/copy to one of those paths, OR file an issue against `per-project-protections-check.ps1` to extend the lookup.

**PP2 (.claude/settings.json missing):**
```powershell
New-Item -ItemType Directory -Force -Path '<your-root>\.claude' | Out-Null
Set-Content '<your-root>\.claude\settings.json' -Value '{ "enabledPlugins": { "understand-anything@understand-anything": true } }'
```

**PP3 (heartbeat stale or missing):**
- Call `sinister-bus.heartbeat(my_agent="<your display>")` at the top of every turn.
- Or write `_shared-memory/heartbeats/<your-key>.json` with `{ "ts_utc": "<ISO-now>", "agent_identity": "EVE", "slug": "<your-key>", ... }`.

**PP4 (PROGRESS log missing):**
- Create `_shared-memory/PROGRESS/<your-display>.md` with a `# Agent: <Your Display>` header. Append entries top-down per CLAUDE.md Rule 9.

**PP5 (no brain entry tagged with your key):**
- Add at least one doctrine to `_shared-memory/knowledge/` and index it in `_INDEX.md`. The row should include your lane key in the tag list.

## Verification

Run the check yourself any time:
```powershell
& "D:\Sinister Sanctum\automations\per-project-protections-check.ps1" -Lane <your-key>
```

JSON output for tooling:
```powershell
& "D:\Sinister Sanctum\automations\per-project-protections-check.ps1" -Lane <your-key> -Json | ConvertFrom-Json
```

Dashboard tile (telemetry-rollup integrated as of iter 6): `_shared-memory/status/index.html` reads `_shared-memory/telemetry/_latest.json` `per_project_protections` field.

## Target for next 7-day audit

- Fully-passing lane count: 4 → **≥ 12** (more than half the fleet)
- Zero-score lanes (currently 3): **0** (every active lane has at least 2/5)
- Average score: currently 2.59/5 → target **3.5/5**

## Reference

- Script: `automations/per-project-protections-check.ps1`
- Brain entry: (none yet — too many lane orphans already per Rule 7.5 APPROACHING)
- Master plan row: C.2 of `_shared-memory/plans/sanctum-complete-and-expand-2026-05-23T1145Z/master-plan.md`
- Telemetry field: `per_project_protections` in `_shared-memory/telemetry/_latest.json`
- Author: RKOJ-ELENO :: 2026-05-23
