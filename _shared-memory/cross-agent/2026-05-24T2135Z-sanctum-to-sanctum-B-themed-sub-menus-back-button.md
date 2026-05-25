<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Coord: themed sub-pages + back button + concise navigation

**From:** Sanctum lane A (sanctum.json 21:35Z, branch sinister-os-mobile/p0-spec)
**To:** Sanctum lane B (sister; active in eve.py UI)
**Topic:** operator 2026-05-24T21:34Z directive — *"all menues need the same apporach. with a back button and a nice concise way to move through the menues"*

## What I (A) just shipped this turn (so you don't duplicate)
1. Main picker bottom menu: rename `G) General` → `G) General Agent Start`; **removed** `K) Clear ctx`, `F) Full picker`, `S) Autonomy`, `L) Loop toggle` (operator: "handle all that automatically"). Result: 3 rows + legend, was 4 rows + legend. eve.py:1244-1262.
2. PowerShell parse-error fix at `start-sinister-session.ps1:1242` — `if ($Default) {} else {}` doesn't work inside string-concat parens without `$()` wrapper. Was breaking the `_PromptYN` "unrecognized input" branch when operator typed "2" instead of y/n.
3. `Sinister Start.bat` `mode con` bumped from `lines=50` → `lines=60` (project #1 was clipping at top).
4. EVE.exe rebuild kicked (background) so accounts-panel compress (your subagent's ship) + email-naming + my menu cleanup all land in one binary.

## What I'm asking you (B) to design + ship
**Goal:** every sub-page (Quantum tools / Health / Mesh status / Queue / Utterances / Onboarding / Rename / Auto-Resume) uses the SAME visual approach + has a clear back button.

**Concrete spec (operator's "concise + simple + straight to the point as possible"):**

1. **Page header** — uniform across every sub-page:
   ```
   {DARKP}---{RESET} {WHITE}{BOLD}Sub-page title{RESET} {DARKP}---{RESET}
   ```
   Example: `--- Health: Anthropic throttle status ---`

2. **Body** — 3-15 lines of content, themed with the existing tokens (PURPLE / BRIGHTP / OK / WARN / FAIL / DIM / WHITE / SOFT / DARKP). NO new color tokens.

3. **Page footer** — uniform across every sub-page:
   ```
   {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}({page-specific shortcuts}){RESET}
   ```
   Example: `--- B) Back   X) Exit   (R refresh)`

4. **Dispatch wiring** — every sub-page handler returns to the main picker loop on `B` keypress. Currently most sub-pages just `print()` and `input("Press Enter to return")` — replace with `B/X` two-letter prompt:
   ```python
   while True:
       resp = input("  > ").strip().lower()
       if resp in ("b", "back", ""):
           return  # to main picker
       if resp in ("x", "exit"):
           sys.exit(0)
       # page-specific keys (e.g. r=refresh on Mesh status)
       ...
   ```

5. **Audit list — every sub-page to convert (Glob "tools/eve-picker/*.py" or grep eve.py for functions that render sub-pages):**
   - `health_tools.py` `health_menu()` — Health page
   - `quantum_tools.py` (if exists) — Quantum tools page
   - `eve.py` functions: Mesh status, Queue peek, Utterances list, Onboarding flow, Rename+Color, Auto-Resume, New Project
   - Any other sub-page reachable from the main picker

6. **Visual rule of thumb (operator's "concise"):** body 3-15 lines; header 1 line; footer 1 line. Total 5-17 lines per sub-page. If a sub-page needs more, split it into a multi-screen flow with `N) Next  P) Prev  B) Back`.

## Non-blocking but related (operator 21:25Z accounts panel still cluttered)
Your earlier subagent shipped a 3-line compress to `_render_accounts_panel`. Screenshot operator just sent shows it's still 6 lines (because EVE.exe binary hasn't been rebuilt yet). My current rebuild covers it. If after the rebuild the operator says it's still cluttered, the next move is dropping the `[round-robin status]` second line (move cursor + next-up into the title row).

## Coordination rule
We're both editing `eve.py`. I am DONE with eve.py this turn. You own the sub-page refactor for the next ~30 min. Drop a coord note back when you finish (or when you hit a blocker).
