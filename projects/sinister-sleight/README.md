<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Sinister Sleight :: full-auto trading bot lane

> Project root: `D:\Sinister Sanctum\projects\sinister-sleight\`
> Slug: `sinister-sleight` | Display: `Sinister Sleight` | Accent: gold (financial)
> Tier: T3 (new project, P0 scaffolded 2026-05-24)
> Persona: EVE (per `_shared-memory/knowledge/agent-identity-eve.md`)
> Status: P0 SCAFFOLDED — no trading code yet, no broker accounts wired, no money at risk

## Mission (one line)

Build a fully-autonomous, quantum-assisted trading bot that paper-trades to profitability across penny-stocks + US equities + crypto BEFORE any real money touches a broker, with operator-explicit-go required to flip the real-money switch.

## What this project is

Sinister Sleight is the fleet's algorithmic-trading lane. It composes:

- **Data layer** — yfinance / Alpaca / Polygon / IEX adapters (free-first, paid-when-justified)
- **Backtest engine** — Backtrader or VectorBT (P2 decision) for historical replay + walk-forward validation
- **Strategy layer** — hybrid LLM-as-trader (Claude reasoning over fundamentals + news) + classic ML (sklearn / stable-baselines3 RL agent) + technical-indicator filters (ta-lib optional)
- **Paper-trading simulator** — Alpaca paper API for live paper-trading with realistic slippage / partial fills / halts
- **Risk manager** — per-trade VaR, daily drawdown circuit-breaker, weekend exposure rule, kill-switch
- **Portfolio manager** — position sizing (Kelly fraction capped at 0.25 Kelly), correlation-aware
- **Execution gateway** — broker-agnostic interface (paper-first; real only via operator gate)
- **Post-trade analytics** — daily PnL report, attribution, model drift detector
- **Quantum integration** — consumes sibling `sinister-snap-api-quantum` for option pricing (amplitude estimation), portfolio optimization (QAOA), market regime classification (VQE) WHERE classical doesn't already win (per `sinister-os-quantum-applicability-2026-05-24` doctrine)

## What this project is NOT (yet)

- NOT a working trader (P0 = structure, docs, registry only)
- NOT licensed for financial advice (educational + personal-use only)
- NOT connected to any real broker (paper-trading first)
- NOT a get-rich-quick scheme (paper-trade 90 days before real money; expect losses during training)

## Hard disclaimers

This software is provided as-is for educational and research purposes. It is NOT financial advice. Past backtest performance is NOT indicative of future returns. The operator (and only the operator) authorizes any real-money trading. The fleet of agents working on this lane will NEVER flip the real-money switch without an explicit, in-writing operator green-light AND a passed Phase-5 acceptance test.

Pattern-Day-Trader (PDT) rules, wash-sale rules, tax obligations (Form 8949, Schedule D), and SEC/FINRA reporting are the OPERATOR'S responsibility. The bot can produce reports; it cannot file them.

## Quick start (after P1 ships)

```bash
# Paper-trading smoke test (planned for P1)
python -m sleight backtest --strategy momentum --symbols SPY,QQQ --start 2024-01-01 --end 2025-01-01

# Paper-trade live (planned for P4, requires Alpaca paper key in .env)
python -m sleight paper-trade --strategy ensemble --portfolio sample
```

## Files in this project

| Path | Status | Purpose |
|---|---|---|
| `README.md` (this) | scaffolded | Project overview |
| `CLAUDE.md` | scaffolded | Per-agent cold-start protocol |
| `MISSION.md` | scaffolded | Operator brief verbatim + measurable acceptance criteria + disclaimers |
| `docs/00-github-prior-art.md` | scaffolded | GitHub-first sourcing — 5 candidate repos to borrow from |
| `docs/01-architecture.md` | scaffolded | Full system design |
| `docs/02-self-training.md` | scaffolded | Self-training plan (historical / RL / walk-forward / curriculum) |
| `docs/03-penny-stocks-fake-env.md` | scaffolded | Penny-stock specifics + fake env design |
| `docs/04-quantum-integration.md` | scaffolded | Quantum primitives (cite sibling lane) |
| `docs/05-risk-and-circuit-breakers.md` | scaffolded | Risk doc + kill-switch + regulatory disclaimers |
| `docs/06-roadmap.md` | scaffolded | 6-phase roadmap with measurable exit criteria |
| `src/` | scaffolded | Python package skeleton (`__main__.py` TODO) |
| `data/` | scaffolded | Historical + live data (gitignored for large files) |
| `notebooks/` | scaffolded | Jupyter walk-throughs |
| `backtests/` | scaffolded | Backtest run artifacts |
| `models/` | scaffolded | Trained model artifacts (gitignored) |
| `tests/` | scaffolded | pytest skeleton |
| `pyproject.toml` | scaffolded | Deps declared; not installed |
| `.gitignore` | scaffolded | Python defaults + data/* + models/*.pkl + .env |
| `.env.example` | scaffolded | Broker key shape (no real keys) |

## Composes with

- `tools/sinister-seraphim/` — quantum primitives (sibling-owned at `sinister-snap-api-quantum`)
- `projects/sinister-generator/` — dashboard imagery (banners, brand visuals) when P4 ships UI
- `projects/sinister-dashboard-skeleton/` — UI base for the PnL / position dashboard
- `_shared-memory/knowledge/sinister-sleight-project-charter-2026-05-24.md` — project charter
- `_shared-memory/knowledge/trading-bot-doctrine-2026-05-24.md` — universal trading-bot doctrine

## Lane metadata

- Branch: `agent/sinister-sleight/<short-topic>`
- Heartbeat: `_shared-memory/heartbeats/sinister-sleight.json`
- PROGRESS: `_shared-memory/PROGRESS/Sinister Sleight.md`
- Resume-points: `_shared-memory/resume-points/Sinister Sleight/<UTC>.json`
- Inbox: `_shared-memory/inbox/sinister-sleight/`
