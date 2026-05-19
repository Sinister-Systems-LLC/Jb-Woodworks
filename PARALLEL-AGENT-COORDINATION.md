# Parallel-Agent Coordination

The operator works with multiple Claude sessions simultaneously â€” one for each
of the 5 Sinister repos (Sanctum + Snap EMU + TikTok EMU + Control Center +
Kernel APK), plus the master orchestration session. Each session can
unintentionally step on others' work if they all touch shared files at once.

This doc defines the boundaries so sessions stay out of each others' way.

## Ownership zones

| Zone | Owner | Editable by other sessions? |
|---|---|---|
| Sanctum `bots/agents/<bot>/server.py` | master/orchestration | rare; flag in operator chat first |
| Sanctum `bots/agents/<bot>/SYSTEM-PROMPT.md` | master | hand-edit only |
| Sanctum `bots/agents/<bot>/learned.md` | any (via `<bot>.absorb`) | shared; absorption-log audit |
| Sanctum `docs/*.md` | master | other sessions read-only by default |
| Sanctum `SESSION-START/*.md` | master | other sessions read-only |
| Sanctum `automations/*.ps1` | master | other sessions add, never modify |
| Sanctum `INDEX.md` | master | other sessions read-only |
| Sanctum `LICENSE` | operator | nobody else |
| Product repo `<repo>/` source | that repo's session | nobody else |
| Product repo `<repo>/CLAUDE.md` | that repo's session | this is per-repo |
| Hub `D:\Sinister\Sinister Skills\01_MEMORY\<project>\TODO.md` | master OR that project's session | last write wins; coordinate via `bus.dispatch` |
| Hub `D:\Sinister\Sinister Skills\01_MEMORY\_consolidated\*.md` | refresh.ps1 ONLY | hand-edits get overwritten |
| `~/.claude/.mcp.json` | operator (or install-fleet.ps1) | NEVER hand-edit from a session â€” use install-fleet.ps1 |
| `~/.claude/.mcp.json` `sinister-apk` entry | **apk agent only** | master MUST NOT touch â€” apk session owns it because the underlying path moves as the apk project reorganizes |
| `D:\Sinister\01_Projects\Sinister\Sinister-APK\` + `Kernel-SU-Setup\` source | **apk agent** | other sessions read-only |
| `D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\` source | **snap-emu agent** | other sessions read-only |
| `D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU\` source | **tiktok-emu agent** | other sessions read-only |
| `D:\Sinister\01_Projects\Sinister\Sinister-Panel\` source | **panel agent** | other sessions read-only |
| `D:\Sinister\01_Projects\Sinister\Sinister-Bumble-EMU\` source | **bumble-emu agent** | other sessions read-only |
| `D:\Sinister\01_Projects\Sinister\Sinister-RKA\` source | **rka agent** | other sessions read-only |
| `D:\Sinister\01_Projects\Sinister\Snap-Signer\` source | **snap-signer agent** | other sessions read-only |
| `D:\_backups\` | Custodian daemon ONLY | other sessions read snapshots; never write |
| `D:\Sinister Sanctum\_vault\` | master + operator | other sessions add notes inside their project's section |

## Conflict-avoidance protocol

When a session needs to touch a file outside its own zone:

1. **Check `sinister-bus.list_recent`** â€” has another session touched this file in the last 5 minutes? If yes, defer or coordinate via the operator.
2. **Use `custodian.snapshot_now path=<file>` BEFORE editing.** Creates a restore point in case of cross-session conflict.
3. **Make the edit, mention the cross-zone touch in the response,** and ask the operator to relay if needed.
4. **Record the handoff via `sinister-bus.dispatch`** so the audit trail captures cross-session intent.

## Three-session example workflow

```
Session A (orchestration / master): updating bots
Session B (Sinister Snap EMU): working on Argos signing
Session C (Sinister TikTok EMU): porting Snap a11y patterns to TT

Session B says: "remember this Argos hypothesis"
   -> Session B calls scribe.absorb(fact="...", source="Session B Snap signing", tags=["argos"])
   -> Goes into shared scribe/learned.md (audit-logged)

Session C wants the same fact (Argos is platform-shared):
   -> Session C calls scribe.list_facts(limit=20)
   -> Sees Session B's fact AND the source attribution
   -> Uses it without re-discovering

Session A notices a stale alarm:
   -> Session A calls sentinel.remove "old-alarm-id"
   -> Other sessions see the removal next time they call check_urgent

Session B is about to push:
   -> Session B calls bus.run_script "verify-backups" (read-only; never blocks others)
   -> Session B then runs git-toolkit safe-push from operator's terminal
   -> The runlog manifest is visible to A + C via bus.runlog_latest "safe-push"
```

## What sessions NEVER do without operator confirmation

- Modify `~/.claude/.mcp.json` directly (operator runs `install-fleet.ps1` instead)
- Run any destructive script (`migrate-projects.ps1` non-dryrun; `Deploy-Hetzner.bat`; `install-task.ps1`)
- Delete files from `_backups/snapshots/` (operator runs `custodian.cleanup` instead)
- Push to a git remote (operator runs `git-toolkit safe-push`)
- Change the LICENSE
- Disable / unregister another session's bot

## Cross-session memory pattern

Per `BOT-MEMORY-PROTOCOL.md`: every `<bot>.absorb` writes to `runtime-state/absorption-log.jsonl`. So when Session B absorbs a fact, Session A + C can `bus.runlog_list` or directly read `bot/learned.md` to see it.

`<bot>.absorb` tags should include the originating session's project (e.g.
`tags=["snap-emu", "argos"]`) so other sessions can filter relevance.

## TL;DR

- **How we won:** Ownership zones make cross-session conflicts explicit; bot memory is shared via append-only audit-logged absorb.
- **What you need to do (per session):**
  - Read this doc on cold-start.
  - When touching out-of-zone files, snapshot via Custodian first + tell the operator.
  - When absorbing a fact, tag it with the originating project.
  - Never modify `.mcp.json` / `LICENSE` / `_backups/snapshots/` directly.
