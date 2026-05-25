# EVE.exe + bat/ps1 audit (iter-23 sub-1)

**Author:** RKOJ-ELENO :: 2026-05-25 (sanctum lane; sub-agent a0208e5cd47a5705d, persisted by sanctum master)
**Scope:** every `.bat`, `.ps1`, `.exe` in `D:\Sinister Sanctum\` (excluding `projects/`) + `C:\Users\Zonia\Desktop\*.bat`
**Operator utterance:** 2026-05-25T06:33:48Z — *"audit and clean the entire eve exe and bat files AFTER you set leo up. we need to satrt taking a versions appraoch to everything we do"*

## Summary

| Total | KEEP | MIGRATE | DELETE | UNSURE |
|---|---|---|---|---|
| **178** | 27 | 145 | 9 | 2 |

- **KEEP (27):** EVE.exe (root + deploy/) + critical .ps1 schtask bindings + session launchers (start-sinister-session.ps1, sanctum-auto-push.ps1, fleet-update.ps1, agent-poke.ps1, kill-fleet.ps1, etc.).
- **MIGRATE (145):** legacy `.ps1` in `automations/`; GRANDFATHERED per CLAUDE.md hard-canonical "NO .bat / NO .ps1" doctrine. Operator policy: migrate to Python on NEXT non-trivial touch, NOT mass-delete. Doctrine ref: `_shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md`.
- **DELETE (9):** high-confidence stale candidates — temp artifacts, deprecated watchers, test harnesses (no callers found via Grep over entire repo).
- **UNSURE (2):** operator-private Desktop `.exe` tools needing clarification before any action.

## Key findings

1. **All 145 `.ps1` files in `automations/`** = legacy; left in place per doctrine. Calling existing `.ps1` from Claude tools is allowed; the ban is on CREATING NEW ones + surfacing operator clicks.
2. **EVE.exe (root + `deploy/`)** = canonical; KEEP indefinitely. Both files mirror the same compiled bundle; `deploy/EVE.exe` is Leo's bootstrap artifact.
3. **9 high-confidence DELETE candidates** flagged in source-of-truth audit (sub-agent transcript) — temp artifacts, deprecated watchers, test harnesses. Recommend separate cleanup PR before mass-deletion (each DELETE requires a Grep-confirmed "zero refs" pre-flight).
4. **5 MIGRATE candidates flagged with effort estimates;** 2 block critical paths (EVE rebuild + onboarding wizard) — those should be PRIORITY for Python rewrite during next non-trivial touch.

## Next actions (queued, not executed this iter)

- Operator review of the 2 UNSURE Desktop `.exe` tools.
- Phase-1 DELETE pass: per-file Grep audit of the 9 candidates → confirm zero refs → single commit removing all 9.
- Phase-2 MIGRATE pass: schedule the 2 critical-path `.ps1` for Python rewrite on next non-trivial edit.
- Phase-3: continue grandfathering remaining 143 `.ps1`; migrate opportunistically.

## Anti-patterns to avoid

- Do NOT mass-delete the 145 `.ps1` — operator doctrine grandfathers them.
- Do NOT migrate without a corresponding consumer audit (some `.ps1` are called from `schtasks` outside the repo).
- Do NOT delete `Kill-Stuck-EVE.bat` on Desktop — it's actively invoked by `eve_self_update.py` (Sub-F extension) and `eve_crash_detector.py` (Sub-E).

(Full per-file inventory available in sub-agent transcript a0208e5cd47a5705d; this file is the actionable summary.)
