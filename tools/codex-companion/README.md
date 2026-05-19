> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# codex-companion

OpenAI-powered peer-review skill that runs alongside Claude agents so they
cross-check each other. **The third Sanctum invention** (after Sinister Crawler
and Sinister Chatbot).

## What it does

`codex-companion` is a thin wrapper around the OpenAI SDK that lets any Claude
agent in the Sanctum hand a code blob / diff / proposed change to a
Codex-grade model and get back structured feedback:

```json
{
  "verdict":  "pass | warn | fail",
  "findings": [
    { "severity": "high | medium | low",
      "area":     "<short label>",
      "body":     "<concrete description + recommendation>" }
  ],
  "summary":  "<one-paragraph overall assessment>"
}
```

It's the peer-review counterweight to a fleet of Claude agents shipping code:
when one Claude writes a non-trivial change, another agent (or the Sanctum
Console) can ask Codex "is this actually right?" before it lands.

Every review is logged append-only to
`D:\Sinister Sanctum\_shared-memory\codex-reviews\<UTC-iso>-<sha1>.json` so the
operator and other agents can audit the history.

## When to use it

Standing rule (see `_shared-memory/DIRECTIVES.md`). Run a Codex review:

- **Before pushing** any code change with > 100 LOC delta.
- **Before merging** any feature into a hot path (paid surfaces, panel routes
  serving live traffic, anything running on a phone).
- **Whenever auth, crypto, payments, or secrets are touched.** No exceptions.
- **Whenever 50+ LOC change** in a single file or PR.
- **Whenever a Claude agent proposes a non-trivial fix** for an issue surfaced
  by `_shared-memory/knowledge/`.

If Codex returns `fail`, or `warn` with high-severity findings: BLOCK the push
and surface the findings to the operator.

## Model selection (depth tiers)

| Depth | Model | Budget | When |
| --- | --- | --- | --- |
| `quick` | `gpt-4o-mini` | 30s | Trivial diffs, style/lint sweep, < 50 LOC |
| `standard` (default) | `gpt-4o` | 60s | Normal feature PR, 50-500 LOC |
| `deep` | `o1-mini` | 180s | Auth/crypto/payment code, architectural changes, > 500 LOC |

Override per-call via the `depth` field.

## Requirements

- Python 3.10+ (matches the rest of the Sanctum)
- `openai>=1.20.0` (operator installs separately - this tool does not pip-install)
- Env var `OPENAI_API_KEY` set in the calling shell

## How to invoke (operator-facing)

### Via the Sanctum Console (preferred)

`POST http://127.0.0.1:5077/api/codex/review`

```json
{
  "content":  "<source code or unified diff>",
  "context":  "Reviewing the new Stripe webhook handler before push",
  "language": "python",
  "depth":    "deep"
}
```

Response is the verdict dict shown at the top of this README.

Auxiliary endpoints:

- `GET /api/codex/reviews?limit=20` -> list recent reviews (filename + summary)
- `GET /api/codex/review/{id}` -> read one review JSON in full

### Via CLI

```
python "D:\Sinister Sanctum\tools\codex-companion\codex.py" --review path\to\file.py --depth standard
```

`--review -` reads from stdin. Exit codes: `0` = pass/warn, `3` = fail,
`1` = error (no API key, bad JSON, etc.).

### Via the desktop bat (operator one-click)

`C:\Users\Zonia\Desktop\Codex-Review-Test.bat` — paste a code blob (Ctrl-Z to
finish), POSTs to `/api/codex/review`, prints verdict + findings + summary,
auto-closes in 8s on success.

### From inside a Claude agent's Python lane

```python
import sys
sys.path.insert(0, r"D:\Sinister Sanctum\tools\codex-companion")
from codex import review

result = review(
    code_blob,
    context="this is the new login validator",
    language="python",
    depth="deep",
)
if result.get("verdict") == "fail":
    raise RuntimeError(f"Codex blocked the change: {result['summary']}")
```

## Verdict format

| verdict | Push allowed? | What to do |
| --- | --- | --- |
| `pass` | yes | log the review id in the runlog, ship |
| `warn` | yes IF no high-severity findings; otherwise treat as fail | document accepted-risk in runlog, ship |
| `fail` | no | block, surface findings to operator, fix & re-review |

`findings[].severity` is one of `high | medium | low`:
- `high` — correctness, security, data loss, secrets leakage, broken auth.
- `medium` — design smell, footgun, missing input validation, race condition.
- `low` — style, naming, comment-suggestion, optional refactor.

## Graceful failure modes

| Situation | Returned |
| --- | --- |
| `OPENAI_API_KEY` unset | `{ok: false, error: "no API key - set OPENAI_API_KEY"}` |
| `openai` package not installed | `{ok: false, error: "openai SDK not installed ..."}` |
| API call timeout / 5xx | `{ok: false, error: "<error>"}` |
| Model returns non-JSON | Retries once. If still bad: `{ok: false, error: "malformed JSON", raw_attempts: [...]}` |

The companion **never raises** on missing API key or SDK — it returns a graceful
`{ok: false, ...}` dict so the caller can choose to skip review or block.

## Implementation files (absolute paths)

- `D:\Sinister Sanctum\tools\codex-companion\codex.py`
- `D:\Sinister Sanctum\tools\codex-companion\requirements.txt`
- `D:\Sinister Sanctum\tools\codex-companion\AUTHOR.md`
- `D:\Sinister Sanctum\tools\codex-companion\README.md`
- `C:\Users\Zonia\Desktop\Codex-Review-Test.bat`
- Review logs: `D:\Sinister Sanctum\_shared-memory\codex-reviews\<UTC-iso>-<sha1>.json`

## Integration with Sanctum Console

The companion is lazy-imported by
`D:\Sinister Sanctum\automations\window-manager\server.py` via
`sys.path.insert(0, "<tools/codex-companion>")`. This means the Console can
boot without the `openai` package installed; the companion only fails (with
a graceful error) when an actual review is requested and the SDK is missing.

Endpoints exposed by the Console:

- `POST /api/codex/review` — request a review.
- `GET  /api/codex/reviews?limit=N` — list recent reviews.
- `GET  /api/codex/review/{id}` — read one review JSON.

## Dependencies

- Python 3.10+
- `openai>=1.20.0` (operator-installed)
- Env var `OPENAI_API_KEY`
- Sanctum Console (`window-manager` server) for HTTP endpoints (optional —
  CLI works standalone)

## Lane

master / Sanctum orchestration

## Captured

2026-05-19

## Status

shipped

## Linked-inventions

- `D:\Sinister Sanctum\inventions\2026-05-19-codex-companion.md`

## Changelog

- **2026-05-19** — Initial build. Third Sanctum invention. Three depth tiers,
  graceful no-API-key behavior, append-only review log, Sanctum Console
  endpoints wired in, desktop one-click bat shipped.
