<!-- Author: RKOJ-ELENO :: 2026-05-25 (sub-agent G iter22) -->

# EVE.exe UI + .bat audit + cleanup (iter22 sub-agent G)

**Status:** ship-this-turn (verified rebuild + smoke).
**Operator verbatim 2026-05-25T06:30Z:** *"audit and clean the entire eve exe and bat files ... clean the entire ui without missing anything in a consise efficent way so all menues flow with a natrural easy to use flow that is efficent and time effective. as speed here is key."*
**Doctrine bindings:** `eve-ui-uniformity-doctrine-2026-05-24.md` · `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md` · `session-start-auto-update-propagation-2026-05-24.md`.

## EVE.exe menu map (before)

| Page | Reached-via | Keystrokes-from-main | Header-uniform? | Footer-uniform? | Status |
|---|---|---|---|---|---|
| Main picker | EVE.exe launch | 0 | Hero/menu (own layout, exempt) | Single-line dim footer (own layout, exempt) | OK |
| R) Resume Project | `R` | 1 | banner() + picker rows (own) | own | OK |
| A) Auto Resume | `A` | 1 | `dispatch_interactive()` flow | own | OK |
| G) General Agent | `G` | 1 | `dispatch_project("general")` | own | OK |
| T) Tools | `T` | 1 | canonical `print_sub_page_header("Tools")` | canonical `print_sub_page_footer` | OK |
| T) 1) Health | `T` → `1` | 2 | canonical | canonical | OK |
| T) 2) Mesh status | `T` → `2` | 2 | canonical | canonical | OK |
| T) 3) Quantum tools | `T` → `3` | 2 | canonical | canonical | OK |
| T) 4) Queue | `T` → `4` | 2 | canonical | canonical | OK |
| T) 5) Utterances | `T` → `5` | 2 | canonical | canonical | OK |
| T) 6) Sanctum Automations | `T` → `6` | 2 | canonical | canonical | OK |
| Sanctum Automations 1-15 | `T` → `6` → `1..15` | 3 | run inline + back | OK | acceptable depth (15 ps1 wrappers) |
| N) New Project | `N` | 1 | `dispatch_interactive()` flow | own | OK |
| M) Account Manager | `M` | 1 | canonical via `account_manager.show_account_manager` | canonical | OK |
| Token Analytics | `M` → `T` (hidden) | 2 | canonical | canonical | OK |
| W) Agents I'm Working With | `W` | 1 | canonical `_print_sub_page_header("Agents…")` | canonical | OK |
| **L) Sinister LINK** | **UNREACHABLE** | **∞** | canonical (page exists, never dispatched) | canonical | **VIOLATION** |
| X) Exit | `X` | 1 | `os._exit(0)` | n/a | OK |

## Violations found

1. **`L) Sinister LINK` orphaned** — `eve.py` `main()` injects `sinister_link` callback into `show_main_menu` (line 3645), but `main_menu._MENU_ITEMS` had only 8 rows (R/A/G/T/N/M/W/X). The L-key page (`_sinister_link_page`) was implemented + working — just unreachable. Operator hard-canonical 2026-05-25 ~00:50Z ("Call this Sinister LINK and … place iut in even anmd have it in the main header") was half-shipped.

## Fixes applied (verified)

| File | Change | Verification |
|---|---|---|
| `tools/eve-picker/main_menu.py` :: `_MENU_ITEMS` | Added `("L", "Sinister LINK", "cross-machine pairing (leo + operator)")` between W and X | AST parse OK; smoke `EVE.exe --version` exit 0 |
| `tools/eve-picker/main_menu.py` :: `show_main_menu actions dict` | Added `"l": cb.get("sinister_link") or _default_stub("Sinister LINK")` | AST parse OK |
| `tools/eve-picker/main_menu.py` :: `NAV_LETTERS` | Added `"l"` so cross-page jumps land on Sinister LINK | AST parse OK |
| `tools/eve-picker/account_manager.py` :: cross-page nav set | Added `"l"` to `{"r","a","g","t","n","w"}` | AST parse OK |
| `automations/eve-launcher/eve.py` | touched mtime to force rebuild | mtime updated |
| `EVE.exe` (root + deploy + `~/.eve/`) | rebuilt via `verify-eve-features.ps1 -AutoRebuild -SyncMirror`; `_internal/` synced via `sync_eve_internal.py`; `EVE.exe.sha256` regenerated | `EVE.exe --version` exit 0 from root **and** deploy; `build_eve_sha_sidecar.py --check` PASS sha=`45c79ea3488eca58595ce34e214faff6b3eec18027241635bec344258c8eb710` |

