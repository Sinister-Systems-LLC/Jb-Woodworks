# Sinister Generator — PROGRESS log

> **Author:** RKOJ-ELENO :: 2026-05-23
>
> Append-only, most-recent first. Display-name file per fleet convention.
> Slug: `sinister-generator` · Lane owner: EVE on `general`.

---

## 2026-05-23T19:30Z — Source-package promotion shipped

**Branch:** `agent/sinister-generator/source-package-2026-05-23` (cut from `agent/rkoj/next-slate-2026-05-23` HEAD `a4b71cf`)

Shipped the `sinister_generator` application-layer Python package on top of the `nano_banana` SDK. All checks green; smoke test passes; no API calls (billing on Google Cloud project `492031902572` still 🔴 in OAQ — separate gate).

**Files added (10):**
- `source/sinister_generator/brands/__init__.py` — exports `jkor_image`, `smpl_image`, `jbw_image`, `BRAND_REGISTRY` (5 keys: 3 canonical + 2 aliases `smpl`/`jbw`)
- `source/sinister_generator/brands/jkor.py` — `JKOR_STYLE` (595 chars) + helper
- `source/sinister_generator/brands/showmasters.py` — `SMPL_STYLE` (187 chars) + helper
- `source/sinister_generator/brands/jb_woodworks.py` — `JBW_STYLE` (219 chars) + helper
- `source/sinister_generator/audit/__init__.py` — re-exports for `append_cost_row`, `structural_check`, `move_to_rejected`
- `source/sinister_generator/audit/cost.py` — markdown cost-ledger writer at `memory/cost-ledger.md`; reads price from `config/models.json`
- `source/sinister_generator/audit/checklist.py` — structural pre-save checks (PNG/JPEG signature, min 1024×1024, meta sidecar present); returns `StructuralReport`
- `source/sinister_generator/audit/reject.py` — moves failed gen + meta sidecar to `_rejected/` with `.reject.txt` capturing reason
- `source/sinister_generator/cli.py` — `python -m sinister_generator --brand jkor|smpl|jbw|jb-woodworks|showmasters|none --prompt ... --output ... [--ref ...] [--no-audit]`. Post-gen runs structural check + appends cost-ledger row.
- `source/sinister_generator/__main__.py` — entry for `python -m sinister_generator`
- `source/_smoke_test.py` — regression check (imports + introspection + structural-check on an existing JPEG; runs without API). Verified passing.

**Files modified (2):**
- `source/sinister_generator/__init__.py` — top-level re-exports for the new brand + audit surfaces; bumped to `__version__ = "0.2.0"`
- `automations/resume-point-write.ps1` — added `sinister-generator` → `Sinister Generator` to the slug→display lookup (resume-point dir) + the slug→PROGRESS.md lookup. Same pattern as the Sanctum fix in OAQ 2026-05-23T08:35Z. Verified live — new resume-point now routes to `_shared-memory/resume-points/Sinister Generator/` and picks up the PROGRESS top-3.

**Smoke test output** (no API call):

```
version: 0.2.0
brands registry keys: ['jb-woodworks', 'jbw', 'jkor', 'showmasters', 'smpl']
Structural check on existing JKOR banner-wide-character.jpg:
  resolution: (1254, 493)  ← below 1024px floor + missing .meta.json
  passes: False
  issues: ['min dimension 493px is below 1024px floor', 'missing .meta.json sidecar']
```

The structural check correctly flagged two real gaps in shipped outputs from earlier today: `outputs/jkor/banners/banner-wide-character.jpg` (1254×493) is below the canonical 1024px floor AND has no `.meta.json` sidecar. Future generations through `python -m sinister_generator --brand jkor ...` (or any direct call to a `brands.<name>_image()` helper through the audit-gated CLI) will be automatically flagged.

**Architecture:** `tools/nano-banana/` stays as the raw Gemini SDK adapter; this project's `source/sinister_generator/` is the application layer (brand locks + anti-slop audit + memory routing). Both surfaces work today — the legacy `from nano_banana import jkor_image` continues unchanged (4× `_one_shot_smpl_*.py` scripts still import this way). The new `from sinister_generator import jkor_image` is the recommended path.

**Open items remaining for this lane:**
- 🟢 Banner v7 iteration — requires Google Cloud billing on project `492031902572` (🔴 in OAQ) + operator visual review
- 🟢 Wire a cost-ceiling check into the CLI (soft budget per project per `config/projects.json`) — not requested this session; deferred
- 🟢 Operator picks whether to `pip install -e D:\Sinister Sanctum\projects\sinister-generator\source\` for fleet-wide import; for now the smoke test demonstrates the sys.path-prepend pattern works

---

## 2026-05-23T19:00Z — Lane bootstrap + source-package promotion (in progress)

**Branch:** `agent/sinister-generator/source-package-2026-05-23` (will cut on first commit)

Fresh `sinister-generator` lane spawn — no prior resume-point. Picked up the open OAQ items:

- **BRAND.md trio verified populated** (not stubs): jkor 108 lines, showmasters 127 lines, jb-woodworks 68 lines. This closes the OAQ row "Have other lane agents drop their BRAND.md into the per-project memory dir" (2026-05-23 — Sinister Generator project live).
- **Building `source/sinister_generator/` Python application layer.** The package was scaffolded earlier today with `compose.py` (PIL local helpers) + empty `brands/` + `audit/` dirs. Promoting:
  - `brands/{jkor,showmasters,jb_woodworks}.py` — thin wrappers around `nano_banana.generate()` with per-brand style suffix + BRAND.md spec loader
  - `audit/{cost,checklist,meta}.py` — cost-ledger append + structural pre-save checks + canonical meta sidecar
  - `cli.py` + `__main__.py` — `python -m sinister_generator --brand jkor --prompt ... --output ...` front door
- **Banner v7 iteration deferred** — needs operator visual review + Google Cloud billing on project 492031902572 (still 🔴 in OAQ). No API calls this session.

Architecture intent: `tools/nano-banana/` remains the raw SDK wrapper (Gemini adapter + `generate()`). This project layers brand-locks + anti-slop audit + memory routing on top. `nano_banana.{jkor_image,smpl_image,jbw_image}` keep working — the new package adds the cleaner application surface without breaking existing callers (4× `_one_shot_smpl_*.py` scripts).
