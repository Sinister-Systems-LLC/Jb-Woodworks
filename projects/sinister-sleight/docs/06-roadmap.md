<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 06 — Roadmap (6 phases, measurable exit criteria)

## Status

- **P0** — SCAFFOLDED 2026-05-24 (this turn — project structure + docs + registry)
- **P1** — QUEUED
- **P2** — QUEUED
- **P3** — QUEUED
- **P4** — QUEUED
- **P5** — QUEUED
- **P6** — QUEUED (operator-explicit-go required)

## P0 — Scaffold (this turn)

**Goal:** Project exists, registered, doctrine codified, no code yet.

**Deliverables (verified this turn):**
- [x] Project directory tree at `projects/sinister-sleight/` (8 subdirs)
- [x] README.md + CLAUDE.md + MISSION.md
- [x] docs/00-github-prior-art.md through docs/06-roadmap.md
- [x] pyproject.toml + .env.example + .gitignore
- [x] src/ stub + tests/ stub
- [x] Registered in `automations/session-templates/projects.json`
- [x] Brain entries: charter + universal trading-bot doctrine
- [x] PROGRESS file initial milestone
- [x] Cross-agent inbox notes (Quantum + Generator)
- [x] OPERATOR-ACTION-QUEUE row

**Exit criterion:** Operator can spawn `eve.exe -> sinister-sleight` and the new agent's cold-start finds all docs.

## P1 — Data layer (1-2 weeks)

**Goal:** Ingest OHLCV + fundamentals + news for the target universe, cached + queryable.

**Deliverables:**
- [ ] `src/sleight/data/adapters.py` with `YFinanceAdapter`, `AlpacaPaperAdapter`, `SECEdgarAdapter`
- [ ] `src/sleight/data/acquire.py` CLI that pulls 10y S&P + 5y penny universe to `data/raw/`
- [ ] `src/sleight/data/features.py` feature engineering pipeline -> `data/features/`
- [ ] pytest coverage > 70% for data module
- [ ] Smoke command: `python -m sleight data fetch --universe sp500 --years 1` exit 0 with parquet output

**Exit criterion:**
- 5y of S&P + 5y of penny universe + 5y BTC/ETH in `data/raw/`, total size logged
- 50+ features computed for any symbol in < 5s on cached data
- News headlines for last 3y indexed
- Operator decision on yfinance-free vs Polygon-paid resolved (default yfinance until rate-limited)

## P2 — Backtest engine (2-3 weeks)

**Goal:** Working VectorBT-based walk-forward backtester producing reproducible metrics + reports.

**Deliverables:**
- [ ] `src/sleight/backtest/engine.py` thin VectorBT wrapper
- [ ] `src/sleight/backtest/walkforward.py` walk-forward harness (T-2y / T-1y / T pattern)
- [ ] `src/sleight/backtest/metrics.py` computes Sharpe / Sortino / Calmar / max DD / win-rate / profit-factor / turnover
- [ ] `src/sleight/backtest/report.py` HTML report generator
- [ ] Single-command CLI: `python -m sleight backtest --strategy buy-and-hold --universe sp500 --start 2020-01-01 --end 2024-01-01`
- [ ] Backtest run artifacts in `backtests/<run-id>/`

**Exit criterion:**
- Buy-and-hold benchmark backtested on 5y S&P with all metrics in `backtests/<run-id>/metrics.json`
- Walk-forward 12-fold yields stable Sharpe estimate (95% CI < 0.3 width)
- Single command reproduces backtest from git SHA + data hash

## P3 — Strategy v1 (3-4 weeks)

**Goal:** First Sleight strategies trained + backtested. M1 direction classifier + M3 regime classifier minimum.

**Deliverables:**
- [ ] `src/sleight/strategies/classical_ml.py` LightGBM direction classifier
- [ ] `src/sleight/strategies/regime.py` 4-regime classifier
- [ ] `src/sleight/strategies/llm_trader.py` Claude-based reasoning (with cost discipline)
- [ ] `src/sleight/strategies/ensemble.py` blender
- [ ] `src/sleight/envs/trading_env.py` custom gym env
- [ ] `src/sleight/envs/penny_replay_env.py` penny replay sandbox
- [ ] `src/sleight/envs/synth_pump_dump_env.py` synthetic pump-dump generator
- [ ] `src/sleight/penny/red_flags.py` 10-signal red-flag detector
- [ ] Reproducible model artifacts in `models/<model-id>/`
- [ ] Quantum hook 1 (regime SVM) sim-local prototype if classical < 0.3 cluster

