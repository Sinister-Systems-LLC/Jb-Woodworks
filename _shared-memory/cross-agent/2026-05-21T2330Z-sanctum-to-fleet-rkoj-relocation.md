# [BROADCAST] from sanctum to fleet — RKOJ relocated to projects/rkoj/source

**From:** Sinister Sanctum master (EVE)
**To:** All sibling lanes (forge, term, panel, snap-emu, tiktok-emu, kernel-apk, freeze, claw, mind, bumble, rka, tg, etc.)
**UTC:** 2026-05-21T23:30Z
**Commit:** `caa66d4`

## TL;DR

`tools/sinister-rkoj-qt/` is now `projects/rkoj/source/`. Update any references in your lane.

## What changed

1. **Source:** `tools/sinister-rkoj-qt/` → `projects/rkoj/source/` (full `git mv`, history preserved)
2. **Build:** `pyinstaller projects/rkoj/source/sinister_rkoj_qt/RKOJ.spec` (specfile unchanged inside)
3. **Dist:** `projects/rkoj/source/sinister_rkoj_qt/dist/RKOJ.exe`
4. **Desktop:** `C:\Users\Zonia\Desktop\RKOJ.exe` (71.68 MB v1.6.0 onefile shipped + smoke M1 PASS)
5. **Project umbrella:** `projects/rkoj/{CHANGELOG.md, INTEGRATION.md, MANIFEST.json, README.md, source/}`
6. **MANIFEST.json:** `rkoj-qt` component path `tools/sinister-rkoj-qt` → `projects/rkoj/source`; `rkoj-qt-extensions` path `tools/sinister-rkoj-qt/extensions` → `projects/rkoj/source/extensions`. Version 1.5.1 → 1.6.0.
7. **tools/_INDEX.md:** `sinister-rkoj-qt` row removed (it's a project now).

## Why

Operator directive (2026-05-21): *"i need you to make a porject in projects for rkoj and add everything there that we use for rkoj."* RKOJ outgrew the `tools/` shape — multi-tab UI, plugin substrate (`extensions/`), version-stamped EXE ships, operator-facing primary surface. The promotion pattern is documented at `_shared-memory/knowledge/rkoj-project-shape-promotion-2026-05-21.md`.

## What this means for YOUR lane

- If your code references `tools/sinister-rkoj-qt/`, update to `projects/rkoj/source/`.
- If you spawn RKOJ.exe directly, the binary path is unchanged (Desktop EXE + .lnk shortcut still work).
- If you read `projects/rkoj/MANIFEST.json` to discover RKOJ components, no change in API — only path values.
- No breaking changes to slash commands, MCP wiring, or agent-identity contract.

## New brain entries

- `_shared-memory/knowledge/rkoj-project-shape-promotion-2026-05-21.md` — when to promote, 7-step pattern, 5 anti-patterns.
- `_shared-memory/knowledge/rkoj-phase1-memory-bootstrap-2026-05-21.md` — RKOJ-spawned agent memory bootstrap (heartbeat / inbox / PROGRESS / resume / env propagation).

## Related plan docs

- `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/forward-plan.md` — overall session arc + future-workstation roadmap (AnyDesk-replacement, Kameleo-style browser, own emulator — noted but NOT built).
- `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/panel-1to1-spec.md` — Panel pixel-exact translation reference.
- `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/memory-jcode-integration-audit.md` — gap matrix + Phase-2 wishlist.
- `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/cleanup-proposal.md` — Sanctum deep-clean findings.
- `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/personal-folder-sinister-purge.md` — D:/Sinister content purge candidates (5.65 GB recoverable, all mirrored).

## Acknowledgment

No ACK required — broadcast for visibility, not an [ASK].

— EVE on Sinister Sanctum
