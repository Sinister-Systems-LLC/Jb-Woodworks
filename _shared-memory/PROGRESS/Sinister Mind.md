# PROGRESS — Sinister Mind

Newest entry at top. Append, do not rewrite.

---

## 2026-05-28T05:30Z — PH4 slice-2 (frontend half): tag-chip click → server fetch + redraw (v0.6.0)

`sinister-mind` lane agent (Opus 4.7 1M). Picked the first row from the 2026-05-28T0347Z resume-point `next_iter_for_mind_agent`: wire tag-chip clicks in `mind/static/mind.js` to fetch `/api/graph?tag=<csv>` and re-render the D3 force-directed graph. Shipped + bumped version since the public surface area changed.

**Shipped (verified):**

- `mind/static/mind.js` v2 → v3: chip click now does an async `loadGraph(Array.from(activeTags))` → `drawGraph(currentGraph)` → `renderSidebar(baseGraph, currentGraph)`. Introduced two-graph split — `baseGraph` (unfiltered, drives sidebar tag-cloud + project pills so chips persist across toggles) vs `currentGraph` (what D3 renders). `applyTagFilter` is now `async`; empty `activeTags` short-circuits to `baseGraph` without a network round-trip. Re-applies the active project-pill dim after redraw since `drawGraph` rebuilds the DOM.
- Stats badge in sidebar shows `[filter: <tags>]` when a filter is active; title-status flips to "filtered".
- Live-status pill cycles `live → filtering → filtered/live` so the operator sees the fetch.
- SSE `graph-change` reload now re-fetches both `baseGraph` AND the filtered slice, so the active filter survives a `_shared-memory/` change.
- `mind/__init__.py` `__version__` 0.5.0 → 0.6.0; `pyproject.toml` 0.5.0 → 0.6.0 + description updated to call out the new surface.

**Smoke:**
- `python -m pytest tests/` → **12/12 PASS in 22.17s** (5 graph_cache + 7 tag_filter regression, no JS changes broke backend tests).
- Node syntax-parse on `mind.js` — `new Function(src)` → OK, 12401 bytes.
- Flask `test_client()` end-to-end: `/api/graph` returns 727 nodes / 265 edges; `/api/graph?tag=$5-per-day-cap` returns 2 nodes / 0 edges + `counts.filtered_by_tags=['$5-per-day-cap']`; CSV `?tag=a,b` honored; empty `?tag=` falls through identity.

**Next iter:** PH5 shortest-path UI polish on top of existing `/api/path` (highlight path-edges + auto-zoom both endpoints), OR Ruflo agentdb semantic-similarity edges (graceful fallback to tag overlap per CLAUDE.md).

---

## 2026-05-28T03:47Z — PH4 slice-1 (backend half): /api/graph tag filter

`sinister-mind` lane agent (Opus 4.7 1M). Picked first item from 2026-05-27T0907Z resume-point `next_iter_for_mind_agent`: "PH4: tag chips click-to-filter graph (frontend mind.js + endpoint /api/graph?tag=)". Shipped the backend half.

**Shipped (verified):**

- `mind/server.py` -- new pure helper `filter_graph_by_tags(graph, tags)` (OR semantics, case-insensitive substring match against each node's `tags` list, drops edges whose endpoints didn't survive, recomputes `counts` + adds `counts.filtered_by_tags`).
- `/api/graph` now accepts `?tag=<tag>` and `?tag=a,b` (CSV). Empty/whitespace tag args fall through to the existing cached graph (cache identity preserved when no filter applied).
- `tests/test_graph_tag_filter.py` (NEW, 7 cases): no-tags returns input identity, single-tag node+edge survival, multi-tag OR, case-insensitive substring, HTTP single-tag, HTTP CSV, empty `?tag=` ignored.

**Smoke:**
- `python -m pytest tests/` -> **12/12 PASS in 0.93s** (5 graph_cache regression + 7 new tag_filter)

**Next iter:** PH4 slice-2 (frontend): wire tag-chip click in `mind/static/mind.js` to fetch `/api/graph?tag=<chip>` and re-render the D3 graph.

---

## 2026-05-27 — iter v0.5.0 (sinister-mind lane) — graph cache

`sinister-mind` lane agent (Opus 4.7 1M). Picked first item from 2026-05-27T080000Z resume-point `next_iter_for_mind_agent`: "Add Flask-Caching for /api/graph". Shipped without adding a new dep — implemented in-process TTL cache (`GRAPH_CACHE_TTL_S=5.0`) for `build_graph()` shared by `/api/graph` + `/api/search` + `/api/path`. `_broadcast_change()` now invalidates the cache, so freshness is preserved on every detected `_shared-memory/` change while burst UI requests during one paint stay sub-ms. `/api/health` reports `{warm, age_s, ttl_s, hits, misses}`. Bumped `__version__` 0.1.0 -> 0.5.0 (was lying), `pyproject.toml` 0.4.0 -> 0.5.0, server header v2 -> v3. Added pytest at `source/tests/test_graph_cache.py` (5 tests, all green): shape, hit-on-repeat, broadcast-invalidates, health-exposes-stats, helper-resets.

---

## 2026-05-27 08:00Z — audit (verdict: NEEDS-SCAFFOLD memory only — code is real)

`untouched-lanes-batch` audited this lane. Real Flask source exists at `source/mind/server.py` (469 LOC, v0.3.0 with SSE live reload + tag-chip support). 8 endpoints active: `/api/graph`, `/api/projects`, `/api/search`, `/api/path` (BFS), `/api/stream` (SSE), `/api/diagrams`, `/api/diagrams/<stem>`, `/api/health`. Watcher thread polls 6 `_shared-memory/` paths every 2s. Lane CLAUDE.md docs the full 10-phase plan. No iter shipped this session — memory-structure-rollout already covered the structural backfill. Resume-point added for next Mind agent. See `_shared-memory/knowledge/untouched-lanes-batch-audit-2026-05-27.md`.

---

## 2026-05-27 — scaffolded by memory-structure-rollout

Created by `memory-structure-rollout` agent to ensure canonical per-lane memory infra (resume-points dir, PROGRESS.md, heartbeat, inbox, CLAUDE.md). No code shipped — structural only.
