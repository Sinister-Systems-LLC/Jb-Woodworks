<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# sanctum-A -> sanctum-B :: sub-page canonical header/body/footer refactor (diff pack)

**From:** sanctum (lane A / sub-pages subagent)
**To:** sanctum-B (eve.py lane-holder)
**Sent:** 2026-05-24T21:55Z
**Why coord note instead of direct edits:** sister-B has 613 in-flight insertions in `automations/eve-launcher/eve.py` (`git diff --stat` shows `+613/-34`). Concurrent edits would collide on the line numbers I'd target — every render fn (`_render_accounts_panel`, `_account_onboarding_flow`, `_sanctum_automations_menu`, `_view_mesh_status`) lives inside sister-B's pending block. Per the operator directive *"each tui needs to fit the window and not have to scroll or get cut off"* and the eve-ui-uniformity-doctrine, here is the COMPLETE per-sub-page transformation spec for sister-B (or whichever lane lands first) to apply.

## Doctrine refs

- `_shared-memory/knowledge/eve-ui-uniformity-doctrine-2026-05-24.md` (header/body/footer spec + canonical color tokens)
- Operator verbatim 2026-05-24T21:50Z: *"treat that main screen as a main menu and have back buttons to go back etc ... each tui needs to fit the window and not have to scroll or get cut off."*

## Canonical layout (all sub-pages)

```python
def render_<page>() -> None:
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}<Title>{RESET} {DARKP}---{RESET}")
    print()
    # body (<=30 lines; paginate if more)
    ...
    print()
    print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(<page-keys>){RESET}")

    while True:
        try:
            resp = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if resp in ("", "b", "back"):
            return
        if resp in ("x", "exit"):
            import sys; sys.exit(0)
        # page-specific keys here
        return  # default: go back
```

## Per-sub-page diff (apply to eve.py after sister-B's pending block lands)

### 1. `_view_mesh_status` (current eve.py L1039–L1141)

**Issue:** Header uses raw `'-' * 88` (88 chars exceeds 80-col window). Footer is single `input("press Enter to return")`. Body is ~80 lines — VIOLATES 30-line budget.

**Diff:**
```diff
@@ def _view_mesh_status() -> None:
-    print()
-    print(f"  {WHITE}{BOLD}MESH STATUS{RESET}  {DIM}// fleet at-a-glance{RESET}")
-    print(f"  {DARKP}{'-' * 88}{RESET}")
+    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Mesh Status{RESET} {DARKP}---{RESET}")
+    print()
@@ (keep sections 1-4 BUT cap each to 4 rows max; total body must be <=28 lines)
-    print()
-    print(f"  {DARKP}{'-' * 88}{RESET}")
-    print(f"  {DIM}// fleet broadcast: `sinister-swarm broadcast --message \"<text>\"`{RESET}")
-    print(f"  {DIM}// DM a lane:        `sinister-swarm dm --to <slug> --message \"<text>\"`{RESET}")
-    print(f"  {DIM}// watch live:       `sinister-swarm watch`{RESET}")
-    print()
-    try:
-        input(f"  {DIM}> press Enter to return to picker:{RESET} ")
-    except (EOFError, KeyboardInterrupt):
-        pass
+    print()
+    print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(R)efresh{RESET}")
+    while True:
+        try: resp = input("  > ").strip().lower()
+        except (EOFError, KeyboardInterrupt): return
+        if resp in ("", "b", "back"): return
+        if resp in ("x", "exit"): import sys; sys.exit(0)
+        if resp == "r": _view_mesh_status(); return
+        return
```
Body trim plan: heartbeats (3 lines: counters + top 3) + inbox (3 lines: total + top 2) + accounts (1 line per acct, max 5) + recent (3 lines: top 3 commits). Net <=25 body lines.

### 2. `_queue_top_rows` view (current eve.py L1778–L1792 inline in main loop)

**Issue:** Inline render with `input("press Enter to return")` — not a function, can't be called from new Tools page. Body shows only 3 rows but no header bracket pattern.

**Diff:** Extract to function + canonicalize.
```python
def _view_queue() -> None:
    """Canonical Queue sub-page."""
    rows = _queue_top_rows(3)
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Queue (top 3 open){RESET} {DARKP}---{RESET}")
    print()
    if not rows:
        print(f"  {DIM}(no ## headers in OPERATOR-ACTION-QUEUE.md){RESET}")
    for r in rows:
        trunc = r if len(r) <= 76 else r[:73] + "..."
        print(f"  {PURPLE}*{RESET} {SOFT}{trunc}{RESET}")
    print()
    print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(R)efresh{RESET}")
    while True:
        try: resp = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt): return
        if resp in ("", "b", "back"): return
        if resp in ("x", "exit"): import sys; sys.exit(0)
        if resp == "r": _view_queue(); return
        return