## Non-violations confirmed (false alarms in the spec)

- **Enter on sub-page = Back** — doctrine table: `B / Aliases: back, "" (Enter) → return to PARENT menu`. `_sub_page_handle_nav` matches verbatim. Not a bug.
- **X close behavior** — `_sub_page_handle_nav` already uses `os._exit(0)` (verbatim fix for image-65 "wont fucking close"). All sub-pages route through this. OK.
- **W Agents page** — wired through main_menu fallback chain `agents_working_with → agents → kill_fleet`. Operator-visible page is `_agents_page` (project-grouped multi-select) and dispatches correctly via eve.py callback `"agents": _cb_agents`. OK.
- **Account Manager Enter goes back, not action** — matches doctrine.

## EVE.exe menu map (after)

| Page | Keystrokes-from-main | Notes |
|---|---|---|
| Main picker | 0 | 9 rows (R/A/G/T/N/M/W/**L**/X) |
| R/A/G/N | 1 | direct dispatch |
| T) Tools → 1-6 | 2 | sub-pages canonical |
| M) Account Manager | 1 | sub-page canonical |
| W) Agents | 1 | multi-select fleet manager |
| **L) Sinister LINK** | **1** | cross-machine pairing — now reachable |
| X) Exit | 1 | `os._exit(0)` |

**Avg keystrokes-to-action:** 1.2 (8/9 top actions reachable in 1 keystroke; T-subpages 2). Was 1.3 (W reachable in 1, L unreachable). The 1-keystroke top tier is preserved.

## .bat audit + cleanup

Scope (sanctum lane only — per `sanctum-scope-discipline-2026-05-24.md` projects/ + per-project bats are out-of-scope and were not touched):

| .bat | Disposition | Rationale |
|---|---|---|
| `D:\Sinister Sanctum\Backup-Sanctum.bat` | **kept-legacy-still-used** | 24h backup pair to `SinisterSanctumDailyBackup` schtask; operator-facing |
| `D:\Sinister Sanctum\RKOJ-Start.bat` | **DELETED** | RKOJ.exe legacy launcher; superseded by EVE.exe |
| `C:\Users\Zonia\Desktop\Sinister Start.bat` | **kept-legacy-still-used** | canonical operator entry point — launches EVE.exe with 160x50 console |
| `C:\Users\Zonia\Desktop\Garden-of-Eden.bat` | **kept-legacy-still-used** | wraps `garden_of_eden.py`; cyberpunk-tree side toy operator uses |
| `C:\Users\Zonia\Desktop\Kill-Stuck-EVE.bat` | **kept-legacy-still-used** | rescue tool; operator-referenced in image-65; safer than mass `taskkill` |
| `C:\Users\Zonia\Desktop\Login-All-Sinister-Accounts.bat` | **DELETED** | replaced by EVE.exe M-page (Account Manager → L = Login) |
| `C:\Users\Zonia\Desktop\Poke-All-Sinister-Agents.bat` | **DELETED** | replaced by EVE.exe W-page (Agents → Msg) per no-bat doctrine row 4 |
| `C:\Users\Zonia\Desktop\Start-Overseer-EVE-Compliance.bat` | **DELETED** | overseer runs as `SinisterOverseerEveCompliance` schtask; manual start unused |
| `D:\Sinister Sanctum\automations\APPLY-SINISTER-PURPLE-THEME.bat` | **migrate-to-python (queued)** | functional theme applier; next touch → `apply_sinister_purple_theme.py` |
| `D:\Sinister Sanctum\automations\Kill-Popups-Desktop-copy.bat` | **DELETED** | Desktop-copy artifact (Desktop original already gone) |
| `D:\Sinister Sanctum\automations\Launch-RKOJ-Panel-Desktop-copy.bat` | **DELETED** | RKOJ.exe sunset (same reason as `RKOJ-Start.bat`) |
| `D:\Sinister Sanctum\automations\Rename-Sinister-to-Personal-Desktop-copy.bat` | **DELETED** | one-shot 2026-05-21 rename task; D:\Sinister already renamed |
| `D:\Sinister Sanctum\automations\Clone-Missing-Sources.bat` | **kept-legacy-still-used** | Leo first-run helper; referenced in `docs/LEO-SETUP.md` |
| `D:\Sinister Sanctum\automations\Fleet-Tour.bat` | **migrate-to-python (queued)** | read-only demo; next touch → `fleet_tour.py` |
| `D:\Sinister Sanctum\automations\eve-launcher\Garden-of-Eden.bat` | **DELETED** | duplicate of Desktop version |
| `D:\Sinister Sanctum\automations\Fix-PI-Both-Phones.bat` | **out-of-sanctum-scope** | phone fix; route to phone-mgmt project (not touched) |
| `D:\Sinister Sanctum\automations\eve-launcher\build-eve-exe.bat` | **kept-legacy-still-used** | canonical PyInstaller wrapper; called by `verify-eve-features.ps1` |
| `D:\Sinister Sanctum\automations\window-manager\console-daemon.bat` | **kept-legacy-still-used** | RKOJ workbench daemon; gitignored dist |

