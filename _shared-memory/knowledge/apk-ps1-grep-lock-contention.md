<!-- decay:
  category: fact
  confidence: 0.9
  reinforcements: 0
  half_life_days: 90
-->
---
updated: 2026-05-19
audience: claude (all Sinister-APK + sister-project agents)
format: prose
purpose: workaround for "Device or resource busy" failures on D-drive ops when another Claude session holds a recursive grep lock on the same tree - read on cold-start when "busy", "lock", "device busy", "permission denied" surfaces on a mv/cp call into D:/Sinister/01_Projects/Sinister/Sinister-APK/
rotates-at: never (workaround doc; status block only)
---

> **Author:** tiktok-emu agent (Claude) :: 2026-05-19 (cross-zone, operator-authorized)

# APK PS1 grep-lock contention - multi-session D-drive collisions

**Slug:** apk-ps1-grep-lock-contention
**Status:** workaround
**Tags:** apk, multi-session, d-drive, grep, lock, mv, cp, file-handle
**First discovered:** 2026-05-19 09:30 by Sinister Kernel APK
**Last updated:** 2026-05-19 by tiktok-emu agent (cross-zone fix)

## Problem

When the operator is running multiple Claude Code sessions in parallel (per the standing 2026-05-19 "use all parrallel and local agents you need" directive), `mv` or `cp` operations against paths under `D:\Sinister\01_Projects\Sinister\Sinister-APK\` intermittently fail with:

```
mv: cannot stat 'D:/.../source/old-path': Device or resource busy
mv: cannot remove 'D:/.../source/old-path': Permission denied
```

This is not a sandbox / classifier issue. It's an OS-level file-handle conflict.

## Why it happens

Another currently-running Claude session is holding a recursive grep open on the same tree. Recursive greps (typically from `Grep` tool calls, or background sub-agents doing search work) maintain an OS file-handle on every directory + file they're walking. On Windows, that handle blocks atomic rename ops like `mv`.

Real-world example (2026-05-19 09:30):

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'grep.*Sinister-APK' }

# Output:
# PID 2932  : C:\Program Files\Git\usr\bin\grep.exe -r "pinned phone|active phone|26031JEGR17598|2A061JEGR09301|95.216.240.227|snap.sinijkr.com|Yurikey5" D:/Sinister/01_Projects/Sinister/Sinister-APK/
# PID 44428 : bash wrapper
# PID 62788 : bash wrapper
# PID 60812 : bash wrapper
```

That grep was launched by a DIFFERENT Claude session (parent session running in parallel, doing its own search work). It held handles on every subdirectory it walked, blocking the current session's mv calls.

## Fix / workaround

**RULE 1: Identify the lock holder before retrying.** Run:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'grep.*Sinister-APK' }
```

Or equivalent on the path you're trying to touch. If output is non-empty, you have a lock holder.

**RULE 2: Do NOT kill the lock holder.** The other Claude session is using it for legitimate work. Killing it can corrupt that session's in-flight ops.

**RULE 3: Wait it out OR pivot.** Two options:

- **Wait:** recursive greps complete on their own (usually 5-30s for D-drive APK tree at ~8 GB). Re-poll the lock holder list every 10s; retry the mv when empty.
- **Pivot to non-contending sub-paths:** if the grep is recursive on `D:/Sinister/01_Projects/Sinister/Sinister-APK/`, the lock is on the WHOLE tree. But mv/cp ops on `D:/Sinister/01_Projects/Sinister/Sinister-APK/_assets/...` or `.../_archive/...` may succeed if the grep has already passed those dirs. Try the leaf-level op; if it fails, try a different leaf.

**RULE 4: Use the PS1 bridge for batch ops.** `SinisterAPK_RunMe.bat` numbered phases land in `_runme/runme_<phase>_<ts>/` which is a fresh path per run. PS1-driven file ops don't typically conflict with greps on the SOURCE tree because they write to `_runme/`. Use the bridge when you have many file ops to do.

**RULE 5: Surface to operator if blocked > 60s.** If the lock persists past one minute, the other Claude session may be stuck (e.g. waiting on operator input). Surface: "another Claude session has a grep lock on the D-drive tree; please confirm you're OK to wait OR pivot to a different work surface."

## Caveats

- **Windows-only.** WSL2 and Linux Claude Code sessions don't have this exact issue (Linux handles allow concurrent renames). The APK agent runs in Windows Claude Code; TT-EMU runs in WSL2 - that's why TT-EMU doesn't hit this.
- **Sub-agent greps count too.** If you spawn an Explore sub-agent that does its own recursive grep, you can deadlock against your own background work. Avoid recursive greps in sub-agents when the parent agent is also doing mv/cp work.
- **Single-session is fine.** This is a multi-session issue. If you're the only Claude session active, you can't hit it.
- **Read-only ops never hit this.** `Read` tool calls + `cat` + `head` + `tail` use share-read handles that don't block other share-read handles. The conflict is specifically between exclusive-write ops (mv / rm / cp -f) and share-read ops (grep).

## Detection script

Add this to the project's pre-flight to flag potential contention BEFORE attempting mv ops:

```powershell
$conflicts = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match 'grep.*Sinister-APK' -or
    $_.CommandLine -match 'find.*Sinister-APK'
}
if ($conflicts) {
    Write-Warning "Found $($conflicts.Count) processes holding handles on Sinister-APK tree:"
    $conflicts | ForEach-Object { Write-Host "  PID $($_.ProcessId): $($_.CommandLine.Substring(0, [Math]::Min(100, $_.CommandLine.Length)))" }
    Write-Warning "Wait 10s + re-poll, OR pivot to a non-contending sub-path."
}
```

## Cross-refs

- Project: `D:\Sinister\01_Projects\Sinister\Sinister-APK\source\living-mds\GOTCHAS.md` - operator-facing surface for "grep lock contention" with workaround.
- PROGRESS: `D:\Sinister Sanctum\_shared-memory\PROGRESS\Sinister Kernel APK.md` 2026-05-19 09:30 entry - the source incident.
- Coordination doc: `D:\Sinister Sanctum\PARALLEL-AGENT-COORDINATION.md` - lane discipline (don't run greps over other agents' lanes without need).

## Discoveries (append-only - most-recent at top)

### 2026-05-19 by tiktok-emu agent (cross-zone)

First brain entry for this. APK agent hit it 2026-05-19 09:30 mid C->D consolidation; lock-holder identified via Get-CimInstance Win32_Process. Cross-zone authored under operator directive 2026-05-19 LATE ("not get blocked"). Pairs with `apk-classifier-aup-doctrine.md` + `apk-post-reboot-adb-reverse-wipe.md` (also this session).
