---
target: codex-companion
kind: case-study
reviewed_by: Sinister Sanctum master agent (via Explore subagent)
reviewed_at: 2026-05-19T12:35Z
tags: [case-study, codex-companion, KEEP]
---

# Case study: codex-companion

## 1. What it is

The `codex-companion` tool lives at `D:\Sinister Sanctum\tools\codex-companion\` and is the **third Sanctum invention** (after Sinister Crawler and Sinister Chatbot). It is a thin Python wrapper around the OpenAI SDK that lets any Claude agent hand a code blob or diff to a Codex-grade model (gpt-4o-mini / gpt-4o / o1-mini) and get back a structured verdict `{verdict: pass|warn|fail, findings:[{severity,area,body}], summary}`. The single public function is `review(content, *, context="", language="python", depth="standard")` in `codex.py` (339 LOC, real implementation — not a stub). Three surfaces expose it: (a) HTTP via the Sanctum Console (`POST /api/codex/review`, `GET /api/codex/reviews`, `GET /api/codex/review/{id}` — wired in `automations/window-manager/server.py:1776-1875` via lazy import); (b) CLI (`python codex.py --review <path> --depth <tier>`, exit codes 0/1/3); (c) direct Python import from any agent lane. Every review is persisted append-only to `D:\Sinister Sanctum\_shared-memory\codex-reviews\<UTC-iso>-<sha1>.json`. The DIRECTIVES.md standing rule (2026-05-19) makes Codex review **mandatory** for auth/crypto/payment/secrets touches and any push > 100 LOC. Five real review artifacts already on disk, all from the 2026-05-19 build day.

## 2. Strengths

- **Real, working, non-stub implementation.** 339 LOC of production-shaped Python: input validation, env-key gate, lazy OpenAI SDK import, depth-tiered model routing, JSON schema validation (`_validate_shape`), one-shot retry on malformed JSON, code-fence stripping, dual API contract handling (`o1-*` uses `max_completion_tokens`; `gpt-4o` uses `max_tokens`+`temperature`+`response_format`). Smoke-tested end-to-end on 2026-05-19 — `def add(a,b): return a+b` returned `pass` in 2.5s via gpt-4o-mini and persisted log (`20260519T103119Z-80125ad946.json`, 555 bytes).
- **Graceful failure on every error path.** Missing API key, missing SDK, API timeout, malformed JSON, empty content, bad depth — all return `{ok: False, error: <str>}` instead of raising. `_persist` is best-effort and never raises (`codex.py:97-103`). The Console can boot without the `openai` package installed because of the lazy import pattern (`server.py:1786-1801`).
- **Depth tiers map cost to stakes correctly.** `quick` -> gpt-4o-mini / 30s / 1500 tok for <50 LOC lint sweeps; `standard` -> gpt-4o / 60s / 2500 tok for normal feature PRs; `deep` -> o1-mini / 180s / 4000 tok for auth/crypto/payment and architectural changes (`codex.py:52-56`). Operator can override per call.
- **Append-only audit trail.** Every review persists to `_shared-memory/codex-reviews/<UTC-iso>-<sha1>.json` with full provenance — model, depth, language, context, content_sha1, content_len, elapsed_s, reviewed_at, verdict, findings, summary. Five real artifacts already on disk (panel sweep, captcha solver, TikTok captcha dispatcher). Operator and other agents can grep history forever.
- **Standing rule + brain entry + invention card all aligned.** `DIRECTIVES.md` entry 299-330 codifies the mandatory-review trigger conditions. `_shared-memory/knowledge/codex-companion-usage.md` documents when-to-invoke from the agent side with depth cheat-sheet and verdict-handling rules. `inventions/2026-05-19-codex-companion.md` captures the why and the architecture diagram. Tool card README is comprehensive (197 LOC).
- **Three response surfaces, one core.** HTTP for cross-process / Console use, CLI for shell / git hooks / desktop bat, direct import for in-process Python agents. All three call the same `review()` function — single implementation, three ergonomic front doors.
- **JSON-only contract enforced.** System prompt mandates strict JSON, `_parse_response` strips code fences if the model ignores instructions, validates shape (`verdict` in pass/warn/fail, `findings` is list of `{severity,area,body}` dicts, `summary` is string), and retries once with a reminder suffix if parse fails.

## 3. Weaknesses + risks

- **Logs persist `context` verbatim.** The review log JSON includes the operator-supplied `context` string in full (`codex.py:284`). If an agent paste-includes secrets, internal URLs, or credentials in the context field (the field is designed to be free-form), they land on disk in the append-only review log forever. No scrubbing. Existing real reviews show context strings like "Sanctum master sweep" and "Sinister TikTok-EMU" — benign so far, but the discipline is operator-trust, not enforcement.
- **No size cap on `content`.** `review()` accepts arbitrarily large strings; the only limit is the OpenAI API's max-context limit, which manifests as a 400 error from the SDK. A multi-MB blob will burn tokens, time, and money before the API rejects it. One existing review (`20260519T104138Z-4d6b078bda.json`) was 88906 chars / ~22k tokens — the upper end of what gpt-4o accepts cleanly.
- **`content_sha1` collision in filename.** Log filename is `<UTC-iso>-<sha1[:10]>.json`. Two reviews of the same content within the same second produce the same filename and the second silently overwrites the first via `Path.write_text` (`codex.py:100-103`). In practice the UTC-iso has 1-second resolution so concurrent reviews are possible. The existing 5-file directory shows two reviews with sha `334039deeb` 1 minute apart — no collision because the timestamps differ, but the design relies on temporal spacing rather than uniqueness.
- **No streaming, no batching.** Every call is a single blocking HTTP request to OpenAI. `deep` reviews can take up to 180s and block the calling agent the whole time. The Sanctum Console endpoint is synchronous (`@app.post("/api/codex/review")` — no background task). A slow `o1-mini` review will hold a worker thread for minutes.
- **Single model family (OpenAI only).** The whole point per the brain entry is "different model family catches Claude's blind spots." That works for OpenAI vs Anthropic. But there is no escape hatch for "OpenAI is down" or "operator wants to add Gemini / DeepSeek / local llama for a third opinion." Hard-coded to one provider.
- **No rate limiting or budget tracking.** Each call hits OpenAI; the operator pays per token. The tool does not track cumulative spend, does not warn if a session has burned > $X, and does not enforce a per-day cap. The audit log records `elapsed_s` and `content_len` but not estimated cost. If a runaway agent loops on `review()`, the bill grows silently.
- **`response_format` JSON-mode silently disabled for `o1-mini`.** The `o1-*` branch in `_call_openai` (`codex.py:179-181`) only sets `max_completion_tokens` and skips the `response_format={"type":"json_object"}` hint that gpt-4o gets. This is correct (the o1 family rejects that parameter at the API level), but it means `deep` reviews are *more* likely to fall into the malformed-JSON retry path than `standard` reviews. Mitigated by the explicit "Return JSON only" instructions in both system + user prompts, but the asymmetry is not flagged in the README.
- **No way to re-review with a different model after a `warn` or `fail`.** If gpt-4o returns `warn` and the agent wants a `deep` second opinion via o1-mini, it must call `review()` again from scratch (which produces a new log entry, not a linked thread). The audit log has no `re_reviewed_from` or `chain_id` field. Hard to trace "we did three passes and the third one finally passed."
- **Console endpoint is HWID-locked but not rate-limited.** Auth gating works (smoke test confirms 401 for unauthenticated curl), but a compromised session can fire reviews in a tight loop. No per-session cap, no exponential backoff on misbehavior.

## 4. Better-than-found proposal

Add three lightweight safety nets without changing the public API contract.

**Changes to `D:\Sinister Sanctum\tools\codex-companion\codex.py`:**

1. **Context-field scrub (line 284, before `_persist`):** before writing `record["context"] = context`, run it through a regex scrub of common secret patterns (`sk-[A-Za-z0-9]{20,}`, `ghp_[A-Za-z0-9]{20,}`, `AKIA[A-Z0-9]{16}`, `xoxb-[A-Za-z0-9-]{30,}`). Replace matches with `<REDACTED:secret>`. Same scrub on `content` before persistence (do not scrub the OpenAI request itself — the model needs the real bytes — but do scrub the disk copy). Roughly 20 LOC of regex.

2. **Content size cap (line 208, after the empty check):** `if len(content) > 200_000: return {"ok": False, "error": f"content too large ({len(content)} chars, max 200000)"}`. The current largest real review is 89k chars; 200k gives 2x headroom and prevents accidental megablob.

3. **Filename uniqueness via microsecond timestamp (line 84-94):** change `_utc_iso()` to `"%Y%m%dT%H%M%S%fZ"` (microsecond resolution) so concurrent reviews can never overwrite each other. Two-line change.

**Changes to `D:\Sinister Sanctum\automations\window-manager\server.py` (Console endpoint, lines 1811-1834):**

4. **Move the `/api/codex/review` POST to a background task** so the HTTP request returns immediately with a `{ok: True, pending: True, review_id: <id>}` and the actual review runs async. Caller polls `GET /api/codex/review/{id}` for completion. Roughly 30 LOC using FastAPI `BackgroundTasks`. Removes the 180s blocking window on `deep` reviews.

**Optional follow-up (not blocking ship):**

5. Add a `chain_id` field to `review()` so a re-review can be linked to its predecessor (`review(..., chain_id=prev_review_id)`). Append to existing record's `re_reviews` list. Five-line change in the record dict + the list endpoint.

6. Add a `total_spend_estimate_usd` running total in `_shared-memory/codex-reviews/_budget.json`, updated best-effort on each successful review. Use OpenAI's published per-token prices and the `elapsed_s` / token-count returned by the SDK. Operator-facing only; no enforcement.

**Rationale:** the tool is already well-built; these are safety nets, not redesigns. The scrub closes a real data-leak path (free-form context strings on disk). The size cap prevents accidental megablob cost-blasts. The filename uniqueness fix removes a silent-overwrite footgun. The async endpoint unblocks the Console during long `deep` reviews. None of these break the existing surface; all five existing review artifacts would still parse and load.

## 5. Recommendation

**KEEP**

The tool is the third Sanctum invention, already shipped, already wired into the Console, already used (5 real review artifacts on disk from real master-sweep work on 2026-05-19), already codified as a standing rule in `DIRECTIVES.md`, and already documented in the brain (`_shared-memory/knowledge/codex-companion-usage.md`). The implementation is production-shaped — graceful failure on every path, dual API contract handling for `o1-*` vs `gpt-4o`, JSON schema validation with retry, append-only audit log. It solves the genuine problem (Claude self-review blind spots) with the genuine fix (different-model-family peer review) and the operator + every agent in the fleet now has a one-line way to invoke it from HTTP, CLI, or direct Python.

The weaknesses in section 3 are real but none of them are show-stoppers. The context-field secret-leak risk is the only one approaching urgent, and it is mitigated by the fact that only trusted agents inside the loopback-HWID-locked Console can call the endpoint. The size cap, filename microsecond, and async endpoint are quality-of-life improvements that can land as a follow-up commit when the operator has a spare hour; they do not block the current verdict. Ship the proposal in section 4 as a single small PR (~80 LOC across two files) when convenient, but the tool is keep-as-is today.

## Operator decision

*(left blank for operator's thumb + free text)*
