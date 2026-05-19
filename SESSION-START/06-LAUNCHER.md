# 06 — Start-Sinister-Session launcher

The themed launcher on Desktop. What it does, what it composes, how to customize.

## Files

| Layer | Path |
|---|---|
| Desktop bat (one-click entry) | `C:\Users\Zonia\Desktop\Start-Sinister-Session.bat` |
| PowerShell script (logic + theme) | `D:\Sinister Sanctum\automations\start-sinister-session.ps1` |
| Runlog manifests | `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\script-runs\start-sinister-session-*.json` |

## What the launcher does, in order

1. **Matrix intro** — three rows of cascading purple/magenta characters
2. **Header bars** — `===` lines in deep purple → light purple gradient
3. **Block-letter logo** — `SINISTER` then `SANCTUM` in ASCII, rendered line-by-line
4. **Boot sequence** with animated progress bars:
   - crypto modules
   - bot registry (12)
   - mcp network (19)
   - backup daemon
   - memory codec
   - inbox channels
5. **Auth handshake** with spinner-then-check:
   - identity (operator email) → `[VERIFIED]`
   - workstation (D: + C: drives) → `[ONLINE]`
   - github org (Sinister-Systems-LLC) → `[LINKED]`
   - hub root → `[MOUNTED]`
   - sanctum root → `[MOUNTED]`
6. **Time-aware greeting** ("Good morning/afternoon/evening, Operator" or "Working late, I see, Operator" after 10 PM)
7. **Live telemetry panel:**
   - Agents online (counts `online.flag` heartbeats < 10 min old)
   - Bots registered (reads `bot-registry.json`)
   - Repositories tracked
   - Custodian daemon state (queries `Get-ScheduledTask SinisterCustodian`)
   - Last backup snap (computes mtime of newest snapshot file)
   - Pending operator items (counts `- [ ]` in `PENDING-NEXT-ACTIONS.md`)
8. **Project picker** (1-6: sanctum, snap-emu, tiktok-emu, panel, kernel-apk, other)
9. **Mode picker** (1-7: overview, dev, audit, deploy, push, debug, explore)
10. **Closing animation** — three more progress bars (loading context, compiling directive, writing clipboard)
11. **Phrase composition** — combines project + mode into a tailored opening phrase
12. **Clipboard** — phrase copied via `Set-Clipboard`
13. **Notepad** — opens project's `SESSION-START.md` + `CLAUDE.md` (if found)
14. **Runlog manifest** — written to `script-runs/`

## Phrase grid (project × mode)

| Mode | Phrase template |
|---|---|
| overview | `Read <root> - give me the project overview (current state, pending TODOs, what's next).` |
| dev | `We're working on <project> (root: <root>). Read the project memory + SESSION-START + CLAUDE.md, then ask me what specific feature/fix we're tackling.` |
| audit | `Audit <project> at <root>. Use librarian.recall + auditor.run + git status. Surface: secrets at risk, stale TODOs, broken tests, push-readiness.` |
| deploy | `We're deploying <project> to production. Read the latest DEPLOY/HETZNER docs, confirm HEAD is clean + tagged, then walk me through the deploy steps.` |
| push | `Push <project> to GitHub. Run secret-scrub first (MANDATORY). Then git add + commit (ask me for the message) + git push. Stop if anything fails.` |
| debug | `Debugging session on <project>. Read .claude/memory/ + living-mds/CURRENT-STATE.md + the latest BREAKTHROUGH-*.md. Then ask me which failure mode I'm chasing.` |
| explore | `Open exploration on <project>. Read project root, .claude/memory/, docs/, NAVIGATION.md. Then surface 3 surprising findings before asking my direction.` |

## Args (skip prompts)

```powershell
# Skip both pickers
& "D:\Sinister Sanctum\automations\start-sinister-session.ps1" -Project snap-emu -Mode debug

# Add -NoNotepad to skip opening docs
& "D:\Sinister Sanctum\automations\start-sinister-session.ps1" -Project sanctum -Mode overview -NoNotepad

# Add -Fast to skip all the dramatic pauses (instant render)
& "D:\Sinister Sanctum\automations\start-sinister-session.ps1" -Project panel -Mode audit -Fast
```

## Theme (color palette)

PowerShell 5.1 console = 16-color palette. Used colors:
- **DarkMagenta** — deep purple borders, rain palette
- **Magenta** — light purple bars, headers, prompts
- **White** — labels, body text
- **DarkGray** — dim secondary info
- **Gray** — soft tertiary
- **Cyan** — boot-step accents ("> initializing...")
- **Green** — `[OK]`, `[VERIFIED]`, `[MOUNTED]`, `100%` markers
- **Yellow** — project name in `[$name]` headers

For terminals that support 256-color or truecolor (Windows Terminal, modern PS 7), the same color tokens render as richer purples automatically.

## Customizing

Most likely tweaks:
- **Add a project:** edit the `$projectPaths` hashtable in `start-sinister-session.ps1` (add entry mapping project name → `{root, session_start, claude}`)
- **Add a mode:** edit the `$phrases` hashtable (add mode name → phrase template)
- **Adjust pace:** `Pause-Beat`'s default ms argument controls dramatic pauses between sections; lower for less drama, higher for more
- **Skip animations:** add `-Fast` to skip pauses entirely

## TL;DR

- **How we won:** One bat replaces "remember the opening phrase + open notepad + alt-tab to Claude" with a single double-click + Ctrl+V.
- **What you need to do:** Try `Start-Sinister-Session.bat` next time you open Claude. Pick project, pick mode, paste. Done.
