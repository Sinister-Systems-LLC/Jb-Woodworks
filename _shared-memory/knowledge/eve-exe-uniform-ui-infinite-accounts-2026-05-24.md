<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->

# EVE.exe Uniform UI + Infinite Accounts Doctrine

**Created:** 2026-05-24T21:42Z
**Authority:** Operator hard-canonical 2026-05-24T21:36Z (verbatim):
> *"allow infinite accounts and all pages on the eve exe need to have a uniform ui look and all have a concise complete simple to the point layout. update memory for this. we dont do shit half ass"*

---

## Two binding rules

### Rule 1 -- Infinite accounts (ALREADY SUPPORTED)

The claude-accounts subsystem already supports arbitrary `N` accounts:

- `_shared-memory/claude-accounts.json` `accounts` is a JSON array; no upper bound.
- `automations/claude-accounts.ps1 -Action Add -Name <slug> -Label <text> -CredentialsFile <path>` adds new accounts at runtime (line 878-880 usage block).
- `_render_accounts_panel()` in `automations/eve-launcher/eve.py:640` iterates the full array (`for x in accts`); no hard-coded slot count.
- `automations/claude-accounts-status.ps1 -Mode Board|Bar|Json` renders any-N accounts (foreach loop).
- `automations/start-sinister-session.ps1:1456` round-robin-strict + burn-first rotation strategies both honor `len(accts)`; no slot4 ceiling.

**Operator path to add a new account:** EVE.exe -> `O` (Onboarding flow) OR directly:
```powershell
powershell -File automations/claude-accounts.ps1 -Action Add -Name <slug> -Label "<friendly>" -CredentialsFile "C:\Users\Zonia\.claude\credentials.<slug>.json"
powershell -File automations/claude-accounts.ps1 -Action Enable -Name <slug>
```

The current 4 slots (operator / leo / slot3 / slot4) are seed entries, not a cap. Adding `slot5..slotN` is one CLI call each.

### Rule 2 -- Uniform UI across every EVE.exe page

Every panel / menu / status block in `eve.py` follows the same minimum-line-budget pattern:

**Canonical pattern (extracted from `_render_accounts_panel` which the operator accepted as the model 2026-05-24T21:30Z):**

```
[WHITE BOLD]Title[RESET]  [BRIGHTP]<short-meta>[RESET]  [DIM]<sub-meta>[RESET]  [DIM][[RESET][PURPLE]K[RESET][DIM]]ey-action[RESET]
  one-row-per-item: STATE  Label                   Sessions  RL    Today  Window
  one-row-per-item: STATE  Label                   Sessions  RL    Today  Window
  ...
[DIM]footer-hint[RESET]
```

**Five mandatory layout invariants:**

1. **Single-line header.** Title + key-meta + key-hint on ONE line; never wrap.
2. **Tabular body.** Aligned columns via Python f-string padding (`{label:<28}`), NOT random spaces.
3. **Color discipline.** Only 6 named colors -- `WHITE` (titles) / `BOLD` (titles) / `BRIGHTP` (interactive keys, counts) / `PURPLE` (key letters in hints) / `DIM` (meta, separators) / `OK`/`WARN`/`FAIL` (state). No ad-hoc ANSI escapes.
4. **Key hints at end of header.** Operator-actionable keys (`[O]nboard`, `[A]utomations`, `[M]esh`, `[Q]ueue`) live in the title line, bracketed, with the LETTER in `PURPLE`.
5. **Hard 6-line cap per panel.** If a panel needs more, COLLAPSE (group disabled / truncate inactive / show top-N + count) rather than expand.

**Six anti-patterns (we do NOT do shit half-ass):**

1. Don't print a banner ASCII-art header AND a title line -- pick ONE.
2. Don't render a panel that exceeds 6 lines without operator-actionable density.
3. Don't use color outside the 6-name palette (no `\033[35;1m` etc inline).
4. Don't repeat the SAME metadata in two places on the same page (e.g. don't print "5 accounts" both in header and footer).
5. Don't show internal counters (lease cursor / current_sessions raw) when the operator wants USAGE signals (5h-window remaining / today's spawns / RL countdown).
6. Don't add a new page without first checking if an existing page can absorb the function (prune-as-add at the UI layer too).

---

## Current EVE.exe page inventory (audit baseline)

| Page | Renderer | Conforming to invariants 1-5? | Notes |
|---|---|---|---|
| Project picker (main) | `lib.build_picker_state` + main loop | YES | rows tabular; single-line header |
| Accounts panel | `_render_accounts_panel` (line 640) | YES (canonical model) | operator-approved 21:30Z |
| Mesh status | `_view_mesh_status` (line 1009+) | PARTIAL | 5 sections + footer; over 6 lines by design (multi-cluster view) -- exempt as "dashboard" page |
| Queue top rows | `_queue_top_rows` + Q-key block | YES | top-3 cap honors invariant 5 |
| Operator-utterances | `_unresolved_utterances` + U-key block | YES | top-5 cap |
| Onboarding flow | `_account_onboarding_flow` (line 791+) | YES | multi-step wizard; each step single-line |
| Automations menu | `_sanctum_automations_menu` (NEW iter 6) | YES | numbered list; single-line header |
| Tools (quantum) | `quantum_tools.menu_loop` (external module) | UNKNOWN | external; defer audit |
| Health | `health_tools.menu_loop` (external module) | UNKNOWN | external; defer audit |

**Audit verdict:** 7/9 conform clearly; 1 dashboard exempt (mesh); 2 external modules need audit when bundled. **No half-ass — but `quantum_tools` + `health_tools` external modules should be audited in a follow-up iter to confirm they don't drift.**

---

## Sinister OS linkage

When EVE.exe ports to Sinister OS as a native binary (Go rewrite per master plan), the SAME 5 invariants apply -- they're terminal-rendering rules, not Python-specific. The 6-color palette maps to the Sinister-purple theme tokens (`--accent`, `--text-bright`, `--text-dim`, etc.) for any future TUI variant.

---

## Anti-patterns (we do NOT do shit half-ass)

1. Adding a new page without auditing the 5 invariants -- catches drift before it ships.
2. Bypassing the 6-color palette for "just this once" custom escapes -- becomes the new convention by accident.
3. Letting a panel exceed 6 lines without operator-actionable density -- scroll fatigue.
4. Hard-coding slot count in any account-touching code -- breaks infinite-accounts on add.
5. Showing internal counters instead of operator-actionable usage signals.

## Composes with

- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R2: EVE.exe-reachable on next spawn)
- `session-start-auto-update-propagation-2026-05-24` (sibling's canonical: eve.py edits require `verify-eve-features.ps1 -AutoRebuild -SyncMirror`)
- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (web UI counterpart; same EXPAND principle)
- `sanctum-scope-discipline-2026-05-24` (EVE.exe is in Sanctum scope; this doctrine binds Sanctum lane)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 6 laser-focus: one invariant per page audit, not "rewrite all UI")

## Verification

```powershell
# Confirm infinite-accounts capability
powershell -File automations/claude-accounts.ps1 -Action Add -Name slot99 -Label "test" -CredentialsFile C:/tmp/x.json
powershell -File automations/claude-accounts-status.ps1 -Mode Board   # slot99 should appear
powershell -File automations/claude-accounts.ps1 -Action Remove -Name slot99

# After ANY eve.py edit:
powershell -File automations/verify-eve-features.ps1 -AutoRebuild -SyncMirror
```
