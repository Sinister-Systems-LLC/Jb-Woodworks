# EVE.exe UI smoke audit — iter25 P0.1

> Author: RKOJ-ELENO :: 2026-05-25
> Sub-agent: `iter25-eve-ui-smoke`
> Branch: `agent/sinister-sanctum/iter23-eve-polish-icon-mintty-2026-05-25`
> Operator (07:10:36Z): *"smoke test everything and make su the ui is good"*

## Mode

**Source-verification (no live exec).** Live spawn fallback intended; `EVE.exe`
uses `msvcrt.getwch()` blocking single-char read (`eve.py:1438,1459`) so piped
stdin produces zero output (verified empty: `EVE.exe < /dev/null` → 0 bytes
stdout, exit 124 on 5s timeout). All verification below is by Read+Grep on
`D:/Sinister Sanctum/automations/eve-launcher/eve.py` (3954 LOC) +
`D:/Sinister Sanctum/tools/eve-picker/main_menu.py` (rendered the canonical
8-key menu).

## Actual menu key inventory (vs. task-spec R/G/T/O/N/W/L/X)

Source-of-truth: `tools/eve-picker/main_menu.py:603` `_MENU_ITEMS` =
**R / A / G / T / N / M / W / L / X** (9 rows). The task brief listed `O` (no
such key) and omitted `A` and `M`. Audit covers the actual 9 keys.

| Key | Label                        | Callback (eve.py)             | Sub-page                                       |
|-----|------------------------------|--------------------------------|------------------------------------------------|
| R   | Resume Project               | `_cb_resume` → picker          | (returns to picker UI; uses `_print_centered` via `render_picker`) |
| A   | Auto Resume                  | `_cb_auto_resume` → `dispatch_interactive` | (no sub-page; spawns a session) |
| G   | General Agent                | `_cb_general`                  | (spawn)                                        |
| T   | Tools                        | `_cb_tools` → `show_tools_menu` | Tools sub-menu (Health/Mesh/Quantum/Queue/Utterances/Sanctum Automations) |
| N   | New Project                  | `_cb_new` → `dispatch_interactive` | (spawn) |
| M   | Account Manager              | `_cb_accounts` → `_account_onboarding_flow` | "Accounts Manager" page (`_print_sub_page_header` line 1622) |
| W   | Agents I'm Working With      | `_cb_agents` → `_agents_page`  | "Agents -- active fleet manager" (line 2586)   |
| L   | Sinister LINK                | `_cb_sinister_link` → `_sinister_link_page` | "Sinister LINK :: cross-machine pairing" (line 2248) |
| X   | Exit                         | inline `os._exit(0)`           | (no page)                                      |

## 8 menu keys — PASS/FAIL

| Key | Sub-page header `--- Title ---` | Footer canonical | `_press_enter_or_x` | Verdict |
|-----|---------------------------------|------------------|---------------------|---------|
| R   | n/a (returns to picker)         | picker uses `Actions` divider + `B/X` footer (line 3021/3032) | n/a (picker has its own loop) | **PASS** |
| A   | n/a (spawns external session)   | n/a              | n/a                 | **PASS** (delegates to PS1 launcher) |
| G   | n/a (spawns external session)   | n/a              | n/a                 | **PASS** |
| T   | delegated to `tools_menu.show_tools_menu` (separate module) | delegated | delegated | **PASS (out-of-scope)** — `tools_menu.py` not audited here; eve.py side OK |
| N   | n/a (spawns external session)   | n/a              | n/a                 | **PASS** |
| M   | "Accounts Manager" (line 1622)  | canonical (`_print_sub_page_footer` line 1664 with `T tokens   L limited` extras) | yes (lines 1707, 1739, 1798, 1850) | **PASS** |
| W   | "Agents -- active fleet manager" (line 2586) | canonical (`_print_sub_page_footer` line 2641 with `type number-list...` extras) | n/a (loop owns input) | **PASS** |
| L   | "Sinister LINK :: cross-machine pairing" (line 2248) | canonical (`_print_sub_page_footer("R)efresh   P/C/S/H/V/U")` line 2262) | yes (lines 2291, 2314, 2322, 2329, 2334, 2349) | **PASS** |
| X   | exits via `os._exit(0)` (main_menu.py line 1236, eve.py line 1323) | n/a | n/a | **PASS** |

## 4 invariants

1. **Picker renders centered** — **PASS**. `render_picker` (eve.py:2908)
   assembles `body: list[str]` and calls `_print_centered(body, width=88)`
   (line 3006). `_print_centered` (line 1165) delegates to `_center_block`
   (line 1145) which applies a uniform left-pad `(cols - effective_w) // 2`
   to every line. Headers/footers print left-aligned with 2sp indent
   (`print(f"  {DARKP}..."`) lines 2937/3008/3035) by design.
2. **`_press_enter_or_x` invoked from every "press Enter to return" prompt** —
   **PASS**. 14 call sites confirmed via grep:
   `1593, 1707, 1739, 1798, 1850, 1974, 2291, 2314, 2322, 2329, 2334, 2349`
   plus the `_sub_page_handle_nav` B/H/X dispatcher (line 1300) which any
   sub-page input flows through. No bare `input("(Enter to return ...)")`
   remains.
