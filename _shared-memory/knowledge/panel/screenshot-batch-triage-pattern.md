> **Author:** sinister-panel agent (Claude Opus 4.7) :: 2026-05-21

# Topic: Screenshot-batch triage pattern (operator drops N verbatim asks + 1 screenshot)

**Slug:** screenshot-batch-triage-pattern
**First discovered:** 2026-05-21 17:00 by sinister-panel
**Last updated:** 2026-05-21 13:51 by sinister-panel
**Status:** fixed
**Tags:** panel, ux, triage, batch-shipping, screenshot-driven, no-stop, doctrine, design-system, autonomy

## Problem

Operator regularly drops 3-7 verbatim asks in rapid succession with one screenshot showing the broken UI. Naïve handling = thrash: 7 sequential commits each fixing one ask, 7 deploys, 7 round-trips. Builds drift between asks because some asks invalidate others ("filters menu" makes the "inline chip strip" no longer needed; "no blank space" affects "card sizing"). Single-ask iteration also misses the operator's underlying intent: they're pattern-matching the whole surface, not 7 unrelated bugs.

## Why it happens

The operator's mental model is **per-surface** (Overview, Activity, Fleet PhoneDetail, Command Center, Analytics), not per-component. When they screenshot the dashboard they see all the drift at once and call out everything offensive in one breath. The agent's natural reaction is to enqueue 7 tasks. That's the wrong granularity.

The correct mental model: **bucket by surface, then by chrome-vs-content**. Many asks collapse into shared changes:
- "no scrolling. have a filter menu" + "in a check box manner so i can select many things at once" = ONE component change (replace inline chip strip with multi-select popover).
- "all cards need a concise complete uniform look. i need the text on there never to be cut off" = ONE global rule on `<StatCard>`, not a per-card fix.
- "make this more concise" + "remove all popup menus from the nap" = ONE component change (the `bare` boolean on geo-heat suppresses everything noisy at once).
- "remove double hader here" + "add the folders to the analytics bar here" = ONE refactor (fold platform-tabs INTO TabHeader's right slot, drop the outer useHeaderSlot row).

## Fix or workaround

**Triage rubric for the 7-ask drop (used 2026-05-21):**

1. **Read all asks first.** Don't start until the full operator turn is parsed. They're connected.
2. **Bucket by surface.** Group asks by `app/<page>/page.tsx` they touch. 7 asks → typically 4-5 surfaces.
3. **Detect the meta-pattern.** "Uniform" / "concise" / "no truncation" / "no scrolling" / "no double headers" — these are global rules, not per-card fixes. Identify them and fix at the component primitive layer (`StatCard`, `TabHeader`, `geo-heat`) not at the call-site.
4. **Detect the supersede-chain.** Some asks invalidate other asks. "Filter menu" supersedes "more chip room"; ship the menu, drop the chip-room work.
5. **Batch into ONE commit.** All 7 in one logical commit. One commit message that lists each ask + the fix in a table. Operator's "stop fucking stopping" turn is met with one commit + one deploy, not seven.
6. **Run the 3 gates ONCE at the end.** tsc + next build + doctrine-audit:strict 0/0/0/0/0. If any fails, fix in-place — don't split.
7. **Master self-execute deploy.** SSH + `bash /tmp/remote-deploy.sh --with-backend`. No bat file. No "operator double-click" surfacing. Per canonical-18 + 2026-05-20 no-bat-files directive.
8. **Verify dashboard image rebuilt.** `docker inspect sinister-panel-dashboard:latest --format "{{.Created}}"` — if older than ~2 min, rebuild didn't happen and the deploy is stale. Force `docker compose up -d --build` again. (Bug seen 2026-05-21 in `0c3da2e` cycle — dashboard image cache held an old layer; chunk hash didn't rotate. Fixed by explicit `--build`.)
9. **Snapshot the result for the operator.** PROGRESS row with the ask→fix table + commit hash + LIVE status + verification chain. Plain language. Don't make them re-derive.

## Anti-patterns

- ❌ One commit per ask. The operator already said "complete everything"; making them count to 7 commits is friction.
- ❌ Per-card `truncate`/`overflow` fixes when the meta-pattern is "labels never cut off anywhere" → fix at `StatCard`.
- ❌ Wrapping inline chips in `overflow-x-auto` to "fit one row" when the operator explicitly asked for a Filters menu. Half-measure that signals you didn't read the ask.
- ❌ Deploying without the dashboard image rebuild check, then claiming LIVE when the chunk hash didn't rotate.
- ❌ Asking "should I also do X" between asks. Operator already specified scope; ask is friction unless there's a true ambiguity.
- ❌ Pause-after-batch ("Shipped, awaiting your eyes"). The NO-STOP contract says keep cycling — write resume-point + PROGRESS + pick the next master-actionable row.

## Concrete commit pattern (used 2026-05-21 in `450b426`)

```
panel: 7-fix batch — map bare, KPI links + no-truncate, Filters menu, Fleet auto-size, CC/Analytics header consolidation

| # | Operator ask                                  | Fix                                                                    |
|---|-----------------------------------------------|------------------------------------------------------------------------|
| 1 | "remove all popup menus from the nap"         | geo-heat.tsx: bare boolean prop suppresses leaderboard+tooltip+chips   |
| 2 | "text never cut off no matter what view"      | StatCard.tsx: drop truncate; flex-1 min-w-0 leading-tight break-words  |
| 3 | "allow me to click overview cards hyper link" | 6 KPIs wrapped in next/link to /analytics, /for-use, etc.              |
| ... etc ...                                                                                                            |
```

One commit hash. One LIVE verification. One PROGRESS row. One resume-point.

## Discoveries (append-only log, most-recent at top)

### 2026-05-21 13:51 by sinister-panel
Resume-session validation: pulled chunk 037a41aeac0fb6a7.js from snap.sinijkr.com and confirmed it serves the route table including the KPI link hrefs (`/for-use`, `/chatter`, `/for-sale`, `/account-health`) from ask #3. Demonstrates the deploy genuinely shipped the new code — not just a config flip. Direct DB query confirmed Stage 2 of recover-from-recovery (separate parallel feature) schema is live with 4/4 cols. The screenshot-batch shipping pattern + per-batch verification chain holds up under resume-mode revalidation.

### 2026-05-21 17:00 by sinister-panel
First captured. After 6 deploys across one session (fa87e8a → c9ce2e2 → 0c3da2e → 0905443 → 450b426), the screenshot-batch pattern emerged consistently: operator drops 3-7 asks + 1 screenshot, expects ONE batch deploy that addresses everything. Each cycle the same triage worked: bucket by surface → identify meta-rules → fix at primitive layer → batch commit → master-self-execute SSH → verify chunk rotation. Doctrine-audit + tsc + next build kept zero drift across all 6 commits.

## Related topics

- [panel-master-self-execute-ssh-deploy](./panel-master-self-execute-ssh-deploy.md)
- [panel-doctrine-audit-5-counter](./panel-doctrine-audit-5-counter.md)
- [panel-one-click-deploy-bat](./panel-one-click-deploy-bat.md)
