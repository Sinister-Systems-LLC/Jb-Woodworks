<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 01 — Architecture

## System overview (top-down)

```
                              +----------------------------+
                              |  OPERATOR (gate, kill-sw)  |
                              +-------------+--------------+
                                            |
                                            v
+-----------------+    +-----------------+    +--------------------+    +-----------------+
| DATA INGESTION  |--->| FEATURE ENGINE  |--->| STRATEGY ENSEMBLE  |--->| RISK MANAGER    |
| yfinance        |    | OHLCV ind / TA  |    | LLM-trader + ML +  |    | VaR / DD / PDT  |
| Alpaca paper    |    | news embeddings |    | RL agent + TA      |    | kill-switch     |
| Polygon (opt)   |    | regime detector |    | (signal blend)     |    +--------+--------+
| IEX (opt)       |    +-----------------+    +--------------------+             |
| SEC EDGAR       |                                                              v
+--------+--------+    +-----------------+    +--------------------+    +-----------------+
         |             | BACKTEST ENGINE |    | PORTFOLIO MANAGER  |--->| EXECUTION GW    |
         +------------>| vectorbt        |--->| Kelly-sized        |    | Alpaca paper -> |
                       | walk-forward    |    | corr-aware         |    | (P6: real)      |
                       +-----------------+    +--------------------+    +--------+--------+
                                                                                 |
                                                                                 v
                                                                       +-----------------+
                                                                       | POST-TRADE LEDGER|
                                                                       | PnL + attribution|
                                                                       | model-drift mon |
                                                                       +-----------------+
```

## Layer-by-layer

### 1. Data ingestion

**Sources (tiered by cost):**

| Tier | Source | Cost | Latency | Use |
|---|---|---|---|---|
| Free | yfinance | $0 | 15min delayed | historical OHLCV, fundamentals |
| Free | Alpaca paper data | $0 | real-time (paper) | live paper-trading quotes |
| Free | SEC EDGAR | $0 | T+0 filing day | 8-K / 10-Q / Form-4 insider |
| Paid | Polygon.io Starter | $29/mo | real-time | live trading + better tick data (P4+) |
| Paid | IEX Cloud | $9/mo | real-time | backup live feed |
| Free | CCXT (crypto) | $0 | real-time | crypto exchange aggregator |

**Operator decision point:** yfinance-free vs Polygon-paid for P1. Default = yfinance until rate-limited.

**Adapter interface:**

```python
class DataAdapter:
    def fetch_ohlcv(symbol, start, end, interval) -> pd.DataFrame: ...
    def fetch_fundamentals(symbol) -> dict: ...
    def stream_quotes(symbols, callback) -> None: ...  # live
```

All adapters yield the same canonical DataFrame schema (open/high/low/close/volume + UTC datetime index).

### 2. Feature engineering

- **Price features:** returns (1d/5d/20d), log-returns, realized vol, ATR, Bollinger %B
- **Technical indicators (ta-lib optional, pure-python fallback):** RSI, MACD, ADX, OBV, VWAP, Ichimoku
- **Cross-sectional:** rank within sector / market-cap bucket
- **News features:** embed headlines via Claude (per-day; cache to `data/news/`); sentiment score; surprise vs consensus
- **Regime features:** rolling-90d realized vol percentile, term-structure slope (VIX9D / VIX), trend strength
- **Calendar features:** day-of-week, days-to-earnings, days-to-FOMC, days-to-options-expiry

### 3. Strategy ensemble

3 sub-strategies, blended via weighted vote (weights walk-forward optimized).

**(a) LLM-as-trader (Claude reasoning):**
- Daily: feed Claude the watchlist's 5d OHLCV + latest 10 headlines per symbol + sector context + macro context
- Output: ranked conviction list with "BUY / HOLD / SELL / SHORT" + 1-line reason
- Cache responses to `data/llm-traders/<date>/` for replay + audit
- Cost discipline: per `sinister-generator` model — cap LLM cost at $5/day; surface to operator queue if exceeded