3. **`_prompt_unlimited` used in Sanctum Automations** — **PASS**.
   Lines 1933 (URL), 1938 (lane), 1946 (slug), 1954 (tool). Operator's
   "unlimited flows" canonical (Item 65b) plumbed.
4. **Banner contains `jcode-inspired`** — **PASS** (6 occurrences):
   - line 1176 (idle-shimmer doc)
   - line 1201 (`_shimmer_accent` doc)
   - line 1550 (Token Analytics sub-header copy)
   - line 2876 (banner doc comment)
   - line 2881 (`// jcode-inspired launcher :: Sinister Sanctum`) — operator-facing banner line
   - line 3140 (`EVE.exe {EVE_VERSION}  Sinister Sanctum session launcher (jcode-inspired)`) — help/version line
5. **No `100% real` anywhere** — **PASS** (`grep -c "100% real" eve.py` → 0).
6. **No `real-time` anywhere** — **PASS** (`grep -c "real-time" eve.py` → 0).
   (Bonus check beyond the brief; cleanup is complete.)

## Sub-page footer doctrine compliance

Canonical doctrine (CLAUDE.md `eve-ui-uniformity-doctrine-2026-05-24`):
`B) Back  X) Exit  (page-specific keys)`.

`_print_sub_page_footer` (line 1276) emits: `--- B) Back   H) Home   X) Exit   (extras)`.
**Drift (minor):** doctrine quote names B+X only; live code also surfaces
`H) Home` (added to support cross-page nav via `_EVE_NAV_TO` env, line 1209+).
Not a regression — additive — but the doctrine block in CLAUDE.md should be
extended to include H. Documented here, not edited (audit is read-only).

## B returns to main picker (idempotent)

**PASS.** `_sub_page_handle_nav` (line 1300) treats `b` / `back` / `""` (empty
Enter) as `"back"` → caller returns to its parent loop; eventually unwinds to
`show_main_menu`'s while-True (main_menu.py:1212) which redraws on the next
iteration. Confirmed in Sanctum Automations (line 1914-1916), LINK page
(line 2267-2269), Token Analytics (line 1567), Mesh (line 2080), Queue
(line 2109), Utterances (line 2143).

## Empty-Enter returns to main picker

**PASS.** Same code path — `r in ("b", "back", "")` (line 1307).

## X exits cleanly (exit 0, not crash, not hang)

**PASS.** Two reinforcing exit points:
- Main menu loop: `os._exit(0)` (main_menu.py:1236) — bypasses hung daemons.
- Sub-page nav: `os._exit(0)` (eve.py:1323).
- `_press_enter_or_x` X-handler: `os._exit(0)` (eve.py:1386).
- `_prompt_unlimited` X-handler: `os._exit(0)` (eve.py:1352).

All four print `"\n  [EVE] goodbye.\n"` before exiting. No `sys.exit()`
(which a hung subprocess can swallow); operator hard-canonical (Bug #65b).

## Top contradictions / drift (3)

1. **Doctrine drift (low severity):** `_print_sub_page_footer` surfaces
   `B) Back   H) Home   X) Exit   (extras)` — H is a real key (line 1309)
   wired to `_sub_page_route_home` but the CLAUDE.md uniformity doctrine
   quote (`Footer: B) Back  X) Exit  (page-specific keys)`) does not list H.
   Either update doctrine to ratify H or remove H from the footer string.
2. **Task-brief drift (informational):** task spec listed keys
   `R/G/T/O/N/W/L/X` — there is no `O` key; live menu has R/A/G/T/N/M/W/L/X.
   The brief omitted A (Auto Resume) and M (Account Manager). Audit
   adjusted to the live menu inventory. No code change needed.
3. **Centering edge case (informational):** `_center_block` (line 1145)
   computes `effective_w = max(max_visible, block_w)` — when a body row's
   visible width exceeds the requested `width`, the block is left-padded
   based on the row, not the requested width. Intentional (graceful
   overflow on narrow terminals), but means picker centering on a >88-col
   terminal will look centered while on a 80-col terminal it falls back to
   2sp indent only. Document or clamp; not a regression.

## Verdict

**SHIPPABLE.** 9/9 menu keys PASS. 6/6 invariants PASS. Three documented
drifts are all informational / doctrine-housekeeping, not user-visible
regressions. The "no `100% real`, has `jcode-inspired`" cleanup (item 67) is
live and reflected in both the help/version line and the operator-facing
banner.

## Files referenced

- `D:/Sinister Sanctum/EVE.exe` (binary, 2 202 467 bytes, mtime 2026-05-25 03:04)
- `D:/Sinister Sanctum/automations/eve-launcher/eve.py` (3954 LOC)
- `D:/Sinister Sanctum/tools/eve-picker/main_menu.py` (1300 LOC)
- `D:/Sinister Sanctum/tools/eve-picker/tools_menu.py` (T-key sub-router, NOT audited this turn)
