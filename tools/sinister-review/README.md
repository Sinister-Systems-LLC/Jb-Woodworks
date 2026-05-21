# sinister-review

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Lane:** Sanctum-side tool. Every agent in the fleet can shell out for a peer review.
> **Status:** v0.1.0 — disk-first verdict persistence + four review kinds. `dispatch_llm()` is a stub; v0.2.0 wires it.

## What it is

jcode-review parity for the Sinister fleet. Take a piece of work (diff / commit / transcript / freeform judgment question), get a structured verdict written to `_shared-memory/reviews/<UTC>-<from-slug>-<topic>.json`, then ship.

The LLM is intentionally pluggable. v0.1.0 raises `NotImplementedError` from `dispatch_llm()` so the disk schema + four review kinds + CLI are exercised first without burning tokens. v0.2.0 wires the LLM per `automations/agent-host-routing.md` (Anthropic SDK / `claude --json` CLI / `codex -q` / `ollama run`).

## Quickstart

```bash
cd "D:/Sinister Sanctum/tools/sinister-review"
pip install -e .

# CLI
sinister-review --commit HEAD --focus "lane-discipline"
sinister-review --transcript path/to/turn.jsonl --focus "AUP compliance"
sinister-review --diff - < my.patch
sinister-review --judge "is this commit safe to push to main?" --context my-context.md
sinister-review --recent 5            # review last 5 commits in cwd
sinister-review --list --limit 20     # list prior verdicts
sinister-review --list --namespace forge --limit 10
```

```python
from sinister_review import review_commit, review_diff, judge, recent_reviews

review_commit("4f0ed94", model="opus-4-7", focus="lane-discipline")
judge("is this commit safe to push to main?", context=open("ctx.md").read())
recent_reviews(limit=20, namespace="forge")
```

## Public API (`sinister_review`)

| Function | Returns |
|---|---|
| `review_diff(diff_text, *, model="opus-4-7", focus=None)` | persisted verdict dict |
| `review_transcript(transcript_path, *, model="opus-4-7", focus=None)` | persisted verdict dict |
| `review_commit(sha, *, model="opus-4-7", focus=None, cwd=None)` | persisted verdict dict |
| `judge(question, context=None, *, model="opus-4-7", options=None)` | persisted verdict dict |
| `recent_reviews(limit=10, *, namespace=None)` | list of summary dicts |
| `dispatch_llm(prompt, *, model, max_tokens)` | **STUB v0.1.0** — wire per agent-host-routing.md in v0.2.0 |
| `set_reviews_root(p)` / `get_reviews_root()` | reviews dir override |

## On-disk layout

```
_shared-memory/reviews/
└── <UTC stamp>-<from-slug>-<kind-topic>.json
```

Each verdict schema (`sinister.review.v1`):

```json
{
  "_author": "RKOJ-ELENO :: 2026-05-21",
  "schema_version": "sinister.review.v1",
  "ts_utc": "2026-05-21T12:55:00Z",
  "from": "sanctum",
  "model": "opus-4-7",
  "kind": "commit|diff|transcript|judgment",
  "input": { "summary": "...", "source_path": "git:<sha>" },
  "verdict": {
    "rating": "approve|approve-with-changes|revise|reject|stub|see_raw",
    "confidence": 0.85,
    "headline": "one line",
    "concerns": ["..."],
    "suggestions": ["..."],
    "rationale": "..."
  },
  "cost_estimate_usd": 0.0,
  "duration_s": 0.123,
  "stub": false
}
```

## v0.1.0 stub behavior

Without `dispatch_llm()` wired, every review call:
1. Builds the prompt correctly (so prompts are debuggable).
2. Catches `NotImplementedError` cleanly.
3. Persists a verdict with `rating="stub"`, `stub=true`, and the error inline in `concerns[0]`.
4. Returns immediately with `cost_estimate_usd=0.0` so nothing is silently burning tokens.

This lets the rest of the fleet wire `sinister-review` into hooks / cron / cross-agent flows now and get useful verdicts later when the LLM goes live.

## Composes with

- **`automations/agent-host-routing.md`** — picks the model + provider per task class (Forge gets opus-4-7 1M; smaller lanes can use codex / ollama)
- **`tools/sinister-cli/`** — likely to absorb `sinister review` as the 8th umbrella subcommand once the umbrella has a stable contract (today: separate `sinister-review` script)
- **`automations/memory-consolidate.ps1`** — could append top-rated reviews to `_shared-memory/forge-memory/<from-slug>/` for cross-session recall
- **`tools/forge-memory-bridge/`** — verdict rationale could be `write()`-en there with tags `["review", kind, rating]` so future agents recall prior verdicts

## Non-goals (v0.1.0)

- Live LLM wiring (intentionally stubbed; v0.2.0)
- Async batch (one verdict at a time; jcode does batches and we can copy if cron load demands it)
- Verdict aggregation / weighted ensemble across multiple reviewers (later)
- GUI / dashboard view (use the Forge mermaid render pipeline if needed)
