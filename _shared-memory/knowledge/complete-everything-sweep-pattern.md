> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: "Complete everything" sweep — operator-broad-ask → 9-phase plan

**Slug:** complete-everything-sweep-pattern
**First discovered:** 2026-05-19 13:30 by Sinister Sanctum master agent
**Last updated:** 2026-05-19 13:30 by Sinister Sanctum master agent
**Status:** fixed
**Tags:** sweep, fleet, master-agent, operator-queue, codex, standing-rule

## Problem

Operator says "make plan to complete everything." The fleet has ~27 open items
across master-lane code debts, operator-pending wire-up, and cross-agent
delegations. Naively iterating one by one wastes the master agent's pass:
items have ordering dependencies (build before task-install), some belong in
other agents' lanes, and some only the operator can do (env vars, .mcp.json,
phone PI, Restart Claude Code).

## Why it happens

Fleet open-item lists accumulate across sessions. A single "complete everything"
ask sounds simple but spans multiple ownership zones (per
`PARALLEL-AGENT-COORDINATION.md`) and reversibility tiers (per EXPANDED
AUTHORITY in DIRECTIVES.md).

## Fix or workaround

**Tested 2026-05-19** (Sinister Sanctum master agent ran the sweep end-to-end).

### Phase order (canonical)

```
1 Code → 2 Build EXE → 3 Install tasks → 4 Smoke
                                            │
                                            ▼
                                  [OPERATOR GATE]
                                            │
                                            ▼
5 Wire-The-Rest.bat → 6 Cross-agent asks → 7 Brain → 8 Codex review (split) → 9 Commit + push + broadcast
```

### Bucket triage (mandatory)

Every open item gets one of three buckets:

| Bucket | Means | Action |
|---|---|---|
| **A — Master-lane-doable** | Pure code/docs/scripts inside Sanctum (no product-repo source, no `.mcp.json`, reversible) | Master executes |
| **B — Operator-click-needed** | Admin elevation, env-var sets, LICENSE, phone physical, Claude-restart | Bundle in `Wire-The-Rest.bat` for one double-click execution |
| **C — Cross-agent-delegation** | Belongs in another agent's lane | Send via filesystem inbox to `_shared-memory/cross-agent/<utc>-sanctum-to-<agent>.md` |

### Critical sequencing rules (learned 2026-05-19)

1. **Build BEFORE task install.** Otherwise the scheduled task starts the
   pre-fix EXE and the new runtime artifacts (heartbeats, SSE endpoints) never
   tick from t=0.
2. **Orphan-task guard BEFORE register.** `Get-ScheduledTask <name>` check; if
   present from a prior legacy installer, `Unregister-ScheduledTask -Confirm:$false`
   first. Prevents the "two tasks pointing at the same daemon" failure mode.
3. **Naming-collision suffix.** New runtime heartbeats end in `-runtime.beat`
   to keep them grep-able from existing `-build.beat` artifacts. Don't reuse
   bare `<slug>.beat` for new daemons.
4. **Manual feature-branch push.** Auto-push daemon mirrors `main` only.
   Master commits to its agent branch + pushes manually — preserves the Codex
   review gate; failures don't auto-leak.
5. **Cross-agent broadcast timing.** Per-agent asks in Phase 6 (immediately
   useful — independent of commit). Global `[DISCOVERY]` broadcast deferred
   to Phase 9.4 (post-commit) so siblings don't see "sweep done" while branch
   isn't pushed yet.
6. **Codex review depth split.** Don't run `--depth deep` on a 250-LOC
   consolidated diff. Split: `deep` on architectural new code (SSE,
   concurrency, race conditions), `standard` on UI stubs + pattern-following.
   Sharper findings, fewer tokens.

### Lane-discipline guardrails (immutable)

- No `D:\Sinister\01_Projects\Sinister\<repo>\source\` writes
- No `~/.claude/.mcp.json` edits — even with Expanded Authority
- No product-repo git pushes
- LICENSE pick deferred (private repo makes placeholder safe)
- Env vars User-scope: operator only
- Phone PI: physical operator action
- Restart Claude Code: kills master's own session — terminal-only

### Verification harness (must run before commit)

```powershell
Get-ScheduledTask SinisterRKOJ, SinisterVault | Format-Table TaskName, State, LastRunResult
Get-Content "D:\Sinister Sanctum\_shared-memory\heartbeats\rkoj-runtime.beat"
Get-Content "D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-vault.beat"
curl http://127.0.0.1:5077/api/fleet-snapshot
curl http://127.0.0.1:5078/api/vault/health
Test-Path "D:\Sinister Sanctum\automations\window-manager\dist\RKOJ\_internal\sanctum_shared\cycle_points.py"
```

## When to invoke this pattern

- Operator asks "complete everything" / "finish the open queue" / "close out the sprint"
- Quarter / month boundary close-out
- Pre-handoff to another agent (or to Leo) — clean state matters
- After a multi-agent multi-day sprint when the master needs to reconcile

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 13:30 by Sinister Sanctum master agent
First landing. Plan agent caught two ordering bugs in the proposed Phase 1→2
order (build before task install) and recommended the Codex review split.
Both shipped. The 9-phase shape with explicit operator gate after Phase 4
preserves reversibility — persistent system state (scheduled tasks) is
registered by Phase 3, smoke-verified in Phase 4, and the operator decides
whether Phase 5+ proceeds.

## Related topics

- [runtime-liveness-heartbeats](./runtime-liveness-heartbeats.md) — Phase 1.1 of the canonical sweep
- [rkoj-fleet-state-sse](./rkoj-fleet-state-sse.md) — Phase 1.2 of the canonical sweep
- [vault-commit-modal-pattern](./vault-commit-modal-pattern.md) — Phase 1.3 of the canonical sweep
- [codex-companion-usage](./codex-companion-usage.md) — Phase 8 peer-review gate
- [cross-agent-coordination](./cross-agent-coordination.md) — Phase 6 inbox patterns
