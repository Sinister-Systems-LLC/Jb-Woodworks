<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 2
  half_life_days: 365
-->
# No-visible-PowerShell-windows doctrine

**Status:** HARD-CANONICAL 2026-05-25T02:25Z (operator verbatim, fleet-wide binding). REINFORCED 2026-05-25T03:29Z.

**Operator verbatim 2026-05-25T02:25Z:** *"this fucking powershell winddow keeps poping up stop all shit like this from happening. if you need things like this make a fucking tool or system to use our sinister term in a headless way"*.

**Operator REINFORCEMENT 2026-05-25T03:29Z (fleet-binding strengthened):** *"another thing is this fucking power shell that randomly opens. like stop random shit like that that happen and make everything headless and real smooth and efficent and all agents adhear to these same terms that they not have complete control and we can really begin to become so powerful"*.

Reinforcement binds: (a) every spawned agent MUST adhere — no per-lane opt-out, (b) agents have COMPLETE CONTROL to fix violations (no operator-permission prompt for headless-conversion edits), (c) zero tolerance for "random PowerShell windows" — operator perceives them as power-drain on the fleet. The 5 host-crash scheduled tasks listed in `fleet-freeze-and-zombie-windows-diagnosis-2026-05-25` are the active violation surface — fix order F1-F2 in that doc is now operator-mandated, not just suggested.

Screenshot evidence: a fresh `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` window overlaying the LetsText apply page mid-scroll. Almost certainly fired by `SinisterBrainBroadcast` or `SinisterSanctumDailyBackup` scheduled tasks (audited 2026-05-25T02:25Z — both were missing `-WindowStyle Hidden`).

## The rule

**No EVE-fleet automation may produce a visible PowerShell / cmd / console window unless the operator EXPLICITLY launches it (Sinister Start.bat, EVE.exe spawn, mintty sessions).**

If a background task / cron / post-spawn hook needs to run powershell code, route it through `automations/sinister-headless.ps1` OR use `Start-Process -WindowStyle Hidden -NoNewWindow:$false` + `-RedirectStandardOutput` to a log.

## Audit findings 2026-05-25T02:25Z

19 Sinister scheduled tasks inspected; 17 already used `-WindowStyle Hidden`; **2 violations PATCHED same turn**:

| Task | Old args | New args | Status |
|---|---|---|---|
| SinisterBrainBroadcast | `-NoProfile -ExecutionPolicy Bypass -File ...brain-broadcast.ps1 -Action Broadcast -WindowHours 24` | `-WindowStyle Hidden ` + old | PATCHED |
| SinisterSanctumDailyBackup | `-NoProfile -ExecutionPolicy Bypass -File ...sanctum-daily-backup.ps1` | `-WindowStyle Hidden ` + old | PATCHED |

Verified clean (already had `-WindowStyle Hidden`): SinisterAPKAutoPush, SinisterAPKWatchdog, SinisterCustodian, SinisterCustodian-DailyRestart, SinisterMeshCoordSweep, SinisterOverseer, SinisterOverseerDistribute, SinisterSanctumAutoPush, SinisterToolAutotrigger, SinisterWindowPosMonitor.

Non-PowerShell tasks (out of scope for this doctrine but documented): SinisterScrcpyP1/P2 (scrcpy.exe — visible window is the POINT, mirrors phone screen); SinisterVault (cmd.exe → vault-daemon.bat — should also go headless; queued); Sinister-daily-digest / fleet-monitor / sheets-sync (jupyter-workstation pythonw.exe → already windowless via pythonw).

## sinister-headless.ps1 :: canonical wrapper

Shipped same turn: `automations/sinister-headless.ps1` (180 LOC).

Two modes:
1. **Synchronous** — `sinister-headless.ps1 -Script X.ps1 -ScriptArgs @(...)` → spawns hidden, captures stdout/stderr to per-invocation log, blocks until exit, returns rc. Supports `-TimeoutSec N` for hard wall-clock cap (kill on overshoot, rc=124).
2. **Detach** — `sinister-headless.ps1 -Script X.ps1 -ScriptArgs @(...) -Detach` → fire-and-forget hidden spawn, returns immediately, pid + log path echoed to caller.

Every invocation appends one JSON row to `_shared-memory/sinister-term-history/headless-invocations.jsonl` so the operator can grep / audit what ran silently and what produced what output.

Why this is needed (vs just `-WindowStyle Hidden`):
- Some scheduled-task hosts still flicker a window briefly on cold-start while .NET loads
- Direct `powershell.exe -File X.ps1` from .lnk / .bat / explorer keeps console alive if parent is itself a console host
- Proper fix: `Start-Process -WindowStyle Hidden` with redirected stdio (which IS what the wrapper does)

## When NOT to use the headless wrapper

- **Operator-initiated interactive flows** — Sinister Start.bat, EVE.exe spawn, mintty sessions, the operator clicking a .bat. These SHOULD show terminals because the operator wants to see them.
- **Setup wizards** — when leo-auto-setup-doctrine spawns the Setup Wizard claude session, it intentionally shows a window so Leo can interact.
- **Debug runs** — when the operator says "show me what this script does", run it visibly so the operator can watch.

Rule of thumb: **scheduled-task / cron / post-spawn-hook / background-poll = hidden.** Operator-clicked = visible.

## Anti-patterns (NEVER)

1. Register a scheduled task action of `powershell.exe -File X.ps1` without `-WindowStyle Hidden` (the 2 patched tasks above)
2. Use `Start-Process powershell.exe ...` without `-WindowStyle Hidden` (visible window flicker on cold-start)
3. Use `cmd.exe /c X.bat` for background work without redirected stdio (cmd window flashes briefly)
4. Suppress the window but also suppress the LOG — operator must be able to audit what ran silently
5. Detach (fire-and-forget) without writing the pid + start-ts to the invocation log — orphan processes are unfindable

## Composes with

- `sanctioned-bypasses-doctrine-2026-05-21` (we may still run `--dangerously-skip-permissions`, but never with a popup)
- `jcode-condensed-log-discipline-2026-05-25` (1-line condensed logs are the visible counterpart; this doctrine is the invisible counterpart — every background task hides AND logs)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (scheduled tasks register/release locks; lock writes go through headless path now)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 2 test-before-claim — both patched tasks verified via `Get-ScheduledTask | %{$_.Actions[0].Arguments}` post-patch)
- `do-not-revert-operator-canonical-protections-2026-05-23` (future EVE sessions MUST NOT unpatch the 2 fixed tasks; add this doctrine to the protected list)

## Measurable pass criterion

- `Get-ScheduledTask | Where-Object { $_.TaskName -match 'Sinister|Sanctum' } | %{$_.Actions[0].Arguments}` → zero rows lacking `-WindowStyle Hidden` (for powershell.exe actions)
- `_shared-memory/sinister-term-history/headless-invocations.jsonl` is being written by every script that uses the wrapper (audit by `wc -l`)
- No new visible PowerShell windows pop up during a normal 1-hour idle session (operator can verify by leaving the desktop alone for an hour)

Updated: 2026-05-25
