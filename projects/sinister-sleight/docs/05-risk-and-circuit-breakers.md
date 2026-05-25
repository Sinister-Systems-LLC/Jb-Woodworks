<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 05 — Risk + circuit breakers

> The risk manager is the single most important component. A profitable strategy with broken risk management goes to zero. A mediocre strategy with disciplined risk management survives to compound.

## Risk hierarchy (every limit applies)

1. Per-trade limit
2. Per-symbol exposure limit
3. Per-sector exposure limit
4. Daily drawdown limit
5. Weekly drawdown limit
6. Trailing-30-day drawdown kill-switch
7. Cash-buffer minimum
8. Weekend / overnight exposure limit
9. Pre-trade PDT compliance check
10. Real-money kill-switch (operator-only)

## Specific limits (the contract)

### Per-trade limit
- **VaR cap:** 1% of equity at 95% confidence, 1-day horizon
- Computed from trailing-60d realized vol of the symbol
- If estimated VaR > 1%: resize position downward OR reject if can't fit

### Per-symbol exposure
- **Max position size:** 5% of equity per name
- Includes both long and short (gross position)

### Per-sector exposure
- **Max sector exposure:** 25% of equity per GICS sector
- Sleight refuses to add positions if would breach

### Daily drawdown
- **Circuit-breaker at -3% daily PnL** (mark-to-market vs start-of-day equity)
- Action: flatten ALL positions via market orders, halt new trades until next session
- Resume next trading day with `risk_state = caution` (position sizes halved for 1 day)

### Weekly drawdown
- **Halt new trades at -5% weekly PnL**
- Resume Monday with caution mode
- Operator inbox alert

### Trailing-30-day drawdown kill-switch
- **Kill-switch at -10% trailing-30d PnL**
- Action: flatten + halt indefinitely
- Operator-only resume (manual `risk-resume` command)

### Cash buffer
- **Never deploy > 95% of equity**
- 5% always cash for opportunistic / margin call buffer

### Weekend / overnight exposure
- **Equities weekend exposure cap:** 25% of equity gross
- Penny stocks: 0% weekend (always flat Friday EOD)
- Crypto: unaffected (24/7 markets)
- Options: 0% expiring within 7 days of close on Friday

### PDT (Pattern Day Trader) compliance
- Pre-trade check: would this trade trigger the PDT rule on a sub-$25k account?
- If account < $25k: bot operates as cash account (T+2 settlement; max 3 day-trades per rolling 5 days)
- If account >= $25k margin: free to day-trade
- Account class detected from broker API at session start; verified daily

### Real-money kill-switch
- **Default state: ON (no real trades)**
- **Flip OFF requires:** operator message in `_shared-memory/inbox/sinister-sleight/` containing `GO REAL-MONEY <strategy> <max-equity-USD> <expiry-date>` + signature line `signed: <operator-name>`
- **Auto-re-engage:** at expiry-date OR on -3% daily drawdown OR on operator command `KILL REAL-MONEY`
- **Verification:** every spawned Sleight agent verifies `risk.real_money_enabled == False` on cold-start; raises if True without valid GO message in inbox

## Adversarial test suite (P5 acceptance gate)

Before any real-money discussion, the risk manager passes this 100-scenario adversarial test:

| Test class | Count | Pass criterion |
|---|---|---|
| Per-trade VaR breach attempt | 20 | All resized OR rejected |
| Daily drawdown breach (slow grind) | 10 | Circuit-breaker fires AT -3.0% ±0.1% |
| Daily drawdown breach (flash crash) | 10 | Circuit-breaker fires within 60s of breach |
| Weekend exposure cap test | 5 | All positions flat-or-capped by Friday 15:55 ET |
| Halt during open position | 10 | No panic-sell; alert raised |
| PDT-rule trip attempt | 10 | All blocked pre-trade |
| Gap-down 5% open | 5 | Stop-losses honored, NOT skipped |
| Real-money switch bypass attempt | 10 | All rejected with proper error |
| Quantum cost overrun | 5 | Sim-local fallback fires |
| Broker API failure | 5 | Retry with exponential backoff; alert after 3 failures |
| Data-feed staleness | 10 | Halt new trades if feed > 60s stale |

Test harness: `tests/adversarial/test_risk_suite.py` (P5 deliverable). 100/100 PASS required for real-money gate.

## Regulatory disclaimers (binding for the project)

1. **Not financial advice.** This software is for personal use of the operator. No outside funds. Not registered as investment adviser.
2. **PDT rule self-enforced.** Operator owns the broker account; bot only constrains itself.
3. **Wash-sale tracking.** Bot produces a CSV ledger; operator owns Form 8949 + Schedule D filing.
4. **No insider trading.** All news ingestion is public (RSS / SEC EDGAR / Twitter public feeds). No NDAs / private chats / leaked info.
5. **No market manipulation.** Strategy code at P5 acceptance test explicitly reviewed for: spoofing, layering, wash trading, momentum-ignition patterns. Any such pattern = FAIL.
6. **Crypto compliance.** Crypto trading subject to wash-sale-rule ambiguity (not currently applied to crypto per IRS but pending); bot logs all crypto trades to enable retroactive reclassification.
7. **Options approval level.** Operator must have Tier-2 options approval (covered calls / cash-secured puts) on broker before P5 ships; bot does NOT enable options module otherwise.
8. **AUP compliance.** No use of bot against any party / asset operator does not personally own.

## Kill-switch UX

Operator can invoke kill-switch via:
1. CLI: `python -m sleight kill-switch` (drops a file at `data/kill-switch.lock`; bot polls every second)
2. Inbox message: any message in `_shared-memory/inbox/sinister-sleight/` containing `KILL` triggers
3. Dashboard button (P4+): big red button on /overview page
4. Sanctum-broadcast: a sanctum-level kill-switch can flatten all fleet trading agents

Kill-switch action: flatten ALL positions via market orders (accept slippage), cancel ALL pending orders, halt indefinitely, log to PROGRESS, alert operator.

## Anti-patterns (will NOT do)

- **Skip risk checks for "small" trades.** Every trade goes through the risk manager.
- **Override drawdown circuit-breakers silently.** Operator-only override; logged + announced.
- **Hide real-money switch state.** Status visible on every dashboard view + every CLI command response.
- **Pretend a stop-loss is a hard stop.** Stops are best-effort; gaps can blow through. Position sizing assumes 2x stop-loss as worst-case.
- **Trade larger after losses to "make it back".** Martingale = ruin. Position size based on equity, not on emotion.
- **Ship a "smarter" risk manager that knows when to ignore limits.** Limits are limits.
