<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 02 — Self-training plan

> Operator brief includes: *"full complete plans how you can self train, use our quantum toools to expand and how you are oing to train on penny stocks or fake envirments"*.

## Training philosophy

The market is adversarial — every edge gets arbitraged out. Sleight trains in three regimes (historical / simulated / paper-live) and is REQUIRED to demonstrate walk-forward generalization, not just in-sample fit.

Five rules:
1. **Walk-forward only.** No simple train/test split. Train T-2y, validate T-1y, deploy T, re-train monthly.
2. **Out-of-sample is sacred.** OOS data is touched ONCE per model version; if we touch it twice and tune, that's overfitting.
3. **Multiple regimes required.** A model that worked 2017-2021 (low-vol bull) must also be tested on 2022 (rate-hike bear), 2020-Q1 (COVID crash), 2008-2009 (GFC if available).
4. **Adversarial scenarios mandatory.** Stress-tested against flash crashes, halt cascades, gap opens.
5. **Drift detection always on.** KS test on feature distributions; alert when distribution shifts > 0.2.

## Phase A — Historical backtest training (P1-P3)

### Data acquisition

| Universe | Source | Lookback | Cost |
|---|---|---|---|
| S&P 500 OHLCV | yfinance | 10y | $0 |
| NASDAQ 100 OHLCV | yfinance | 10y | $0 |
| Penny stocks (sub-$5, ADV > 500K) | yfinance bulk | 5y | $0 |
| Crypto (BTC/ETH/SOL) | CCXT or yfinance | 5y | $0 |
| Fundamentals (P/E, EPS, sector) | yfinance | 10y | $0 |
| News headlines | SEC EDGAR + RSS aggregators | 3y | $0 |

Acquisition script: `src/sleight/data/acquire.py` (P1 deliverable). Outputs to `data/raw/<universe>/<symbol>.parquet` (parquet = fast + small).

### Feature engineering pipeline

Output: `data/features/<universe>/<symbol>.parquet` with 50-100 features per row per day. Cached; recomputed only on feature-set version bump.

### Models trained at this phase

**Model M1 — Direction classifier (binary up/down next day):**
- Algo: LightGBM
- Features: 50 (price + TA + fundamentals + calendar)
- Target: sign of next-day close-to-close return
- Validation: walk-forward, 12 folds (1 month each)
- Success: AUC > 0.55 on average across folds (slightly better than coin-flip is enough at this stage)

