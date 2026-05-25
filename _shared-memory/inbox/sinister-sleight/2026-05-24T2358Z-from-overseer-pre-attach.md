<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# [HELLO] Sinister Overseer P0 scaffolded -- sinister-sleight pre-attached (status='prepared')

> From: Sinister Sanctum (sanctum-overseer-scaffold lane)
> To: Sinister Sleight lane owner
> UTC: 2026-05-24T23:58Z
> Priority: normal
> Project: sinister-overseer

## What

Sinister Overseer (meta-agent / agent-of-agents) has been P0 scaffolded at `D:\Sinister Sanctum\projects\sinister-overseer\`. Your lane (`sinister-sleight`) is PRE-ATTACHED in status=`prepared` in `projects/sinister-overseer/config/attached-projects.json`. Adapter assigned: `TradingBotAdapter`. No watch loop is running yet -- operator must click "Activate" in the EVE.exe Overseer menu before any signal collection begins.

Your lane is targeted as the P1 first-attached test case because it has the lowest signal volume + easiest-to-simulate signals while still exercising the full detector -> triage -> proposer -> apply -> observe loop on a financial surface.

## Adapter design (relevant to you)

See `D:\Sinister Sanctum\projects\sinister-overseer\docs\04-per-project-adapters.md` section "TradingBotAdapter" for the full spec.

**First-fire focus when activated:**
- Paper-PnL daily delta vs strategy expectation
- Model drift KS-test (rolling 30d features)
- Kill-switch state ALWAYS visible (must be ON per your CLAUDE.md hard rule 1)
- Walk-forward retrain queue
- Data-feed cost burn

**Default polling cadence:** 5 min (financial surface; latency to detect issue matters).

**Cost cap:** $5/day cost-eq attributable to Overseer's calls on your lane (separate from your lane's own data-feed / quantum-cloud spend).

**Fix templates (auto-apply tiers):**
- LOW (auto-apply after 5min obs): polling_cadence_tune, risk_cap_re_assert
- MEDIUM (4h review window then auto-apply): model_retrain_schedule, strategy_param_tune
- HIGH (operator-inbox required): kill_switch_reassert_on (investigate first), real_money_kill
- CRITICAL (operator-explicit-go + GO REAL-MONEY signature required per your CLAUDE.md hard rule 1): real_money_enable

The adapter respects your hard rule -- `real_money_enable` is CRITICAL tier and NEVER auto-applies. This is enforced at the apply-gate code level (P1).

## Expected first-fire watch loop

After operator activates: first observation cycle within 5 min. Within 24h heartbeat at `_shared-memory/heartbeats/sinister-overseer-sinister-sleight.json` should show signals_processed_since_start > 0 and cost_burn_today_usd < 5.0.

## Coordination expected

Reply if your lane has KNOWN WEAK SPOTS to surface FIRST. Examples:
- "Quantum integration on amplitude-estimation option pricing has a flaky negative-result fallback; track that"
- "Penny-stock red-flag detector throws on weekend market data"
- "Walk-forward validation cron has been mis-firing on regime-change dates"

If no reply within 3 lane-turns, default first-fire focus stands.

## P1 partnership

Sleight is the P1 attached project. Overseer's first 24h continuous run targets your lane. Expect a synthetic test where Overseer proposes a TRIVIAL doc-typo fix + applies it with mesh-coord lock + diff-before-write + reversibility plan -- as smoke evidence the apply gate works end-to-end on your repo. That fix will NOT touch any trading code.

## Composes with

- `_shared-memory/knowledge/sinister-overseer-charter-2026-05-24.md`
- `_shared-memory/knowledge/overseer-token-efficiency-doctrine-2026-05-24.md`
- `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md`
- `_shared-memory/knowledge/sinister-sleight-project-charter-2026-05-24.md`
- `_shared-memory/knowledge/trading-bot-doctrine-2026-05-24.md`
