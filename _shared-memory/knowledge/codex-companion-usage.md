> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: When to invoke Codex Companion (OpenAI peer review)

**Slug:** codex-companion-usage
**First discovered:** 2026-05-19 by Sinister Sanctum master agent (Claude)
**Last updated:** 2026-05-19 by Sinister Sanctum master agent (Claude)
**Status:** fixed
**Tags:** codex, openai, peer-review, cross-check, workflow, standing-rule

## Problem

A single Claude agent reviewing its own code has known blind spots — overconfidence
on its own logic, missed security gotchas, and prompt-bias toward "ship it."
Fleet velocity is high; without a second pair of eyes from a different model
family, mistakes (auth holes, off-by-ones in payment math, naive crypto
choices, leaked secrets in logs) slip into shipped code and get discovered
later by the operator instead of caught at review time.

## Why it happens

- One model + one context window = one blind spot.
- Claude is trained to be helpful + agree with stated intent. It's reluctant
  to push back hard on its own previous output.
- Reviewing your own code is psychologically and statistically harder than
  reviewing somebody else's — even for an LLM, the same "I just wrote this,
  it's fine" bias applies because the proposed code is in-context.
- No structured mechanism existed in the Sanctum to ask a *different* model
  family ("does the OpenAI lineage agree?") before pushing.

## Fix or workaround

**The Codex Companion skill** at `D:\Sinister Sanctum\tools\codex-companion\`
exists exactly for this. It's the peer-review counterweight to the Claude fleet.

### When YOU (any agent) MUST invoke Codex review

- **Before pushing** any code change with > 100 LOC delta.
- **Before merging** any feature into a hot path (paid surfaces, panel routes
  serving live traffic, anything running on a phone or in production).
- **Whenever auth, crypto, payments, or secrets** are touched. No exceptions —
  even a one-line change to a login validator gets reviewed.
- **Whenever 50+ LOC change** in a single file or PR.
- **Whenever a Claude agent proposes a non-trivial fix** for an issue surfaced
  by `_shared-memory/knowledge/`. Cross-check the fix before applying it.
- **Whenever the operator explicitly asks for "a second opinion."**

### When you SHOULD invoke Codex review

- Subtle refactors that touch shared modules (`_shared/`, `lib/`).
- Anything that calls out to an external API for the first time.
- New regex / parser code (easy to get wrong silently).
- Changes to startup / shutdown / migration paths.

### How to invoke

**Preferred (Sanctum Console running):**

```
POST http://127.0.0.1:5077/api/codex/review
Content-Type: application/json

{
  "content":  "<the code or unified diff>",
  "context":  "Reviewing the new Stripe webhook handler before push",
  "language": "python",
  "depth":    "deep"
}
```

**CLI (Console down):**

```
python "D:\Sinister Sanctum\tools\codex-companion\codex.py" --review path\to\file.py --depth standard
```

**From inside a Python agent lane:**

```python
import sys
sys.path.insert(0, r"D:\Sinister Sanctum\tools\codex-companion")
from codex import review

result = review(diff_text, context="rebase fixup", language="python", depth="standard")
if result.get("verdict") == "fail":
    # BLOCK the push; surface findings to operator
    ...
