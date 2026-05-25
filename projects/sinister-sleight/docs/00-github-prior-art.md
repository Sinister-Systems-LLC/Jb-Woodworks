<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 00 — GitHub prior art (sourcing-first, per Sanctum cold-start step 9)

> Per CLAUDE.md hard-canonical 2026-05-24: *"everytimg we start a porject or look for complex feature i want us to always aerach giuthub for pre madecode that we can use and then build ours based off of per project to save time. i want everything to be as speeedy efficent and concise as possible"*.

This doc is the operator-facing surface listing the high-star GitHub trading-bot projects Sleight will study + selectively borrow from before writing custom code. The standing rule (per `github-first-sourcing-doctrine-2026-05-24`): borrow, don't reinvent; cite, don't strip.

## Candidate list (5 primary + 3 quantum-finance)

### 1. Freqtrade — `freqtrade/freqtrade`

- **What:** Crypto-first algo trading bot, Python, very mature (10+ years), strong community.
- **Why look:** Excellent reference for: strategy interface design, backtest engine architecture, paper + live broker abstraction, telegram bot integration pattern. The strategy plugin model is exemplary.
- **Borrow:** Strategy interface shape + hyperopt module + telegram-bot reporting layer.
- **Skip:** Crypto-exchange-specific adapters (we use Alpaca); the freqtrade-UI (we'll inherit from dashboard-skeleton).
- **License:** GPLv3 (compatibility check needed before code copy; reference + adapt is fine).

### 2. Lean / QuantConnect — `QuantConnect/Lean`

- **What:** C#-first institutional-grade algo engine; Python interface available. Used by professional quants.
- **Why look:** Best-in-class backtest engine + portfolio construction primitives + universe selection model. Walk-forward / cross-validation primitives are mature.
- **Borrow:** Universe selection pattern, portfolio construction class hierarchy, alpha/risk/execution model separation.
- **Skip:** The C# core (we're Python); the QuantConnect Cloud lock-in.
- **License:** Apache-2.0 (compatible).

### 3. Backtrader — `mementum/backtrader`

- **What:** Python backtest framework, event-driven, very flexible.
- **Why look:** Reference architecture for an event-driven backtest engine. Battle-tested.
- **Borrow:** Cerebro engine pattern, line-based indicator system, analyzers (Sharpe / SQN / Calmar).
- **Skip:** The visualization layer (we use our skeleton); the live trading adapters (we use Alpaca directly).
- **License:** GPLv3.

### 4. VectorBT — `polakowo/vectorbt`

- **What:** Vectorized backtesting on top of NumPy/Pandas; FAST (1000x backtrader for grid searches).
- **Why look:** Fastest backtester for hyperparameter sweeps + Monte Carlo robustness tests.
- **Borrow:** The vectorized portfolio class for sweep-class workloads (hyperopt phases).
- **Skip:** Their Plotly default dashboards (we use skeleton).
- **License:** Apache-2.0 (note: VectorBT Pro is paid; we use VectorBT free unless operator authorizes Pro).

### 5. Stable-Baselines3 examples — `DLR-RM/stable-baselines3` + `AminHP/gym-anytrading`

- **What:** SB3 = canonical RL algorithm library; gym-anytrading = trading-specific gym envs.
- **Why look:** Reference RL trader implementations (PPO / A2C / DQN against OHLCV). Custom env design is well-documented.
- **Borrow:** PPO trader baseline, gym env class shape, observation space design (windowed OHLCV + indicators).
- **Skip:** Their default reward functions (we'll design Sleight-specific reward based on Sharpe-of-trade vs raw PnL to discourage YOLO trades).
- **License:** MIT (SB3), MIT (gym-anytrading).

### Quantum-finance candidates

### 6. Qiskit Finance — `Qiskit/qiskit-finance`

- **What:** IBM's quantum-finance primitives: amplitude estimation for option pricing, QAOA for portfolio optimization, quantum-kernel SVM for regime classification.
- **Why look:** First-party reference implementations of the 3 quantum primitives Sleight might use.
- **Borrow:** API patterns for amplitude estimation + QAOA portfolio optimizer. Adapt to use Sinister Seraphim's sim-local backend.
- **Skip:** Their hardware-specific backends (we go through Seraphim).
- **License:** Apache-2.0.

### 7. PennyLane — `PennyLaneAI/pennylane` + tutorials

- **What:** Quantum ML library with differentiable quantum circuits. Hybrid quantum-classical training natural.
- **Why look:** Reference for variational quantum classifiers on financial time series.
- **Borrow:** VQC tutorial code adapted to regime classification on 1y of S&P regimes.
- **Skip:** PennyLane-only hardware backends (compose with Seraphim).
- **License:** Apache-2.0.

### 8. zipline-reloaded — `stefan-jansen/zipline-reloaded`

- **What:** Community-maintained fork of Quantopian's Zipline. Still alive after Quantopian shutdown.
- **Why look:** Reference for the pipeline API (factor research / cross-sectional alpha factors).
- **Borrow:** Pipeline API pattern for factor research.
- **Skip:** Quantopian-bundles (we use yfinance / Alpaca direct).
- **License:** Apache-2.0.

## Borrow protocol (per Sanctum external-imports doctrine)

For each project actually borrowed from:
1. Add a row to `_shared-memory/external-imports/CANDIDATES.md` with: repo URL, SHA pinned, license, what we borrow, why we DON'T just use it as a dep.
2. If we copy code: header with `Adapted from <repo> <sha> under <license>` + RKOJ-ELENO authorship for our additions.
3. If we use as dep: pin to a SHA / tagged version in `pyproject.toml`, never `latest`.

## Verdict for P1

Recommended path for P1 (data layer + first backtest):
- Use **VectorBT** as the backtest engine (speed for sweep workloads).
- Reference **Backtrader** patterns for the event-driven Cerebro shape (Phase 2 ensemble).
- Reference **Freqtrade** for strategy plugin interface design.
- DEFER **Lean** / **Qiskit Finance** / **PennyLane** / **SB3** / **zipline-reloaded** until their respective phases (P3 / P3+ quantum / P3 RL).

Operator decision needed: VectorBT free vs VectorBT Pro ($400/yr). Default = free; revisit if grid-search speed becomes bottleneck.
