# PROGRESS - JOKR

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Display rename history:** JKOR → JOKR (2026-05-24 — Option A, slug `jkor` kept for path stability)

## 2026-05-24 15:55 - RESUME / Option-A jkor→JOKR rename SHIPPED + sorter dashboard LIVE on :7099

**Status:** shipped (verified) — smoke test PASS, sorter HTTP-200, dashboard open in browser.

Operator (verbatim 2026-05-24T15:30Z): *"rename all this to JOKR not jkor. find all dsahbaord and such we was working on and pickup where we left off. open the dashboard in the local host"* → followed by *"do option A and rename the function and outputs"* (15:45Z).

### Shipped (verified this turn)

| # | Item | Evidence |
|---|---|---|
| 1 | `sorter_web/__main__.py` written | `python -m sinister_generator.sorter_web --folder ... --port 7099` now works (was crashing on no-`__main__`) |
| 2 | Sorter dashboard live | `http://127.0.0.1:7099/` — netstat LISTENING pid 21192; `/api/queue` returns 200 with stats `{great:48, good:83, size_off:9, wrong_guy:155, wrong_style:52, skip_concept:4, bad:29, refs:8, queue:0}` |
| 3 | Browser opened to localhost | `Start-Process http://127.0.0.1:7099/` |
| 4 | Function `jkor_image` → `jokr_image` | Smoke import: `from sinister_generator import jokr_image, jkor_image` both work; `jokr_image is jkor_image: True` (back-compat alias preserved). 7 source files edited (api.py, brands/jkor.py, brands/__init__.py, nano_banana/__init__.py, sinister_generator/__init__.py, library/registry.py, library/generator.py). |
| 5 | Constant `JKOR_STYLE` → `JOKR_STYLE` | Both names still importable (alias); JOKR_STYLE preview reads "preserve the canonical JOKR look..." |
| 6 | `outputs/jkor/` → `outputs/JOKR/` | 16 MB / hundreds of files renamed via 2-step `git mv` (Windows case-insensitive). All renames recorded by git as `R` (rename) — history preserved. Desktop junction `C:\Users\Zonia\Desktop\Sinister Generator\` auto-pointed at new `JOKR/`. |
| 7 | `config/projects.json` updated | `display_name: "JOKR"`, `brand_lock_helper: "jokr_image"`, `output_root: "outputs/JOKR/"` |
| 8 | `library/registry.py` BrandConfig updated | `display_name="JOKR"`, `style_helper="jokr_image"` (brand-key `"jkor"` stays as slug-anchor) |
| 9 | Display rename in docs | `projects/jkor/CLAUDE.md` + `projects/jkor/BRAND.md` + per-project canonical `memory/per-project/jkor/BRAND.md` + sinister-generator README/CLAUDE/ANTI-SLOP code-examples |
| 10 | PROGRESS rename | `_shared-memory/PROGRESS/JKOR.md` → `JOKR.md` (2-step rename on case-insensitive Windows) |
| 11 | Heartbeat updated | `_shared-memory/heartbeats/jkor.json` `agent_display: "JKOR"` → `"JOKR"` |
| 12 | Smoke test PASS | `python _smoke_test.py` ran clean: version 0.3.0, structural-check resolved `outputs\JOKR\banners\banner-wide-character.jpg`, both registry keys live |

### What deliberately did NOT change (per Option A — keep slug paths)

- `_shared-memory/heartbeats/jkor.json` (file path stays — slug = `jkor`)
- `_shared-memory/inbox/jkor/` (inbox path stays)
- `_shared-memory/resume-points/jkor/` (path stays)
- `projects/sinister-generator/memory/per-project/jkor/` (path stays — back-compat for hardcoded `BRAND_MD = ...\jkor\BRAND.md` constants)
- `projects/sinister-generator/source/sinister_generator/brands/jkor.py` (file path stays — module imported as `from .jkor import ...`)
- `BRAND_REGISTRY["jkor"]` (key stays — both `"jkor"` AND new `"jokr"` work)
- `projects/sinister-generator/source/_fire_jkor_*.py` (12 fire scripts kept original names — they already target `Desktop\JOKR\` directly, not `outputs/jkor/`)
- Historical PROGRESS / memory / inbox-archive entries (preserve audit trail)

### Back-compat aliases written (so old `from nano_banana import jkor_image` callers don't break)

- `jkor_image = jokr_image` in nano_banana/api.py + brands/jkor.py
- `JKOR_STYLE = JOKR_STYLE` (same alias pattern)
- Both names exported in `__all__` of both packages

### Branch + commit hygiene

- Branch: `agent/jkor/jkor-to-JOKR-rename-2026-05-24` (per CLAUDE.md `agent/<slug>/<topic>` convention; slug stays lowercase `jkor`)
- Not committed this turn (operator hasn't asked for commit). Changes staged for review via `git status -- projects/sinister-generator/` (Rs = renamed, Ms = modified).

### Open

- Operator visual-verify sorter UI renders OK at `http://127.0.0.1:7099/` (we already see queue=0 + 388 sorted images; UI should show the empty-queue state).
- Commit + push to operator OK signal.
- Should fire-scripts `_fire_jkor_*.py` rename to `_fire_jokr_*.py`? They already target Desktop\JOKR directly so functionally fine either way.