**(b) Classical ML (sklearn):**
- Gradient-boosting classifier (XGBoost or LightGBM) on feature vector -> next-day direction
- Walk-forward retrained monthly; calibration check before deploy
- Probability threshold tuned for precision (we'd rather pass than trade noise)

**(c) RL agent (stable-baselines3 PPO):**
- Custom gym env (see `docs/02-self-training.md`)
- Trained 1M timesteps on historical S&P + 200K on penny stocks
- Reward shaped to discourage excess turnover (deduct 5bps per trade)

**Ensemble blender:** softmax-weighted vote, weights = trailing-90d Sharpe of each strategy on out-of-sample.

### 4. Backtest engine

**Primary: VectorBT** for speed (vectorized; handles sweep workloads).
**Reference: Backtrader** for event-driven Phase-2 work.

Backtest run produces:
- `backtests/<run-id>/equity_curve.csv`
- `backtests/<run-id>/trades.csv`
- `backtests/<run-id>/metrics.json` (Sharpe, Sortino, Calmar, max DD, win-rate, profit factor, turnover)
- `backtests/<run-id>/report.html` (vectorbt-style dashboard)
- `backtests/<run-id>/meta.json` (strategy version, data window, params, git SHA)

**Walk-forward harness:**

```python
for fold in range(n_folds):
    train_window = (T - (n_folds - fold) * 365, T - (n_folds - fold - 1) * 365)
    val_window   = (T - (n_folds - fold - 1) * 365, T - (n_folds - fold - 2) * 365)
    model = train(train_window)
    metrics = backtest(model, val_window)
    accumulate(metrics)
return summarize(folds)
```

### 5. Paper-trading simulator

Two modes:
- **Offline simulator:** backtest engine running on cached historical data; instant.
- **Online paper:** Alpaca paper-trading API; real-time quotes + simulated fills + simulated slippage.

Online paper adds adversarial-fill model:
- Market orders: midpoint + 1bp slippage for liquid / 10bp for penny stocks
- Limit orders: only fill if quote crosses limit (no jumping the queue)
- Partial fills: simulated for any order > 0.5% of trailing-5min volume
- Halts: subscribe to SEC SSR / LULD feeds; freeze affected positions

### 6. Risk manager

See `docs/05-risk-and-circuit-breakers.md` for full rules. Architecture-wise:
- Pre-trade check: every order goes through `risk.precheck(order)` returning approve/reject/resize
- In-flight check: per-minute portfolio-level VaR re-estimation
- End-of-day check: drawdown breach -> circuit-breaker

### 7. Portfolio manager

- Kelly-fraction position sizer, CAPPED at 0.25 Kelly (per Edward Thorp / standard quant practice; full Kelly is too volatile)
- Correlation matrix on trailing 60d returns; penalize new positions correlated > 0.7 with existing
- Sector exposure cap: 25% max per sector
- Single-name exposure cap: 5% max per name
- Cash buffer: never deploy > 95% of equity

### 8. Execution gateway

Broker-agnostic interface:

```python
class Broker:
    def submit_order(symbol, qty, side, order_type, limit_price=None) -> OrderID: ...
    def cancel_order(order_id) -> bool: ...
    def get_positions() -> List[Position]: ...
    def get_account() -> Account: ...
```

Implementations:
- `AlpacaPaper` (P1-P5)
- `AlpacaLive` (P6, behind operator gate)
- (future) `IBKR` / `Schwab` if operator wants brokerage flexibility

### 9. Post-trade analytics

- Daily PnL report -> `_shared-memory/PROGRESS/Sinister Sleight.md` + dashboard
- Trade-by-trade attribution: which sub-strategy generated the signal, slippage vs expected, P&L
- Model drift detector: weekly KS test of current feature distribution vs training window; alert on > 0.2

### 10. Dashboard (P4+)

Inherits from `projects/sinister-dashboard-skeleton/` per fleet UI doctrine. `--accent gold` (financial). Pages:
- `/` overview: equity curve, today's PnL, open positions, kill-switch status
- `/strategies` per-strategy attribution + weights
- `/risk` VaR, drawdown, exposure breakdown
- `/trades` filterable trade log
- `/research` notebooks browser

## Quantum integration touchpoints

See `docs/04-quantum-integration.md`. Three candidate hooks:
- Strategy (b) ML -> swap classifier for quantum-kernel SVM (where classical loses on cluster-similar regime docs)
- Portfolio manager -> swap mean-variance for QAOA (where classical loses on 50+ asset universes with hard constraints)
- Options pricing (P5+) -> swap Black-Scholes-MC for amplitude estimation (RMSE win demonstrable per Qiskit Finance examples)

Per `sinister-os-quantum-applicability-2026-05-24` doctrine: each candidate measured against classical FIRST; only ship quantum if measurable win.

## What's deliberately NOT in this architecture

- HFT / sub-second execution (retail infra; not chasing latency)
- Custom FIX engine (Alpaca REST is fine)
- On-prem co-located servers (cloud only; latency-fair retail tier)
- Naked options / unlimited-downside strategies (risk doctrine)
- Crypto DEX trading (separate lane if operator wants)