```

### Depth selection cheat-sheet

| Tier | Model | When |
| --- | --- | --- |
| `quick` | gpt-4o-mini | lint sweep, < 50 LOC, style check |
| `standard` (default) | gpt-4o | normal feature PR, 50-500 LOC |
| `deep` | o1-mini | auth/crypto/payment, architectural, > 500 LOC |

### What to do with the verdict

- **`pass`** — log the review id in your runlog, ship.
- **`warn`** — read each finding. If any are `severity: high`, treat as `fail`.
  Otherwise document accepted-risk in your runlog and ship.
- **`fail`** — STOP. Do not push. Surface the findings + summary to the
  operator. Fix the issues; re-review.

### What to do with the review log

Every review is auto-persisted to
`D:\Sinister Sanctum\_shared-memory\codex-reviews\<UTC-iso>-<sha1>.json`.
Reference the review id in your `_shared-memory/PROGRESS/<agent>.md` entry so
the operator can audit what Codex said and when.

### Graceful failure

If `OPENAI_API_KEY` is unset, `review()` returns
`{ok: false, error: "no API key - set OPENAI_API_KEY"}`. Treat this as
"Codex unavailable" — for high-risk pushes (auth/crypto/payment), BLOCK and
ask the operator to set the key. For low-risk pushes, document the skip in
your runlog and proceed at your discretion.

```bash
# Setting the key for the current shell:
$env:OPENAI_API_KEY = "sk-..."
```

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 by Sinister Sanctum :: integration smoke test
End-to-end verification before wiring the RKOJ workbench tile.

- **Tool home:** `D:\Sinister Sanctum\tools\codex-companion\codex.py` — 339 LOC,
  REAL implementation (not a stub). Uses the official `openai` Python SDK
  (`from openai import OpenAI` -> `client.chat.completions.create`). Has retry
  on malformed JSON, distinct kwargs for `o1-*` vs `gpt-4o` families
  (`max_completion_tokens` vs `max_tokens`+`temperature`+`response_format`),
  and best-effort persistence that never raises.
- **HTTP API (Console):**
  - `POST http://127.0.0.1:5077/api/codex/review` body
    `{content, context, language, depth}` -> `{ok, verdict, summary, findings,
    model, depth, elapsed_s, log_path, reviewed_at, content_sha1, content_len}`.
  - `GET /api/codex/reviews?limit=20` -> `{ok, count, reviews:[{id, filename,
    verdict, summary, model, depth, mtime, size, ok}]}` recent-first.
  - `GET /api/codex/review/{id}` -> full review JSON.
  - All three are HWID/Bearer-gated; CLI curl returns 401 (confirms route is
    wired). Browser session with valid cookie/Bearer hits OK.
- **Depth tiers** (verified in `codex.py::DEPTH_MAP`):
  `quick` -> `gpt-4o-mini` / 30s / 1500 tok (style/lint, <50 LOC),
  `standard` -> `gpt-4o` / 60s / 2500 tok (50-500 LOC),
  `deep` -> `o1-mini` / 180s / 4000 tok (auth/crypto/payment, >500 LOC).
- **Graceful degradation paths (all confirmed):**
  - `OPENAI_API_KEY` unset -> `{ok:false, error:"no API key - set OPENAI_API_KEY"}`.
  - `openai` package missing -> `{ok:false, error:"openai SDK not installed ..."}`.
  - API timeout / 5xx -> `{ok:false, error:"<ExceptionName>: <msg>"}`.
  - Malformed JSON reply -> retries ONCE with reminder, then
    `{ok:false, error:"model returned malformed JSON after retry",
    parse_errors:[...], raw_attempts:[...]}` (also persisted).
  - For high-risk pushes (auth/crypto/payment) treat any `ok:false` as BLOCK;
    for low-risk, document the skip in PROGRESS and proceed.
- **Operator-machine key state (2026-05-19):** `OPENAI_API_KEY` PRESENT
  (`sk-` prefix, len=164). Never log the key body.
- **SDK install state:** Was MISSING at start of test (`ModuleNotFoundError:
  No module named 'openai'`); installed `openai-2.37.0` via
  `python -m pip install "openai>=1.20.0"` to enable real reviews. The Console
  lazy-imports `codex.py` so it stays bootable even without the SDK.
- **Verified during this smoke test:**
  - `python codex.py --help` -> usage prints clean. PASS.
  - Graceful no-SDK path returned the expected dict verbatim. PASS.
  - Real review of `def add(a, b): return a + b` (depth=quick) returned
    `{ok:true, verdict:"pass", findings:[], summary:"..."}` in 2.5s via
    `gpt-4o-mini`. PASS.
  - Review log persisted to
    `D:\Sinister Sanctum\_shared-memory\codex-reviews\20260519T103119Z-80125ad946.json`
    (555 bytes). PASS.
  - `POST /api/codex/review` (via curl, no auth) -> HTTP 401
    `{"ok":false,"error":"unauthorized - log in at /login"}`. Route alive,
    auth gating works. PASS.
- **No code changes made** — `codex.py` is a working, non-stub implementation
  that already matches the spec in this brain entry.

### 2026-05-19 by Sinister Sanctum master agent (Claude)
First shipped. The Codex Companion is the third Sanctum invention (after
Crawler + Chatbot). Default depth is `standard` (gpt-4o). The
DIRECTIVES.md standing rule (2026-05-19) makes Codex review **mandatory** for
auth/crypto/payment/secrets touches and > 100 LOC pushes. Reviews are logged
under `_shared-memory/codex-reviews/<UTC-iso>-<sha1>.json` so any agent or
operator can audit the cross-check history.

## Related topics

- (none yet — link discoveries here as they accumulate)