**Model M2 — Return regressor:**
- Algo: XGBoost regressor
- Target: next-day return magnitude
- Used for position sizing (high-conviction = bigger position)
- Success: out-of-sample R^2 > 0.05 (yes, that's low; finance is hard)

**Model M3 — Regime classifier:**
- Algo: kmeans on rolling features (vol / trend / breadth) OR quantum-kernel SVM if classical < 0.3 cluster (per doctrine)
- 4 regimes: bull-quiet / bull-vol / bear-quiet / bear-vol
- Used as a meta-feature for M1/M2 + ensemble blender

## Phase B — RL simulation environment (P3)

Custom gym env in `src/sleight/envs/trading_env.py`.

```python
class TradingEnv(gymnasium.Env):
    """
    Observation space: Box(low=-1, high=1, shape=(window=20, n_features=50))
    Action space: Discrete(3) = {flat, long, short} OR Box(-1, 1, (1,)) for position size
    Reward: sharpe_of_realized_trade - 0.0005 * turnover_penalty
    """
```

**Why custom (not gym-anytrading default):**
- Reward shaping discourages turnover (gym-anytrading defaults reward PnL only -> RL agent overtrades)
- Slippage + commission modeled (gym-anytrading default ignores)
- Halt + gap-open scenarios injected (10% of training episodes are gap-up/down > 5%)
- Walk-forward train/val episodes (not random sampling -> overfit)

**Training recipe:**
- Algorithm: PPO (stable-baselines3)
- Timesteps: 1M on S&P, 200K on penny stocks (separate models per universe)
- Env-parallel: 8 envs in parallel
- Hardware: CPU only at first; GPU if needed for scaling
- Checkpoints: every 100K steps; best by val-Sharpe kept

## Phase C — Curriculum (paper-money progression)

Three stages, sequential, NO skipping:

### Stage C1 — Sandbox paper, $10k

- Backend: VectorBT OR Alpaca-paper with $10k starting equity
- Duration: 30 calendar days
- Strategies enabled: M1 + M3 (no ensemble blender yet)
- Pass criterion: positive PnL OR Sharpe > 0.5 (low bar; this is the "did it crash" stage)

### Stage C2 — Larger sandbox, $100k

- Backend: Alpaca-paper with $100k starting equity
- Duration: 30 calendar days
- Strategies enabled: M1 + M2 + M3 + ensemble blender
- Pass criterion: Sharpe > 1.0, max DD < 10%, win-rate > 50%

### Stage C3 — Pre-real paper, $1M

- Backend: Alpaca-paper with $1M starting equity
- Duration: 30 calendar days
- Strategies enabled: full ensemble + RL agent
- Pass criterion: ALL of MISSION.md Outcome-1 thresholds met
- This is the LAST stage before operator-gate for real money

Total curriculum: 90 calendar days of paper-trading before any real-money discussion can begin. Per MISSION.md, this is non-negotiable.

## Phase D — LLM-in-context strategy reasoning

The LLM-as-trader sub-strategy (Strategy a in `docs/01-architecture.md`) does NOT get "trained" in the gradient sense — Claude is the base model. Instead:

1. **Prompt engineering:** versioned prompts at `src/sleight/strategies/llm/prompts/v<N>.md`
2. **Few-shot context:** retrieved from `data/llm-traders/<date>/` cache of past good calls + bad calls
3. **A/B test:** monthly prompt-version bake-off on out-of-sample week; winner promoted to default
4. **Cost discipline:** see architecture doc Strategy (a); cap $5/day; surface if exceeded

## Phase E — Quantum-assisted training (where it wins)

See `docs/04-quantum-integration.md` for the doctrine.

Three candidate hooks where quantum might beat classical on training:

1. **Quantum-kernel SVM** for regime classification — only if classical TF-IDF off-diag > 0.4 (bidirectional scope rule from `sinister-os-quantum-applicability-2026-05-24`).
2. **QAOA portfolio optimization** for the position-sizer when universe > 50 assets with hard constraints (e.g., sector exposure caps + ESG screens).
3. **Amplitude estimation** for option pricing in P5+ options strategies (Qiskit Finance has reference implementations).

Cost discipline: default `backend='sim-local'`; cloud Wukong-180 budget gated behind operator [ASK].

## Phase F — Drift detection + retraining triggers

Continuous (every trading day after close):
1. Run KS test on today's feature distribution vs trailing-180d training distribution.
2. If KS statistic > 0.2 on > 5 features: alert operator + flag for retraining.
3. Auto-retrain monthly regardless (calendar trigger).
4. Auto-retrain on regime change (M3 regime-classifier flips).

Retrained model goes through walk-forward validation BEFORE replacing the live model. Replacement is logged + reversible (keep N-1 model in `models/_archive/` for 30 days).

## Anti-patterns (will NOT do)

- **In-sample bragging.** "97% accuracy on training data" means nothing.
- **Lookahead bias.** Use only data available AT time T to predict T+1.
- **Survivorship bias.** Penny stock universe must include delisted tickers; index constituents must reflect HISTORICAL membership.
- **Data snooping.** No "I tried 200 strategies and report the best" without Bonferroni correction or HOLD-OUT data.
- **Curve fitting.** Number of strategy params << number of OOS data points.
- **Slippage / commission ignored.** Every backtest includes realistic costs (1bp + per-share commission per Alpaca pricing).
- **Single regime test.** Always test across bull + bear + sideways minimum.
- **Backtesting on signals you can't trade live.** No "buy at the close" assuming you got the close (signal arrives at close; trade fills next open with slippage).

## Reproducibility

Every model version pinned by:
- Code git SHA (via git-rev-parse at training time)
- Data slice hash (sha256 of input parquet files)
- Library versions (frozen `requirements-lock.txt`)
- Random seeds (numpy + sklearn + torch + sb3 all seeded)
- Hardware (CPU model / GPU model logged)

All written to `models/<model-id>/meta.json` alongside the model artifact. A model that can't be reproduced is a model we don't deploy.
