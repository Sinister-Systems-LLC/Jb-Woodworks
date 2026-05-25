<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

# EVE.exe Main-Menu Redesign Plan

**Created:** 2026-05-24T22:02Z
**Authority:** Operator hard-canonical 2026-05-24T21:51Z (verbatim spec in section 2).
**Owner:** sanctum-mesh-foundation (Phase 1); sibling sanctum (Phase 2/3/4 per inbox split)

---

## 1. Goal

Replace EVE.exe's current direct-to-picker behavior with a centered MAIN MENU that:
- Opens first when EVE.exe launches
- Displays jcode-style random moving animations (banner region)
- Shows centered MCP count + bot count + EVE name + general info
- Offers 6 picks: Resume / General / Tools / Onboarding / New Project / Exit
- All sub-screens have BACK buttons to return
- Every TUI fits the window (no scroll, no cut-off)
- Honors `eve-exe-uniform-ui-infinite-accounts-2026-05-24` doctrine 5 invariants

The current project picker becomes a SUB-SCREEN reached via Resume + New Project.

## 2. Operator verbatim spec (2026-05-24T21:51Z)

> *"i want the exe to first open to a menu that looks like this WITH THE RANDOM MOVING SAME CODE FROM JCODE ANIMATIONS JUST LIKE THERE. here is the code legit take it and have it the same its not that hard. C:/Users/Zonia/Desktop/jcode-0.12.4 - some nice looking things to same our mcp, bots, name of eve and i want it cetnered and look just like this too. show some geenral info here. then i what a section that we can pick from on what we want to do that are the following in the following order: Resume -> that looks like this. then Auto resume that will go to that and take that same logic to have the rest of these: General, tools, new project, onboarding, exit. then fill in the rest. treat that main screen as a main menu and have back buttons to go back etc. so this part wont be on this screen. each tui needs to fit the window and not have to scroll or get cut off. have the start ui same size as we have now. that will lead to different places like the main screen we open to now to pick a project to work on with these notes. help my other agent do this as well."*

## 3. Four-phase ship

| Phase | Scope | Owner | Effort | Status |
|---|---|---|---|---|
| **Phase 1** | `_main_menu_loop()` skeleton in `eve.py` + entry-point wire + 6 menu picks + back-button routing + Uniform-UI compliant header | sanctum-mesh-foundation | 1 iter | **shipping this iter** |
| **Phase 2** | JCODE animation port (HSV-to-RGB rotation + donut + orbit_rings; ~150 LOC Python) | sibling sanctum (option a from inbox) — default at 30min: me | 1 iter | inbox-coordinated |
| **Phase 3** | Centered MCP/bot/EVE/general info block | sibling sanctum (option b) | 1 iter | inbox-coordinated |
| **Phase 4** | Window-fit detection (shutil.get_terminal_size + dynamic line budget; codify as 6th invariant in Uniform UI doctrine) | sibling sanctum (option c) | 1 iter | inbox-coordinated |

## 4. Phase 1 design (THIS ITER)

**New function in `eve.py`:** `_main_menu_loop()` — invoked from `main()` BEFORE the existing project picker. Returns the operator's pick; main() then dispatches to existing handlers.

**Menu layout (6 lines max per Uniform UI 6-line cap):**

```
  Sinister Sanctum  EVE :: <mcp_count> MCP / <bot_count> bots  [R]esume [G]eneral [T]ools [O]nboard [N]ew [X]it
  -----------------------------------------------------------------------------------------------------------
  [R]esume    -> latest resume-point per lane + project picker (current screen)
  [G]eneral   -> general-purpose agent (no project scope)
  [T]ools     -> automations menu (current A-key sub-menu)
  [O]nboard   -> account/skill onboarding wizard
  [N]ew       -> create new project
  [X]it       -> close EVE
  > pick a letter:
```

**Wiring:** main() entry calls `_main_menu_loop()` first. Pick R or N routes to existing `build_picker_state` + main loop. Pick G routes to `dispatch_project('general')`. Pick T routes to `_sanctum_automations_menu()`. Pick O routes to `_account_onboarding_flow()`. Pick X exits.

**BACK button:** sub-screens that loop back call `_main_menu_loop()` again instead of `lib.build_picker_state` to refresh.

**Environment flag:** `SINISTER_SKIP_MAIN_MENU=1` skips the new menu and falls into the legacy direct-to-picker behavior (escape hatch for operator if anything goes sideways).

## 5. Phase 2 design (NEXT ITER if I take it)

**Port `C:/Users/Zonia/Desktop/jcode-0.12.4/src/tui/ui_animations.rs:1-50`** to `automations/eve-launcher/animations.py`:
- HSV-to-RGB hue rotation: `hue = (time_hue + t * 160.0) % 360.0`
- Donut 3D ASCII (orbit_rings variant)
- Ease-out-cubic transitions (150ms ticks)
- Render into a banner region (top 5 rows of main menu)
- Threading: use a background thread that ticks every 80ms; main thread reads the rendered frame string and prints; non-blocking

**Constraint:** must NOT exceed 5 rows in the banner area (Uniform UI 6-line cap minus 1 line for menu header).

## 6. Phase 3 design (centered MCP/bot/EVE/general info)

Right side of main menu (or below banner):
```
                    [EVE on Sinister Sanctum]
              MCP:  13 servers, 4 loaded   Bots: 13 (0 awake)
              Mode: --skip-perms           Loop: <ON|OFF>
              Acct: operator (4h00m left, 80% used today)
```

Center via terminal-width detection. Falls back to left-aligned on terminals <60 cols.

## 7. Phase 4 design (window-fit detection)

Add `_terminal_fits(min_rows, min_cols)` helper in `eve.py` using `shutil.get_terminal_size()`. Every TUI panel calls this before rendering:
- If terminal smaller than required, render a COLLAPSED variant (top-3 instead of top-5; truncate labels; drop banner)
- Codify as Uniform UI doctrine 6th invariant (next iter brain edit)

## 8. Compose with

- `eve-exe-uniform-ui-infinite-accounts-2026-05-24` (5 mandatory invariants apply to every menu)
- `session-start-auto-update-propagation-2026-05-24` (sibling's: post-edit `verify-eve-features.ps1 -AutoRebuild -SyncMirror`)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (mesh-lock claim on eve.py shared edits; I hold `eve.py-main-menu-loop-phase-1` lock TTL 1800s)
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R3 gradual not big-bang; R2 EVE-reachable on next spawn)
- `loop-mode-continuous-iteration-2026-05-24` (ship Phase per iter; never ScheduleWakeup)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 6 laser-focus: one phase per iter, parse-clean smoke before claimed-shipped)

## 9. Verification

```powershell
# Phase 1 acceptance
python -m py_compile D:\Sinister\ Sanctum\automations\eve-launcher\eve.py    # parse OK
# Then manually: launch EVE.exe; observe main menu opens FIRST; pick each letter; verify back-buttons return
# Then: powershell -File automations\verify-eve-features.ps1 -AutoRebuild -SyncMirror
# Then: re-open EVE.exe (running instance holds old bundle)
```
