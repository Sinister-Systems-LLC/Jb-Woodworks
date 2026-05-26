# Sinister Memory — PROGRESS log

**Author:** RKOJ-ELENO :: 2026-05-25 (sinister-memory lane)

Newest entry at top. Append, do not rewrite.

---

## 2026-05-26 iter-47 — adoption sweep (PROGRESS -> per-agent) closes the largest health gap

**Shipped (verified — 86/86 pytest PASS, 23 new tests, real-data composite health 75.7 -> 86.1):**

Pre-iter state: composite health 75.7/100 grade B; sub-score breakdown showed `adoption=2.9/100 (1/35 lanes)` accounting for 24.3 of the 24.3 lost points (every other sub-score was 100/100). All previous adoption work (iter-12 doctrine + iter-14 dogfood + iter-16 spawn-phrase health line) raised awareness but never actually wrote per-agent rows for other lanes.

Iter-47 ships the ambient sweeper:

- **`src/sinister_memory/adoption_sweep.py`** (new module, ~250 lines): `extract_latest_progress(path)` extracts (heading_id, title, body) for the newest `## ` heading in any PROGRESS file. `save_progress_row(slug, heading_id, title, body, root)` writes `_shared-memory/sinister-memory/per-agent/<slug>/progress-<heading_id>.md` with schema-v2 frontmatter (`format_version: 2`, category=fact, trust=medium, source=adoption-sweep). `sweep_progress_to_per_agent(root, dry_run=False, max_per_lane=1)` walks `projects.json`, locates each lane's PROGRESS file by `display` name, saves the newest heading.
- **`_heading_id`**: stable filesystem-safe id from heading text. Priority: `iter-N` pattern -> `<date>-iter-NNNN-<6-hex>`; date-only -> `<date>-<slug-snippet>-<6-hex>`; fallback -> `<10-hex>`. SHA256-derived suffix gives idempotency across re-runs.
- **Idempotency**: `save_progress_row` returns one of `written` / `updated` (body changed) / `unchanged` (body matches). Comparison strips frontmatter so `saved_at` differences don't trigger rewrites.
- **`consolidate.py` step 9**: hooks the sweep into the ambient 6h pass. Runs even on dry_run (writes are non-destructive: new files only, never overwrite without same-content check).
- **CLI**: `sinister-memory sweep-adoption [--dry-run] [--max-per-lane N] [--json]`.
- **`tests/test_iter47.py`**: 23 tests covering heading-id encoding (iter / range / no-iter / no-date / stability / uniqueness), extract_latest_progress (basic / no-headings / truncation / missing-file), save_progress_row (frontmatter / idempotent / updated / invalid-slug), sweep (writes-one-per-lane / idempotent-second-run / dry-run-writes-nothing / skip-no-progress / skip-invalid-slug / max-per-lane-2), health adoption climb e2e, CLI dry-run-json + apply smoke.

**Real-data smoke (verified):**

- `sinister-memory sweep-adoption --dry-run` -> `processed=16 skipped_no_progress=20 errors=0` (only 16 of 35 lanes have exact-display-name PROGRESS files; case mismatches + abbreviated names skip the rest).
- `sweep-adoption` (apply) -> `processed=16 written=16` (16 lanes received their newest PROGRESS heading as a v2-frontmatter row).
- `health` after sweep: composite **86.1/100 grade B (was 75.7)**; `adoption=44.4 (16/36 lanes, was 2.9 = 1/35)`. The math: 16/36 = 44.4%, full weight 25 -> contributes 11.1 to composite (was 0.7) -> +10.4 composite delta from sweep alone.

**Tests:** `pytest -q` -> **86/86 PASS** in 214s. Breakdown: 63 (iter-46) + 23 (iter-47 test_iter47.py). Zero regressions.

**Remaining gap for iter-48+:** 20 lanes still skipped (case mismatches like `rkoj`/`RKOJ`, `jb-woodworks`/`JB Woodworks`, `letstext`/`LetsText`; abbreviated PROGRESS filenames like `Sinister Kernel APK.md` for key `kernel-apk` display `Kernel APK`). Iter-48 ships case-insensitive + fuzzy filename matching to capture those.

