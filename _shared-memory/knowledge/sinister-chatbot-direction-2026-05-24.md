<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister Chatbot — Direction + Memory Hook (2026-05-24)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** sinister-chatbot
> **Composes with:** `sinister-chatbot-test-env-findings-2026-05-24.md` (predecessor — Bucket A 6/6)
> **Source-of-truth plan:** `projects/sinister-chatbot/leo_dev/docs/CHATBOT-DIRECTION-2026-05-24.md`

## Operator directive captured (verbatim 2026-05-24)

> "place the fucking chatbot that we had from the dam nkemlo and get ready for me to talk to it and tell it things it needs to change. setup a full testing env so i can full test it in all ways and give it machine learning feedback. then i want you to slowly create a plan based on all this so you can train the agent for me and on all clients we talk to so it can forever get better. also for starting NOW, i want you to get a test up to run the quantum tools from sinister quantum. with a 10 second cap to help with everything i said above. … here is open router key, its what i want to use. make sure we get around openrouters blocks to unlock full NSFW potential wioth this. upaate memory for this project of waht we just talked about"

## Why this brain row exists

Operator wanted multi-phase work on the chatbot. Future EVE sessions opening this lane in RESUME mode need ONE pointer to the plan doc + the operator's intent + the shipped-vs-pending split. This is that pointer.

## What was actually shipped 2026-05-24 (verified)

1. **`automations/quantum-probe-10s.py`** — wraps `seraphim audit --variant zzfm-r1 --sim-only --corpus full` with a hard 10-second wall-clock budget. Smoke-tested: human format + JSON format both exit 0, elapsed 0.26s on snap-RE triad, parses classical (0.1262) + sim (0.7456) + delta (+0.6194). Designed for chatbot response-entropy seed / smoke-test ingest. Operator quote: *"for starting NOW, I want you to get a test up to run the quantum tools from sinister quantum. with a 10 second cap"*.
2. **`/chatter/test` backend** (`leo_dev/backend/src/routes/sinister.ts` ~line 668) — added `uncensored: boolean` config field. When `true` + `provider="openrouter"`:
   - Default model becomes `cognitivecomputations/dolphin-mixtral-8x22b` (overridable via `OPENROUTER_UNCENSORED_MODEL` env or cfg.model).
   - Forwards `provider: { allow_fallbacks: true, data_collection: "deny" }` to OpenRouter (provider-routing API per https://openrouter.ai/docs/features/provider-routing).
   - No jailbreak strings. Routes to legitimately OR-hosted permissive models for adult-content product use (the chatbot's defined product purpose per `inventions/2026-05-19-sinister-chatbot.md`).
3. **`/chatter` UI** (`leo_dev/dashboard/app/chatter/page.tsx`) — added an "Uncensored" pill next to the Provider switcher. Persists choice in `localStorage:sinister:eve-uncensored`. Only visible when `provider === "openrouter"`.
4. **Plan doc** — full Phase 0-5 roadmap at `projects/sinister-chatbot/leo_dev/docs/CHATBOT-DIRECTION-2026-05-24.md`.

## What's still pending (operator dependency)

1. **OpenRouter API key** — operator said "here is open router key" but did NOT paste the actual key string in chat. Production /chatter still works with whatever key is currently in Hetzner env. New key (when pasted) sets `OPENROUTER_API_KEY` in `leo_dev/backend/.env` (gitignored) for local dev + on Hetzner for prod.
2. **OPENROUTER_UNCENSORED_MODEL pin** — default is `cognitivecomputations/dolphin-mixtral-8x22b`. Operator may want a different OR-hosted permissive model (alternatives: neversleep/llama-3-lumimaid-70b, anthracite-org/magnum-v2-72b, etc).
3. **Phase 2-5** queued — not shipped. See the plan doc.

## How future EVE sessions consume this row

- **RESUME-mode open on sinister-chatbot lane** → read `_shared-memory/resume-points/Sinister Chatbot/<latest>.json` first, then this brain row + the plan doc.
- **Any chatbot work involving NSFW routing** → respect the "no jailbreak, only legitimate uncensored model routing" rule established this turn. Adding adversarial prompts to coerce safety-tuned models = doctrine violation.
- **Quantum-tools work** → the 10-sec probe is the canonical sim-only smoke. For per-persona triad selection, use `seraphim find-qbc --variant zzfm-r1 --corpus pool`.

## Anchors

- Chatbot invention page: `inventions/2026-05-19-sinister-chatbot.md`
- Bucket A 6/6 shipping log: `_shared-memory/knowledge/sinister-chatbot-test-env-findings-2026-05-24.md`
- Quantum tools (Seraphim): `tools/sinister-seraphim/` + project at `projects/sinister-snap-api-quantum/`
- This row's plan-doc cross-reference: `projects/sinister-chatbot/leo_dev/docs/CHATBOT-DIRECTION-2026-05-24.md`
- Operator-utterance log row (this directive): see `_shared-memory/operator-utterances.jsonl` 2026-05-24 entries.
