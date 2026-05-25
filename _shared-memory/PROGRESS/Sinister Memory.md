# Sinister Memory — PROGRESS log

**Author:** RKOJ-ELENO :: 2026-05-25 (sinister-memory lane)

Newest entry at top. Append, do not rewrite.

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
