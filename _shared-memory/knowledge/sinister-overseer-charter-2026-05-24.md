<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: preference
  confidence: 0.95
  reinforcements: 0
  half_life_days: 365
-->
# sinister-overseer-charter-2026-05-24

> Charter for the Sinister Overseer meta-agent project.
> Project root: `D:\Sinister Sanctum\projects\sinister-overseer\`
> Slug: `sinister-overseer` | Display: `Sinister Overseer` | Accent: cyan | Tier: 3.
> Persona: EVE.
> Status: P0 scaffolded 2026-05-24 (sanctum-overseer-scaffold lane).

## Operator brief (verbatim 2026-05-24 ~23:48Z, two screenshots stitched)

> "I need you to make the project or find it that we should have started called sinister overseer and add it as a menu on the main menu called overseer. Have the be a project in the sanctum called sinister overseer and add it to the resume section so I can work on this, but when I click it in resume and only for overseer it needs to ask me what project would I like to begin overseer work for.
>
> Once I click in make the best system based off this:
> I want an overseer that finds all weak spots in a project and fixes them. Fails with the project to learn how to fix the mistakes. Overview and watch every key piece looking for places of improvement. Auditing all analytics and if applicable user data to actively suggest and expand the project it's connected to.
>
> In the overseer menu I need to be able to open it for the project it's connected to see stuff based on this project scope. Idk go crazy this kind of ties into the contradicting forever expanding system that can make things better. For example I can plug it into the chatbot and start training chat bot with it then it will be able to train chatbot by itself. I kind of want these to always be opening watching things, waiting for things to go wrong to fix them like for example for sinister snap panel that overseer could detect when a phone has an issue or snap updates and auto solve the issue push the fix or update. And this same methodology needs to be taken to all projects I decide to launch this for.
>
> So when I go to overseer menu it will first show no projects until I in that menu decide the overseer will now like to the project so have button support for that and have projects populate as they become overseen. I need a super efficient approach to this so we don't rape token use.
>
> In parallel first prepare to use overseer on eve compliance image system, sinister chatbot and the sinister sleight (make sure this is setup and is a active project)
>
> Make sure the overseer evolves across projects as it gets more projects under its belt"

## P0 SHIPPED (verified)

- `projects/sinister-overseer/` with 7 docs (README + CLAUDE + MISSION + docs/01-07).
- `pyproject.toml` (deps DECLARED, not installed).
- `.env.example` (cost cap envs + OAuth guidance).
- `.gitignore` (Python defaults + lessons.db + .env).
- `src/overseer/` package (CLI + config_io + watch + detector + triage + proposer + gate + lessons stubs).
- `src/overseer/adapters/` 5 adapters registered: ChatbotAdapter, ImageScannerAdapter, TradingBotAdapter, SnapPanelAdapter, GenericAdapter.
- `tests/test_smoke.py` (4 tests covering imports + adapter registry + CLI + attached-projects config).
- `config/attached-projects.json` (3 lanes status=`prepared`: eve-compliance, sinister-chatbot, sinister-sleight).
- Registry row in `automations/session-templates/projects.json` (key=sinister-overseer, cyan accent, tier=3, swarm+loop true, picker.visible_keys).
- Brain entries: this charter + `overseer-token-efficiency-doctrine-2026-05-24.md` + `fails-to-learn-doctrine-2026-05-24.md`.
- PROGRESS row at `_shared-memory/PROGRESS/Sinister Overseer.md`.
- Cross-agent inbox notes to eve-compliance + sinister-chatbot + sinister-sleight.
- OPERATOR-ACTION-QUEUE row pointing at activation flow.
- Mesh-coord lock `sinister-overseer-project` acquired by `sanctum-overseer-scaffold` + released at end of scaffold.
- Fleet-update HIGH priority push.

## 9 binding mission outcomes (measurable; see MISSION.md for criteria)

1. Attach UX -- empty-start; operator-click to populate.
2. Per-project menu -- attached project's scope sub-page.
3. Token efficiency -- $5/day cost-eq cap per attached project.
4. Watch architecture -- live, not batch; latency under 60s chat / 5min file.
5. Detector + triage + proposer -- cheap (Haiku-4.5) -> medium (Sonnet-4.6) -> high (Opus-4.7 rate-limited <= 5/day/attachment).
6. Apply gate -- TRIVIAL/LOW auto-apply, MEDIUM 4-hour window, HIGH/CRITICAL operator-gated forever.
7. Fails-to-learn -- failure -> lesson capture; 3+ same-shape failures auto-escalate to operator.
8. Cross-project evolution -- daily aggregator promotes >=2-project patterns to brain.
9. Self-training -- chatbot ML feedback +10% improvement attributable to overseer (P5).

## 6-phase roadmap (see docs/07-evolution-roadmap.md)

P0 scaffold (this turn) -> P1 single-project watcher (sinister-sleight) -> P2 multi-project pool (3 pre-attached) -> P3 fails-to-learn store -> P4 cross-project aggregator -> P5 self-training -> P6 fleet autonomous mode (operator-explicit-go required).

## Token efficiency commitment (THE first-class concern)

- Hard cap: $5/day cost-eq per attached project.
- Model-tier routing BINDING table in `docs/02-token-efficiency.md` (Haiku-4.5 cheap / Sonnet-4.6 medium / Opus-4.7 rare).
- Caching: stable prompt prefixes (adapter type + risk table + top-5 lessons).
- Diff-not-full-state policy.
- Per-project polling cadence (chat 5min / file 30min / ML 60min).
- Auto-throttle at 80% of cap; hard suspend at 100% with operator notification.

## Pre-attached lanes (status=`prepared`, NOT activated)

| Lane | Adapter | First-fire focus |
|---|---|---|
| eve-compliance | ImageScannerAdapter | vision-model drift; per-agency throughput; admin-review queue lag |
| sinister-chatbot | ChatbotAdapter | per-fan memory hit-rate; NSFW-route violations; ML feedback backlog; latency P95 |
| sinister-sleight | TradingBotAdapter | paper-PnL delta; KS-test drift; kill-switch always visible; walk-forward retrain queue |

## Composes with

- `_shared-memory/knowledge/overseer-token-efficiency-doctrine-2026-05-24.md` -- model-tier routing (sibling, same turn).
- `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md` -- fails-to-learn pattern (sibling, same turn).
- `_shared-memory/knowledge/token-efficiency-analytics-doctrine-2026-05-24.md` -- analytics primitive Overseer consumes.
- `_shared-memory/knowledge/oauth-pivot-max-quota-pooling-2026-05-24.md` -- Overseer uses OAuth round-robin pool.
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` -- precise verbs (scaffolded vs shipped).
- `_shared-memory/knowledge/forever-improve-review-doctrine-2026-05-24.md` -- Overseer IS forever-improve operationalized.
- `_shared-memory/knowledge/mesh-coordination-and-resource-lifecycle-2026-05-24.md` -- apply gate uses mesh-coord.
- `_shared-memory/knowledge/gradual-growth-memory-push-eve-exe-ready-2026-05-24.md` -- promotion pushes via fleet-update + inbox.
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` -- Overseer-lane = framework; per-attached-project work delegated.
- `_shared-memory/knowledge/sinister-sleight-project-charter-2026-05-24.md` -- pre-attached lane.
- `_shared-memory/knowledge/sinister-chatbot-direction-2026-05-24.md` -- pre-attached lane.
