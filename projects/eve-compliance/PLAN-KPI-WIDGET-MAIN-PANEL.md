# Plan — EVE Compliance KPI widget on main admin panel

> Author: RKOJ-ELENO :: 2026-05-25
> Status: PLANNED (not shipped this turn — too much scope on top of R2 + workstation work)
> Open follow-up: #5 from `D:/Sinister Sanctum/projects/eve-compliance/CLAUDE.md`
> Owner: eve-compliance lane

## Goal

Operator (verbatim 2026-05-25): *"prepare for the demo video and linking this to the main panel."*

Surface 4 KPI tiles at the TOP of `/admin` so compliance posture is the first thing a SUPER_ADMIN / COMPLIANCE_AUDITOR sees, not buried under the Image Moderation tab.

## Tiles to ship

| # | Tile | Source | Color rule | Click-through |
|---|---|---|---|---|
| 1 | Scans pending review | `GET /api/admin/image-moderation/queue?status=pending` (count only) | green ≤ 5 / amber 6-20 / red > 20 | open Image Moderation tab |
| 2 | Agencies with active cooldowns | new agg `GET /api/admin/image-moderation/analytics/cooldowns/agencies` | green 0 / amber 1-3 / red > 3 | open agencies tab filtered to "cooldown" |
| 3 | Scanner precision (last 7d) | derived from `ContentScan` rows where `wasGoodCatch != null` | green ≥ 0.95 / amber 0.90-0.94 / red < 0.90 | open analytics drill-down (open follow-up #4) |
| 4 | NCMEC drafts pending submission | `GET /api/admin/image-moderation/ncmec/drafts?status=DRAFT` (count) | green 0 / amber 1-3 / red > 3 (SLA risk) | open NCMEC drafts tab (open follow-up: NCMEC drafts admin view) |

## Files to touch

| File | Change |
|---|---|
| `dashboard/app/(dashboard)/admin/admin-page.tsx` | Add `<EveComplianceKpiStrip />` at top of the page, above the existing tab list |
| NEW `dashboard/components/admin/eve-compliance-kpi-strip.tsx` | The strip itself — 4 tiles in a responsive grid (1 col mobile, 4 col desktop) |
| NEW `dashboard/hooks/use-eve-compliance-kpis.ts` | React-query hook polling all 4 sources every 60s with parallel queries |
| `backend/src/routes/image-moderation.ts` | New endpoints: `/analytics/cooldowns/agencies` (count), `/analytics/precision-rolling?days=7` (computed from labels), `/ncmec/drafts/count?status=DRAFT` |
| `backend/src/lib/__tests__/image-moderation-analytics.test.ts` | NEW — vitest cases for the 3 new aggregations |

## Estimated scope

- Backend: ~150 LOC (3 routes + helper aggregations) + ~8 vitest cases
- Frontend: ~200 LOC (1 hook + 1 component + 1 import in admin-page)
- Total: ~350 LOC + 8 tests
- One agent turn, no operator-action required (no migrations, no env changes)

## Acceptance criteria

1. All 4 tiles visible on `/admin` for SUPER_ADMIN role
2. COMPLIANCE_AUDITOR role sees the strip too (read-only — same as their existing tab access)
3. AGENCY_OWNER role does NOT see the strip (route-level gate)
4. Tile colors update within 60s of any underlying change (poll interval)
5. Click-through navigates to the appropriate deep page
6. `npx tsc --noEmit` PASS in backend + dashboard
7. `npx vitest run` adds 8+ tests without regressing existing 58
8. Operator-eye smoke test: seed 10 scans → counts show 10 pending → mark 5 as good-catch → counts drop to 5

## Dependencies

- Open follow-up #4 (per-agency analytics) — tile #3 (precision) reuses that aggregation logic. If #4 lands first, tile #3 trivially reads from it.
- Operator-action: confirm the dashboard SUPER_ADMIN doesn't already have a different KPI strip we'd be displacing (check `admin-page.tsx` first thing)

## Why not this turn

This turn already shipped R2 (cooldown UI, 5 surfaces, 850 LOC) + the satellite workstation (10+ files) + the Overseer briefing. Stacking a 350-LOC frontend+backend change on top risks quality drift per no-bullshit doctrine rule 8 ("Expansion has quality-degradation limits"). Next iter picks this up clean.

## Next iter intent

Pick this plan as R3. Branch: `agent/eve-compliance/kpi-strip-2026-05-26`. Expected duration: one focused turn, no operator-blockers.
