# sanctum-self-heal

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

Hourly drift detector across the Sanctum fleet. Read-only. Produces a per-run report at `_shared-memory/self-heal-<UTC>.md`; prunes reports older than 30 days at the end of each run.

This is the operational backbone for the operator's "work forever" directive — without something watching for drift between sweeps, fleet state silently degrades (tasks unregister, MCP entries point at moved files, INDEX rows break, heartbeats go stale). Self-heal runs hourly, gives you a green / yellow / red signal in one glance.

## What it checks

| # | Check | Pass condition |
|---|---|---|
| 1 | Scheduled tasks present | `SinisterCustodian`, `SinisterSanctumAutoPush`, `RKOJ`, `SinisterVault` all registered |
| 2 | `~/.claude.json` parseable + each MCP server's cwd/command resolves | JSON valid; each server's `command` path + first path-arg exist on disk |
| 3 | `tools/_INDEX.md` row paths | Every row in the catalog points at a folder/file that exists |
| 4 | `skills/_INDEX.md` row paths | Both tables (folder-shaped + code-libs); rows resolve |
| 5 | Auto-push log freshness | `_shared-memory/auto-push.log` mtime within last 60 min (overridable via `-AutoPushFreshMinutes`) |
| 6 | Per-project CLAUDE.md presence | Every `projects.json` entry's `claude_md` file exists |
| 7 | Heartbeats fresh | Per-agent `_shared-memory/heartbeats/<agent>.json` mtime within last 60 min |

Pass = ✓, Warn = ⚠ (non-blocking), Fail = ✗ (operator-action needed). Report ends with an "Action required" or "Notes" block depending on severity.

## Run

```powershell
# One-shot, default thresholds
& "D:\Sinister Sanctum\tools\sanctum-self-heal\heal.ps1"

# Custom thresholds
& "D:\Sinister Sanctum\tools\sanctum-self-heal\heal.ps1" -AutoPushFreshMinutes 90 -HeartbeatFreshMinutes 30 -RetentionDays 14
```

Exit codes:
- `0` — all PASS (or only WARN)
- `1` — at least one FAIL (operator-action needed)
- `2` — fatal: Sanctum root not resolvable

## Schedule

For hourly automation, register a Windows scheduled task that runs the script. The simplest install (one operator click):

```powershell
# Register hourly task (no admin needed; RunLevel Limited)
schtasks /Create /TN SanctumSelfHeal `
  /SC HOURLY `
  /TR "powershell -ExecutionPolicy Bypass -File \"D:\Sinister Sanctum\tools\sanctum-self-heal\heal.ps1\"" `
  /F
```

Or use the Desktop one-click: `C:\Users\Zonia\Desktop\Sanctum-Self-Heal.bat`.

## Report format

```markdown
# Sanctum self-heal report :: 2026-05-19T134500Z

> **Pass / Warn / Fail:** 18 / 2 / 0

## scheduled-tasks

| Status | Item | Detail |
|---|---|---|
| [OK] | SinisterCustodian | state=Ready last=2026-05-19T09:00 result=0 |
| [OK] | RKOJ | state=Running last=2026-05-19T09:56 result=267009 |
...

## mcp-entries
...

## Action required (only if FAIL present)
...
```

## Retention

Reports under `_shared-memory/self-heal-*.md` older than 30 days (configurable via `-RetentionDays`) auto-prune at the end of each run. Newest 720 hours (≈30 days) of audit trail kept; older drops cleanly without operator intervention.

## Lane discipline

This tool NEVER:
- Modifies `~/.claude.json` (operator-owned).
- Registers, unregisters, or starts/stops scheduled tasks.
- Touches `projects/<project>/source/` (product-repo sources).
- Edits `_vault/`.
- Pushes git.

It only **reads** and **writes its own report file**. If a check FAILS, the report explains what's broken; the operator (or master agent in a follow-up session) actions it.

## See also

- `_shared-memory/self-heal-<UTC>.md` — latest run output
- `automations/verify-auto-push.ps1` — narrower check, just the auto-push task
- `_shared-memory/foundation-sweep-2026-05-19.md` — the manual sweep this tool automates
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` — where FAIL items typically need to land
