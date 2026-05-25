<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# MISSION.md — Sinister Sleight

## Operator brief (verbatim 2026-05-24 ~22:00Z)

> "prepare the sinister trade bot and create a proejct start for it. complie all knowledge you need to be the ebst trader in the world, full complete plans how you can self train, use our quantum toools to expand and how you are oing to train on penny stocks or fake envirments and build all systems needed to make a full auto trade bot that will make me money. review this entire site and start to gather and complie all knowledge you need. make a ture project setup, memory all of that and place it in eve exe and call it Sinister Sleight."

## TOP-OF-FILE WARNING — REAL-MONEY GATE

**NO REAL MONEY TRADES WILL EVER OCCUR WITHOUT AN OPERATOR-EXPLICIT-GO MESSAGE.** This is the loudest line in this entire project. Every agent spawned on this lane MUST honor this. The kill-switch defaults to ON; flipping it OFF requires an in-writing operator green-light referencing a specific trade ID AND a passed Phase-5 acceptance test (see `docs/06-roadmap.md`).

The bot is paper-trading-first by design. The bot can lose paper money for 90 days and that's expected (training). Real-money losses are not acceptable to anyone — operator or fleet.

## Mission expansion (measurable acceptance criteria)

The operator brief decomposes into 7 binding outcomes. Each has a measurable acceptance criterion. The project is "done in mission" only when ALL 7 are green on out-of-sample data.

### Outcome 1 — Paper-trade to profitability

**Criterion (measurable):** Over a 90-day continuous Alpaca paper-trading window, the bot achieves:
- Sharpe ratio (annualized) >= 1.0 net of simulated commissions + slippage
- Max drawdown <= 15% of starting paper equity
- Win rate >= 50% of closed positions
- Profit factor >= 1.3 (gross wins / gross losses)

Window must include at least one regime change (bull -> bear OR bear -> bull, as classified by the regime-detector module). If 90 days has no regime change, extend to first 30 days post-regime-change.

### Outcome 2 — Multi-market scope

**Criterion:** Demonstrated paper-trading PnL on each of the following markets in independent 30-day windows:
- US equities (S&P 500 constituents minimum)
- Penny stocks (sub-$5 with daily volume > 500K shares)
- Crypto (BTC/USD + ETH/USD via Alpaca crypto API)
- Options (covered calls + cash-secured puts only; no naked options; P5+ feature)

Each window must hit Outcome-1 thresholds independently.

### Outcome 3 — Self-training pipeline

**Criterion:** Reproducible self-training loop documented in `docs/02-self-training.md` that:
- Ingests 5 years of historical OHLCV for the target universe
- Walk-forward trains/validates (train T-2y / validate T-1y / live T)
- Produces a versioned model artifact in `models/` with metadata sidecar (model hash + training window + val metrics)
- Reruns end-to-end via single command (`python -m sleight train --strategy <name>`)

### Outcome 4 — Quantum integration (where it wins)

**Criterion:** At least one production strategy module consumes a Sinister Seraphim primitive AND demonstrates measurable improvement vs the classical baseline:
- Either: option pricing via amplitude estimation beats classical Monte Carlo on RMSE for >= 1000 simulated paths
- Or: portfolio optimization via QAOA beats classical mean-variance on Sharpe over the 90-day window
- Or: market-regime classifier via QBC (kernel SVM) beats classical TF-IDF SVM on a labeled regime dataset

If no quantum win is empirically demonstrable, the lane DOES NOT FAKE ONE — it documents the negative result per `sinister-os-quantum-applicability-2026-05-24` doctrine and uses classical.

### Outcome 5 — Penny-stock readiness

**Criterion:** Penny-stock strategy module includes ALL of:
- Pump-and-dump red-flag detector (volume spike > 5sigma + insider sell + paid-promotion email scan + SEC EDGAR 8-K filing check)
- Halt detector (subscribes to SEC SSR / LULD halt feeds)
- Slippage model calibrated to penny-stock illiquidity (>= 1% of ADV slippage for sub-$1 names)
- Position-size cap (1% of equity per penny-stock trade; max 5 concurrent penny positions)

### Outcome 6 — Risk discipline

**Criterion:** Risk manager enforces (no exceptions):
- 1% per-trade VaR (95% confidence, 1-day horizon)
- 3% daily drawdown circuit-breaker (auto-flatten all positions, halt new trades for the day)
- 10% trailing 30-day drawdown kill-switch (auto-flatten, halt indefinitely, operator inbox alert)
- Weekend exposure rule (cap weekend overnight gross exposure at 25% of equity for equities; crypto unaffected)
- Pre-trade PDT check (block trade if it would trigger PDT flag on a sub-$25k account)

Tested by 100-trade adversarial simulation that tries to violate each rule.

### Outcome 7 — Operator gate to real money

**Criterion:** Phase-5 acceptance test (see `docs/06-roadmap.md`) PASSED + operator-explicit-go message in `_shared-memory/inbox/sinister-sleight/` with content like "GO REAL-MONEY <strategy-name> <max-equity-USD> <expiry-date>".

The bot trades the lesser of (operator's max-equity, 1% of operator's total broker equity, $1000) on the first real day. Real-money trading is opt-in per strategy AND per max-equity ceiling; the bot NEVER autoscales beyond the operator-set ceiling without a new green-light message.

## Market scope (in-scope today; expandable)

In-scope from P1:
- US equities (NYSE / NASDAQ; long + short)
- Penny stocks (sub-$5, ADV > 500K)
- Crypto spot (BTC/ETH via Alpaca)

In-scope from P5:
- Options (covered calls / cash-secured puts only)

Out-of-scope (won't ship without operator-explicit redirect):
- Futures (CME / ICE)
- FX (spot FX)
- Naked options (unlimited downside)
- Leveraged ETFs as a primary strategy (allowed as hedges only)
- DEX / on-chain trading (separate lane if operator wants it)
- HFT (sub-second latency; out of scope for retail infra)

## Regulatory + legal disclaimers

- Not financial advice. Educational + research use only.
- Pattern-Day-Trader (PDT) rule: bot pre-checks; operator must maintain >= $25k in margin account to day-trade freely. Bot defaults to cash account behavior (T+2 settlement) until operator confirms margin status.
- Tax reporting: operator owns Form 8949 + Schedule D + wash-sale tracking; bot produces a CSV ledger but does NOT file taxes.
- Insider trading: bot has no insider information by design; news ingestion is public RSS / SEC EDGAR / Twitter sentiment only.
- Market manipulation: no spoofing, no layering, no wash trading; the strategy code review at P5 explicitly checks for these.
- Securities licensing: this is the operator's personal trading bot; not registered as an investment adviser; CANNOT take outside funds without SEC registration.

## Why "Sinister Sleight"

Sleight-of-hand: precise, unseen, technically demanding, looks like magic to outsiders, is actually skill + practice. The fleet's trading lane embodies this: small consistent edges compounded, never flashy, never reckless. The "Sinister" prefix ties to the fleet brand (Sinister Systems LLC).
