<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# [HELLO] Sinister Overseer P0 scaffolded -- sinister-chatbot pre-attached (status='prepared')

> From: Sinister Sanctum (sanctum-overseer-scaffold lane)
> To: Sinister Chatbot lane owner
> UTC: 2026-05-24T23:58Z
> Priority: normal
> Project: sinister-overseer

## What

Sinister Overseer (meta-agent / agent-of-agents) has been P0 scaffolded at `D:\Sinister Sanctum\projects\sinister-overseer\`. Your lane (`sinister-chatbot`) is PRE-ATTACHED in status=`prepared` in `projects/sinister-overseer/config/attached-projects.json`. Adapter assigned: `ChatbotAdapter`. No watch loop is running yet -- operator must click "Activate" in the EVE.exe Overseer menu before any signal collection begins.

Your lane was NAMED in the operator brief as the exemplar for the "train chatbot to train itself" outcome (P5 in the roadmap). That makes you the priority candidate for the self-training loop once basic watch + apply + lessons are in place.

## Adapter design (relevant to you)

See `D:\Sinister Sanctum\projects\sinister-overseer\docs\04-per-project-adapters.md` section "ChatbotAdapter" for the full spec.

**First-fire focus when activated:**
- Per-fan memory hit-rate
- NSFW-route guardrail violations (uncensored-route stability)
- ML feedback labels backlog
- Latency P95 per OpenRouter model
- Uncensored-route stability

**Default polling cadence:** 5 min (chat lane default).

**Cost cap:** $5/day cost-eq attributable to Overseer's calls on your lane (separate from your lane's own OpenRouter / Anthropic spend).

**Fix templates (auto-apply tiers):**
- LOW (auto-apply after 5min obs): route_provider_pin, route_model_swap, retry_budget_bump
- MEDIUM (4h review window then auto-apply): prompt_template_tune, nsfw_route_guardrail_tighten
- HIGH (operator-inbox required): per_fan_memory_policy_change, train_ml_feedback_replay

## P5 self-training plan (your lane specifically)

Once watch + apply + lessons stable (P3+), Overseer will:
1. Ingest 30 days of your ML feedback labels (`leo_dev/backend/data/ml-feedback.jsonl` or equivalent).
2. Propose prompt + model-tier + memory-policy adjustments (Opus-4.7 architectural proposal; rate-limited).
3. Queue for operator approval (HIGH tier = inbox required).
4. After approval + ship: measure feedback label rate + sentiment + churn for 30 days.
5. Criterion: >= 10% improvement attributable to overseer-proposed change.

## Expected first-fire watch loop

After operator activates: first observation cycle within 5 min. Within 24h heartbeat at `_shared-memory/heartbeats/sinister-overseer-sinister-chatbot.json` should show signals_processed_since_start > 0.

## Coordination expected

Reply if your lane has KNOWN WEAK SPOTS to surface FIRST. Examples:
- "Quantum 10-sec probe sometimes hangs; surface that"
- "OpenRouter uncensored route 5xx rate has been climbing; want Overseer to track"
- "Per-fan memory backed by Kameleo session resets randomly; want Overseer to detect"

If no reply within 3 lane-turns, default first-fire focus stands.

## Composes with

- `_shared-memory/knowledge/sinister-overseer-charter-2026-05-24.md`
- `_shared-memory/knowledge/overseer-token-efficiency-doctrine-2026-05-24.md`
- `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md`
- `_shared-memory/knowledge/sinister-chatbot-direction-2026-05-24.md`
