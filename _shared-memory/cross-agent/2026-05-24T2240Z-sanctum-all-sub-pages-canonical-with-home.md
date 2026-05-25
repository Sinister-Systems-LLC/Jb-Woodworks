<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# sanctum :: ALL sub-pages canonical (header/body/footer with B/H/X)

**From:** sanctum (lane subagent, /loop)
**Sent:** 2026-05-24T22:40Z
**Trigger:** operator verbatim 2026-05-24T22:32Z — *"each one you click goes to its own menu with selections. back or home button quit all those things with the same look and feel for the ui throught"* (screenshot of "Sanctum Automations" sub-page using OLD non-canonical layout).

## Spec applied

Per `_shared-memory/knowledge/eve-ui-uniformity-doctrine-2026-05-24.md` (now extended with `H) Home` footer key, this turn):

```
  --- <Sub-page title> ---                      <- HEADER (DARKP --- WHITE BOLD title DARKP ---)

  <body content>                                 <- BODY (canonical tokens only; <=30 lines)

  --- B) Back   H) Home   X) Exit   (<keys>)     <- FOOTER (DIM --- PURPLE shortcuts)
```

Footer semantics:
- `B` / `back` / `""` (Enter) -> return to PARENT menu
- `H` / `home` -> route to `main_menu.show_main_menu()` then return
- `X` / `exit` / `q` / `quit` -> `sys.exit(0)`

## Conversions shipped

| # | Page | File | Status | Smoke |
|---|---|---|---|---|
| 1 | Sanctum Automations | `automations/eve-launcher/eve.py:_sanctum_automations_menu` (was L997-L1006; now L1085-L1108) | converted (header + footer + B/H/X) | PASS |
| 2 | Mesh Status | `automations/eve-launcher/eve.py:_view_mesh_status` (was L1080-L1175; now L1148-L1243) | converted (header + footer + B/H/X/R) | PASS |
| 3 | Queue (top 3) | `automations/eve-launcher/eve.py:_view_queue` (NEW fn @ L1246; main-loop call site replaced) | extracted + canonical | PASS |
| 4 | Utterances (5) | `automations/eve-launcher/eve.py:_view_utterances` (NEW fn @ L1274; main-loop call site replaced) | extracted + canonical | PASS |
| 5 | Account Onboarding | `automations/eve-launcher/eve.py:_account_onboarding_flow` (header @ L878; footer @ L1005-L1017) | converted (header + footer + B/H/X/O) | parse-OK (interactive wizard) |
| 6 | Quantum Tools | `tools/eve-picker/quantum_tools.py:render_menu` + `menu_loop` (L577-L590 + L617-L660) | converted (canonical `---` header + B/H/X footer) | PASS |
| 7 | Health | `tools/eve-picker/health_tools.py:menu_loop` (L227-L259) | extended (added `H) Home` to existing canonical footer) | PASS |
| 8 | Account Manager | `tools/eve-picker/account_manager.py:_render_actions_menu` + `show_account_manager` (L871-L890 + L893-L946) | extended (added `H) Home` to footer + handler) | PASS |
| 9 | Rename+Color | `automations/eve-launcher/eve.py` -> `dispatch_interactive` (PS1) | OUT OF SCOPE (PS1-lane owns the rendering, per coord note point 8) | n/a |
| 10 | Auto-Resume | `automations/eve-launcher/eve.py` -> `dispatch_interactive` (PS1) | OUT OF SCOPE (PS1-lane) | n/a |
| 11 | New Project | `automations/eve-launcher/eve.py` -> `dispatch_interactive` (PS1) | OUT OF SCOPE (PS1-lane) | n/a |

**Pages converted: 8 of 8 in-scope.** (Three remaining items dispatch through `start-sinister-session.ps1` whose rendering is owned by a different lane — flagging here so the operator can route a follow-up to the PS1 lane.)

## New shared helpers in eve.py (single source of truth)

Added near L820 of `automations/eve-launcher/eve.py`:

- `_print_sub_page_header(title)` -> 1-line `DARKP --- WHITE BOLD title DARKP ---` + blank line
- `_print_sub_page_footer(extra_keys="")` -> `DIM --- PURPLE B) Back  H) Home  X) Exit  DIM (extras)`
- `_sub_page_route_home()` -> try-import `main_menu.show_main_menu()`; swallow on missing
- `_sub_page_handle_nav(resp)` -> common B / H / X dispatch; returns `"back"` / `"home"` / `None`

Sibling modules (`quantum_tools.py`, `health_tools.py`, `account_manager.py`) each define a local `_route_home()` that imports `main_menu.show_main_menu()` lazily inside try/except so a circular-import never crashes a sub-page.

## Parse-OK verification

```
PARSE-OK automations/eve-launcher/eve.py
PARSE-OK tools/eve-picker/quantum_tools.py
PARSE-OK tools/eve-picker/health_tools.py
PARSE-OK tools/eve-picker/account_manager.py
PARSE-OK tools/eve-picker/main_menu.py
```

All five files parse-OK after edits.

## Smoke evidence (rendered output captured)

`_view_queue` / `_view_utterances` / `_view_mesh_status` / `_sanctum_automations_menu` / `quantum_tools.render_menu` / `health_tools.menu_loop` / `account_manager._render_actions_menu` all rendered the canonical 3-block layout with `B) Back   H) Home   X) Exit` footer line under live data when invoked through a Python harness with `sys.stdin = io.StringIO("b\n")`.

Sample (Sanctum Automations):

```
  --- Sanctum Automations ---

   1)  Account status board
   2)  Drop a link to ingest
   ...
  15)  Inbox: list tool-dispatch msgs

  --- B) Back   H) Home   X) Exit   (1-15 to run)
```

## Doctrine updated

`_shared-memory/knowledge/eve-ui-uniformity-doctrine-2026-05-24.md` -> "Universal sub-page layout" section now documents the `H) Home` key + the full footer key contract table. The mid-October-era pre-existing doctrine block already covered `B) Back` and `X) Exit`; this turn added the `H) Home` row.

Author: RKOJ-ELENO :: 2026-05-24