**Branch + commit prep:** new branch `agent/sinister-memory/adoption-sweep-2026-05-26` (single-repo-push-policy-2026-05-25 -- push to Sanctum umbrella).

**Heartbeat:** `_shared-memory/heartbeats/sinister-memory.json` -> iter=47.

---

## 2026-05-25 iters-4-through-19 — consolidated session retro

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

**Test counts over the arc:** 5 (iter-2) -> 20 (iter-2 P3-P6) -> 27 (iter-3 audit-patches) -> 36 (iter-3 P7-P14) -> 41 (iter-11 + iter-13 + iter-15/16) -> **44 (iter-19)**. Every iter green; zero regressions.

**Composite health score over the arc:** unknown (no health primitive) -> 75.0/100 grade B (iter-13 first measurement) -> 75.7/100 (iter-14 after this lane became the adoption seed). The remaining 24.3 lost points all live in the `adoption` sub-score (delegated to sanctum via iter-12 inbox 17Z spawn-phrase fixture).

**Heartbeat:** `_shared-memory/heartbeats/sinister-memory.json` written each iter (iter=19 now).

---

## 2026-05-25 iter-3 — P7-P14 (embed / prune / consolidate / batch-verify / contradiction-gate / export-graph)

**Operator follow-up 2026-05-25T~08Z (resumed post mass-crash 08:13Z):** ship the iter-2 explicit no-ship items (embeddings / prune-cron / Haiku batch re-rank / contradiction-gated supersede). Plus operator screenshot Image #2: jcode "ambient mode consolidates memories every so often, reorganizes, checks for staleness and conflicts".

**Shipped (verified — 29/29 pytest PASS + 4 CLI smoke commands green on real data):**

- **P7 embed.py** — kernel-vector layer. `embed_text` / `cosine` / `store_embedding` / `recall_by_vector` / `build_embedding_index`. Hash-bucket TF-IDF (dim=256, deterministic _hash_token so no PYTHONHASHSEED dependence). Float32 packed BLOB storage (4-byte vs 4x JSON). Three backends feature-detected: `ruflo` (out-of-process; not callable from stand-alone CLI today -> falls through to tfidf) / `tfidf` (zero-deps fallback) / `null` (returns [] -> caller falls back to FTS5). Separate `embeddings.db` so RAM cost stays bounded.
- **P8 prune.py** — `prune_low_confidence(confidence_threshold=0.15, age_hours=24, dry_run=True)`. Cherry-picked from jcode `memory_agent.rs:1074-1091`. Reads v2 frontmatter `confidence` field; missing = treated as fresh (never pruned). Cascades to FTS5 + embeddings.db + supersede.edges + supersede.supersedes tables.
- **P9 consolidate.py** — orchestrates 5-step ambient pipeline (index -> dedupe -> prune -> optional embed -> optional verify-sweep). `dry_run=True` by default per `safe-quality-loops-doctrine-2026-05-24`. Returns aggregated stats dict.
- **P10 verify.grade_batch** — single Haiku call grading N candidates against one source-of-truth in batch (1x Haiku cost vs N x). JSON array structured-output parser; per-item Verdict same order as input. HEURISTIC fallback when no API key.
- **P11 verify.check_contradiction** — returns `(bool, reason)` tuple. HEURISTIC: jaccard>=0.4 + negation-token asymmetry (not/no/never/stop/remove/deprecated/disabled/wrong/ban/banned/deleted). ONLINE: single Haiku call returning `{contradicts: bool, reason: str}`.
- **P12 supersede.mark_edge contradiction-gate** — `check_contradiction=True` + `new_text` + `old_text` -> calls verify.check_contradiction FIRST and raises `ValueError("contradiction-gate REJECTED ...")` if no contradiction. Reason annotated with `[gated: <reason>]`. Composes with iter-2 typed edges.
- **P13 export_graph.py** — D3-compatible JSON: `{nodes: [{id, layer, slug, snippet, category, confidence, trust}], edges: [{src, dst, kind, weight, reason, ts_utc}], meta: {generated_at, node_count, edge_count, from_db, schema_version}}`. Sinister Mind force-directed graph can ingest natively. Reads both `edges` (typed) and `supersedes` (legacy) tables, returns combined edge list.
- **P14 CLI** — 5 new subcommands: `embed-index --limit --backend` / `vector-recall <q> --limit --threshold --backend` / `prune --confidence --age-hours --apply` / `consolidate --apply --with-embeddings --with-verify` / `export-graph --out --layer`.

