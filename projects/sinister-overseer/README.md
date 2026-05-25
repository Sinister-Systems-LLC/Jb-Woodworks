<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Sinister Overseer :: meta-agent / agent-of-agents

> Project root: `D:\Sinister Sanctum\projects\sinister-overseer\`
> Slug: `sinister-overseer` | Display: `Sinister Overseer` | Accent: cyan (overseer-class)
> Tier: T3 (new project, P0 scaffolded 2026-05-24)
> Persona: EVE (per `_shared-memory/knowledge/agent-identity-eve.md`)
> Status: P0 SCAFFOLDED -- structure + docs + registry + pre-attach config; ZERO watch loops running yet.

## Mission (one line)

A token-efficient meta-agent that ATTACHES to one or more projects, WATCHES for weak spots + regressions + signals, PROPOSES fixes (low-risk auto-applied; high-risk operator-gated), LEARNS from its own failures, and CROSS-PROJECT-EVOLVES so a lesson learned on project A becomes a candidate fix on project B.

## What makes Overseer different from a standard bot

A normal bot does ONE task on demand. Overseer is a CLASS of agent that:

1. Is **attached** (not spawned-and-die). It owns a long-running watch loop per attached project.
2. Is **token-aware first**. Cheap-tier (Haiku-4.5) handles tail/scan/heartbeat at near-zero cost; medium-tier (Sonnet-4.6) handles analyze/diagnose; high-tier (Opus-4.7) is RESERVED for rare hard-reasoning. See `docs/02-token-efficiency.md` -- the most important doc in this project.
3. Is **per-project-pluggable** via Adapters. Each project type has its own adapter that knows the signals + fix templates + auto-apply criteria. See `docs/04-per-project-adapters.md`.
4. **Fails to learn**. When a proposed fix breaks something, that failure is stored in a per-project + cross-project lessons knowledge base. Future fixes consult lessons first. See `docs/05-fails-to-learn.md`.
5. **Cross-project-evolves**. Lessons aggregate across projects -- "credentials swap mid-spawn breaks sessions" becomes a transferable doctrine that ALL adapters consult. See `docs/06-cross-project-learning.md`.
6. **First-show-no-projects UX**. Operator opens the Overseer menu -> empty state -> clicks "Attach Project" -> picks from fleet -> attached state begins. NEVER auto-attaches.

## Token-efficiency commitment (top-line)

**Hard cap: $5 / day cost-eq per attached project**, per attachment, unless operator explicitly bumps the ceiling. Default polling intervals: chat lanes 5 min, file-based lanes 30 min, ML training lanes 60 min. Full enforcement model + measurement hooks live in `docs/02-token-efficiency.md`. The fleet already ships the measurement primitives we depend on:

- `automations/claude-usage-meter.ps1` -- transcript-derived per-session token + cost meter.
- `automations/token-analytics.ps1` -- per-project / per-model / waste-pattern aggregator with P0-P3 recommendations.

Overseer's daily cost burndown is read from these two; if a per-attachment cost exceeds the cap, Overseer auto-throttles (drops to lower polling cadence + downshifts the model tier) before alerting the operator.

## Pre-attached projects (status = `prepared`, NOT activated)

At P0 scaffold time, three lanes are PREPARED in `config/attached-projects.json`. They are NOT actively watched yet; the operator MUST click "Activate" inside the Overseer menu before any watch loop fires.

| Lane | Adapter (planned) | First-fire focus | Adapter spec doc |
|---|---|---|---|
| `eve-compliance` | `ImageScannerAdapter` | Per-agency moderation throughput, training-feedback loop labelling lag, vision-model drift on flagged-vs-cleared deltas. | `docs/04-per-project-adapters.md` section "ImageScannerAdapter" |
| `sinister-chatbot` | `ChatbotAdapter` | Per-fan memory hit-rate, NSFW-route guardrail violations, latency P95 per model, machine-learning feedback labels backlog. | `docs/04-per-project-adapters.md` section "ChatbotAdapter" |
| `sinister-sleight` | `TradingBotAdapter` | Paper-PnL daily delta vs strategy expectation, model drift KS-test, kill-switch state ALWAYS visible, walk-forward retrain queue. | `docs/04-per-project-adapters.md` section "TradingBotAdapter" |

## Files in this project

| Path | Status | Purpose |
|---|---|---|
| `README.md` (this) | scaffolded | Project overview |
| `CLAUDE.md` | scaffolded | Per-agent cold-start protocol |
| `MISSION.md` | scaffolded | Operator brief verbatim + measurable acceptance criteria |
| `docs/01-architecture.md` | scaffolded | Full architecture: adapter pattern + event bus + watch loop + apply gate + lessons store + cross-project aggregator |
| `docs/02-token-efficiency.md` | scaffolded | THE critical doc: model-tier routing + caching + diff-not-state + per-project polling + hard cap enforcement |
| `docs/03-watch-architecture.md` | scaffolded | Event sources -> detector -> triage -> proposer -> apply gate |
| `docs/04-per-project-adapters.md` | scaffolded | Per-adapter spec (Chatbot / ImageScanner / TradingBot / SnapPanel / Generic) |
| `docs/05-fails-to-learn.md` | scaffolded | Failure -> lesson capture + per-project + cross-project lesson stores |
| `docs/06-cross-project-learning.md` | scaffolded | Cross-project lesson aggregator + transferable-pattern detector |
| `docs/07-evolution-roadmap.md` | scaffolded | 6-phase roadmap (P0 scaffold this turn -> P6 fleet autonomous mode) |
| `pyproject.toml` | scaffolded | Deps DECLARED, NOT installed |
| `.env.example` | scaffolded | ANTHROPIC_API_KEY guidance per OAuth-pivot doctrine; cost-cap envs |
| `.gitignore` | scaffolded | Python defaults + lessons db + .env |
| `src/overseer/__init__.py` | scaffolded | Package + version |
| `src/overseer/__main__.py` | scaffolded | CLI stub (`attach`, `detach`, `list`, `dryrun`, `apply`) |
| `src/overseer/adapters/__init__.py` | scaffolded | Adapter registry |
| `src/overseer/adapters/chatbot.py` | scaffolded | ChatbotAdapter stub |
| `src/overseer/adapters/image_scanner.py` | scaffolded | ImageScannerAdapter stub |
| `src/overseer/adapters/trading_bot.py` | scaffolded | TradingBotAdapter stub |
| `src/overseer/adapters/snap_panel.py` | scaffolded | SnapPanelAdapter stub |
| `src/overseer/adapters/generic.py` | scaffolded | GenericAdapter fallback |
| `src/overseer/watch.py` | scaffolded | Watch-loop stub |
| `src/overseer/detector.py` | scaffolded | Weak-spot detector stub |
| `src/overseer/triage.py` | scaffolded | Triage stub |
| `src/overseer/proposer.py` | scaffolded | Fix proposer stub |
| `src/overseer/gate.py` | scaffolded | Apply gate stub (auto vs operator) |
| `src/overseer/lessons.py` | scaffolded | Fails-to-learn store stub |
| `tests/test_smoke.py` | scaffolded | 3 smoke tests (import / adapter registry / CLI parse) |
| `config/attached-projects.json` | scaffolded | Pre-attach config (3 lanes status=`prepared`) |

## Composes with

- `automations/claude-usage-meter.ps1` -- per-session token + cost measurement (Overseer reads this for cap enforcement).
- `automations/token-analytics.ps1` -- per-project / per-model / waste-pattern recommendations engine.
- `automations/claude-oauth-accounts.ps1` -- account rotation for Overseer's own Claude calls (uses round-robin pool, not API key).
- `automations/mesh-coordinator.ps1` -- resource locks before Overseer edits any shared file.
- `automations/fleet-update.ps1` -- broadcast lessons + escalations to sibling agents.
- `_shared-memory/knowledge/sinister-overseer-charter-2026-05-24.md` -- project charter.
- `_shared-memory/knowledge/overseer-token-efficiency-doctrine-2026-05-24.md` -- model-tier routing doctrine.
- `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md` -- universal fails-to-learn doctrine.

## Lane metadata

- Branch: `agent/sinister-overseer/<short-topic>`
- Heartbeat: `_shared-memory/heartbeats/sinister-overseer.json`
- PROGRESS: `_shared-memory/PROGRESS/Sinister Overseer.md`
- Resume-points: `_shared-memory/resume-points/Sinister Overseer/<UTC>.json`
- Inbox: `_shared-memory/inbox/sinister-overseer/`

## What this project is NOT

- NOT a generic linter or test runner -- it watches LIVE running projects.
- NOT autonomous-by-default for risky fixes -- apply gate operator-approval for anything touching credentials / production / financial / external-facing.
- NOT a replacement for per-project agents -- it COMPLEMENTS them by surfacing weak spots they may not notice mid-task.
- NOT permitted to spend unlimited tokens -- cap defaults to $5/day cost-eq per attached project.

## Self-improvement engine (compiled this iter)

Beyond the per-adapter watch loop, the Overseer ships a UNIFIED improvement engine that ties together sensors (analyzer + meter + forever-improve) -> WatchBus -> Detector -> Triage -> Contradiction Engine -> Proposer -> ApplyGate -> LessonsStore -> CrossProjectAggregator. The pipeline runs cheap-tier (Haiku) for sensors + classify + counter-arg, medium-tier (Sonnet) for triage + adversarial cycle, high-tier (Opus) ONLY for rare proposer rebuilds. The Contradiction Engine challenges every proposed fix with 3 counter-argument questions before the gate; score above threshold rolls back; cross-project invariant collisions force operator escalation. Per-lane recipes in `config/improvement-recipe.json` (3 prepared: eve-compliance / sinister-chatbot / sinister-sleight) declare WHAT counts as improvement for that lane WITHOUT forking the engine. Full pipeline in `docs/09-unified-improvement-engine.md`; contradiction doctrine in `docs/08-contradiction-engine.md`. Brain rows: `_shared-memory/knowledge/contradiction-engine-doctrine-2026-05-24.md` + `_shared-memory/knowledge/overseer-unified-improvement-engine-2026-05-24.md`.
