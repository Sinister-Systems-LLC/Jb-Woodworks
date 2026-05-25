<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Headless spawn pattern (no visible cmd / powershell windows)

**Status:** doctrine, standing-rule, binding
**Created:** 2026-05-23
**Origin:** Operator hard-canonical 2026-05-23 (verbatim): *"all these cmd windows that keep coming up need to be headless and not seen by me. do this with out sinister term and add it as a feature"*

## TL;DR

Any spawn surface that produces a console window without operator interaction MUST run hidden. The reusable helper is `automations/hidden-spawn.ps1`. Three modes — PowerShell file, raw cmdline, Python module — all return the wrapped exit code.

## The wall

Hooks (SessionStart, Stop, PostToolUse, etc.), scheduled tasks, launcher background daemons, install scripts, and any non-interactive automation should not flash a window. The operator sees these as "cmd window popups" and they break flow. This is independent of sinister-term — sterm is the operator-facing post-spawn shell, not the headless layer.

## Approved patterns

### A. Hook commands in `.claude/settings.json`

Always pass `-WindowStyle Hidden` to `powershell.exe`:

```json
"command": "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File \"<path>.ps1\" -Quiet"
```

The Sanctum SessionStart hook (canonical-protections-check) was migrated 2026-05-23 to this pattern.

### B. From within a PowerShell script

```powershell
Start-Process -FilePath 'powershell.exe' `
    -ArgumentList '-WindowStyle','Hidden','-NoProfile','-ExecutionPolicy','Bypass','-File',$script `
    -WindowStyle Hidden -PassThru
```

Note the redundant `-WindowStyle Hidden` on both `Start-Process` AND the inner argument list — Windows requires both to fully suppress the flash on some shells.

### C. Python — use `pythonw.exe` not `python.exe`

`pythonw.exe` is the windowless Python launcher (no console at all). For modules:

```powershell
Start-Process -FilePath 'pythonw.exe' -ArgumentList '-m', $module -WindowStyle Hidden
```

If `pythonw.exe` is not on PATH, fall back to `python.exe` with `-WindowStyle Hidden` — this still flashes briefly on first invocation but is the best available fallback.

### D. cmd.exe one-liners

```powershell
Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $cmdLine -WindowStyle Hidden
```

For fire-and-forget background tasks: add `-NoWait` (via the helper) so the caller doesn't block.

### E. Scheduled tasks

Per `sanctioned-bypasses-doctrine-2026-05-21`: `schtasks` MUST register with hidden window mode. Recipe:

```powershell
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument '-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File "<path>.ps1"'
$settings = New-ScheduledTaskSettingsSet -Hidden
Register-ScheduledTask -TaskName 'MyTask' -Action $action -Settings $settings
```

The `-Hidden` flag on `New-ScheduledTaskSettingsSet` makes the task itself invisible in Task Scheduler UI (operator preference for the Sinister fleet tasks). The `-WindowStyle Hidden` on the action suppresses the spawned window.

## Anti-patterns

1. **`powershell.exe -File ...` from a hook without `-WindowStyle Hidden`** — flashes a window every spawn. The screenshot operator showed 2026-05-23 was a Stop hook that did this.
2. **`Start-Process` without `-WindowStyle Hidden`** — defaults to "Normal", which shows the window.
3. **Using `python.exe` for daemon-style scripts** — even with hidden flags, the console attaches briefly. Use `pythonw.exe`.
4. **Wrapping a hidden PowerShell call inside `cmd /c`** — adds an extra cmd window that itself flashes. Call PowerShell directly via the helper.
5. **Using `Start-Job` for "background" but the inner command spawns a window** — `Start-Job` doesn't suppress console-window creation in child processes; the inner command still needs `-WindowStyle Hidden` or `CREATE_NO_WINDOW`.
6. **Conflating sterm with headless** — sterm is the OPERATOR-VISIBLE post-claude shell. Headless is the NON-INTERACTIVE automation layer. They are orthogonal; the operator explicitly said "do this without sinister-term".

## When a window is OK

- **The launcher mintty window** that spawns the agent — operator interacts with it.
- **`Sinister Start.bat`** — operator double-clicks it; visible is intentional.
- **Install scripts run via UAC** — Windows requires visible UAC prompt; can't hide.
- **Operator-invoked terminal scripts** — anything the operator launches knowingly.

## Helper inventory

- `automations/hidden-spawn.ps1` — the reusable wrapper. Used by future hooks/tasks.
- `automations/canonical-protections-check.ps1` SessionStart wiring — uses `-WindowStyle Hidden` directly.

## Composition

Composes with:
- `sanctioned-bypasses-doctrine-2026-05-21` (top 2026-05-23-evening block — schtask hidden + CREATE_NO_WINDOW are sanctioned)
- `do-not-revert-operator-canonical-protections-2026-05-23` (the SessionStart hook now uses hidden style; P9 already verifies the hook path)
- `agent-autonomy-push-and-completion-2026-05-23` (visible windows interrupt autonomy)
- `handterm-vs-sinister-term-clarification-2026-05-23` (sterm is operator-facing; headless is automation-facing — different layers)

## Audit checklist

For every new hook / scheduled task / background daemon, verify:

1. [ ] `Start-Process` calls include `-WindowStyle Hidden`.
2. [ ] PowerShell-via-hook command strings include `-WindowStyle Hidden`.
3. [ ] Python scripts that don't need stdout use `pythonw.exe`.
4. [ ] Scheduled tasks registered with `-Hidden` settings + `-WindowStyle Hidden` action arg.
5. [ ] No `cmd /c` wrappers around already-hidden commands.

If any item fails: route via `automations/hidden-spawn.ps1` instead. Operator's standing rule: invisible by default; visible only when operator-invoked.

## Future: P10 in canonical-protections-check

A future iteration could add P10 to scan all `settings*.json` hook commands AND `schtasks /Query /XML` output for missing `-WindowStyle Hidden`. Deferred; the helper + this doctrine are the immediate fix.
