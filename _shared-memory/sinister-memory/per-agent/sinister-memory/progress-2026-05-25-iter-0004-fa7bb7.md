---
format_version: 2
author: RKOJ-ELENO
slug: sinister-memory
heading_id: 2026-05-25-iter-0004-fa7bb7
saved_at: 2026-05-26T21:11:31Z
length: 6035
category: fact
confidence: 0.500
trust: medium
source: adoption-sweep
---

# sinister-memory :: 2026-05-25 iters-4-through-19 — consolidated session retro

Same calendar day as iter-3, but a long uninterrupted relentless-loop session (operator hard-canonical `/loop create a plan to complete + contradict everything ... until you go down in quality`). Each iter has its own heartbeat row in `_shared-memory/heartbeats/sinister-memory.json` (overwritten each iter; full history was relayed iter-by-iter in the operator's terminal). Condensed retro:

**iter-4 :: ROOT-CAUSE for fleet-wide memory loss** — bash-style `--root /d/Sinister Sanctum` was a relative path on Windows, writing FTS5 to a phantom DB. Patched `sinister_memory.cli._normalize_path` (`/<drive>/<rest>` -> `<DRIVE>:/<rest>`). Rebuilt index at canonical path (327 rows). Verified recall returns hits. Fleet broadcast posted. Brain doctrine: `sinister-memory-path-bug-and-restore-doctrine-2026-05-25.md`.

**iter-5 :: R1 auto-rebuild-on-stale-detect** — `recall.py _peek_newest_source_mtime` + `_auto_rebuild_if_stale`. Stale FTS5 auto-refreshes before every recall (~1ms stat cost). Just-written brain rows immediately recallable. Operator-named spawns LIVE: sinister-mcp PID 46968 + sinister-panel PID 60176.

**iter-6 :: R11 fleet-updates rotation + R2 RRF + R3 --lane** — Three shipped. R11: `rotate_fleet_updates.py` compacted 1.33 GB -> 18.5 KB live (archive preserved); future PS broadcasts no longer OOM. R2: BM25+cosine RRF merge default-on in `recall()`; `--no-rrf` opts out; RRF surfaces semantic cross-refs BM25 misses. R3: `--lane <slug>` filter restricts to per-agent + brain.

**iter-7 :: R4 PROGRESS rotation** — `rotate_progress.py` + applied to 6 oversized files (1.44 MB -> 510 KB live + 932 KB archived). Footer in live files points to archive. Plus systemic git race finding flagged out-of-scope to sanctum.

**iter-8 :: R7 LRU cache + consolidate.py steps 6+7** — `_RECALL_CACHE` with mtime_ns-keyed bust; cold 50.7s -> warm 1.0ms (~50,000x speedup). Consolidate gained rotate-progress + rotate-fleet-updates as ambient steps (6h pass auto-maintains).

**iter-9 :: D8.4 per-lane audit (operator's "full auditing starting with main projects")** — `audit_per_lane.py` + first audit report. 35 lanes measured. Three systemic gaps named: 0/35 saves; only sanctum has embeddings; 0 supersede edges. Triage taxonomy formalized (path-bug / stale-index / adoption). Brain doctrine: `sinister-memory-audit-systemic-gaps-2026-05-25.md`.

**iter-10 :: embeddings batched-insert speedup** — diagnosed slow per-row open/close (25h estimate); patched to batch in single transaction + WAL + synchronous=NORMAL. Full 30K-row rebuild in 32s (~2800x speedup). Closed gap #2 from iter-9 audit.

**iter-11 :: R8 IDF table** — `build_idf_table` / `save_idf_table` / `load_idf_table` + integrated in `build_embedding_index` + `embed_text(idf=)` param + `_IDF_CACHE` module global. Sklearn-style smoothed IDF. 3 new regression tests (iter-10 batched-insert throughput floor + iter-11 IDF persist/reload + IDF distinguishes rare terms).

**iter-12 :: full IDF-active rebuild + adoption-gap doctrine** — 30,270 rows rebuilt with IDF in 113s. Quality verified on 3 queries (RRF+IDF surfaces P7 PROGRESS entry as top hit for "embeddings cosine kernel vector"). Brain doctrine: `sinister-memory-save-adoption-doctrine-2026-05-25.md` + sanctum inbox 17Z with spawn-phrase fixture + 3 optional auto-save hooks.

**iter-13 :: composite memory health primitive** — `sinister_memory.health` + `sinister-memory health [--json]`. 7 weighted sub-scores (index 15 + embeddings 15 + layer-coverage 10 + recall 15 + vector 10 + rotation 10 + adoption 25 = 100). Real-data: **75/100 grade B** (only adoption gap remaining). 4 regression tests.

**iter-14 :: eat-own-dog-food** — invoked `sinister-memory save` for sinister-memory lane (5 per-agent rows: iter-10/11/12/13/14). Surfaced 2 bugs same-iter: CLI save missing --category/--confidence/--trust flags (wired); health _sub_adoption checked only fleet-root per-agent dir (now checks both canonical + fleet-root paths). First real Contradicts edge fleet-wide: `iter-4-fix:cli._normalize_path --Contradicts--> broken-pre-iter-4:cli-relative-path-bug`. Health 75.0 -> 75.7.

**iter-15 :: consolidate end-to-end verified + memory-doctor primitive** — verified all 7 consolidate steps fire correctly on real 30K corpus. New `sinister_memory.doctor` + `sinister-memory doctor [--json]`: picks worst-leverage sub-score (lost_points) + emits exact fix command. On real data: identifies adoption (24.27 lost pts) + emits save recipe.

**iter-16 :: spawn-phrase health line** — `spawn_inject._health_one_liner` + `inject_for_spawn(include_health=False)` keyword + CLI `--include-health` flag. Every future spawn that uses the flag sees `SINISTER_MEMORY_HEALTH: 75.7/100 (B); worst=adoption (24.27pt loss); run sinister-memory doctor for fix` at cold-start. 5 regression tests.

**iter-17 :: per-lane briefings** — `generate_lane_briefings.py` + 32 per-lane briefing docs at `_shared-memory/audits/per-lane-briefings/<slug>.md`. Each: top-5 R3 --lane recall + last 5 per-agent saves + recent supersede edges + cold-start hint. Plus `_INDEX.md` +2 rows for previously-unindexed iter-9 + iter-12 doctrines.

**iter-18 :: consolidate step 8 + CLI reference doc** — extended consolidate.py with step 8 `lane_briefings` auto-regenerate (ambient 6h pass refreshes briefings without manual invocation). Plus comprehensive `docs/00-cli-reference.md` covering all 18 CLI subcommands + 4 script-only utilities + common workflows + cross-references to brain doctrines. End-to-end consolidate run on real corpus: lane_briefings=35 written.

**iter-19 :: end-to-end consolidate integration test** — `test_consolidate_end_to_end.py` with 3 cases: all-eight-steps shape check + step-8 briefing content + apply-persists-rotation. Catches future regressions in the 8-chain wiring.

**Test counts over the arc:** 5 (iter-2) -> 20 (iter-2 P3-P6) -> 27 (iter-3 audit-patches) -> 36 (iter-3 P7-P14) -> 41 (iter-11 + iter-13 + iter-15/16) -> **44 (iter-19)**. Every iter green; zero regr

... [truncated by adoption_sweep]
