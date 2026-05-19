> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Archived — legacy console-task install scripts

**Archived:** 2026-05-19 13:30 UTC by Sinister Sanctum master agent
**Reason:** Superseded by `automations/window-manager/install-rkoj-task.ps1` (and the matching uninstall via `-Uninstall` switch on the same file).

## Files

- `install-console-task.ps1` — early version of the RKOJ scheduled-task installer. Registers task name `RKOJ` from `console-daemon.bat`. Lacks the explicit `-BatPath` parameter that `install-rkoj-task.ps1` ships; this matters because when invoked via `powershell -ExecutionPolicy Bypass -File ...`, `$PSScriptRoot`/`$MyInvocation.MyCommand.Path` resolution has a known corner case (called out in `OPERATOR-ACTION-QUEUE.md`).
- `uninstall-console-task.ps1` — companion uninstaller. Functionality already covered by `install-rkoj-task.ps1 -Uninstall`.

## Why retired (not deleted)

If operator still references either by name in muscle-memory shell history, the archived copy lets them recover quickly. Promote back by:

```powershell
Move-Item "D:\Sinister Sanctum\_archive\automations\window-manager\install-console-task.ps1" "D:\Sinister Sanctum\automations\window-manager\"
```

## Recommended replacement

```powershell
powershell -ExecutionPolicy Bypass -File `
  "D:\Sinister Sanctum\automations\window-manager\install-rkoj-task.ps1" `
  -BatPath "D:\Sinister Sanctum\automations\window-manager\console-daemon.bat"
```

Or to uninstall:

```powershell
powershell -ExecutionPolicy Bypass -File `
  "D:\Sinister Sanctum\automations\window-manager\install-rkoj-task.ps1" -Uninstall
```

## Related

- HR-B audit findings — `_shared-memory/PROGRESS/Sinister Sanctum.md` 2026-05-19 11:17 entry
- Plan that drove this archive — `C:\Users\Zonia\.claude\plans\make-plan-to-complete-foamy-squid.md` Phase 1.6