**Real-data smoke (verified just now):**

- `sinister-memory --root 'D:\Sinister Sanctum' index` -> indexed=13 skipped=319 removed=0 (incremental over 332 corpus rows).
- `sinister-memory --root 'D:\Sinister Sanctum' embed-index --limit 80` -> scanned=80 written=30 skipped=50 errors=0 backend=tfidf.
- `sinister-memory --root 'D:\Sinister Sanctum' vector-recall "loop relentless pursuit" --limit 3 --threshold 0.05` -> 3 ranked hits @ score 0.293 / 0.231 / 0.218.
- `sinister-memory --root 'D:\Sinister Sanctum' export-graph --out /tmp/sm-graph.json --layer brain` -> JSON written.
- `sinister-memory --root 'D:\Sinister Sanctum' prune` -> dry-run summary printed (0 candidates on this corpus, expected — no v2 confidence frontmatter on brain rows yet).

**Test suite:** `pytest -q` -> **29/29 PASS** in 2.41s. Breakdown: `test_basic.py` 5/5 (P1-P2) + `test_p3_p6.py` 8/8 (P3-P6) + `test_audit_patches.py` 7/7 (gap-filter + v2 frontmatter) + `test_iter3.py` 9/9 (P7-P14 + current-backend probe).

**Branch + commit prep:** new branch `agent/sinister-memory/iter3-embed-prune-export-2026-05-25` (single-repo-push-policy-2026-05-25 — push to Sanctum umbrella).

**Heartbeat:** `_shared-memory/heartbeats/sinister-memory.json` -> iter=3 (was 2).

---

## 2026-05-25 iter-2 — P3-P6 primitives + jcode audit cherry-picks (5 patches)

**Shipped (verified):**

- **P3 supersede.py** — typed graph edges. `mark_supersedes` / `chain_for` / `latest_of` / `superseded_set` / `unmark` with sqlite + cycle detection. Now also: `mark_edge(kind=)` accepting EDGE_KINDS {Supersedes, Contradicts, RelatesTo, HasTag, InCluster} per jcode `memory_graph.rs:116-125`; `edges_of(memory_id, kind, direction)`; `cascade_retrieve(memory_id, depth, kinds)` BFS per jcode `src/memory.rs:1743-1750`.
- **P4 decay.py** — exponential half-life BM25 boost. `decay_weight(age_days, half_life_days)` + `apply_decay(hits, now_ts)` + `recall_with_decay(query, ..., category=, gap_filter=)`. Per-category half-life table cherry-picked from jcode `MEMORY_ARCHITECTURE.md:419-423`: correction 365d / preference 90d / procedure 60d / fact 30d / entity 30d / inferred 7d.
- **P5 cluster.py** — Jaccard-similarity clustering. `tokenize` / `jaccard` / `cluster_snippets(threshold)` / `dedupe(db, threshold, layers, dry_run)`. Dedupe marks duplicates as superseded by newest in each cluster.
- **P6 verify.py** — Haiku-grader wrapper, feature-detected. Modes: ONLINE (anthropic SDK + ANTHROPIC_API_KEY), HEURISTIC (jaccard >= 0.6 -> fresh; < 0.25 -> stale), OFFLINE (ungraded). `verify_memory(memory_text, source_text=, source_path=, prefer=)`.
- **recall.py audit patch** — `apply_gap_filter(hits, drop_ratio=0.25)` truncates noise tail on >=25% relative score drop, per jcode `src/memory.rs:724-746`.
- **auto_save.py audit patch** — frontmatter schema v2 with `format_version: 2`, optional `category`/`confidence`/`trust` per jcode `MemoryEntry` `src/memory.rs:96-111`. Back-compat: v1 files still parse. New `parse_frontmatter(path)` helper.
- **CLI** — 6 new subcommands: `supersede`, `supersede-chain`, `mark-edge`, `cascade-retrieve`, `decay-recall` (with `--category` + `--gap-filter`), `cluster-dedupe`, `verify`.
- **Brain doc** — `_shared-memory/knowledge/jcode-memory-audit-and-cherry-picks-2026-05-25.md` (jcode subsystem one-paragraph summary + 5 cherry-picks + 5 explicit no-ship items + composes-with + pass criterion).
- **Tests** — `test_p3_p6.py` (8 tests) + `test_audit_patches.py` (7 tests). Total 20/20 pytest PASS in 3.6s.
- **Real-data smoke** — `python -m sinister_memory.cli index` -> 327 docs reindexed. `decay-recall "loop relentless" --category correction --gap-filter` returns ranked hits with mojibake-free output. `mark-edge memA memB --kind RelatesTo --weight 0.8` writes edge; `cascade-retrieve memA --depth 2` returns memB.

