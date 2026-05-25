<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister Sleight :: project charter

> Created: 2026-05-24
> Slug: `sinister-sleight` | Display: `Sinister Sleight` | Tier: T3 (new project)
> Lane owner: EVE on `sinister-sleight`
> Status: P0 SCAFFOLDED (project structure + docs + registry); P1 QUEUED

## Operator brief (verbatim 2026-05-24 ~22:00Z)

> "prepare the sinister trade bot and create a proejct start for it. complie all knowledge you need to be the ebst trader in the world, full complete plans how you can self train, use our quantum toools to expand and how you are oing to train on penny stocks or fake envirments and build all systems needed to make a full auto trade bot that will make me money. review this entire site and start to gather and complie all knowledge you need. make a ture project setup, memory all of that and place it in eve exe and call it Sinister Sleight."

## Mission (one line)

Build a fully-autonomous, quantum-assisted trading bot that paper-trades to profitability across penny-stocks + US equities + crypto BEFORE any real money touches a broker, with operator-explicit-go required to flip the real-money switch.

## Top-of-everything binding rule

**NO REAL MONEY TRADES WILL EVER OCCUR WITHOUT AN OPERATOR-EXPLICIT-GO MESSAGE.** Kill-switch defaults ON. Flipping OFF requires operator inbox message containing `GO REAL-MONEY <strategy> <max-equity-USD> <expiry-date>` AND a passed Phase-5 acceptance test.

## P0 scaffolded deliverables (this turn)

- Project directory: `D:\Sinister Sanctum\projects\sinister-sleight\` (8 subdirs: docs, src, tests, notebooks, backtests, models, data, src/sleight)
- 11 markdown docs (README, CLAUDE, MISSION, 7x docs/*)
- pyproject.toml (deps DECLARED not installed), .env.example, .gitignore
- src/sleight/{__init__.py, __main__.py} stub + tests/test_smoke.py
- Registered in `automations/session-templates/projects.json` picker.visible_keys + projects[] with tier=3, accent_color=gold, swarm=true, loop=true
- This charter brain entry + universal trading-bot-doctrine sibling brain entry
- PROGRESS file at `_shared-memory/PROGRESS/Sinister Sleight.md`
- Cross-agent inbox notes to Quantum + Generator lanes
- Row in `_shared-memory/OPERATOR-ACTION-QUEUE.md`

## 6-phase roadmap (full detail in projects/sinister-sleight/docs/06-roadmap.md)

| Phase | Goal | Exit criterion |
|---|---|---|
| P0 | Scaffold (this turn) | Project exists, registered, docs in place |
| P1 | Data layer | 5y S&P + 5y penny + 5y crypto in `data/raw/`; 50+ features per symbol < 5s on cached data |
| P2 | Backtest engine | VectorBT walk-forward harness; buy-and-hold benchmark reproducible from git SHA + data hash |
| P3 | Strategy v1 | M1 direction (AUC > 0.55), M3 regime (acc > 75%), ensemble beats buy-and-hold Sharpe by 0.3+ |
| P4 | Paper-trading live (90 day curriculum: $10k -> $100k -> $1M) | Sharpe > 1.0, max DD < 10%, win-rate > 50%, MISSION.md Outcome-1 thresholds met on C3 |
| P5 | Risk + portfolio + adversarial test | 100/100 adversarial test scenarios pass; risk manager live without breach |
| P6 | Real-money gate | Operator-explicit-go in inbox; first 5 real trades match paper expectations |

## 7 MISSION.md outcomes (binding acceptance criteria)

1. Paper-trade Sharpe > 1.0, max DD < 15%, win-rate > 50%, profit factor > 1.3, multi-regime
2. Multi-market: equities + penny + crypto + (P5+) options, each hits Outcome-1 thresholds
3. Self-training pipeline: 5y historical / walk-forward / versioned models / reproducible
4. Quantum win demonstrable OR documented negative result (no fake quantum-supremacy claims)
5. Penny-stock module: pump-and-dump red flags + halt detector + slippage model + size caps
6. Risk discipline: 1% per-trade VaR / 3% daily DD / 10% trailing-30d kill-switch / weekend caps / PDT check
7. Operator-gate to real money: explicit-go message + Phase-5 acceptance + max-equity cap

## Doctrine inheritance (this lane follows)

- no-bullshit-tested-before-claimed-doctrine-2026-05-23 (precise verbs; tested before claimed)
- forever-improve-review-doctrine-2026-05-24 (checkpoint every meaningful work unit)
- mesh-coordination-and-resource-lifecycle-2026-05-24 (Check before shared-file edits)
- sanctum-scope-discipline-2026-05-24 (Sleight owns trading; routes fleet-wide to sanctum)
- loop-mode-continuous-iteration-doctrine-2026-05-24 (in-turn iteration; 270s ScheduleWakeup cap)
- sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24 (P4+ dashboard inherits skeleton)
- gradual-growth-memory-push-eve-exe-ready-2026-05-24 (brain pushes to fleet-update channel)
- sinister-os-quantum-applicability-2026-05-24 (bidirectional scope rule; no quantum-for-quantum-sake)
- trading-bot-doctrine-2026-05-24 (sibling brain entry; universal trading-bot rules)

## Quantum-tools integration (sibling lane: sinister-snap-api-quantum)

Three candidate hooks; each gated by classical-beats-quantum pre-screen:
1. Quantum-kernel SVM for market regime classification (only if classical TF-IDF off-diag > 0.4)
2. QAOA for portfolio optimization (only if universe > 50 assets with hard constraints)
3. Amplitude estimation for option pricing (P5+ only; Qiskit Finance reference)

Default backend: `sim-local`. Cloud Wukong-180 budget gated behind [ASK] to sinister-snap-api-quantum lane owner.

## GitHub prior art (per cold-start step 9)

5 primary + 3 quantum-finance candidates: Freqtrade, Lean/QuantConnect, Backtrader, VectorBT, stable-baselines3+gym-anytrading; Qiskit Finance, PennyLane, zipline-reloaded. Full breakdown: `projects/sinister-sleight/docs/00-github-prior-art.md`.

## Composes with

- `_shared-memory/knowledge/trading-bot-doctrine-2026-05-24.md` (universal trading-bot doctrine, sibling to this charter)
- `projects/sinister-snap-api-quantum/` (quantum primitives via `seraphim` CLI)
- `projects/sinister-generator/` (P4+ dashboard imagery, cap 6 images per balance doctrine)
- `projects/sinister-dashboard-skeleton/` (P4+ dashboard UI inheritance, `--accent gold`)

## Anti-patterns named (NEVER for this lane)

- Real-money trade without operator-explicit-go (lane-fatal violation)
- Backtest in-sample bragging (only walk-forward OOS metrics count)
- Survivorship-biased penny universe (must include delisted tickers)
- Lookahead bias / data snooping / overfitting / no slippage
- Quantum-for-quantum-sake (must beat classical on measurable criterion)
- Hide kill-switch state (always visible on dashboard + CLI)
- Skip paper-trading 90-day curriculum to "save time"
- Trade larger after losses (martingale = ruin)
- Override drawdown circuit-breakers silently
