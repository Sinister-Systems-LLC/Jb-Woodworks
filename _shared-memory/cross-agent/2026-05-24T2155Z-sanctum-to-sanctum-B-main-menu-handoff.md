# Sanctum -> Sanctum-B :: main_menu handoff + project-picker extraction

Author: RKOJ-ELENO :: 2026-05-24
From: Sanctum (this lane)
To: Sanctum-B (eve.py main() owner)
Operator: ezekielromero314@gmail.com (operator)
Trigger: operator 2026-05-24T21:50Z verbatim hero-menu spec

## What shipped this turn

NEW FILE: `D:\Sinister Sanctum\tools\eve-picker\main_menu.py` (v0.1.0)

- Renders jcode-hero centered panel (8-line block) + animation slot + 7-item menu (R/A/G/T/N/M/X)
- Fits in a 60-line terminal, no scroll
- Centers via `os.get_terminal_size().columns` (60-col floor)
- Hero reads: `_shared-memory/claude-accounts.json` (acct label, email-naming already shipped), `eve_picker_lib.count_mcp/count_bots`, `_shared-memory/heartbeats/*.json` filtered by mtime < 300s
- Imports `jcode_animation.render_frame()` (sibling sub-agent) - graceful no-op fallback
- Single-letter shortcut OR arrow-key+Enter; X / Ctrl-C / EOF -> sys.exit(0)
- Public entry: `show_main_menu(callbacks={resume, auto_resume, general, tools, new_project, account_mgr})` - all callbacks optional, each missing one falls back to a friendly stub
- ANSI palette mirrors eve.py (Sanctum purple); NO_COLOR / TERM=dumb respected
- Smoke-tested: `python -c "import main_menu"` import-clean; hero renders 8 lines, 7 menu items, parse-clean

ONE EDIT: `D:\Sinister Sanctum\automations\eve-launcher\eve.py` main() (just before the existing `_filter_query = ""` line at the picker-loop preamble)

```python
try:
    from main_menu import show_main_menu  # type: ignore
    show_main_menu(callbacks={
        "resume": lambda: None,  # break out -> existing picker loop runs
    })
except ImportError:
    pass  # main_menu module missing; render legacy picker directly.
```

eve.py parse-clean (`ast.parse` OK). The lambda is a tactical bridge: R falls through to the existing picker loop already in `while True:` below.

## What sister-B needs to do

1. **Extract project-picker body into `def show_project_picker(state) -> str:`** inside eve.py (or a new module). Currently the picker render + input loop lives directly inside `main()` as a `while True:` block. The extraction:
   - Takes `state` (PickerState) + returns the user's `raw` selection (or empty for quit/back)
   - Wraps the existing banner / render_picker / input / fuzzy-filter logic
   - Honors B/Esc as a back-button -> return early to main_menu
2. **Wire the callback dict** in the `show_main_menu(callbacks=...)` call. Replace the placeholder lambda with real callables:
   - `resume`: `lambda: show_project_picker(state)`
   - `auto_resume`: existing auto-resume flow (search for `--auto-resume` argv handler or `state.default_key` shortcut)
   - `general`: existing General Agent Start flow
   - `tools`: combined `quantum_tools.menu_loop()` + `health_tools.menu_loop()` page (per operator 2026-05-24T21:35Z themed sub-menus with back-button)
   - `new_project`: existing N flow
   - `account_mgr`: rename from Onboarding -> Account Manager (operator 2026-05-24T21:50Z)
3. **Tools combined page**: drop a small wrapper `def tools_page():` that prints "1) Quantum  2) Health  B) Back" then dispatches. Quantum + Health currently have separate menu_loop()s; the wrapper composes them under one Tools entry per spec.

## Coord status

- File created, parse-clean, import-clean, smoke-tested.
- eve.py edit is non-destructive (try/except ImportError; lambda for R = no-op pass-through).
- No file lock contention encountered; sister-B can edit eve.py freely.
- Sibling sub-agent ships `jcode_animation.py` in same dir (`tools/eve-picker/`). main_menu.py uses graceful try/except - works today even without that module.

## References

- Spec: operator 2026-05-24T21:50Z verbatim ("first open to a menu that looks like... random moving same code from jcode animations... Resume -> Auto resume -> General, tools, new project, oboarding, exit")
- Composes with: `_shared-memory/cross-agent/2026-05-24T2135Z-sanctum-to-sanctum-B-themed-sub-menus-back-button.md` (back-button doctrine)
- Email-naming: already shipped per `2026-05-24T2130Z-sanctum-account-email-naming.md`
- Brain doctrine: `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md` (terminal UI is exempt from skeleton CSS but the centered-hero pattern mirrors the dashboard hero)
