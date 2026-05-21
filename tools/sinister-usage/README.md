# sinister-usage

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Status:** v0.1.0 (env-check + endpoint registry; no network calls)

Sinister Sanctum's jcode-usage parity tool. Mirrors `jcode usage --json` shape with a per-provider quota / billing endpoint registry. v0.1.0 is **endpoint discovery only** — it lists which providers expose a per-key usage API and which only have console-side dashboards. v0.2.0 will add authenticated HTTP calls behind `--allow-network`.

## What it tells you

| Provider | endpoint known | auth |
|---|---|---|
| claude | no — console only | — |
| openai | yes (`/v1/usage`) | bearer |
| gemini | no — GCP billing | — |
| copilot | yes (`/user/copilot/billing`) | bearer |
| azure | no — Azure Cost Management | — |
| alibaba-coding-plan | no — DashScope console | — |
| fireworks | yes (`/inference/v1/usage`) | bearer |
| minimax | no — platform console | — |
| lmstudio | local — no quota | — |
| ollama | local — no quota | — |
| openai-compatible | depends on host | bearer |

## Install

```bash
pip install -e "D:/Sinister Sanctum/tools/sinister-usage"
```

## CLI (via umbrella or direct)

```bash
sinister usage list              # endpoint registry (no env lookup)
sinister usage check openai      # env-check + endpoint-known + cross-ref to sinister-login
sinister usage check-all         # 11-row table
sinister usage matrix            # the jcode-feature-matrix row for this tool
```

## API

```python
from sinister_usage import check, check_all, list_endpoints, get_endpoint

check("openai")          # -> {"ok": True, "endpoint_url": ".../v1/usage", "configured": True, ...}
check_all()              # [11 rows]
list_endpoints()         # endpoint-only view (no env cross-ref)
get_endpoint("ollama")   # UsageEndpoint dataclass
```

## Soft dependency on sinister-login

If `sinister_login` is installed, `check()` cross-references its `provider_status()` so the `configured` field reflects actual env-key presence. If sinister-login is missing, `configured` returns `None` (rendered as `—`).

## Design constraints

- **Stdlib only**. No `requests`, no `httpx`.
- **No network in v0.1.0** — canonical-11 reversibility wall. Endpoint URLs are *registered*, not *called*. v0.2.0 will add `report()` behind `--allow-network`.
- **Honest about gaps** — when a provider has no public per-key usage API (claude, gemini, azure, minimax, alibaba), the tool says so instead of inventing fake endpoints. Operator sees the console URL instead.
- **Local providers are no-ops** — lmstudio and ollama are local; the registry surfaces this explicitly rather than reporting a phantom quota.

## v0.2.0 planned

- `sinister usage report <provider>` — actually call the endpoint with the operator's key (when configured)
- `--allow-network` flag (required)
- `--since YYYY-MM-DD` / `--until` for OpenAI date-window queries
- Per-call cost estimation from response shape
- Aggregated `sinister usage report --all` across all configured providers

## Lane

`tools/sinister-usage/` is Sanctum's lane. Forge picker Q4 can call `sinister-usage check <provider>` to surface "quota visible/not visible" alongside the host pick. Term shell can show a `usage:openai` chip in its toolbar.