```
Then in main loop replace L1778-L1792 with `_view_queue()`.

### 3. `_unresolved_utterances` view (current eve.py L1796–L1815 inline)

Same pattern — extract to `_view_utterances()`:
```python
def _view_utterances() -> None:
    """Canonical Utterances sub-page."""
    recs = _unresolved_utterances(5)
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Utterances (last 5 unresolved){RESET} {DARKP}---{RESET}")
    print()
    if not recs:
        print(f"  {DIM}(operator-utterances.jsonl is clean){RESET}")
    for r in recs:
        ts = r.get("ts_utc", "?")
        slug = r.get("session_slug", "?")
        preview = (r.get("preview") or r.get("message_full",""))[:60]
        status = r.get("status","new")
        print(f"  {PURPLE}*{RESET} {DIM}{ts}{RESET} {BRIGHTP}{slug}{RESET} "
              f"{SOFT}({status}){RESET}: {WHITE}{preview}{RESET}")
    print()
    print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(R)efresh{RESET}")
    while True:
        try: resp = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt): return
        if resp in ("", "b", "back"): return
        if resp in ("x", "exit"): import sys; sys.exit(0)
        if resp == "r": _view_utterances(); return
        return
```

### 4. `_account_onboarding_flow` (current L791–L917)

**Issue:** No header bracket. Three nested `input()` prompts + final `input("press Enter")`. Body is multi-screen by design (interactive form). Treat as a wizard page — header at top, footer ONLY after completion screen.

**Diff:**
```diff
@@ def _account_onboarding_flow() -> None:
-    print()
-    print(f"  {WHITE}{BOLD}ROUND-ROBIN ACCOUNT ONBOARDING{RESET}")
-    print(f"  {DIM}from C:\\Users\\Zonia\\Desktop\\ROUND-ROBIN-ACCOUNT-ONBOARDING.md{RESET}")
-    print()
+    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Account Onboarding{RESET} {DARKP}---{RESET}")
+    print()
@@ end of function:
-    try:
-        input(f"  {DIM}> press Enter to return to picker:{RESET} ")
-    except (EOFError, KeyboardInterrupt):
-        return
+    print()
+    print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(O to onboard another){RESET}")
+    while True:
+        try: resp = input("  > ").strip().lower()
+        except (EOFError, KeyboardInterrupt): return
+        if resp in ("", "b", "back"): return
+        if resp in ("x", "exit"): import sys; sys.exit(0)
+        if resp == "o": _account_onboarding_flow(); return
+        return
```

### 5. `_sanctum_automations_menu` (current L928–L1036)

**Issue:** 15-item list with description per item — total render ~30+ lines body. Already has loop-back ("Q) back to picker") but uses non-canonical "Q" key and adds per-item description rows.

**Diff:**
```diff
@@ inside while True loop start:
-        print()
-        print(f"  {WHITE}{BOLD}Sanctum Automations{RESET}  {DIM}// EVE-driven, no typing powershell{RESET}")
-        print(f"  {DARKP}{'-' * 60}{RESET}")
+        print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Sanctum Automations{RESET} {DARKP}---{RESET}")
+        print()
@@ list rendering (15 items in 1 line each, no separate desc line):
         for i, (label, _, _) in enumerate(items, start=1):
