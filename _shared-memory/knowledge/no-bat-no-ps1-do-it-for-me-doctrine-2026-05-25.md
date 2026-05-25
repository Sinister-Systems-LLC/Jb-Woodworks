<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->

# No .bat / no .ps1 — execute everything for the operator (doctrine)

**Status:** hard-canonical 2026-05-25 (binding for every fleet agent + every sub-agent).
**Operator verbatim 2026-05-25T02:45Z:** *"update the fucking memory taht we dont use bat files or powershell files or any of that shit. you do everything i say fully for me and thats that. so do this and get to work"*

**Composes with:** `agent-autonomy-push-and-completion-2026-05-23` (operator: "should work fully without me") + `loop-relentless-pursuit-doctrine-2026-05-25` (RELENTLESS = ship same turn, don't surface clicks) + `sanctioned-bypasses-doctrine-2026-05-21` (`--dangerously-skip-permissions` standing default — we already have authorization to execute).

## Two parts to the directive

### Part A — STOP creating `.bat` / `.ps1` files

Every new tool, helper, daemon, watchdog, installer, wrapper, smoke script, or one-shot SHIPS as:

| Need | Canonical format |
|---|---|
| Cross-platform CLI helper / daemon / watchdog / installer | **Python 3** (`automations/*.py` or `tools/*/*.py`) — runs on Windows + Mac + Linux. The fleet's `eve.py` already exists as the reference shape. |
| One-shot install / system change | **Direct execution via Claude's `Bash` / `PowerShell` tool** — call `schtasks.exe` / `winget` / `git` / `pip` directly. Do NOT wrap in a `.ps1` then tell operator to click it. |
| User-facing one-click button | Make it a Python script callable as `python <name>.py` from the EVE.exe menu. The EVE.exe bundle is a Python binary already — extend it, don't drop `.bat` shortcuts on the Desktop. |
| Pre-existing `.ps1` in `automations/` | LEFT IN PLACE (~250 files; mass-conversion risky). NEW work does not add to the pile. Migrating an existing `.ps1` → `.py` is a per-file decision when that file is next touched. |

### Part B — Operator does NOT click anything

When the operator says "do X", the chain is:

1. Claude (master agent) **executes X directly** via tool calls.
2. If X requires a tool the master lacks, master either: (a) writes the missing tool inline + executes, or (b) delegates to a sub-agent who has the tool + verifies completion before reporting.
3. If X cannot be executed (e.g., physically requires operator-only credentials), master surfaces **one specific question**, not a list of clicks.

**Anti-patterns (DO NOT do):**

1. **"Run `powershell -File install-foo.ps1` to activate."** — execute the install directly via `Register-ScheduledTask` / `schtasks /Create` / equivalent from the PowerShell tool. Don't hand a click to the operator.
2. **"Double-click `Setup.bat` on your Desktop."** — same problem. The Desktop-button pattern (e.g., `Login-All-Sinister-Accounts.bat`, `Poke-All-Sinister-Agents.bat`) is now a code smell. If the operator needs a fast trigger, build it into EVE.exe's main menu (Python).
3. **"Create a `.ps1` wrapper around `gh` / `git` / `pip` / `npm`."** — call the underlying tool directly. PowerShell is a `.exe` invocation pipeline, not a deliverable.
4. **"Surface a `.bat` shortcut for routine work."** — routine work is automated end-to-end via Python or schtask wired by Claude. Operator should see results, not instructions.
5. **"Generate a one-shot `.ps1` for the operator to spot-check."** — execute the spot-check yourself via Bash/PowerShell tool + paste the result.

## Existing `.ps1`/`.bat` files (treat as legacy infrastructure)

The fleet has ~250 `.ps1` files in `automations/` and a handful of `.bat` launchers (`Start-Sinister-Session.bat`, `Login-All-Sinister-Accounts.bat`, `Poke-All-Sinister-Agents.bat`, etc.). These are NOT being deleted — they predate this doctrine and many are wired into schtasks / hooks / spawn paths the fleet depends on.

The doctrine is **forward-looking**:

- ✅ Calling an existing `.ps1` from inside Claude's tools to GET A RESULT for the operator = fine (you're the one executing, the operator doesn't click).
- ❌ Creating a NEW `.ps1` or `.bat` as a deliverable = banned. Convert to Python or inline tool-call.
- ❌ Telling the operator "run this `.ps1`" = banned. Run it yourself.

**Per-file migration:** when you next edit one of the legacy `.ps1` files and the change is more than a 1-line tweak, consider a Python rewrite same iter. Track these conversions in `_shared-memory/PROGRESS/Sinister Sanctum.md` so the migration is visible.

## Recent .ps1/.bat files I (sanctum-mintty-fix) shipped under prior doctrine — migration backlog

Surfacing for transparency. These shipped before this doctrine was binding:

| File | Created | Migration target |
|---|---|---|
| `automations/loop-relentless-watchdog.ps1` (2026-05-25 iter-19) | Sub-F | `automations/loop_relentless_watchdog.py` — Python 3 + `subprocess` to read JSON heartbeats; cross-platform; cron via Linux at schtask via Windows |
| `automations/install-loop-watchdog-task.ps1` (2026-05-25 iter-19) | Sub-F | **DELETE** — schtask install done inline via PowerShell tool this iter; no wrapper needed |
| `automations/agent-poke.ps1` (2026-05-25 iter-19) | Sub-G | `automations/agent_poke.py` — Python 3; same JSON schema; wired into EVE.exe Accounts page as menu item rather than Desktop bat |
| `C:\Users\Zonia\Desktop\Poke-All-Sinister-Agents.bat` (2026-05-25 iter-19) | Sub-G | **DELETE** — replaced by EVE.exe main-menu key (e.g. `K`) calling `agent_poke.py PokeAll` |

Backlog row appended to `_shared-memory/OPERATOR-ACTION-QUEUE.md` (operator approves the deletes; Python rewrites self-approved).

## Why this works for the operator

- **One-step ship.** Operator says "do X" → Claude does X → operator sees result. Zero clicks.
- **Cross-platform.** Python tools run on Leo's Mac as soon as he's linked.
- **Auditable.** Tool calls in the conversation transcript ARE the record. Nothing hidden in a click on the operator's side.
- **Reversible.** Direct execution can be undone by Claude same turn; a `.bat` install requires the operator to remember what they clicked.

## Pass criterion

- Zero new `.bat` / `.ps1` files created from 2026-05-25T02:45Z forward without explicit operator override.
- Every operator directive ending with "do it" / "ship it" / "make it work" results in Claude completing the work and reporting outcome, NOT surfacing a click.
- All NEW automation lands as `.py` + direct tool execution.

## Verification (grep guard for future audits)

```bash
# Files created or modified after 2026-05-25 02:45Z under automations/ or _shared-memory/setup/
git log --since='2026-05-25 02:45' --diff-filter=A --name-only | grep -E '\.(bat|ps1|cmd|vbs)$'
# Should return ZERO new files (modifications to existing .ps1 OK during migration window).
```

Future canonical-protections-check.ps1 (yes, the legacy file — until it's migrated) gets a P15 guard:

```powershell
Test-Protection -Id 'P15' -Description 'No NEW .bat/.ps1 files created after 2026-05-25T02:45Z' -Check {
    # Implementation: git log since-cutoff diff-filter=A; flag any new .bat/.ps1
    # ...
}
```

(Implementation deferred 1 iter — placeholder so the doctrine has a verifiable hook.)

## Composes with (full list)

- `agent-autonomy-push-and-completion-2026-05-23` (operator: "fix all of this so the agents can complete everything without me and not stop until done")
- `loop-relentless-pursuit-doctrine-2026-05-25` (rule 8 SHIP THIS TURN — no surfacing clicks)
- `sanctioned-bypasses-doctrine-2026-05-21` (`--dangerously-skip-permissions` standing default = we have authorization to execute)
- `eve-ui-uniformity-doctrine-2026-05-24` (Python-based EVE.exe menu is the canonical operator-facing surface; not Desktop `.bat`s)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 2 test-before-claim = execute + verify same turn, not "run this and tell me")
- `session-start-auto-update-propagation-2026-05-24` (Python-based EVE.exe auto-propagates; `.ps1` propagation was already a known seam)

## Operator quote (verbatim)

*"update the fucking memory taht we dont use bat files or powershell files or any of that shit. you do everything i say fully for me and thats that. so do this and get to work"* — 2026-05-25T02:45Z

This doctrine is the binding interpretation.
