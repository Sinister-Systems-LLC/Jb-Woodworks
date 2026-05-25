# eve-exe master plan — finish everything in parallel

> Author: RKOJ-ELENO :: 2026-05-25T13:15Z
> Lane: `eve-exe` (master coordinator) + cross-lane fan-out
> Trigger: operator (verbatim 2026-05-25 ~13:14Z): *"create a plan to complete all of this in parrallel."*
> Composes with: `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25` + `loop-relentless-pursuit-doctrine-2026-05-25` + `safe-quality-loops-doctrine-2026-05-24` + `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25`.

## Operator directives logged this session (verbatim, all binding)

| # | Time | Utterance | Status |
|---|---|---|---|
| 1 | 11:55Z | resume eve-exe lane post-mass-crash | ✅ done |
| 2 | 12:50Z | "make sure all is efficient and token efficient... resume fast startup, complete entire UI fix I said, smoke test entire, then UI again with sinister designer" | 🟡 partial (UI iter-1 + iter-2 shipped, smoke OK, designer pending) |
| 3 | 12:53Z | "these fucking random cmd and powershell things have to stop popping up and everything needs to be crisp and efficient" | ✅ done (iter-3 monkey-patch) |
| 4 | 12:57Z | "make sure sinister designer is open and project created properly and well-versed on brand and dashboard skeleton and all websites we have made" | 🟡 sub-agent in flight |
| 5 | 13:02Z | "i need the loop system going and i need a forever updating option that stops once quality goes down and reverts back to the peak of the part. jcode did something like this" | 🟡 checkpoint manager built; ps1 wiring pending |
| 6 | 13:05Z | "i need you to have real loop in this and real swarm how jcode does" | ⏳ swarm primitive pending |
| 7 | 13:09Z | "and for fuck sake fix the god damn login for claude" | 🟡 sub-agent in flight |
| 8 | 13:14Z | "[Image] fix all this shit" (1 MCP server failed · /mcp) | ⏳ sub-agent dispatched |
| 9 | 13:14Z | "create a plan to complete all of this in parallel" | ⏳ this doc |

## Shipped this session (verified)

- `f5e3caa` — eve-exe iter-1: Q quick-launch + claude-icon + sub-page centering + bug fix
- `a00a9c7` — eve-exe iter-2: shimmering header/footer separators
- `d38c13d` — eve-exe iter-3: headless subprocess monkey-patch
- `automations/loop_checkpoint.py` — checkpoint manager with restore-to-peak (verified: corrupted file restored to iter-0 state)

## Parallel fan-out (5 lanes)

### Lane M (master, foreground = me)
- M1: Patch `automations/quality-monotonic-loop.ps1` — add `-CheckpointPaths` + `-RevertOnRegression` params that shell out to `python automations/loop_checkpoint.py save` / `restore-best`.
- M2: Wire `quality_score_command` + `quality_paths` defaults into `automations/session-templates/projects.json` per project so spawn loops checkpoint automatically.
- M3: Commit + push final state.
- M4: Final smoke: run quality-monotonic-loop.ps1 in -DryRun against the eve-exe lane to confirm the checkpoint side-channel fires.

### Lane A (sub-agent, in flight)
- A1: Fix Claude OAuth login (eve-bulk-oauth-login.ps1 wizard `processed=0` regression).
- Status: agent `a18e91d0f439c1945` running.

### Lane B (sub-agent, in flight)
- B1: Auto-spawn sinister-designer + write BRAND-BRIEF.md (the brand + dashboard-skeleton + all websites).
- Status: agent `a35ae41eb3509bd42` running.

### Lane C (sub-agent — dispatch this turn)
- C1: Diagnose "1 MCP server failed" surfaced by Claude Code's /mcp status. Read `~/.claude.json` MCP server config + `~/.claude/mcp.log` if present. Identify which server is failing, what error, ship a fix (config edit or stop a server).

### Lane D (sub-agent — dispatch this turn)
- D1: jcode "real swarm" primitive port. Investigate `C:\Users\Zonia\Desktop\jcode-0.12.4\src\agent\` for jcode's parallel agent fan-out abstraction. Port the smallest workable subset to Sanctum as a Python module that wraps the existing `mesh-coordinator.ps1` + inbox protocol. Compose with the FULL-RELENTLESS SWARM doctrine.
- D2: Update CLAUDE.md cold-start to document: (a) quality-monotonic checkpoint+revert via loop_checkpoint.py; (b) real-swarm primitive once D1 ships.

## Acceptance criteria (per lane)

| Lane | Pass criterion |
|---|---|
| M | quality-monotonic-loop.ps1 has `-CheckpointPaths` + `-RevertOnRegression`; dry-run shows checkpoint save line; integration test with planted regression restores peak |
| A | login wizard one full round produces `processed >= 1` AND claude-accounts.json `linked: true` for the new slot |
| B | sinister-designer heartbeat `last_seen_utc` is fresh (<10min); BRAND-BRIEF.md exists with ≥5 website entries |
| C | `claude /mcp` no longer reports `failed`; ~/.claude.json mcpServers list parsed clean |
| D | new `automations/sinister_swarm.py` ships with `fanout(slug, slices, timeout) -> [results]` API; CLAUDE.md doctrine row added |

## Anti-patterns (binding for every lane)

1. NEVER block on operator confirmation; execute directly.
2. NEVER spawn agents with overlapping owned-paths (use mesh-coordinator Check).
3. NEVER stash globally (multi-agent shared repo) — use file-mirror checkpoints.
4. NEVER claim "shipped" without same-turn smoke evidence (no-bullshit doctrine rule 2).
5. NEVER write new .bat / .ps1 — only Python for new artifacts.

## Stop condition

All 5 lane pass criteria met OR operator interrupts with new direction.
