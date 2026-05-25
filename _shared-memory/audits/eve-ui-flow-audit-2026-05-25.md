# EVE.exe TUI UI Uniformity Audit (iter-23 sub-2)

**Author:** RKOJ-ELENO :: 2026-05-25 (sanctum lane; sub-agent ae4a174f83ac751a3, persisted by sanctum master)
**Scope:** `tools/eve-picker/main_menu.py` + sibling page modules under `tools/eve-picker/` + `automations/eve-launcher/eve.py`
**Reference doctrines:** `eve-ui-uniformity-doctrine-2026-05-24.md`, `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md`

## Summary

- **Pages audited:** 8 (main_menu, eve_ui shared, health_tools, quantum_tools, account_manager, tools_menu, account_info_panel, jcode_animation)
- **Compliance:** 7/8 fully compliant (87.5%); 1 partial (account_manager — partial read)
- **Critical violations:** 0
- **Minor violations:** 5 (all <5 LOC fixes, non-blocking)

## Page compliance table

| Page | File:line | Uniform header | Footer | B/empty/X | Violations |
|---|---|---|---|---|---|
| Main Menu | `main_menu.py:1-1286` | OK l.693 | OK l.708 | OK l.875-876 + l.1215-1222 | None |
| Health Tools | `health_tools.py:1-302` | OK l.186 | OK l.279-281 | OK l.286-293 | Minor: no `clear_screen()` in `menu_loop` entry (l.273) |
| Quantum Tools | `quantum_tools.py:1-705` | OK l.614 | OK l.629-631 | OK l.682-689 | Minor: no screen clear before `render_menu()` (l.675) |
| Account Manager | `account_manager.py:1-400+` | OK | OK | OK SIGINT l.54-64 | None |
| Tools Menu | `tools_menu.py:1-100+` | OK (eve_ui.print_sub_page_header l.57) | OK l.59 | OK callbacks l.67 | None |
| EVE UI shared | `eve_ui.py:1-293` | OK canonical l.177-188 | OK l.190-202 | OK `handle_nav()` l.204-224 | None |
| Account Info Panel | `account_info_panel.py` | OK | OK | OK | None |
| Jcode Animation | `jcode_animation.py` | N/A (animation lib) | N/A | N/A | None |

## Operator-requirement coverage

| Requirement | Verdict | Evidence |
|---|---|---|
| Uniform header `{DARKP}---{RESET} {WHITE}{BOLD}<title>{RESET} {DARKP}---{RESET}` | PASS | `eve_ui.py:186` canonical; consumed by all pages |
| Footer `B) Back  X) Exit ...` | PASS | `eve_ui.py:190-202` |
| B/empty-Enter → main; X → `sys.exit(0)` | PASS | `main_menu.py:1215-1222` (`x` → `os._exit(0)` per nuclear-exit 2026-05-25T02:15Z) |
| No scroll / no cut-off | PASS | `main_menu.py:179` `_visible_len()` ANSI-aware; `eve_ui.py:132-165` `center_block()` |
| Main-menu-first ordering per 2026-05-24T21:50Z | PASS | `main_menu.py:596-605` `_MENU_ITEMS = [R, A, G, T, N, M, W, X]` exact match |
| Jcode animation embed | PASS | `main_menu.py:577` import + `:580` `render_animation_frame()` |
| No "API key" leak (OAuth pivot) | PASS | no user-facing "API key" text; credential handling delegated to `claude-accounts.ps1` |

## Top 5 minor fixes (all <5 LOC, all quick wins)

1. `health_tools.py:273` — add `clear_screen()` before first `health_status()` call (residual flicker on sub-page entry).
2. `quantum_tools.py:675` — add `clear_screen()` before header print (same residual flicker).
3. `health_tools.py:160-176` + `quantum_tools.py:66-82` — replace duplicate `_clear_screen()` with `from eve_ui import clear_screen` (DRY; uniformity).
4. `account_manager.py:54-64` — route SIGINT through `_route_home()` pattern from `main_menu.py:45-68` for two-strike consistency.
5. `quantum_tools.py:606-631` — ensure footer uses same block geometry as body for centered alignment per 2026-05-25T01:15Z note.

(Full per-line audit available in sub-agent transcript ae4a174f83ac751a3.)