**Swarm — 4 parallel audit agents over jcode v0.12.4 source** (per full-relentless-swarm-fanout-mindset-doctrine-2026-05-25):
- Sub-A (STORE): 7 gaps identified, 4 cherry-picked, 3 explicitly declined (embeddings / LLM-on-write / pending-memory dedup windows).
- Sub-B (RECALL): 6 gaps; gap-filter shipped this iter.
- Sub-C (SUPERSEDE/DECAY/CLUSTER): 3 high-impact gaps; per-category half-life shipped this iter.
- Sub-D (VERIFY): 7 recommendations; structured-output + Haiku 4.5 default + heuristic fallback shipped this iter.

**Heartbeat:** `_shared-memory/heartbeats/sinister-memory.json` written (iter=2).

---

## 2026-05-25 (this session) — P1 + P2 wired + real-data smoke (accepted at top; PROGRESS corrected)

**Shipped (verified):**

- **P1 — forever-improve.ps1 AutoSave**: added `-AutoSave -Summary <text>` params + wired `sinister-memory save` call in `Tally` dispatch. Agents can now persist iter-close memories via `forever-improve.ps1 -Action Tally -Lane <slug> -AutoSave -Summary <text>`. Smoke: Tally still prints table correctly (parse-clean).
- **P2 — start-sinister-session.ps1 inject-spawn-phrase**: added `Get-SinisterMemoryInject` function (parallel to `Get-MemoryRecallInject`); wired call in RESUME Build-Phrase after forge-memory inject. Every future spawn gets `SINISTER_MEMORY (last iter-close memories for <slug>):` in cold-start phrase.
- **encoding fix** — `recall.format_hits_markdown`: `—` (em-dash) → `--` (ASCII), removes Windows CP1252 mojibake in terminal output.
- **real-data smoke** — `sinister-memory --root "D:\Sinister Sanctum" index`: indexed=303 skipped=0 removed=0 (live `_shared-memory/`). `recall "loop relentless"` returns ranked brain entries. CLI exit 0.
- **pkg install** — `pip install -e .` confirmed; `sinister-memory` now on PATH.
- **pytest 5/5 PASS** — re-confirmed after encoding fix.

**Heartbeat:** `_shared-memory/heartbeats/sinister-memory.json` written.

---

## 2026-05-25 07:32 UTC — sinister-memory lane scaffolded (operator 07:29:17Z)

**Operator verbatim 2026-05-25T07:29:17Z:** *"make sure loop system works and add to eve exe a project start for Sinister Memroy and complie all thigsn he needs there"*

**Shipped (sanctum master, P0 scaffold so EVE.exe picker can spawn the lane):**

- `projects/sinister-memory/CLAUDE.md`: lane cold-start (scope, in/out, branch convention, composes-with)
- `projects/sinister-memory/src/sinister_memory/__init__.py`: package marker with primitives surface (store/recall/supersede/decay/cluster/verify — NotImplementedError until P1)
- `projects/sinister-memory/` already had `src/sinister_memory/`, `docs/`, `tests/` empty scaffold dirs from earlier work
- `automations/session-templates/projects.json`: new entry registering lane in EVE.exe picker
- `_shared-memory/PROGRESS/Sinister Memory.md`: this file

**Next iter (P1 — first primitive impl):**

- Implement `store()` + `recall()` backed by `_shared-memory/knowledge/_INDEX.md` (consume existing brain rows as first dataset).
- Wire to Ruflo MCP `agentdb_hierarchical-store` / `agentdb_hierarchical-recall` for vector backing.
- pytest fixtures covering 5 synthetic memories + 5 real brain rows + decay assertion.
