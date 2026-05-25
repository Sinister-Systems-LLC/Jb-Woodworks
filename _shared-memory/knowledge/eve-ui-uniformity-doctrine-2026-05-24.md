<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  superseded_by: eve-exe-uniform-ui-infinite-accounts-2026-05-24
-->
# EVE UI uniformity + infinite accounts + no half-ass doctrine

**Status:** hard-canonical 2026-05-24 (sanctum lane). CLAUDE.md top block points here.
**Operator verbatim 2026-05-24T21:40Z:** *"allow infinite accounts and all pages on the eve exe need to have a uniform ui look and all hgave a concise complete simple to the point layout. update memory for this. we dont do shit half ass"*

## Universal sub-page layout

```
  --- <Sub-page title> ---                       <- HEADER (1 line, DARKP bracket + WHITE BOLD title)

  <body content>                                  <- BODY (3-30 lines, themed tokens)
  <body content>

  --- B) Back   H) Home   X) Exit   (...)         <- FOOTER (1 line, DIM bracket + PURPLE shortcuts)
```

### Footer key contract (RKOJ-ELENO :: 2026-05-24T22:40Z — operator)

Operator verbatim 2026-05-24T22:32Z: *"each one you click goes to its own menu
with selections. back or home button quit all those things with the same look
and feel for the ui throught"*.

Every sub-page footer MUST expose three navigation keys with these exact
semantics — page-specific keys (R refresh / N next / etc.) MAY follow:

| Key | Aliases | Action |
|---|---|---|
| `B` | `back`, `""` (Enter) | return to PARENT menu (previous screen) |
| `H` | `home` | return to MAIN MENU (`main_menu.show_main_menu()`) |
| `X` | `exit`, `q`, `quit` | `sys.exit(0)` — hard exit the EVE process |

Implementations live in `automations/eve-launcher/eve.py` as
`_print_sub_page_header(title)` + `_print_sub_page_footer(extra_keys)` +
`_sub_page_handle_nav(resp)` helpers; sibling modules (`quantum_tools.py`,
`health_tools.py`, `account_manager.py`) each define a local `_route_home()`
that does `from main_menu import show_main_menu; show_main_menu()` inside a
try/except so circular-import never crashes a sub-page.

## Canonical color tokens (existing in eve.py — DO NOT add new ones)

| Token | Use |
|---|---|
| `PURPLE` (#A06EFF-ish) | shortcut keys, accent |
| `BRIGHTP` (bright purple) | active/default/highlighted item |
| `WHITE` | primary content + titles |
| `SOFT` (medium grey) | labels |
| `DIM` (dark grey) | metadata, less-important |
| `DARKP` (dark purple) | divider rules |
| `OK` (green) | success / ON / healthy |
| `WARN` (yellow) | mid-range / 25-60% |
| `FAIL` (red) | error / rate-limited / <25% |

## Per-sub-page audit (find + convert ALL)

Glob `tools/eve-picker/*.py` + grep `eve.py` for sub-page render functions. The known list:

| Page | Current file:func | Status |
|---|---|---|
| Main picker | `eve.py` `render_picker_*` | OK (sanctum lane updated 2026-05-24T21:33Z menu cleanup) |
| Accounts panel | `eve.py` `_render_accounts_panel` | needs canonical-footer "press B to return" wiring (currently in-line in picker) |
| Onboarding | `eve.py` onboarding flow | NEEDS REWRITE — currently has Multi-account rotation status block with non-themed `[ON ]`/`[OFF]` brackets + non-themed sess=/spawns_today=/label= format |
| Health | `tools/eve-picker/health_tools.py` `health_menu()` | needs header/footer wrap + back-button |
| Quantum tools | `tools/eve-picker/quantum_tools.py` (if exists) | needs same wrap |
| Mesh status | `eve.py` mesh function | needs same wrap |
| Queue (top 3) | `eve.py` queue peek | needs same wrap |
| Utterances (5) | `eve.py` utterances list | needs same wrap |
| Rename+Color | `eve.py` rename flow | needs same wrap |
| Auto-Resume | `eve.py` auto-resume flow | needs same wrap |
| New Project | `eve.py` new project flow | needs same wrap |

## Reference handler skeleton (Python)

```python
def render_sub_page() -> None:
    """Header/body/footer canonical layout per eve-ui-uniformity-doctrine."""
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}<Title>{RESET} {DARKP}---{RESET}")
    print()
    # body (3-15 lines)
    print(f"  {SOFT}key{RESET}  {WHITE}value{RESET}")
    ...
    print()
    print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   {PURPLE}X){RESET} Exit   {DIM}(<page-keys>){RESET}")

    while True:
        resp = input("  > ").strip().lower()
        if resp in ("b", "back", ""):
            return
        if resp in ("x", "exit"):
            import sys; sys.exit(0)
        # page-specific keys
        if resp == "r":
            render_sub_page(); return
```

## Infinite accounts contract

`claude-accounts.ps1` already supports unlimited accounts via `-Action Add -Name <any> -Label <...> -ApiKey sk-ant-...` (line 856). The constraints below MUST hold for all UI surfaces:

1. **Accounts panel `_render_accounts_panel`** iterates the full `accts` array — already does this, just verify when N>4 it doesn't break alignment.
2. **Round-robin iterator** (PS1 `Get-NextAvailableAccount`) — already loops `for i in range(n)` — verified scales.
3. **Onboarding sub-page** must let operator type any name (not just `leo`/`slot3`/`slot4`). Replace hardcoded names with a free-text prompt.
4. **Health view** must show N rows.
5. **No code path may assume `len(accounts) == 4`.**

## "No half-ass" contract

If a feature touches multiple surfaces, ALL surfaces ship together. Examples:
- "Infinite accounts" requires: Add CLI (✓ already) + Onboarding UI rewrite + accounts panel verify + round-robin verify + Health view verify. Shipping just one of these = half-ass.
- "Uniform UI" requires: ALL sub-pages converted to header/body/footer + ALL with back button + ALL using canonical tokens. Converting 3 of 10 pages = half-ass.

Composes with no-bullshit doctrine rule 1 (precise verbs: `scaffolded` vs `shipped`). A page is `shipped` only when header + footer + back-button + body all match the canonical layout AND smoke-tested by launching EVE.exe and tabbing into it.

## Measurable pass criterion

- 100% of sub-pages reachable from main picker conform (audit script: `automations/eve-ui-audit.ps1` — needs to be written) returns PASS.
- `claude-accounts.ps1 -Action Add -Name testN -Label "test"` works for arbitrary N; Onboarding can add it via UI.
- A screenshot of every sub-page shows the 3-block layout.

Updated: 2026-05-24
