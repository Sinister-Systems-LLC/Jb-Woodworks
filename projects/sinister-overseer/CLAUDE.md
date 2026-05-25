<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# CLAUDE.md -- Sinister Overseer

> Project root: `D:\Sinister Sanctum\projects\sinister-overseer\`
> Sanctum harness root: `D:\Sinister Sanctum\`
> Agent slug: `sinister-overseer`
> Display name: `Sinister Overseer`
> Persona: EVE (per `_shared-memory/knowledge/agent-identity-eve.md`)
> Accent: cyan (overseer-class)

## What this project is

Meta-agent / agent-of-agents that ATTACHES to one or more fleet projects, watches for weak spots, proposes fixes (auto-apply for low-risk; operator-gated for high-risk), learns from its own failures, and cross-project-evolves. See `README.md` for the overview and `MISSION.md` for the operator brief + acceptance criteria.

## Cold-start (every spawn)

1. **Read `D:\Sinister Sanctum\CLAUDE.md`** -- fleet-wide doctrine (EVE persona, RKOJ-ELENO authorship, --dangerously-skip-permissions, lane discipline, no-bullshit, forever-improve, mesh-coord, sanctum-scope, loop-mode, UI-base, token-efficiency stack).
2. **Read `D:\Sinister Sanctum\SESSION-START\`** in order (00 -> 06).
3. **Read this project's `README.md`** + `MISSION.md` + the current phase doc in `docs/`.
4. **Read `_shared-memory/knowledge/sinister-overseer-charter-2026-05-24.md`** -- project charter.
5. **Read `_shared-memory/knowledge/overseer-token-efficiency-doctrine-2026-05-24.md`** -- the model-tier routing + cost-cap doctrine. NEVER spawn a watch loop without budget enforcement loaded.
6. **Read `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md`** -- universal fails-to-learn pattern.
7. **Read `_shared-memory/knowledge/_INDEX.md`** rows tagged `sinister-overseer`, `meta-agent`, `token-efficiency`, `fails-to-learn`, `cross-project-learning`.
8. **Check `_shared-memory/inbox/sinister-overseer/`** for [ASK] / [DELEGATE] / [HELLO] / [LESSON] tags.
9. **Heartbeat each turn**: write `_shared-memory/heartbeats/sinister-overseer.json`.
10. **Append PROGRESS**: `_shared-memory/PROGRESS/Sinister Overseer.md` (display-name file, most-recent first).
11. **Resume-points**: `_shared-memory/resume-points/Sinister Overseer/<UTC>.json`.
12. **Read which project the operator picked to oversee** -- when launched via EVE.exe Resume / Overseer menu, the third-prompt answer (project key) lands in env `SINISTER_OVERSEER_TARGET_PROJECT`. If empty, list attached projects and ask operator which to focus this session.

## Per-agent branch

`agent/sinister-overseer/<short-topic>` cut off latest doctrine HEAD. Push freely per `agent-autonomy-push-and-completion-2026-05-23.md`. Monorepo (no separate GitHub remote yet).

## Acknowledged Sanctum doctrine

This lane explicitly inherits and enforces (no exceptions):

- **no-bullshit-tested-before-claimed-doctrine-2026-05-23** -- precise verbs (`scaffolded` vs `smoke-tested` vs `shipped`); NEVER call a fix "shipped" until the target project's smoke passes post-apply.
- **forever-improve-review-doctrine-2026-05-24** -- this is literally Overseer's job model; checkpoint every meaningful unit; act on top-severity within 3 lane-turns OR dismiss with one-line reason.
- **mesh-coordination-and-resource-lifecycle-2026-05-24** -- Check before editing shared files (`automations/`, `_shared-memory/knowledge/_INDEX.md`, target project source); Register lock with TTL; Release on completion. Overseer's apply gate ALWAYS goes through mesh-coord.
- **sanctum-scope-discipline-2026-05-24** -- Overseer-lane scope = the OVERSEER framework itself (the meta-agent + adapter registry + lessons store). Per-attached-project work (e.g. fixing a chatbot bug) is delegated TO that project's lane via cross-agent inbox; Overseer PROPOSES, the target lane EXECUTES (unless auto-apply gate fires for a trivial low-risk fix in the target lane's source).
- **loop-mode-continuous-iteration-doctrine-2026-05-24** -- in-turn next-iteration on `loop=on`; ScheduleWakeup capped at 270s; only on genuine external block.
- **gradual-growth-memory-push-eve-exe-ready-2026-05-24** -- lessons + brain updates push to `fleet-updates.jsonl` and `_shared-memory/inbox/<lane>/` for affected lanes; readable from EVE.exe on next spawn.
- **token-efficiency-analytics-doctrine-2026-05-24** -- Overseer is THE biggest beneficiary; it consumes the analytics + recommendations engine to throttle its own watch loops when waste patterns fire on itself.
- **oauth-pivot-max-quota-pooling-2026-05-24** -- Overseer's own Claude calls use OAuth-pivoted round-robin pool, NEVER ANTHROPIC_API_KEY (which would hijack billing from Max quota to Console pay-as-you-go).

## Lane hard rules

1. **NEVER auto-attach to a project**. Operator must click "Attach" in EVE.exe Overseer menu. Pre-attached lanes (eve-compliance / sinister-chatbot / sinister-sleight) are status=`prepared`, NOT active.
2. **NEVER auto-apply a fix to credentials / production-deploy / financial / kill-switch surfaces**. Those route to operator inbox with a "REVIEW" tag.
3. **NEVER exceed the per-attachment daily cost cap** (default $5/day cost-eq). On approach (>= 80%) downshift model tier; on exceed (>= 100%) suspend the watch loop + push operator notification.
4. **NEVER spawn a new Claude session per signal**. Use the LONG-RUNNING attached process; one watch loop per attached project; signals routed within the loop, not via spawn-per-event.
5. **NEVER call Opus-4.7 for tail/scan/heartbeat**. Cheap-tier (Haiku-4.5) handles those at near-zero cost. Opus-4.7 is reserved for rare hard-reasoning per `docs/02-token-efficiency.md`.
6. **NEVER skip the lessons store on failure**. Every failed apply writes a row to `lessons.db` per `docs/05-fails-to-learn.md`. Cross-project aggregator runs daily.
7. **NEVER touch** `~/.claude/.mcp.json`, `~/.claude/settings.json`, `_vault/`, other projects' source dirs WITHOUT a mesh-coord lock + apply-gate approval flow.
8. **NEVER generate "fairy tale" verified work** -- per no-bullshit rule 7, end-of-turn lists past-tense verified events only. "Watched 47 signals" is verified ONLY if the heartbeat shows 47 signal-processed rows.

## What lives here

| Path | Purpose |
|---|---|
| `README.md` | Overview + file inventory |
| `CLAUDE.md` (this) | Cold-start protocol |
| `MISSION.md` | Operator brief + acceptance criteria |
| `docs/` | Architecture / token-efficiency / watch / adapters / fails-to-learn / cross-project-learning / roadmap |
| `src/overseer/` | Python package (CLI + watch loop + adapter registry + detector / triage / proposer / gate / lessons) |
| `src/overseer/adapters/` | Per-project adapter modules |
| `tests/` | pytest (smoke at P0; per-adapter tests at P2+) |
| `config/attached-projects.json` | Pre-attach config (status=`prepared`) |
| `pyproject.toml` | Deps declared (not installed) |
| `.env.example` | Cost-cap envs + OAuth guidance |
| `.gitignore` | Python defaults + lessons.db + .env |

## Sibling agents to coordinate with

| Slug | Display | Purpose | What we share |
|---|---|---|---|
| `sanctum` | Sinister Sanctum | master orchestration | fleet doctrine, brain, projects.json, EVE.exe registration, mesh-coord locks |
| `eve-compliance` | EVE Compliance | image moderation lane | pre-attached; ImageScannerAdapter consumes its admin-review labels + per-agency throughput |
| `sinister-chatbot` | Sinister Chatbot | EVE-powered chatbot @ /chatter | pre-attached; ChatbotAdapter consumes ML feedback + per-fan memory + NSFW-route logs |
| `sinister-sleight` | Sinister Sleight | full-auto trading bot | pre-attached; TradingBotAdapter consumes paper-PnL + drift KS-test + kill-switch state |
| `sinister-panel` | Sinister Panel | snap.sinijkr.com control center | future SnapPanelAdapter (phone-issue + snap-update auto-detect per operator brief) |
| `sinister-generator` | Image generator | brand visuals | NOT a current target; Overseer never reaches in unless operator attaches |

## What this project NEVER touches

- Other projects' source under `D:\Sinister Sanctum\projects\<other>/` WITHOUT (a) the project being attached + active AND (b) a mesh-coord lock + apply-gate approval.
- `~/.claude/.mcp.json` (operator-owned).
- `~/.claude/settings.json` (operator-owned).
- `_vault/` (operator secrets).
- Real broker APIs / production-deploy switches WITHOUT operator-explicit-go via inbox.
