<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

# Bot Fleet + MCP Server Expansion Plan -- 2026-05-24T21:15Z

**Operator hard-canonical 2026-05-24T20:52Z (verbatim):**
> *"make sure you keep token use in mind and create or exapdn out bot network with new ones or our mcp server. audit all of thise and create a complete plan to do all of it"*

This plan integrates findings from two Haiku-tier parallel sub-agents (bot fleet audit + MCP server audit) into a single execute-able backlog. Token-efficient by design: every recommended add either replaces an Opus-burn workflow OR enables a higher-value workflow that previously required Opus.

---

## 1. Current state (audit summary)

### Bot fleet (13 bots; all operational)

| Bot | Tier | Tools | Usage refs | Verdict |
|---|---|---|---|---|
| vault | 1 | 10 | **2170** | HEAVILY used; no gap |
| scribe | 3 | 7 | **5354** | MOST called (daily digest); caching works |
| researcher | 2 | 8 | 568 | heavy; chains stealth-browser well |
| triage | 2 | 5 | 265 | routine classification, OK |
| sentinel | 1 | 7 | 233 | stable |
| auditor | 1 | 5 | 221 | secrets+freshness OK |
| sinister-bus | 1 | 28 | 164 | backbone |
| watcher | 1 | 5 | 163 | source drift OK |
| custodian | 1 | 7 | 134 | backup daemon OK |
| librarian | 2 | 4 | 105 | **underutilized** vs 8500-MD corpus |
| translator | 1 | 5 | 61 | static catalog; could expand |
| curator | 3 | 8 | 61 | **underused** discovery |
| stealth-browser | 1 | 11 | 51 | underused outside researcher chain |

**Total tools shipped: 110 across 13 bots.** No bot is broken; gaps are around adoption + missing capabilities.

### MCP fleet (22 registered, 4 actively loadable)

| Active (loaded) | Status |
|---|---|
| playwright | high use |
| context7 | med use |
| sequential-thinking | high use |
| memory | med use |
| vault (built-in) | active |
| ruflo (built-in) | mostly dormant (49 tools, ~1 entry stored) |

**18 registered but dormant** (eve / sinister-panel / sinister-snap / sinister-tiktok / letstext + 13 bot servers requiring restart to load).

---

## 2. The 7-item backlog (priority-ranked, effort-estimated)

| # | Item | Type | Effort | Priority | Token-saving estimate | Composes with |
|---|---|---|---|---|---|---|
| 1 | **ingest-router** wrapped as sinister-bus.dispatch hook (no new server; reuses existing bus) | enhancement | 1 day | P1 | ~1-2 Opus turns/day | drop-link Phase 1+2 (already shipped); link-act router (Phase 3 spec) |
| 2 | **transcriber** new Tier-1 bot (whisper.cpp wrap) | new bot | 1 day | P1 | $0.05/min audio replaced; unblocks drop-link video kind | link-download.ps1; drop-link-ingest-spec |
| 3 | **forge-memory-bridge** new Tier-1 bot (unifies 3-tier hybrid memory layer; canonical facade replacing the empty CLI stub) | new bot | 1 sprint | P1 | ~25k tokens/month from de-duplicating Opus brain-recall | memory-backbone-3-tier-hybrid + brain-decay-score.ps1 + librarian.search |
| 4 | **brain-semantic-search MCP** wrapping memory.db HNSW + brain markdown corpus (cross-session semantic recall the operator can grep without loading librarian) | new MCP | 2-3 days | P2 | ~2k tokens/query | librarian + Ruflo agentdb (Tier 3 from memory-backbone doctrine) |
| 5 | **librarian re-index** + adoption push (FAISS over 8500-MD corpus is built but underused) | use-existing | 1 day (index rebuild) + ongoing doctrine | P2 | indirect: every brain-grep Opus replacement | brain markdown vault canonical |
| 6 | **curator scan run** on whole sanctum (currently 61 refs; should be more for code-library proposals) | use-existing | 1 day cron schtask | P3 | ~$0.05/run for cross-project helper hunt | curator existing tooling |
| 7 | **Deprecate 18 dormant MCPs** from ~/.claude/.mcp.json (eve / sinister-panel / sinister-snap / sinister-tiktok / letstext etc -- they're registered but unused, add startup latency, confuse the deferred-tool list) | prune | 1 hour | P3 (operator-gated; mcp.json is operator-owned) | prune-as-add doctrine |

---

## 3. What we are NOT shipping (no-bullshit rule 6 laser-focus)

- **No new Tier-3 bots** (Haiku-priced). scribe + curator already cover that band; adding more would 2x the daily spend without proportional value.
- **No Ruflo big-bang migration.** Memory-backbone doctrine already says Ruflo is OPTIONAL accelerator (Tier 3). 4-8 weeks of effort for marginal gain over markdown vault.
- **No federation / multi-machine sync this plan.** Cross-machine memory sync = next plan when there's a concrete second machine in play (Leo's machine is one but operator-gated).
- **No agentdb hooks activation right now.** Token-saving estimate for those is small; defer until a workflow demands it.

