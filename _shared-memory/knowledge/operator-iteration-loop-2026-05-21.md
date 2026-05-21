> **Author:** RKOJ-ELENO :: 2026-05-21

# operator-iteration-loop-2026-05-21 — anti-pattern + remediation doctrine

**Status:** doctrine, standing-rule
**Tags:** rkoj, ui-iteration, operator-feedback, anti-pattern, spec-first, sub-agent-discipline, x-button-as-first-class, 2026-05-21
**Composes with:** `rkoj-ui-exact-spec-2026-05-21.md`, `rkoj-v1.0-to-v1.1-form-parity-journey.md`, `multi-agent-branch-contention-isolation-pattern.md`, `auto-mode-launcher-pattern.md`

## Empirical anchor — the loop we ran today (2026-05-21, 8h, ~12 ships)

1. v0.5 → v1.5 → v1.5.1 PyQt6 chain. 12+ ships in one calendar day.
2. Every ship was rejected for one of:
   - **wrong-platform** — Textual TUI in cmd window when operator wanted a frameless native window
   - **wrong-chrome** — pywebview HTML surface when operator said "no fucking web ui"
   - **wrong-features** — Excel-style ribbon + 4 KPI tiles operator never asked for
   - **wrong-defaults** — auto-spawn 40 terminals at startup with no opt-in
   - **wrong-location** — folder dropped on Desktop when operator only wants the single `.lnk`
   - **wrong-name** — "workstation" tab clobbering RKOJ-canonical naming
3. Per-cycle rhythm: ship → operator screenshots a complaint → rebuild → re-ship → new complaint. Zero compounding of operator confidence between cycles.
4. Cost: massive token burn, large sub-agent dispatch budget, rising operator frustration over the full 8h window.

## Doctrine — 10 lessons we will not relearn

1. **Operator-canonical UI spec FIRST.** Before any build, capture the operator's exact spec in a brain doctrine. We did this AFTER too many cycles (`rkoj-ui-exact-spec-2026-05-21.md`). Reference images + verbatim quotes pinned. Sub-agents read THAT, not abstracted briefs.
2. **Stop scope-creep at the spec.** When the ask is "add a few placeholder things, looks nice" — do NOT add Excel ribbon + 4 KPI tiles + workstation tab + project sub-tab strip + STATUS panel. Add EXACTLY what was asked. The operator iterates from a minimal base; they will NEVER iterate by deleting your invented chrome.
3. **Screenshots ARE the spec.** When the operator drops an image (e.g. snap.sinijkr.com), that IS the target layout — pixel-accurate. Match the layout shape: sidebar widths, header heights, section labels, button positions. Don't paraphrase.
4. **One operator-clickable artifact, in one operator-asked location.** The operator clicks `Desktop\RKOJ.lnk`. Acceptance bar: if clicking does anything other than open the UI they imagined, it's a bug. If the X button doesn't close, it's a bug. If a cmd window flashes, it's a bug. If a folder appears on Desktop they didn't ask for, it's a bug.
5. **Native means native.** When operator says "no fucking web ui", pywebview is web ui — HTML/JS surface inside a native frame is still web ui. Real native = PyQt6 / Tauri / native Win32. Don't argue terminology with the operator.
6. **Rebuild-from-source velocity ≠ progress.** 12 ships/day with no operator validation between them is the same as 0 ships/day. Insert a smoke + screenshot + operator-approval gate after every milestone before the next one starts.
7. **Sub-agents need TIGHT scope.** When dispatching a UI sub-agent, the brief must include: (a) verbatim operator quotes, (b) exact reference image path, (c) explicit DO-NOT list (no Excel ribbon, no KPI tiles, no extra tabs), (d) milestone-gate (build → smoke → if X button works → next milestone).
8. **Multi-agent file contention.** Two sub-agents touching the same directory creates rewrite races and lost edits. Partition by directory; carve each sub-agent its own subtree.
9. **The X button is first-class.** Without a working close button, no matter how beautiful the chrome, the EXE has failed acceptance. `closeEvent` MUST terminate all `QProcess` children before window close returns.
10. **Forever-expansion ≠ infinite-features-today.** "Forever expandable" means architect for plugin extensions (manifest-driven), NOT cram every Sinister tool into the first ship.

## Anti-patterns (enumerated)

- Adding ribbon / KPI tiles / tabs / status panels the operator never requested.
- Shipping a folder of files on the Desktop when the operator wants a single `.lnk` / `.exe`.
- Calling pywebview / Electron / Tauri-with-HTML "native".
- Auto-spawning terminals, agents, or sub-windows at EXE startup without explicit operator opt-in.
- Recursive `sys.executable` `Popen()` in frozen PyInstaller builds (spawn-loop EXE explosion).
- Hardcoding paths with one-character typos (`D:/Sinister/Sanctum/` vs `D:/Sinister Sanctum/`).
- "Ship + ask if it's right" — the operator cannot validate 12 ships/day; this pattern is just noise.

## Decision rules — when iterating operator-visible UI

- **Before any code change:** is there a canonical UI spec doctrine entry? If no → write it first, get verbatim quotes + reference images pinned, then code.
- **Before any sub-agent dispatch:** does the brief contain the spec path + DO-NOT list + milestone gate? If no → enrich the brief, don't dispatch.
- **Before any ship:** does the build close cleanly via the X button, with no orphan QProcesses? If no → don't ship.
- **Before any second ship in the same day:** did the operator validate the previous ship? If no → don't ship; wait for the validation gate.

## Remediation checklist (next time we touch operator-visible UI)

- [ ] Pin the verbatim operator quote(s) in a `*-exact-spec-<date>.md` doctrine entry.
- [ ] Save reference image paths into the doctrine entry; sub-agent reads from there.
- [ ] Write the DO-NOT list explicitly (every feature the operator did NOT ask for).
- [ ] Build → smoke (X button + no cmd flash + no orphan folder) → screenshot → operator approval → next milestone.
- [ ] One artifact, one location. Confirm the operator-clickable path matches operator's mental model.
- [ ] If "native" is asked, choose PyQt6 / Tauri-native / Win32 — never HTML-in-a-frame.
- [ ] Cap ships-per-day until operator validation gate fires; treat unvalidated velocity as noise.

## Composes-with map

- `rkoj-ui-exact-spec-2026-05-21.md` — the canonical spec we should have written first
- `rkoj-v1.0-to-v1.1-form-parity-journey.md` — companion narrative of the form-parity arc
- `multi-agent-branch-contention-isolation-pattern.md` — partition rule for sub-agent dispatch
- `auto-mode-launcher-pattern.md` — relevant when auto-mode dispatches UI builds without operator gating
