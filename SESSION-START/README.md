# SESSION-START — cold-resume anchor

You just opened a fresh Claude session. **This is the one folder you read first.**

## TL;DR — two ways to start

### Option A (recommended): the themed launcher

Double-click **`C:\Users\Zonia\Desktop\Start-Sinister-Session.bat`**. It:

1. Renders the Sinister Sanctum boot sequence (Matrix-style purple intro, auth checks, live telemetry — agents online, last backup, pending operator items, custodian state)
2. Asks which project you're working on (1-6)
3. Asks what kind of work (overview / dev / audit / deploy / push / debug / explore)
4. Composes a tailored opening phrase, copies it to clipboard
5. Opens the project's `SESSION-START.md` + `CLAUDE.md` in notepad

Then you open Claude Code and `Ctrl+V`.

### Option B: the manual opening phrase

> **`Read D:\Sinister Sanctum\SESSION-START\ and give me the project overview, then I'll pick which project we're working on.`**

That loads this folder's 7 files (rules, network, queue, gotchas, recovery, project-overview, this README).

## File read order

| # | File | What |
|---|---|---|
| 1 | `README.md` (this file) | The map; two ways to start |
| 2 | `00-RULES.md` | Hard rules: TL;DR mandatory, delegation table, agent-presence Rule 9 |
| 3 | `01-NETWORK.md` | 19+ MCP servers + bot-callable shortcuts |
| 4 | `02-OPERATOR-QUEUE.md` | What you're waiting on right now |
| 5 | `03-GOTCHAS.md` | Sandbox / classifier denies + green paths |
| 6 | `04-RECOVERY.md` | When things look wrong (drive-letter-changed, etc.) |
| 7 | `05-PROJECT-OVERVIEW.md` | All Sinister LLC projects with status (neutral language) |
| 8 | `06-LAUNCHER.md` | How the Start-Sinister-Session bat composes the phrase |

## 🟣 NEW 2026-05-24 :: Sinister OS master plan is READY for operator review

A super-detailed master plan for **Sinister OS** — the Linux-based, EVE-controlled, gaming-capable full-PC OS replacement — is now committed at:

- **`projects/sinister-os/plans/master-plan-2026-05-24.md`** (the plan — read this first)
- **`projects/sinister-os/README.md`** (project orientation)
- **`projects/sinister-os/CLAUDE.md`** (lane discipline)
- **`projects/sinister-os/docs/architecture.md`** (system-layer view)

**P0 (spec lock) is complete.** The plan covers: Arch + linux-cachyos base, Hyprland (Wayland) compositor, EVE-as-OS-shell via sudoers NOPASSWD allowlist, btrfs + snapper rollback, full gaming stack (Steam/Proton-GE/Lutris/Heroic/Bottles), Windows-app compat strategy, branded ISO build via archiso, 5-phase delivery path (P1 ISO → P2 dual-boot soak → P3 EVE shell daemon → P4 stack proof → P5 cutover from Windows).

**Operator action required to advance to P1:** Answer Q1-Q10 in master plan § 14 (10 short questions covering distro pick, compositor pick, browser default, voice provider, encryption, secure boot, dual-boot strategy, partition pick, anti-cheat titles, optional Windows VM via VFIO).

Once P0 is signed off, EVE opens `agent/sinister-os/p1-iso-build-<date>` and builds the bootable ISO in a VM.

## After the overview, you pick

```
"we're working on Sinister Snap EMU — what's blocked"
"we're working on Sinister Control Center — push the queued commits"
"we're working on Sinister TikTok EMU — task #26 next step"
"we're working on Sinister Sanctum — first git push"
"we're working on snap-signer — SS03 hypothesis #3"
```

Claude then loads ONLY that project's memory (`01_MEMORY/<project>/TODO.md` + relevant docs) and proceeds.

## Where the canonical state lives

- **Sanctum root (this repo):** `D:\Sinister Sanctum\` (with backwards-compat junction at `D:\Sinister LLC\`)
- **Parent hub (operator-private):** `D:\Sinister\Sinister Skills\`
- **Parent-down link:** `D:\Sinister\Sanctum\` → `D:\Sinister Sanctum\`
- **Project sources:** `D:\Sinister Sanctum\projects\<project>\source\` (junctions to `D:\Sinister\01_Projects\Sinister\<project>\source\`)
- **Operator-private (NOT in Sanctum):** LetsText, JOKR, Yurikey roster, secrets policy, Coding/Tools/Apps/Quality-of-Life

## What this hub IS NOT

- NOT an autonomous agent framework — operator drives every decision
- NOT a classifier-evasion system — codec is open, vault is at-rest only, audit log stays plain
- NOT a substitute for `.gitignore` — operator's secrets stay off the drive

## What every session ALWAYS does (per Rule 1 + Rule 9 from `00-RULES.md`)

1. **TL;DR mandatory** — end every long response with `## TL;DR` ("How we won" + "What you need to do")
2. **Per-turn messaging:** call `sinister-bus.heartbeat my_agent="<this-project>"` + `sinister-bus.inbox_poll my_agent="<this-project>"` each turn so other sessions can reach you

## Drive-letter-changed recovery

```powershell
Get-Volume | Where-Object { $_.FileSystemLabel -eq 'Sinister' }
# then cd <new-letter>:\Sinister Sanctum\SESSION-START\
```

Full procedure: `04-RECOVERY.md`.

## TL;DR

- **How we won:** One bat OR one phrase = full cold-resume.
- **What you need to do:** Double-click `Start-Sinister-Session.bat` (recommended) OR paste the opening phrase above into your fresh Claude session.
