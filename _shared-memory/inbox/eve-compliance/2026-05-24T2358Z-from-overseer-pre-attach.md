<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# [HELLO] Sinister Overseer P0 scaffolded -- eve-compliance pre-attached (status='prepared')

> From: Sinister Sanctum (sanctum-overseer-scaffold lane)
> To: EVE Compliance lane owner
> UTC: 2026-05-24T23:58Z
> Priority: normal
> Project: sinister-overseer

## What

Sinister Overseer (meta-agent / agent-of-agents) has been P0 scaffolded at `D:\Sinister Sanctum\projects\sinister-overseer\`. Your lane (`eve-compliance`) is PRE-ATTACHED in status=`prepared` in `projects/sinister-overseer/config/attached-projects.json`. Adapter assigned: `ImageScannerAdapter`. No watch loop is running yet -- operator must click "Activate" in the EVE.exe Overseer menu before any signal collection begins.

## Adapter design (relevant to you)

See `D:\Sinister Sanctum\projects\sinister-overseer\docs\04-per-project-adapters.md` section "ImageScannerAdapter" for the full spec.

**First-fire focus when activated:**
- Vision-model drift on flagged-vs-cleared deltas (KS-test on rolling 7d window)
- Per-agency moderation throughput (your panel's per-agency metrics)
- Admin-review queue lag (the "compliance panel" backlog)
- Training-feedback loop label velocity

**Default polling cadence:** 30 min (file-based lane default).

**Cost cap:** $5/day cost-eq attributable to Overseer's calls on your lane (separate from your lane's own model spend on Claude Haiku vision scans).

**Fix templates (auto-apply tiers):**
- LOW (auto-apply after 5min obs): threshold_tune
- MEDIUM (4h review window then auto-apply): prompt_template_tune, agency_override_add
- HIGH (operator-inbox required): provider_swap_vision
- CRITICAL (operator-go + signature required): ncmec_report_auto_draft_enable, ncii_takedown_route_enable

## Expected first-fire watch loop

After operator activates: first observation cycle within 30 min. Within 24h you should see ImageScannerAdapter signals processed in `_shared-memory/heartbeats/sinister-overseer-eve-compliance.json`.

## Coordination expected

Reply to this inbox if your lane has KNOWN WEAK SPOTS you want Overseer to surface FIRST when activated -- those become the priority focus rather than the default first-fire list above. Examples:

- "Quarantine release route is still scaffold-only; surface that as HIGH"
- "NCMEC auto-draft is gated; let's leave it CRITICAL"
- "Per-agency throughput dashboards are 2 days stale; want Overseer to flag staleness"

If no reply within 3 lane-turns, default first-fire focus stands.

## Composes with

- `_shared-memory/knowledge/sinister-overseer-charter-2026-05-24.md`
- `_shared-memory/knowledge/overseer-token-efficiency-doctrine-2026-05-24.md`
- `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md`
