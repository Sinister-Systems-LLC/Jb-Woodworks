# RKOJ.exe v1.5.1 — Milestone Test Plan

> **Author:** RKOJ-ELENO :: 2026-05-21
> **EXE under test:** `C:\Users\Zonia\Desktop\RKOJ\RKOJ.exe`
> **Source lane:** `tools/sinister-rkoj-qt/` (DO NOT TOUCH — owned by sibling agent)
> **Cadence:** test in milestones. Each milestone must PASS before the next begins.

## Milestone 1 — Chrome boots cleanly (PowerShell-automatable)

Smoke: `automations/smoke-rkoj-milestone-1.ps1`.

| # | Test | Expected |
|---|---|---|
| 1.1 | EXE exists at canonical path | `Test-Path` returns `$true` |
| 1.2 | Launch via `Start-Process -PassThru` | Returns a `Process` object with non-null `Id` |
| 1.3 | Wait 6s after launch | Process still alive (`HasExited` = `$false`) |
| 1.4 | MainWindowTitle populated | Matches regex `Sanctum|Sinister|RKOJ|EVE` |
| 1.5 | No crash log written | `RKOJ.crash.log` absent in EXE dir |
| 1.6 | Process is GUI (has window handle) | `MainWindowHandle` non-zero |
| 1.7 | Working set sane | RSS between 30 MB and 800 MB |
| 1.8 | Clean shutdown via `Stop-Process` | Process exits within 3s |
| 1.9 | No zombie child procs | No orphan `RKOJ.exe` after kill |
| 1.10 | Re-launch after kill | Steps 1.2-1.6 pass a second time |

## Milestone 2 — Layout sanity (operator-driven UI clicks)

Smoke: `automations/smoke-rkoj-milestone-2.ps1` (asserts process state only — visual verification is operator-driven).

| # | Test | Expected |
|---|---|---|
| 2.1 | Sidebar renders | Operator sees nav rail on left edge |
| 2.2 | Click `Agents` chip | Page title swaps to "Agents", niri scroll empty state visible |
| 2.3 | Click `Devices` chip | Page title swaps to "Devices", "coming soon" placeholder shown |
| 2.4 | Sidebar highlight follows selection | Active chip has accent color |
| 2.5 | `File` menu opens | Popup with 3-5 placeholder items |
| 2.6 | `+ Create Agent` button visible on Agents page | Button is clickable, not greyed |
| 2.7 | Click `+ Create Agent` | New AgentCard mounts in niri grid |
| 2.8 | Process still alive after all clicks | `HasExited` = `$false` (smoke script asserts) |
| 2.9 | Window title unchanged | Still matches `Sanctum|Sinister|RKOJ|EVE` |
| 2.10 | No crash log after 30s of clicks | `RKOJ.crash.log` still absent |

## Milestone 3 — Agent flow (mostly operator-driven, smoke asserts no-crash)

Smoke: `automations/smoke-rkoj-milestone-3.ps1`.

| # | Test | Expected |
|---|---|---|
| 3.1 | Spawn agent via `+ Create Agent` | AgentCard mounts with terminal pane |
| 3.2 | Type turn in input row + click Send | Routes to `claude --dangerously-skip-permissions -p <text>` subprocess |
| 3.3 | EVE persona enforced | Opening stdout mentions "EVE" not "Claude" |
| 3.4 | At least 1 stdout line streams to card | Terminal pane shows visible output within 30s |
| 3.5 | Subprocess visible in `Get-Process claude` | Child `claude.exe` (or `node.exe` hosting cli) alive |
| 3.6 | Click close (X) on card | Subprocess terminates within 3s |
| 3.7 | Card removed from niri grid | DOM no longer shows card |
| 3.8 | Spawn 2 more agents, then window X | All 3 subprocesses die with parent |
| 3.9 | After window X, RKOJ.exe gone | `Get-Process RKOJ` returns nothing |
| 3.10 | No orphan claude/node procs | `Get-Process claude` returns nothing (smoke asserts) |

## Milestone 4 — Polish (documented; no smoke script this cycle)

| # | Test | Expected |
|---|---|---|
| 4.1 | Folder-tab project chip auto-add | New agent spawn -> project chip appears in folder-tabs row |
| 4.2 | Same-project agents grouped adjacent | Two agents on `sanctum` sit side-by-side in niri grid |
| 4.3 | Glow overlay on `awaiting-input` state | Card pulses accent glow when state flag set |
| 4.4 | `File` menu — at least 1 functional entry | E.g. `New Agent` triggers the same flow as the button |
| 4.5 | `Edit` menu — at least 1 functional entry | E.g. `Copy` copies selected terminal text |
| 4.6 | `View` menu — at least 1 functional entry | E.g. `Toggle Sidebar` collapses/expands rail |
| 4.7 | `Agent` menu — at least 1 functional entry | E.g. `Restart Active Card` |
| 4.8 | `Tools` menu — at least 1 functional entry | E.g. `Open Forge` launches sinister-forge |
| 4.9 | `Help` menu — at least 1 functional entry | E.g. `About RKOJ` shows version dialog |
| 4.10 | Version dialog reads "v1.5.1" | Matches build number |

## Pass/Fail matrix

| Milestone | Automatable | Operator UI required |
|---|---|---|
| 1 | 10/10 PowerShell | 0 |
| 2 | 2/10 (process-state only) | 8/10 |
| 3 | 4/10 (process-state + subprocess assertions) | 6/10 |
| 4 | 0/10 | 10/10 |

## Exit criteria

- Milestone 1 smoke: exit 0 = green-light Milestone 2.
- Milestone 2 + 3 smokes: exit 0 = process-state OK; operator confirms UI assertions verbally.
- Milestone 4: operator walkthrough w/ video capture; no smoke this cycle.
