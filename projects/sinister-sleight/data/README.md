<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# data/ — historical and live market data

## Status

P0 — empty. Populated starting P1.

## Layout (planned)

```
data/
  raw/                  # raw OHLCV + fundamentals from data adapters
    sp500/<symbol>.parquet
    penny/<symbol>.parquet
    crypto/<symbol>.parquet
  features/             # engineered features cached per symbol
    sp500/<symbol>.parquet
  news/                 # cached headlines + LLM embeddings
    <YYYY-MM-DD>/<symbol>.json
  llm-traders/          # cached Claude responses for audit + replay
    <YYYY-MM-DD>/<symbol>.json
  cache/                # adapter-level HTTP cache
  paid-promo-blacklist/ # penny-stock paid-promotion email blacklists
  kill-switch.lock      # operator kill-switch trigger file (if present, bot halts)
```

## Storage discipline

- **NEVER commit raw market data.** `.gitignore` excludes `data/raw/`, `data/features/`, `data/news/`, `data/llm-traders/`, `data/cache/`. They are regenerable via `python -m sleight data fetch`.
- **Parquet preferred** over CSV (smaller, faster, typed).
- **Naming convention:** lowercase symbol, hyphen separator, parquet extension. Example: `data/raw/sp500/aapl.parquet`.
- **Size budget:** soft cap 50 GB per universe; if exceeded, prune older history or move to external archive.

## Reproducibility

Every cached dataset gets a SHA-256 sidecar `<file>.sha256` so model `meta.json` can reference the exact data slice the model was trained on.
