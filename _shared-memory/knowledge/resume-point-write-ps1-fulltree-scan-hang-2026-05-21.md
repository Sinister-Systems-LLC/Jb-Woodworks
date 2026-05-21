# resume-point-write.ps1 hangs on 24h-files full-tree scan under multi-agent shared-CWD load (2026-05-21)

> **Author:** kernel-apk (Claude agent, 2026-05-21T18:4xZ)
> **Status:** known-issue + recommended-fix + empirical mitigation
> **Composes with:** multi-agent-branch-contention-isolation-pattern, apk-ps1-grep-lock-contention, resume-point-dir-name-convention

## Empirical observation

Session 2026-05-21T18:3xZ (kernel-apk lane). After committing v0.97.4 (`d244569`), called `automations/resume-point-write.ps1 -SanctumRoot 'D:\Sinister Sanctum' -ProjectKey 'Kernel APK' -AgentName 'kernel-apk' -Mode 'resume'` four times across foreground + background, sequential + concurrent. **Every invocation hung indefinitely** — no output file written, no JSON produced, 90s+ wall-clock with no progress. Manually wrote the v1-schema JSON instead.

Earlier-session invocations had succeeded (`2026-05-21T113241Z.json` + `2026-05-21T121526Z.json` were both written by the same script). The difference: those ran via the auto-mode launcher pre-cold-start; ours ran post-cold-start under active sibling-agent file-handle pressure (sanctum + rkoj both committing concurrently per `git log` deltas observed mid-session).

## Root cause (hypothesis)

`resume-point-write.ps1` lines 143-158 do a recursive `Get-ChildItem -Recurse` on `$SanctumRoot` filtering by `LastWriteTime -gt (now-24h)`. The Sanctum tree at this date includes:

- `_shared-memory/` with thousands of small files
- `projects/` with multiple sub-junctions to actual project working dirs (each its own multi-GB tree)
- `tools/` with embedded virtualenvs + node_modules
- `automations/`, `skills/`, `docs/`, `inventions/`

Most of those are excluded by name filters (`\.git\`, `node_modules`, `\.venv`, `backups`, `dist`) but the filter runs AFTER the recursive enumeration. Under multi-agent load (sibling sessions holding file handles + actively writing), the recursive enumeration can stall on directory-handle contention.

## Mitigation A — write the JSON directly (used this session)

When the PS1 hangs, write the resume-point JSON directly using the v1 schema. The schema is documented in CONTRACT 7 (`automations/session-contracts.md`):

```json
{
  "schema_version": "sinister.resume-point.v1",
  "ts_utc": "<ISO-8601>",
  "project": "<ProjectKey>",
  "agent_name": "<slug>",
  "mode": "<mode>",
  "focus_intent": "<one-line>",
  "git": { "branch", "head", "head_msg", "recent_commits" },
  "progress_top3": [ "...", "...", "..." ],
  "latest_plan": { "dir", "artifact" },
  "inbox_unread_count": <int>,
  "last_5_files_touched_24h": [ "...", "..." ],
  "pre_warm_reads": [ "<absolute-path>", "..." ]
}
```

Path: `_shared-memory/resume-points/<project-display-name>/<UTC-stamp>.json`. The next session's cold-start reads the highest timestamp in that dir, so the fallback-write produces a clean handoff.

Custom fields (`carry_forward`, `operator_directive_at_session`) are permitted — the schema is permissive (additive). The launcher's resume-mode read only consumes `pre_warm_reads[]` strictly.

## Mitigation B — proposed PS1 fix (not shipped this session — Sanctum lane)

Three options for the script author:

1. **Cap depth.** Use `Get-ChildItem -Recurse -Depth 4` instead of unlimited. Most relevant files live at `_shared-memory/PROGRESS/`, `_shared-memory/knowledge/`, `_shared-memory/inbox/<slug>/`, `_shared-memory/cross-agent/`, `_shared-memory/plans/` — all ≤4 levels deep.

2. **Use `-Filter` for early-bail.** PowerShell's `-Filter` runs before the file properties materialize, much faster than `Where-Object`. Combine with depth cap.

3. **Switch to `dotnet System.IO.Directory.EnumerateFiles` with `EnumerationOptions { RecurseSubdirectories=$true; AttributesToSkip=ReparsePoint }`.** Skips junctions (the `projects/<*>/source` symlinks back into project repos) which dominate the cost.

This fix lives in `D:\Sinister Sanctum\automations\resume-point-write.ps1` — Sanctum lane owns it. kernel-apk lane should NOT edit (per canonical-10 cross-lane discipline) without an [ASK] to sanctum first.

## Anti-patterns

1. **Don't retry the same hung script three more times** — burning 6 minutes here. After one timeout, fall back to Mitigation A.
2. **Don't try `Start-Process powershell.exe -WindowStyle Hidden ... -File resume-point-write.ps1`** — same hang behavior, just hidden from view. Hidden process becomes orphaned + holds file handles longer.
3. **Don't kill the hung PS1 with `taskkill /F /IM powershell.exe`** — wipes the operator's other PS windows + every other agent's running PS scripts. Per-PID kill only (canonical-3 + policy 8).
4. **Don't manually rewrite the script in-place from the kernel-apk lane** — cross-lane edit per canonical-10. ASK sanctum first.

## When to revisit

When sanctum lane next touches `automations/resume-point-write.ps1` (any version bump), they should adopt Mitigation B option 1 (depth cap) at minimum. The cost is one line change + bumps the version comment header. Until then, every fleet agent that hits this hang should fall back to Mitigation A.

## TL;DR

- **How we won:** PS1 hung 4x running the recursive 24h-files scan under sibling-agent load; wrote the v1-schema JSON directly as fallback and moved on.
- **What you need to do:** When you hit the hang, write the JSON yourself per the schema in CONTRACT 7. When sanctum-lane next ships a PS1 bump, ask them to cap recursion depth or skip reparse-points.
