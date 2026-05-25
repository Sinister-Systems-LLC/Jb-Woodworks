<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 03 -- Watch Architecture

## The watch loop (per attached project)

```
WHILE attachment.status == "active":
    if cost_burn >= cap: SUSPEND + notify; break
    if cost_burn >= 0.8 * cap: THROTTLE (drop cadence; suspend Opus)

    signals = adapter.collect_signals(since=last_poll_utc)
    last_poll_utc = now()

    FOR signal IN signals:
        event_bus.publish(signal)

    # event_bus subscribers run inline (single-process)
    sleep(adapter.polling_interval_seconds)
```

Single-process per attachment. No background threads beyond the heartbeat writer (60s tick).

## Signal sources (by adapter type)

| Source type | How collected | Cadence | Cheap to read? |
|---|---|---|---|
| File-system change | `watchdog` events buffered into 30-min windows | continuous + windowed | yes (local FS) |
| Heartbeat stall | tail of `_shared-memory/heartbeats/<lane>.json` mtime | per poll | yes |
| Log anomaly | tail of `<project>/logs/*.log` last N lines; rolling stats | per poll | yes |
| Metric regression | adapter-specific endpoint or file (e.g. paper-PnL CSV) | per poll | yes (local) |
| User-data signal | adapter-specific (e.g. feedback labels JSONL) | per poll | yes |
| Configuration smell | scan of `.env` / `settings.json` / `config/*.json` for known anti-patterns | per poll | yes |
| Cost burn | `claude-usage-meter.ps1` filtered by lane | per poll | yes (cached counter) |
| Doctrine violation | grep of recent git diff for forbidden patterns | per poll | yes |
| Process / daemon health | `Get-Process` filter or `schtasks /Query` | per poll | yes |

Adapter declares which subset of sources it consumes.

## Detector (cheap tier)

Input per call:
```
{
  "attachment": "<project-key>",
  "signal_type": "<one of: regression|anomaly|stall|drift|smell|cost-burn|doctrine-violation|user-data-signal>",
  "signal_diff": "<text under 2KB>",
  "context_pointer": "<path-or-url>"
}
```

Output:
```
{
  "classification": "<one of: noise|info|warn|alert|critical>",
  "severity_score": 0-100,
  "evidence_summary": "<text under 200 chars>",
  "recommended_action": "<one of: ignore|log|triage|escalate>"
}
```

Constrained-JSON schema; Haiku-4.5 with stable system prompt.

## Triage (medium tier)

Fires when detector emits classification >= alert OR recommended_action == triage|escalate.

Input includes: signal payload + top-5 lessons matching signal hash + adapter's fix templates + risk-tier policy.

Output: structured triage note (root-cause hypothesis + 1-3 candidate fixes + risk ranking + reversibility plan).

## Proposer (medium tier default; high tier rare)

Fires when triage emits at least one viable candidate.

Default tier = Sonnet-4.6. Escalates to Opus-4.7 ONLY IF:
- The fix is multi-file (3+ files).
- The fix is architectural (introduces new abstraction or schema).
- The fix is a cross-project transferable pattern.
- Daily Opus budget remaining: at least 1 call.

Output: concrete proposal (diff text OR config change text OR delegated-instruction text for target lane's per-project agent).

## Apply gate (rule-based + LLM fallback)

Risk-tier classification table (BINDING):

| Tier | Examples | Default action | Min wait | Operator-required? |
|---|---|---|---|---|
| TRIVIAL | doc typo, comment fix, whitespace | auto-apply | none | no |
| LOW | env config flag flip, log-level adjust, polling-cadence tune | auto-apply | 5 min observation | no |
| MEDIUM | source code change in non-critical surface, dep version bump | 4-hour operator-review window then auto-apply | 4 hr | optional |
| HIGH | credentials, production deploy, financial surface, kill-switch, CI workflow | operator inbox row required, NEVER auto-applies | n/a | YES |
| CRITICAL | (a) fix that failed 3+ times in lessons db, (b) production trading flip, (c) NCMEC reporting flip, (d) anything tagged `_shared-memory/inbox/<lane>` as `critical-surface` | operator inbox + "GO" signature required | n/a | YES + explicit |

Apply gate ALWAYS:
1. Locks the target file(s) via mesh-coord.
2. Snapshots the current state (git stash OR file copy).
3. Writes the diff.
4. Releases the lock.
5. Triggers post-apply observation (5 min window for LOW; 1 hour for MEDIUM).
6. On observation failure: AUTO-REVERT via snapshot, write lessons row, emit fleet-update notice.

## Post-apply observation

For each apply, the adapter declares an OBSERVATION CHECK function. Examples:
- "Did the target project's smoke test still pass within 5 min post-apply?"
- "Did the latency P95 return to pre-incident baseline?"
- "Did the kill-switch state stay ON?"

Observation runs WITHOUT a model call (local code only). If observation fails, the apply is reverted automatically + a lessons row is written.

## Reversibility plan (every apply)

Every applied proposal ships with a REVERSIBILITY PLAN before the apply happens. Plans are one of:
- `git_stash` -- target's current state stashed; revert = `git stash pop`.
- `file_copy` -- target file(s) copied to `_shared-memory/overseer/snapshots/<utc>-<hash>/`; revert = copy back.
- `config_rollback` -- previous config value saved in lessons row; revert = re-write previous.
- `manual` -- operator-only revert path (e.g. real-money trade can't be auto-reverted); used ONLY for CRITICAL tier proposals where operator has signed off.

## Heartbeat

Every 60s the watch loop writes:

```
{
  "agent": "Sinister Overseer",
  "agent_identity": "EVE",
  "slug": "sinister-overseer",
  "attachment": "<project-key>",
  "ts_utc": "<iso>",
  "signals_processed_since_start": <int>,
  "proposals_emitted_since_start": <int>,
  "fixes_applied_since_start": <int>,
  "lessons_captured_since_start": <int>,
  "cost_burn_today_usd": <float>,
  "cap_pct": <float 0-100>,
  "status": "active|throttled|suspended"
}
```

Sanctum's fleet-health view reads this for sibling-detect + overseer-fleet rollups.

## Failure modes (named)

1. **Watch loop dies silently** -- mitigated by heartbeat-sweep cron; stale > 5 min triggers fleet-update notice + auto-restart attempt.
2. **Apply-revert ping-pong** -- mitigated by lessons store: 3+ failures of same shape upgrades to operator-review tier.
3. **Cost cap hit mid-watch** -- mitigated by throttle-at-80 + suspend-at-100.
4. **Mesh-coord lock held by another agent** -- skip this apply, retry next polling cycle, surface to operator after 3 skips.
5. **Adapter version mismatch** -- adapter declares schema version; watch loop refuses to start if mismatched.

## Operator surfaces

- EVE.exe Overseer menu -> per-attached-project sub-page (Outcome 2).
- `overseer list` CLI -> all attachments + their status + cost burn.
- `overseer dryrun --project <key>` CLI -> simulate one watch cycle without applying anything.
- `_shared-memory/inbox/operator/` rows -- cap hits + critical-tier proposals + apply failures.