---

## 4. Execution sequence (composes with gradual-growth + loop-mode canonicals)

### Iter N (this lane next iter)
- Ship `automations/ingest-router.ps1` OR add the routing surface as a new action on sinister-bus (operator preference: standalone OR bus-tool). Smoke with the existing 4 queue rows from link-ingest.

### Iter N+1
- Ship `bots/transcriber/` (whisper.cpp wrap). Wire into link-download.ps1 for instagram-video + youtube-video kinds. Smoke with one operator-provided Instagram URL.

### Iter N+2
- Ship `bots/forge-memory-bridge/` Tier-1 facade. Migrate forge-memory CLI stub callers to the bridge. Brain entries see no change (markdown stays canonical); the bridge is purely a unified read surface for `recall <topic>` queries.

### Iter N+3 (operator-gated; surface to queue)
- brain-semantic-search MCP build OR Ruflo hooks activation (operator picks based on which workflow blocks first)

### Iter N+4 (housekeeping)
- librarian reindex + curator full scan as scheduled tasks (cron schtask).
- MCP prune (operator review of dormant entries).

**Per loop-mode canonical:** each iter ends with a verified ship + queues the next; no ScheduleWakeup; consolidation only when rule-8 signals fire.

---

## 5. Sinister OS linkage (operator 20:36Z "switching to it")

| Component | Windows today | Sinister OS port |
|---|---|---|
| ingest-router | .ps1 wrapper around sinister-bus | systemd-managed Python module |
| transcriber | whisper.cpp via Python wrapper | same; whisper.cpp is Linux-native first |
| forge-memory-bridge | Python MCP server | same; no Windows-specific |
| brain-semantic-search MCP | Python MCP wrapping memory.db | same |
| MCP loading | `~/.claude/.mcp.json` (Windows-userprofile) | `~/.claude/.mcp.json` (Linux-userprofile); identical schema |

Every item in this plan ports unchanged. Sanctum bots are Python; markdown is plain text; MCP is JSON config. **Port, not rewrite.**

---

## 6. Token-efficiency dashboard (estimated monthly savings if all P1+P2 ship)

| Win | Source | Monthly tokens saved |
|---|---|---|
| ingest-router replaces operator-manual triage of drops | item 1 | ~10k |
| transcriber replaces Opus for video transcription | item 2 | ~30k (varies w/ link volume) |
| forge-memory-bridge de-duplicates brain-recall Opus paths | item 3 | ~25k |
| brain-semantic-search MCP replaces grep-then-summarize | item 4 | ~15k |
| **Total P1+P2 estimated savings** | | **~80k tokens/month** |

(Confidence: medium. Actual numbers will refine as we measure post-ship.)

---

## 7. Open decisions for operator (silence-approve in 3 lane turns per gradual-growth R3)

- [ ] Approve P1 backlog (ingest-router / transcriber / forge-memory-bridge) as 3-iter ship schedule?
- [ ] Approve P3 deprecation of 18 dormant MCPs from `~/.claude/.mcp.json` (operator-owned file; requires explicit nod)?
- [ ] Prefer ingest-router as standalone `.ps1` OR as a new sinister-bus tool? (default: bus tool to avoid script-proliferation per prune-as-add)

**Default-if-silent:** ship P1 backlog in order; defer P3 mcp.json prune until operator confirms; default ingest-router as sinister-bus tool.

---

## 8. Composes with

- `memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24` (Tier 3 = forge-memory-bridge canonical recall)
- `drop-link-ingest-spec-2026-05-24` (Phase 1+2 shipped; Phase 3 analyze uses scribe + ingest-router)
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R1 push: each ship -> fleet-update; R2 EVE-ready: bots discoverable on next spawn via existing MCP wiring; R3 gradual: 7 items not 1 monolith)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (Tier 1 bots wake via bot-lifecycle.ps1 on demand; sleep at refcount=0)
- `sanctum-scope-discipline-2026-05-24` (this is fleet-shape work -- in Sanctum scope)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (every ship in §4 = smoke-tested same iter)
- Master plan: `_shared-memory/plans/sanctum-master-plan-2026-05-24T2020Z/plan.md` (this expansion plan extends master section 5 + bot-fleet items)

## Verification (after ship)

```powershell
# Section 2 P1 items as they land
ls automations/ingest-router.ps1
ls bots/transcriber/server.py
ls bots/forge-memory-bridge/server.py

# Use the dashboard
powershell -File automations/claude-accounts-status.ps1 -Mode Board
powershell -File automations/bot-lifecycle.ps1 -Action List
powershell -File automations/mesh-coordinator.ps1 -Action List
powershell -File automations/fleet-update.ps1 -Action List -Tail 5 -Slug sanctum
```