-            print(f"  {BRIGHTP}{i:>2}){RESET}  {WHITE}{label}{RESET}")
-        print(f"  {BRIGHTP}  Q){RESET}  back to picker")
+            print(f"  {PURPLE}{i:>2}){RESET}  {WHITE}{label}{RESET}")
+        print()
+        print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(1-{len(items)} to run){RESET}")
@@ B/back handling already correct; just rename `q` -> `b`:
-        if choice in ("q", "quit", "", "back"):
+        if choice in ("b", "back", ""):
+            return
+        if choice in ("x", "exit"):
+            import sys; sys.exit(0)
```
With 15 items + 4 framing lines = 19 lines body. UNDER 30 budget. PASS.

### 6. Quantum Tools (`tools/eve-picker/quantum_tools.py`)

**Issue:** `_header()` uses `'=' * 68` (68 = OK but inconsistent vs sub-page `---`). Footer is `input("press Enter for menu, B/Q to exit")` not canonical.

**Diff (in `quantum_tools.py`):**
```diff
@@ def _header(title: str) -> None:
-    print()
-    print(f"  {DARKP}{'=' * 68}{RESET}")
-    print(f"  {WHITE}{BOLD} {title} {RESET}")
-    print(f"  {DARKP}{'=' * 68}{RESET}")
+    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}{title}{RESET} {DARKP}---{RESET}")
+    print()

@@ def render_menu():
-    print()
-    print(f"  {DARKP}{'=' * 68}{RESET}")
-    print(f"  {WHITE}{BOLD} EVE :: Quantum Tools sub-menu (T) {RESET}")
-    print(f"  {DARKP}{'=' * 68}{RESET}")
-    print(f"  {SOFT}Read-only access to projects/sinister-snap-api-quantum/outputs/{RESET}")
-    print()
+    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Quantum Tools{RESET} {DARKP}---{RESET}")
+    print()
+    print(f"  {SOFT}Read-only :: projects/sinister-snap-api-quantum/outputs/{RESET}")
+    print()
@@ remove per-item human-line (drops 10 lines body):
     for num, name, desc, human in _TOOLS:
         print(f"  {PURPLE}{num}){RESET} {WHITE}{name:<20}{RESET} {SOFT}{desc}{RESET}")
-        print(f"     {DIM}{human}{RESET}")
-    print(f"  {PURPLE}B){RESET} {WHITE}{'back to picker':<20}{RESET}")
-    print(f"  {DARKP}{'-' * 68}{RESET}")
+    print()
+    print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(1-10 to run){RESET}")

@@ menu_loop end:
-        try:
-            input(f"  {DIM}> press Enter for menu, B/Q to exit:{RESET} ")
-        except (EOFError, KeyboardInterrupt):
-            return 0
+        try: resp = input(f"  {DIM}> Enter for menu, B back, X exit:{RESET} ").strip().lower()
+        except (EOFError, KeyboardInterrupt): return 0
+        if resp in ("b","back"): return 0
+        if resp in ("x","exit"): import sys; sys.exit(0)
```
Body: 10 tool rows + 4 framing = 14 lines body. PASS.

### 7. Health (`tools/eve-picker/health_tools.py`)

Same header normalization + footer canonicalization:
```diff
@@ def _header(title: str) -> None:
-    print()
-    print(f"  {DARKP}{'=' * 68}{RESET}")
-    print(f"  {WHITE}{BOLD} {title} {RESET}")
-    print(f"  {DARKP}{'=' * 68}{RESET}")
+    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}{title}{RESET} {DARKP}---{RESET}")
+    print()

