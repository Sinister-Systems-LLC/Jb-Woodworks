<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Trading-bot doctrine (universal, fleet-wide)

> Created: 2026-05-24
> Status: standing-rule
> Tags: doctrine, trading, finance, backtest, risk, regulatory
> Origin: companion to `sinister-sleight-project-charter-2026-05-24.md`; applies to any fleet lane that touches market trading.

## Scope

Binding for `sinister-sleight` today; applicable to any future trading-class lane (FX, options-only, crypto-only, etc). If a non-sleight lane needs to trade, it inherits this doctrine before adding its own lane-specific rules.

## 10 universal rules

### 1. Paper before real (90-day minimum)

Every strategy paper-trades 90 calendar days minimum before real-money discussion. Paper period includes at least one regime change (bull -> bear OR vice-versa). No exceptions for "we're sure this one works".

### 2. Real-money gate is operator-explicit-go

Flipping real-money requires operator inbox message: `GO REAL-MONEY <strategy> <max-equity-USD> <expiry-date>` with signature line. Auto-re-engage kill-switch on -3% daily / -10% trailing-30d / expiry-date / operator KILL command.

### 3. Risk caps are hard

- Per-trade VaR: 1% of equity at 95% confidence
- Daily drawdown circuit-breaker: -3% (auto-flatten, halt until next session)
- Trailing-30d kill-switch: -10% (auto-flatten, indefinite halt, operator-only resume)
- Cash buffer: never deploy > 95% of equity
- Position cap per name: 5% of equity
- Sector cap: 25% of equity per GICS sector

These limits override every strategy signal. Strategy code that bypasses them = FAIL on review.

### 4. Walk-forward validation only

No simple train/test split. Train T-2y / validate T-1y / live T. Retrain monthly. Out-of-sample data touched ONCE per model version; if touched twice and tuned, that's overfitting.

### 5. The market is adversarial — design accordingly

- Every backtest includes realistic slippage + commissions
- Every strategy assumes the counterparty (market maker / HFT) is smarter
- Position sizing assumes 2x stop-loss as worst-case (gaps blow through)
- Pump-and-dump stocks have insiders selling INTO retail buys; recognize and avoid

### 6. Regulatory + legal discipline

- Not financial advice (educational + personal use only)
- PDT rule self-enforced (block trades that would trip on sub-$25k account)
- Wash-sale tracking via CSV ledger (operator owns Form 8949 / Schedule D filing)
- No insider information (public RSS / SEC EDGAR / Twitter public only)
- No spoofing / layering / wash trading / momentum-ignition (code review at P5)
- No outside funds without SEC investment-adviser registration

### 7. Quote stop-losses (best-effort, not guaranteed)

Stop-losses are best-effort. Gaps + halts can blow through. Position sizing assumes 2x stop-loss as worst-case loss. Never bet the farm on stops actually firing at the level you set.

### 8. No overfitting / no data snooping

- Number of strategy params << number of OOS data points
- Bonferroni correction when testing many hypotheses
- Honest reporting: report ALL strategies tested, not just the best
- Hold-out set untouched until final acceptance test

### 9. Drift detection always on

KS test on feature distributions daily; alert if > 0.2. Monthly auto-retrain regardless. Regime-change auto-retrain. Replacement model goes through walk-forward validation BEFORE replacing live.

### 10. Kill-switch UX is loud and accessible

- CLI: `python -m sleight kill-switch`
- Inbox: any message containing `KILL` triggers
- Dashboard: big red button on /overview
- Sanctum-broadcast: fleet-level can flatten all trading lanes

Kill-switch state visible on every dashboard view + every CLI command response. NEVER hide it.

## 5 measurable acceptance criteria for "this strategy works"

1. **Sharpe ratio (annualized) > 1.0** on out-of-sample data
2. **Max drawdown < 15%** of starting equity over the same window
3. **Win rate > 50%** of closed positions
4. **Profit factor > 1.3** (gross wins / gross losses)
5. **Multi-regime survival** — same thresholds met across bull + bear + sideways (at least 2 of 3)

A strategy that fails any one of these is NOT shipped to real-money. A strategy that passes all five is candidate for operator-gate review.

## Quantum integration policy

Per `sinister-os-quantum-applicability-2026-05-24` bidirectional scope rule:
- **DO use** quantum primitives where classical loses on a measurable criterion
- **DO NOT** ship quantum-for-quantum-sake when classical wins; document negative result honestly

Default backend: `sim-local`. Cloud Wukong-180 budget gated.

Three known hooks (Sleight's `docs/04-quantum-integration.md` for detail):
- Quantum-kernel SVM for regime classification (gated by classical TF-IDF off-diag > 0.4)
- QAOA for portfolio optimization (gated by universe > 50 with hard constraints)
- Amplitude estimation for option pricing (P5+ only)

## Composes with

- `sinister-sleight-project-charter-2026-05-24.md` (project charter, sibling)
- `sinister-os-quantum-applicability-2026-05-24.md` (quantum doctrine inheritance)
- `quantum-memory-kernel-fleet-action-items-2026-05-23.md` (production recipe)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (tested before claimed; precise verbs)
- `sanctioned-bypasses-doctrine-2026-05-21.md` (operator-gated bypasses)
- `forever-improve-review-doctrine-2026-05-24.md` (checkpoint cadence)

## Anti-patterns (lane-fatal if violated)

- Real-money without operator-explicit-go (lane-fatal)
- In-sample Sharpe bragging (lane-fatal credibility)
- Survivorship-biased universe (lane-fatal backtest validity)
- Hidden kill-switch state (lane-fatal trust)
- Trade larger after losses to "make it back" (martingale = ruin)
- Skip the 90-day paper-trading curriculum to "save time"
- Override drawdown circuit-breakers silently
- Quantum-for-quantum-sake marketing claims without measurable win
- Lookahead bias / data snooping / no slippage model
- Insider info / spoofing / wash trading / market manipulation