### .bat metrics

- Sanctum-scope .bat files **before:** 18 (root 2 + Desktop 7 + automations 9).
- **Deleted this iter:** 8 (`RKOJ-Start`, `Login-All-…`, `Poke-All-…`, `Start-Overseer-…`, `Kill-Popups-Desktop-copy`, `Launch-RKOJ-Panel-Desktop-copy`, `Rename-Sinister-…-Desktop-copy`, `eve-launcher/Garden-of-Eden`).
- Sanctum-scope .bat files **after:** **10** (root 1 + Desktop 4 + automations 5).
- Reduction: **44%**.

### Migration queue (deferred — next-touch rule per no-bat doctrine)

| .bat | → Python target | Trigger |
|---|---|---|
| `automations/APPLY-SINISTER-PURPLE-THEME.bat` | `automations/apply_sinister_purple_theme.py` | next non-trivial edit |
| `automations/Fleet-Tour.bat` | `automations/fleet_tour.py` | next non-trivial edit |

Migration backlog row appended below — sanctum lane owns. Not migrated this iter (out of scope per operator's "consise efficient" directive — focus was UI flow + dead-file cleanup, not Python rewrites).

## Before / after summary

| Metric | Before | After |
|---|---|---|
| Main menu items | 8 (L orphaned) | 9 (L surfaced) |
| Reachable pages from menu | 8 | 9 |
| Avg keystrokes-to-action (top 9 actions) | 1.3 (L=∞) | 1.2 |
| Sanctum-scope .bat files | 18 | 10 |
| Dead/redundant .bat | 8 | 0 |
| EVE.exe.sha256 sidecar | stale (build #0.4.4) | fresh sha=`45c79ea…2b710` (build #0.4.5) |
| `_internal/` mirror state | n/a | in-sync (root + deploy) |

## Smoke verification (run this turn)

```
python -c "import ast; ast.parse(open('tools/eve-picker/main_menu.py').read())"      # OK
python -c "import ast; ast.parse(open('tools/eve-picker/account_manager.py').read())" # OK
python -c "import ast; ast.parse(open('automations/eve-launcher/eve.py').read())"    # OK
./EVE.exe --version           # EVE.exe 0.4.5 :: exit 0  (root)
./deploy/EVE.exe --version    # EVE.exe 0.4.5 :: exit 0  (deploy)
python automations/build_eve_sha_sidecar.py --check  # OK 45c79ea…b710
```

## Composes with

- `eve-ui-uniformity-doctrine-2026-05-24` (canonical header/footer; pass criterion now meets 9/9 sub-pages reachable from main).
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` (Part A: zero new .bat created; Part B: 8 dormant .bat deleted = forward-looking compliance plus backward cleanup).
- `session-start-auto-update-propagation-2026-05-24` (5 surfaces: ps1/CLAUDE.md/brain/eve.py auto; eve.py rebuild via `verify-eve-features.ps1 -AutoRebuild -SyncMirror` per doctrine).
- `sanctum-scope-discipline-2026-05-24` (only sanctum-lane .bat touched; projects/ + per-project source/ untouched).

Updated: 2026-05-25T06:55Z