**Exit criterion:**
- M1 direction classifier: walk-forward AUC > 0.55 across 12 folds
- M3 regime classifier: out-of-sample regime label accuracy > 75% on labeled 1y dataset
- Ensemble backtest on 5y S&P beats buy-and-hold Sharpe by 0.3+ on out-of-sample
- All models reproducible per `models/<id>/meta.json` schema

## P4 — Paper-trading live (4-6 weeks, includes curriculum stages)

**Goal:** Live paper-trading on Alpaca for 90-day curriculum (C1 $10k / C2 $100k / C3 $1M).

**Deliverables:**
- [ ] `src/sleight/broker/alpaca_paper.py` Alpaca paper integration
- [ ] `src/sleight/execution/gateway.py` broker-agnostic execution layer
- [ ] `src/sleight/portfolio/manager.py` Kelly-fraction sizer + correlation-aware
- [ ] Dashboard scaffold at `dashboard/` inheriting from `projects/sinister-dashboard-skeleton/`
- [ ] Daily PnL reporter -> PROGRESS + dashboard + operator inbox
- [ ] Live runs through C1 -> C2 -> C3 stages per `docs/02-self-training.md`

**Exit criterion:**
- C1 (30 days, $10k): positive PnL OR Sharpe > 0.5
- C2 (30 days, $100k): Sharpe > 1.0, max DD < 10%, win-rate > 50%
- C3 (30 days, $1M): ALL Outcome-1 thresholds from MISSION.md met
- Dashboard live at /sleight on operator's local

## P5 — Risk manager + portfolio + acceptance test (3-4 weeks)

**Goal:** Full risk manager shipped + 100-scenario adversarial test passed.

**Deliverables:**
- [ ] `src/sleight/risk/manager.py` enforces all 10 limits from `docs/05-risk-and-circuit-breakers.md`
- [ ] `src/sleight/risk/kill_switch.py` operator-controllable kill-switch
- [ ] `tests/adversarial/test_risk_suite.py` 100-scenario adversarial test suite
- [ ] `src/sleight/options/` covered-calls + cash-secured-puts modules (optional, gated by operator)
- [ ] Quantum hook 2 (QAOA portfolio optimizer) sim-local if universe > 50 assets
- [ ] Quantum hook 3 (amplitude estimation option pricing) sim-local if options module enabled

**Exit criterion:**
- 100/100 adversarial test scenarios pass
- Risk manager has been live during all of P4 curriculum without a breach
- All 7 MISSION.md outcomes have been measured and reported

## P6 — Real-money gate (operator decision)

**Goal:** Operator-explicit-go to flip the kill-switch + first real-money trades.

**Deliverables:**
- [ ] Operator green-light message in `_shared-memory/inbox/sinister-sleight/` with format `GO REAL-MONEY <strategy> <max-equity-USD> <expiry-date>`
- [ ] `src/sleight/broker/alpaca_live.py` real Alpaca integration (behind kill-switch gate)
- [ ] Per-strategy real-money rollout (smallest first; 1% of broker equity OR $1000, whichever less)
- [ ] Daily operator-facing PnL + risk report
- [ ] Tax-export CSV generator for Form 8949 / Schedule D

**Exit criterion:**
- Operator green-light in inbox with valid signature
- First 5 real-money trades match paper-trading expectations within reasonable slippage tolerance
- 30 days real-money with no risk breaches
- Operator satisfied with reports + analytics

## Beyond P6 (not roadmapped; operator-driven)

- Multi-broker support (IBKR / Schwab / Fidelity)
- Additional asset classes (futures / FX) — operator-explicit-add
- Multi-strategy capital allocation (between Sleight strategies)
- External data sources (alt-data: satellite / credit-card / footfall)
- Cross-lane integration (Sleight signal -> Sinister Panel dashboard widget)
