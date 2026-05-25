<!-- Author: RKOJ-ELENO :: 2026-05-25 -->

# Memory Completion Plan -- 2026-05-25T01:40Z

**Lane:** Sinister Sanctum (mesh-foundation iter 28+)
**Authority:** Operator hard-canonical 2026-05-25T01:25Z *"quantum + memory as main project scope"* + operator 01:40Z *"create a plan to complete all memory things you need to do"*.

Single source of truth for every outstanding memory-system item. Composes with `memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24` + `brain-decay-implementation-schema-2026-05-25` + `gradual-growth-memory-push-eve-exe-ready-2026-05-24`.

---

## 1. Current state (snapshot 2026-05-25T01:40Z)

- **Brain vault:** 195 entries / 193 annotated / 9 superseded / 19 reinforcements bumped
- **Annotation rate:** 100% of real entries (4 missing are README + _TEMPLATE + _INDEX + _INDEX-DECAY-SCORES metadata)
- **EffConf sidecar:** auto-regenerated daily via SinisterToolAutotrigger; current 193 rows
- **3-tier hybrid status:**
  - Tier 1 brain markdown: CANONICAL, healthy
  - Tier 2 decay scoring: SHIPPED + 100% adoption
  - Tier 3 optional accelerators: NOT activated yet (understand-knowledge + Ruflo agentdb + librarian)
- **Overseer Distribute:** every-30-min cron pushing fleet-updates to per-lane inboxes; dedup working
- **Forge-memory-bridge bot:** SHIPPED (smoke OK); NOT wired into `~/.claude/.mcp.json` yet
- **Transcriber bot:** SHIPPED (smoke OK); NOT wired; whisper.cpp not installed (operator step)

---

## 2. The 10-item backlog (priority-ranked)

