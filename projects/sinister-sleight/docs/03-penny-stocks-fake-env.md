<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 03 — Penny stocks + fake environments

> Operator brief: *"how you are oing to train on penny stocks or fake envirments"*.

## Why penny stocks need special handling

Penny stocks (sub-$5; often sub-$1) are NOT mini-S&P-500 stocks. They behave fundamentally differently:

- **Liquidity is thin.** Average daily volume often < 1M shares; bid-ask spreads can be 5-20%.
- **Pump-and-dump dominates.** Coordinated promotion -> retail buys -> insiders sell -> price collapses. Recognizing this is THE single most important penny-stock skill.
- **News dominates fundamentals.** A single press release can 10x or rug a penny stock in minutes.
- **Halts are frequent.** SEC SSR / LULD circuit-breakers fire often; trapped positions are common.
- **Manipulators are present.** OTC market makers, paid promoters, naked short concerns, regulation T-T+2 settlement matters.
- **Survivorship bias is brutal.** Of the penny universe 5y ago, many delisted, bankrupted, or reverse-split. Training data MUST include these.

## The bagholder problem (and how to avoid being it)

**Bagholder = retail trader who buys the pump and holds through the dump because of cognitive bias.**

Sleight's penny-stock module is designed FIRST to avoid being the bagholder, SECOND to identify legitimate momentum.

### Pump-and-dump red flags (auto-detected; if 3+ fire, ABSTAIN)

1. **Volume spike > 5 sigma** above trailing-90d mean WITHOUT a justifying 8-K / 10-Q filing within 24h
2. **Insider sell within 30 days** (Form 4 filings; SEC EDGAR)
3. **Paid-promotion email scan** (sub-services: Stockwire / Promotionstocksecrets / known scammer lists; cache to `data/paid-promo-blacklist/`)
4. **SEC 8-K within 7 days announcing share dilution** (S-1 / S-3 filings; convertible note triggers)
5. **Reverse-split history within 12 months** (penny stocks often reverse-split to avoid delisting then re-collapse)
6. **Insiders own < 5% post-dilution** (no skin in game)
7. **Float < 5M shares** (easily manipulable)
8. **OTC tier "Pink No Information"** (essentially no disclosure; AVOID entirely)
9. **Twitter / Reddit / Discord coordinated mentions spike** (sub-services for sentiment; track unique-author count, not raw mention count)
10. **Bid-ask spread > 5% of midpoint** (cost-of-trade > expected edge)

Implementation: `src/sleight/penny/red_flags.py` (P3+ deliverable).

### Legitimate momentum signals (need 2+ to enter)

1. **Quarter-over-quarter revenue growth > 50%** (real business, not just hype)
2. **Insider BUY within 30 days** (positive Form 4)
3. **Sector tailwind** (peer companies also rising; not isolated pump)
4. **Liquidity ramp** (volume growing organically over weeks, not a 1-day spike)
5. **Float lock-up expiring soon WITHOUT insider selling** (suggests confidence)
6. **News on credible outlet** (Reuters / Bloomberg / WSJ, not stockwire press release)
7. **Short interest > 20% + ramp in price** (potential squeeze, but careful)

## Sleight penny-stock strategy

**Entry rules:**
- 0 red flags fire AND 2+ momentum signals fire
- Position size: 1% of equity max
- Stop-loss: -8% from entry (penny stocks are volatile; tighter stop = whipsawed out)
- Take-profit: 20% gain OR end-of-week, whichever first (don't get greedy)

**Exit rules:**
- Stop-loss hit -> immediate exit (market order)
- 20% gain -> trailing 5% stop
- End-of-week -> close all penny positions (no weekend exposure)
- Halt detected -> attempt cancel pending orders; alert operator
- Any red flag fires DURING the position -> immediate exit

**Hard caps:**
- Max 5 concurrent penny positions
- Max 5% of equity in penny stocks total
- Daily penny PnL stop: -2% of equity -> halt new penny trades for the day

## The fake environment (training sandbox)

**Why we need a fake env:** real penny-stock data has selection bias (we see the survivors); we want to train against scenarios INCLUDING the rugged ones.

### Sandbox V1 — Historical replay with realism

- Replays historical penny OHLCV at 1-minute resolution
- Adds simulated slippage proportional to 1/ADV (illiquid -> high slippage)
- Adds simulated partial fills if order > 0.5% of trailing-5min volume
- Adds simulated halts on real historical halt dates (SEC SSR + LULD records)
- Survivorship-bias correction: includes delisted tickers (CRSP / Quandl penny universe)

Implementation: `src/sleight/envs/penny_replay_env.py` (P3 deliverable).

### Sandbox V2 — Synthetic pump-and-dump generator

- Procedurally generates pump-and-dump price paths using known statistical fingerprints
- Parameters: pump magnitude, pump duration, dump speed, news-event timing
- Trains the red-flag detector + adversarial-defense modules
- Survives as "stress-test" suite even after V1 paper-trading

Pseudocode:
```python
def generate_pump_dump(seed):
    rng = np.random.default_rng(seed)
    # Pump phase: 3-5 day exponential ramp with volume spike
    pump_days = rng.integers(3, 6)
    pump_ramp = np.cumprod(1 + rng.normal(0.05, 0.02, pump_days))
    # Dump phase: 1-2 day collapse to baseline
    dump_days = rng.integers(1, 3)
    dump_ramp = np.cumprod(1 - rng.uniform(0.10, 0.30, dump_days))
    return concatenate(pump_ramp, dump_ramp)
```

Implementation: `src/sleight/envs/synth_pump_dump_env.py` (P3 deliverable).

### Sandbox V3 — Adversarial market-maker simulator

- Models the OTC market-maker as an opponent
- MM widens spread when Sleight tries to enter; tightens when Sleight is forced to exit
- Trains Sleight to use limit orders + iceberg orders, not naked market orders
- Implements TWAP / VWAP execution algorithms to minimize market impact

Implementation: `src/sleight/envs/adversarial_mm_env.py` (P4 deliverable).

## Halt detection + handling

SEC SSR (short-sale restriction) and LULD (Limit Up / Limit Down) halts are frequent in penny stocks.

**Subscription:**
- SEC SSR feed: `https://www.nyse.com/ssr` (daily list, ingest at market open)
- LULD halts: NASDAQ TotalView or proxied from Alpaca/Polygon (paid tier)
- Trading status from SIP (Consolidated Tape)

**Behavior on halt:**
- Pending orders -> attempt cancel; if rejected, leave + monitor
- Open positions -> freeze, set alert; do NOT panic-sell on resume (often gap-open one direction or the other)
- Trade-cap reduce: while halt active, do not initiate any new positions in halted symbol
- Post-halt: wait 15 minutes after resume before re-entering (avoid the gap-fill volatility window)

## Anti-patterns (will NOT do)

- **YOLO into 100% penny stocks.** Caps are caps.
- **Hold through earnings on penny stocks.** Earnings are catastrophic risk; always flat penny positions before announced earnings.
- **Chase the pump.** If we missed entry by > 5%, the trade is dead; don't FOMO in.
- **Average down on penny losers.** Cut losses; never add to losing penny positions.
- **Trust pink-sheet press releases.** Treat as adversarial information; cross-check with SEC filings.
- **Trade penny stocks on margin.** Cash only for penny module; margin is for liquid names.