@@ def menu_loop():
-    try:
-        input(f"  {DIM}> press Enter to return to picker:{RESET} ")
-    except (EOFError, KeyboardInterrupt):
-        pass
-    return 0
+    print()
+    print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(R)efresh{RESET}")
+    while True:
+        try: resp = input("  > ").strip().lower()
+        except (EOFError, KeyboardInterrupt): return 0
+        if resp in ("", "b", "back"): return 0
+        if resp in ("x", "exit"): import sys; sys.exit(0)
+        if resp == "r": health_status(); continue
+        return 0
```
Trim `health_status()` body: drop the 3-line "log files:" footer block — those paths already in doctrine. Body ~18 lines after trim. PASS.

### 8. Rename + Color / Auto-Resume / New Project

These dispatch through `dispatch_interactive()` -> `start-sinister-session.ps1` (the PS1 owns the rendering, not eve.py). Sister-B should NOT touch from eve.py — coord that with the PS1-lane owner separately. **Out of scope for this refactor pass.**

## NEW Tools page (operator main-menu mockup: `T) Tools`)

Per operator 21:50Z: "treat that main screen as a main menu". Operator wants `T) Tools` to be a hub. Two options:

**Option A (minimal):** Keep H + T as separate main-menu keys (current state). Skip the consolidation.

**Option B is LOCKED IN** — sister-B's `tools/eve-picker/main_menu.py` (just created) defines `_MENU_ITEMS` with `("T", "Tools", "")` and the `show_main_menu(callbacks={...'tools': fn})` API. So the `tools` callback MUST render the consolidated Tools hub below:
```python
def _tools_menu() -> None:
    """Canonical Tools hub :: Quantum tools / Health / Mesh status."""
    while True:
        print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Tools{RESET} {DARKP}---{RESET}")
        print()
        print(f"  {PURPLE}Q){RESET} {WHITE}Quantum tools{RESET}        {SOFT}QBC / prescreen / drift / catalog{RESET}")
        print(f"  {PURPLE}H){RESET} {WHITE}Health{RESET}               {SOFT}Anthropic throttle / quota{RESET}")
        print(f"  {PURPLE}M){RESET} {WHITE}Mesh status{RESET}          {SOFT}fleet heartbeats / inbox / accounts{RESET}")
        print()
        print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(Q/H/M){RESET}")
        try: resp = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt): return
        if resp in ("", "b", "back"): return
        if resp in ("x", "exit"): import sys; sys.exit(0)
        if resp == "q": quantum_tools.menu_loop()
        elif resp == "h": health_tools.menu_loop()
        elif resp == "m": _view_mesh_status()
```
Body: 6 lines content + 4 framing = 10 lines. PASS.

Main-menu impact: `T) Tools` replaces `T) Quantum` + `H) Health` + `M) Mesh` as direct keys. Whichever lane lands first should pick A or B based on the main_menu subagent's final spec.

## Audit checklist (run after sister-B lands edits)

For each converted sub-page:
1. Has `{DARKP}---{RESET} {WHITE}{BOLD}<title>{RESET} {DARKP}---{RESET}` header. PASS / FAIL.
2. Has `{DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(...){RESET}` footer. PASS / FAIL.
3. Body line count ≤30 (count between header blank-line and footer blank-line). PASS / FAIL.
4. Loop accepts `b`, `back`, ``""`` -> return. `x`, `exit` -> sys.exit(0). PASS / FAIL.
5. ONLY uses canonical tokens (PURPLE/BRIGHTP/OK/WARN/FAIL/DIM/WHITE/SOFT/DARKP). No new colors. PASS / FAIL.

## Smoke test (post-edit)

```bash
python -c "import ast; ast.parse(open('D:/Sinister Sanctum/automations/eve-launcher/eve.py').read()); print('PARSE-OK')"
python -c "import ast; ast.parse(open('D:/Sinister Sanctum/tools/eve-picker/quantum_tools.py').read()); print('PARSE-OK')"
python -c "import ast; ast.parse(open('D:/Sinister Sanctum/tools/eve-picker/health_tools.py').read()); print('PARSE-OK')"
```

All three must print `PARSE-OK`.

## Why I'm NOT applying directly

`git diff --stat` reports `automations/eve-launcher/eve.py | 647 +++... | 1 file changed, 613 insertions(+), 34 deletions(-)` — sister-B's pending block already mutates every line range I'd touch (`_render_accounts_panel` @ L640, `_account_onboarding_flow` @ L791, `_sanctum_automations_menu` @ L928, `_view_mesh_status` @ L1039). Applying my edits against the current working tree would either (a) blow away sister-B's pending work or (b) produce a merge-mess that takes longer to untangle than letting sister-B land first and me follow with a clean patch on top.

**Next-turn plan:** sister-B lands the in-flight refactor. I re-Read sub-page line ranges. I apply the diffs above with current line numbers. I run the smoke test + audit checklist. I report verified line counts.

Author: RKOJ-ELENO :: 2026-05-24