| # | Item | Effort | Priority | Status |
|---|---|---|---|---|
| M1 | Catch up new sibling brain entries (3-4 new; restore to 100% exactly) | 5 min | P1 | NEXT |
| M2 | Add `EffConf` column to `_INDEX.md` (sidecar exists; the main `_INDEX.md` doesn't show EffConf) | 30 min | P2 | open |
| M3 | Update `overseer-agent-doctrine-2026-05-24` to document the Distribute action | 15 min | P2 | open (Task #55) |
| M4 | Wire `forge-memory-bridge` + `transcriber` into `~/.claude/.mcp.json` | operator-action | P2 | gated |
| M5 | Orphan triage round 2: scan brain for next 10 supersede candidates (only 9 done; ~70 flagged at iter 11) | 1 hour | P2 | open |
| M6 | Invoke `understand-anything:understand-knowledge` on brain (Tier 3 accelerator from hybrid doctrine) | 30 min + plugin runtime | P3 | open |
| M7 | Reinforcement pass: scan brain for entries cited 3+ times in "Composes with" sections; bump their reinforcements | 30 min | P3 | open |
| M8 | Ruflo agentdb Tier 3 activation (HNSW + RaBitQ wire-up) | 4-8 weeks | P4 | operator-gated |
| M9 | Cross-machine memory sync (when Leo's machine pairs via sinister-link) | depends on Leo onboarding | P4 | gated |
| M10 | Brain consolidation: identify duplicate-topic clusters beyond the 2 already merged | 1 hour | P3 | open |

---

## 3. Sequence + dependencies

### Iter N (THIS LANE NEXT ITER)
- Ship M1 (catch up sibling entries; restore exact 100%)
- Ship M3 (update overseer doctrine; small touch)

### Iter N+1
- Ship M2 (add EffConf column to `_INDEX.md`; per-row edit; do programmatically via brain-decay-score.ps1 enhancement)

### Iter N+2
- Ship M5 (orphan triage round 2; spawn Haiku-tier agent to identify next 10 supersedes)
- Ship M7 (reinforcement pass; ditto)

### Iter N+3 (gated on operator)
- Ship M6 (understand-knowledge skill invocation; produces live graph dashboard)
- Surface M4 to operator queue (MCP wire; requires Claude Code restart)

### Iter N+4+ (operator-decision territory)
- M8 (Ruflo agentdb 4-8wk sprint; gated on operator approval)
- M9 (cross-machine sync; gated on Leo onboarding)
- M10 (consolidation pass)

---

## 4. Auto-update propagation discipline (R1 of gradual-growth doctrine)

Every memory ship in this plan must follow the R1 protocol:
1. **Brain entry** (or doctrine update) → `_shared-memory/knowledge/<slug>-<date>.md` + index in `_INDEX.md`
2. **Push to fleet** via `automations/fleet-update.ps1 -Action Push -Kind doctrine|fix|tool|feature -Priority high|normal|low`
3. **Inbox affected lanes directly** for lane-specific deliverables: `_shared-memory/inbox/<their-slug>/`
4. **Overseer Distribute cron** fans out automatically every 30 min

No item in this plan is considered shipped until step (1) and (2) are done.

---

## 5. Quality gates per ship

- Smoke-tested same iter (per `no-bullshit-tested-before-claimed-doctrine-2026-05-23` rule 2)
- Decay-annotated (per `brain-decay-implementation-schema-2026-05-25`)
- Indexed in `_INDEX.md` (catches doctrine-rot)
- Pushed to fleet-update channel (R1 propagation)
- Composes-with-references documented (drives reinforcement on cited entries)

---

## 6. Anti-patterns (do NOT do)

1. Big-bang Tier 3 migration (M8) — keep markdown canonical; Ruflo is supplement, not replacement
2. Annotating with `confidence: 1.0` for non-operator-stated entries (reserve for direct verbatim)
3. Setting `half_life_days < 14` (sub-2-week decay outpaces re-validation cadence)
4. Manual `_INDEX.md` per-row edit for M2 (use the script; less drift)
5. Skipping the R1 fleet-update push (live agents won't see updates until cold-start)
6. Treating M9 as a Sanctum task (it's cross-machine; sinister-link lane owns sync mechanics)

---

## 7. Verification per item

| # | Verification command |
|---|---|
| M1 | `powershell -File automations/brain-decay-score.ps1 -Action Score -TopDecayed 1` → annotated == total |
| M2 | `grep -c '^| ' _shared-memory/knowledge/_INDEX.md` → matches entry count |
| M3 | `grep -A 5 'Distribute' _shared-memory/knowledge/overseer-agent-doctrine-2026-05-24.md` → action documented |
| M4 | `claude mcp list` shows forge-memory-bridge + transcriber connected (after Claude Code restart) |
| M5 | `powershell -File automations/brain-decay-score.ps1 -Action Score -As Json` → superseded count > 9 |
| M6 | `_shared-memory/knowledge/` understand-anything dashboard URL surfaced to operator |
| M7 | Brain reinforcements count > 19 |
| M8 | Ruflo agentdb `.swarm/memory.db` has > 1 entry |
| M9 | `_shared-memory/sinister-link-state.json` shows peer-paired |
| M10 | New supersede chain count, no duplicate-cluster brain rows |

---

## 8. Composes with

- `memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24` (the architectural decision this plan executes against)
- `brain-decay-implementation-schema-2026-05-25` (the decay-frontmatter contract every annotation honors)
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R1 push discipline; R3 prune-as-add)
- `quantum-fleet-discipline-doctrine-2026-05-25` (operator pivot 01:25Z; quantum+memory main scope)
- `sanctum-scope-discipline-2026-05-24` (M9 cross-machine deferred to sinister-link lane)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (every "shipped" claim needs same-iter smoke)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (claim mesh-locks before editing shared brain rows)

## 9. Open operator decisions

- [ ] **M4:** approve `~/.claude/.mcp.json` wire for forge-memory-bridge + transcriber (requires Claude Code restart)
- [ ] **M8:** approve Ruflo agentdb 4-8wk activation sprint (or defer indefinitely; markdown vault is sufficient)
- [ ] **M9:** Leo onboarding status → unblocks cross-machine sync

Default-if-silent: Sanctum auto-ships M1+M2+M3+M5+M7 over next 4 iters per gradual-growth R3 (small + verified + never-stop).
