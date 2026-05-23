# Sinister Generator — PROGRESS log

> **Author:** RKOJ-ELENO :: 2026-05-23
>
> Append-only, most-recent first. Display-name file per fleet convention.
> Slug: `sinister-generator` · Lane owner: EVE on `general`.

---

## 2026-05-23T16:50Z — 7-tier sorter shipped (📐 Size Off + 👤 Wrong Guy + 🎨 Wrong Style) + 5 iter1 PFPs + 100-pack in flight

Operator directive 2026-05-23T16:38Z verbatim: *"i need new options like good but suize off or good idea but not correct guy etc"*. Existing 3-action sort (Great / Good / Bad) was too coarse — partial-pass gens were being binned with hard rejects, losing salvage paths.

**Shipped (verified):**

1. **3 new tiers wired through the whole stack:**
   - `library/registry.py` — new constants `SIZE_OFF_SUBDIR` / `WRONG_GUY_SUBDIR` / `WRONG_STYLE_SUBDIR`; new BrandConfig properties `size_off_dir` / `wrong_guy_dir` / `wrong_style_dir`; `ensure_sorter_folders()` scaffolds all 7 idempotently.
   - `library/feedback.py` — `LearningState` extended with `size_off` / `wrong_guy` / `wrong_style` lists; scanner pulls each tier; `get_anti_patterns()` now pulls notes from Bad + Wrong Guy + Wrong Style (skips Size Off — those are aspect fixes, not prompt mistakes); `get_endorsed_refs()` UNCHANGED (only Refs + Great + Good become refs — the 3 nuanced-reject tiers don't pollute the ref list).
   - `sorter_web/server.py` — 3 new verdicts (`size_off` / `wrong_guy` / `wrong_style`) with `.sizeoff.txt` / `.wrongguy.txt` / `.wrongstyle.txt` notes; undo unrolls any tier; stats endpoint returns all 7 counts.
   - `sorter_web/index.html` — two-row footer (primary row: Bad / Good / Great / Skip / Undo; secondary row: Size Off / Wrong Guy / Wrong Style), color-coded buttons (teal/amber/magenta), 8-stat header pills, keyboard shortcuts (`S` / `W` / `T` + `4` / `5` / `6`).

   **Smoke tests (green):** library scan → 7 subdirs on disk for jkor; `/api/queue` returns all 7 stat fields (verified live JSON: `great=1 good=8 size_off=0 wrong_guy=8 wrong_style=1 bad=14 refs=2` at 16:50Z); HTML serves 13787 bytes (+ ~2.9 KB vs pre-7-tier).

2. **5 iter1 PFP variants shipped at 16:28Z** (`_fire_jkor_pfp_iter1.py`) — leaned into the canonical peeking pose with 5 variations on lighting/expression/framing (tight-peek, warm-lit, cold-moonlit, eye-contact, horn-forward). 5 ok / 0 error in 70.4s. Operator sort verdict so far: 3 of 5 landed in 👤 Wrong Guy = concept on-direction, character drifted = strong signal for iter2.

3. **100-pack in flight (started 16:49Z)** — `_fire_jkor_100_pack.py`, operator-authorized override of conservative-balance ≤ 6 cap: *"ok give me lik 100 images"*. Composition: 35 PFP (5 lighting × 7 expression matrix) + 25 banner (5 char-position × 5 atmosphere) + 20 card (10 design × 2 treatment; no joker-classic / no tarot) + 12 wordmark (6 layout × 2 typography; no iridescent-glow / no circle-emblem) + 8 logo/icon misc. Refs: canonical pair (banner-CORRECT + peeking-CORRECT). Sequential firing + 1s sleep (AV-quarantine cure). Expected spend: $3.90 if all land; ~23 min wall clock. Progress at 16:50Z: 8/100 ok + 1 text-only-response error (pfp-05-L1-E5).

**Spend so far this session:** $0.39 (10 v1) + $0.78 (20 v4) + $0.51 (10 dual-aspect) + $0.20 (5 iter1) = $1.88; +$3.90 in flight = ~$5.78 today.

**Key learning from operator's first sort with the new tiers:**
> Of 23 sorted gens so far, 👤 Wrong Guy = 8 (the operator's most-used new tier) — meaning concept/composition was on direction but the character kept drifting. iter2 prescription: NOT new prompts; tighter character refs + simplified prompts that focus signal mass on the character vs scene complexity.

**Open for operator:**
- 🟡 100-pack completion (~23 min from 16:49Z, so ~17:12Z) — sort as gens land, sorter auto-polls every 5s
- 🟢 iter2 PFPs after sort settles — character-tightening branch

---

## 2026-05-23T15:26Z — sorter-folder self-heal shipped (operator drag-drop unblocker)

RESUME-mode audit caught a real gap: the 20 JKOR pack PNGs from 14:46Z were sitting in `C:\Users\Zonia\Desktop\JOKR\` flat — but the four sorter subdirs (`💎 Great`, `✅ Good`, `❌ Bad`, `📥 Refs`) **did not exist**, so the operator's drag-drop workflow had no destination folders. Same gap existed for Showmasters + JB Woodworks (their desktop dirs didn't even exist yet).

Root cause: `init_brand()` creates the four subfolders, but seed brands (jkor / showmasters / jb-woodworks) are loaded from `_SEED` without calling `init_brand`, so their subdirs never got scaffolded.

**Fix shipped (3 edits, 1 new helper, 0 API calls):**

1. `source/sinister_generator/library/registry.py` — new public helper `ensure_sorter_folders(cfg)` that idempotently creates `desktop_dir` + the 4 sorter subdirs, returning the list of newly-created paths.
2. `source/sinister_generator/library/feedback.py` — `refresh_feedback()` now calls `ensure_sorter_folders(cfg)` BEFORE scanning. Self-healing: any agent that calls the library API automatically gets sorter folders scaffolded for whichever brand they touch.
3. Imported `ensure_sorter_folders` in `feedback.py` from `registry`.

**Smoke test (PYTHONUTF8=1):**
- `refresh_feedback("jkor")` → 4 subdirs on disk: `['💎 Great', '✅ Good', '❌ Bad', '📥 Refs']`
- `refresh_feedback("showmasters")` → 4 subdirs (folder + subdirs created from scratch)
- `refresh_feedback("jb-woodworks")` → 4 subdirs (folder + subdirs created from scratch)
- All 3 learning JSONs written to `memory/learning/<brand>.json` (each: 0 great + 0 good + 0 rejected + 0 refs, as expected pre-sort)
- `source/_smoke_test.py` re-run → `ALL CHECKS OK` (no regression)
- The 20 existing JOKR pack PNGs still flat in root — unchanged, ready for operator drag-drop

**Operator unblock:** drag-dropping the 20 pack-v4 PNGs into `💎 Great` / `✅ Good` / `❌ Bad` now works. Refs can land in `📥 Refs`. Next `library.generate(brand="jkor", ...)` call will see those moves and auto-bias toward operator-endorsed refs.

**No image generations this turn. Spend: $0.00.** Conservative-balance doctrine: pure code-fix, no Gemini calls — the existing 20-pack is what operator is reviewing.

---

## 2026-05-23T14:46Z — 20/20 JKOR pack variants shipped (5 banner + 5 PFP + 5 card + 5 wordmark)

Task #18 ("Fire 20 gens ... from operator's 2 new packs") complete. All 20 variants generated and verified on disk in `C:\Users\Zonia\Desktop\JOKR\` (31 MB total).

**Two bugs caught + fixed this run:**

1. **`Unable to process input image` (Gemini 400)** — r1 batch ran with 4 refs (above the empirical 3-ref cap from PROGRESS 21:35Z entry); r2 batch dropped to 3 refs but pfp/banner still failed because one of the JOKR `📥 Refs/`+`💎 Great/` refs (`primary-banner-CANONICAL.jpg` or `peeking-pfp-POSE-REFERENCE.jpg` or a stale `💎 Great/*banner-hero-statement*.png`) was malformed for Gemini's input. Cards used a separate ref set (`PACK_CARDS`, `PACK_EXPANDED`, `GREAT_CANONICAL`) and passed.
   **Fix:** new `source/_fire_jkor_pack_all.py` uses just **2 known-good canonical refs** from the Sinister Generator library directly: `Sinister Generator/jkor/banners/banner-CORRECT-canonical-2026-05-23T125744Z.png` + `Sinister Generator/jkor/pfp/peeking-CORRECT-canonical-2026-05-23T125049Z.png`. Both probe-tested individually before the batch; both pass cleanly.

2. **AV-burst quarantine of prior batches** — r1's 5 wordmark + r2's 5 card outputs all returned `status: ok` from the SDK but vanished from disk between bash `ls` and a subsequent Python `os.listdir`. Same pattern as the 21:35Z "3 PNGs vanished" entry — Windows Defender quarantines AI-generated PNGs written in parallel bursts.
   **Fix:** `_fire_jkor_pack_all.py` fires **sequentially** with a 1-second `time.sleep(1)` between writes. All 20 of this batch survived on disk; verified post-run.

**Inventory in `C:\Users\Zonia\Desktop\JOKR\` (20 PNGs, sorter-ready):**

| Kind | Variants |
|---|---|
| Banner (5) | might-magic · iridescent-wordmark-ready · character-ring-halo · action-stance-low-angle · multi-pose-trio |
| PFP (5)    | throwing-card · laugh-fanned-cards · side-glance · spell-cast · arms-crossed-cool |
| Card (5)   | joker-classic · ace-of-diamonds · three-of-diamonds · tarot-the-magician · magic-the-gathering-style |
| Wordmark (5) | hat-icon-stacked · hat-left-text-right · iridescent-glow · circle-emblem · character-left-wordmark-right |

Prompts sourced from `C:\Users\Zonia\AppData\Local\Temp\jkor-pack\*.txt` (operator's 20-prompt pack).

**Refs per kind** (`_fire_jkor_pack_all.py :: pick_refs`):
- banner / pfp / card → 2 refs (banner-CORRECT + peeking-CORRECT)
- wordmark → 1 ref (peeking-CORRECT only, since wordmarks are typography not character art)

**Timing:** 20 gens in ~4 minutes (~12s average each, range 8–31s). All `status: ok`, 0 errors.

**Spend this turn:** $0.78 (20 × $0.039 @ gemini-2.5-flash-image). Including this turn's batch, today's cumulative session: ~$1.67. Conservative-balance doctrine flagged: 20-gen request is above the 6-image soft cap, but this was the explicit task — surfacing in PROGRESS per doctrine.

**Next:** operator drag-drops each PNG into `💎 Great/` · `✅ Good/` · `❌ Bad/` via the sorter web UI (`python -m sinister_generator.sorter_web --folder "C:\Users\Zonia\Desktop\JOKR" --port 7099`).

**7th lesson baked into the system:**
7. *AI-generated PNG bursts trigger Windows Defender quarantine.* Sequential generation with a small inter-write sleep (≥1s) is the empirical cure. Documented in `_fire_jkor_pack_all.py`.

---

## 2026-05-23T21:35Z — 5 PFP + 5 banner variants, character-locked, dual-aspect

Operator directive: *"banner needs to be this size [primary-banner.jpg, 1299×582]. i want both the pfp and banner to have same character on them and banner to be cleaned up do this and make 5 options of each in the correc way"*.

Fired 10 variants in parallel (5 PFP square + 5 banner wide), all locked to the canonical character (primary-banner.jpg + the operator-confirmed `peeking-CORRECT-canonical-...png` as refs[0,1]).

**Two surprises during execution:**

1. **Aspect-swap.** Gemini ignored prompt aspect hints AND ref aspect bias: PFPs labeled `pfp-*` came back at 1536×672 wide (3 of 5); banners labeled `banner-*` came back at 992×1056 square (5 of 5). The character lock held perfectly but the aspect was reversed in ~7/10 cases. Reading order didn't help — even with the square keeper as ref[0] for PFPs, model still went wide for some.

2. **3 PNGs vanished.** Despite `status: ok` returned by the SDK with non-zero `image_bytes`, three files (`pfp-card-throw`, `banner-hero-statement`, `banner-multi-stance`) were missing on disk. Only the `.meta.json` sidecars remained. Likely Windows AV quarantine triggered by the parallel write burst. Re-fired sequentially → all 3 landed.

**Cure shipped:**

- `source/_reshape_jkor_batch.py` — `smart_fit_to_target(src, target_w, target_h)` scales the source preserving smaller dimension + center-pastes onto a target-sized canvas filled with JKOR's canonical deep-purple (#1A0D3A), with a feathered seam. Any source aspect → any target aspect, with the character always centered and visible.
- All 10 originals are preserved in `JOKR/`; reshaped versions land with `-reshaped` suffix at the proper target aspect (1024² square for PFP, 1299×582 wide for banner matching primary-banner.jpg exactly).

**Inventory in `C:\Users\Zonia\Desktop\JOKR\` (20 PNGs):**

| # | PFP variants (1024² square — reshaped) | Banner variants (1299×582 wide — reshaped) |
|---|---|---|
| 1 | `2026-05-23T132745Z-pfp-peeking-classic-reshaped.png` | `2026-05-23T132745Z-banner-char-left-clean-reshaped.png` |
| 2 | `2026-05-23T132745Z-pfp-hero-centered-reshaped.png` | `2026-05-23T132745Z-banner-char-center-spotlight-reshaped.png` |
| 3 | `2026-05-23T133126Z-pfp-card-throw-reshaped.png` | `2026-05-23T132745Z-banner-char-right-action-reshaped.png` |
| 4 | `2026-05-23T132745Z-pfp-wink-reshaped.png` | `2026-05-23T133158Z-banner-multi-stance-reshaped.png` |
| 5 | `2026-05-23T132745Z-pfp-face-only-reshaped.png` | `2026-05-23T133146Z-banner-hero-statement-reshaped.png` |

Plus the 10 raw-aspect originals (kept for `_smoke_test` reproducibility / operator can opt to use them instead).

**Spend this turn:** $0.507 (10 + 3 retries × $0.039). Cumulative session: $0.897.

**6th lesson baked into the system:**
6. *Gemini aspect-locking is unreliable; PIL post-pass is the cure.* Even with ref[0] aspect priming + explicit "do NOT return a square crop" prompts, the model picks aspect arbitrarily. Standard workflow now: generate → check actual size → smart_fit_to_target() into desired aspect. Reshape adds ~0.5s + zero API cost; saves regenerating at $0.039 each.

---

## 2026-05-23T21:05Z — Modular library + feedback loop shipped (operator directive: "1 folder for jokr ... yes/no/refs ... full modular system so all my agents can plug into you")

Operator brief was crystal clear: ONE flat desktop folder per brand, with `✅ Yes` / `❌ No` / `📥 Refs` subfolders. Operator drops new gens into yes/no, drops their own refs into Refs, and the next gen honors that feedback automatically. All fleet agents plug into the same API.

Built — `sinister_generator.library`:

- **`registry.py`** — `BrandConfig` dataclass + brand registry. Seed brands: jkor (desktop `JOKR/`), showmasters (`Showmasters/`), jb-woodworks (`JB Woodworks/`). `init_brand()` lets agents add new brands; saved to `memory/learning/_brands.json`.
- **`feedback.py`** — `refresh_feedback(brand)` scans `Desktop/<brand>/{✅ Yes,❌ No,📥 Refs}/`, parses each image + its `.meta.json` sidecar + any `.endorse.txt`/`.reject.txt`/`.ref.txt` note, and writes `memory/learning/<brand>.json`. `get_endorsed_refs()` returns ranked refs (📥 Refs first, then ✅ Yes); `get_anti_patterns()` returns prompt-ready anti-pattern text from `.reject.txt` notes.
- **`generator.py`** — `library.generate(brand, prompt, kind=None, extra_refs=None)` is the fleet API. Auto-refreshes feedback → pulls endorsed refs → injects anti-patterns into prompt → calls `nano_banana.generate(style_suffix=None)` so refs drive the look (NOT the stale JKOR_STYLE) → lands output directly in the desktop library root.

Operator workflow (documented at `C:\Users\Zonia\Desktop\JOKR\README.md`):
1. Agent drops gen in `JOKR/` root
2. Operator drag-drops into `✅ Yes/` or `❌ No/` (optionally with a `.endorse.txt`/`.reject.txt` note explaining why)
3. Next gen automatically honors the sorting

Fleet-agent workflow (documented at `docs/LIBRARY-AND-FEEDBACK.md`):
```python
from sinister_generator.library import generate
result = generate(brand="jkor", prompt="...", kind="pfp")
# auto-refreshes feedback + pulls endorsed refs + injects anti-patterns
```

**Initial JOKR library state** (after seeding from this session):
- `✅ Yes/` — 1 entry: `peeking-CORRECT-canonical-2026-05-23T125049Z.png` (the operator-confirmed canonical)
- `❌ No/` — 6 entries: all 4 wrong-character PFPs (v1/v2/A/B) + wrong banner + wrong logo (all from the BRAND.md-misread session)
- `📥 Refs/` — 2 entries: `primary-banner-CANONICAL.jpg` + `peeking-pfp-POSE-REFERENCE.jpg`
- Root: `banner-CORRECT-canonical-...png` (has baked JOKR text — operator decides) + `logo-CORRECT-canonical-...png` (large horns properly rendered — likely keeper)

Smoke test green: library imports clean, feedback scanner picks up 1+6+2 entries correctly, ranked refs returned in correct order (refs > endorsed).

**5 lessons baked into the system from this session:**
1. LLM style-suffix wins over prompt — never hard-code suffixes; let refs drive
2. Refs[0] beats refs[1] beats refs[2] — always lead with canonical look-of-record
3. BRAND.md can drift from operator intent — 📥 Refs/ gives a no-Markdown override
4. Operator file moves > Markdown checklists — drag-drop > YAML
5. Aspect ratio: PIL > Gemini — `compose.left_aligned_banner()` for wide aspects

**Session spend:** $0.39 (10 gens × $0.039) — well under $25/mo budget.

---

## 2026-05-23T20:30Z — JKOR variants + banner + logo (operator directive: "fire variants of v2", "do what i said for the banner and logo")

Per operator directive: sent [ASK] to sanctum inbox proposing the JKOR_STYLE patch + fired 4 more gens in parallel (2 variants of v2 + banner + logo).

**Variant A — `outputs/jkor/pfp/peeking-jkor-variant-A-staff-...png`** (1024², $0.039)
- Tried to push the mini-jester-head bell onto a vertically-held staff (vs. v2's held-in-hand)
- Result: model returned a composition very near-identical to v2. The reference-locking is so strong on the v2 keeper that the variant doesn't significantly diverge. Slight cards/staff hand-position shift only.

**Variant B — `outputs/jkor/pfp/peeking-jkor-variant-B-wink-...png`** (1024², $0.039)
- Winking expression (left eye closed, right eye open + arched brow)
- Result: wink is subtle but present. Otherwise locked to v2 composition. Good for "secondary expression" use cases.

**Banner — `outputs/jkor/banners/banner-canonical-...png`** (1024², $0.039)
- Asked for 2.5:1 wide brand banner with character in left third + empty right two-thirds for SVG typography overlay
- Result: model returned 1024×1024 (Gemini's known aspect-ratio-ignore limitation per docs/ANTI-SLOP.md). Character composition is correct + text-free, just not wide.
- **Cure (free, no API):** PIL composite via `sinister_generator.compose.left_aligned_banner(source=this, output=banner-wide-...png, canvas_size=(1620,648), canvas_color=(0x1A,0x0D,0x3A), ...)`. Same pattern used to ship banner-v9 earlier today. Available on operator request.

**Logo — `outputs/jkor/logos/logo-canonical-...png`** (1024², $0.039) — **KEEPER**
- Square icon mark — face-centered, both eyes open, horns + crown + jester hat + collar with central purple gem all readable at small sizes
- Excellent favicon / app icon / social profile mark candidate
- Rounded-square framing came through naturally from the icon-design language in the prompt

**Cross-lane [ASK] dropped:**
- `_shared-memory/inbox/sanctum/2026-05-23T2020Z-ask-from-sinister-generator-jkor-style-jokr-lettering-drop.json` — patch `tools/nano-banana/nano_banana/api.py :: JKOR_STYLE` to drop the JOKR-lettering line so future calls don't need the override

**Session spend so far:** $0.312 (8× $0.039) — 1 rejected (v1 baked-text), 6 kept-or-pending, well under $25/mo budget.

---

## 2026-05-23T20:15Z — JKOR demon-jester peeking-pfp regen shipped (operator unblock confirmed)

Operator gave the green light ("you already have the gemini key do waht i said we are workign to get the jkor imagery"). Fired two generations through `nano_banana.generate()` at `gemini-2.5-flash-image`; v2 is the keeper.

**v1** (`outputs/jkor/pfp/peeking-jkor-regen-2026-05-23T120744Z.png`, 992×1056, $0.039):
- Hit every canonical trait (purple skin, two horns, gold crown in front of jester hat, royal-jester collar w/ central purple gem, mini-jester-head staff, fan of cards, peeking pose, calm dark-purple background)
- **REJECTED** because the model stamped a baked-in "JOKR" wordmark at the bottom — violates JKOR BRAND.md ("text NEVER baked in"). Root cause: `nano_banana.JKOR_STYLE` contains a stale instruction *"The JOKR display lettering stays where the source has it"* which the model honored.

**v2** (`outputs/jkor/pfp/peeking-jkor-regen-v2-2026-05-23T121226Z.png`, 1024×1024, $0.039):
- **KEEPER**. Fixed the SDK-suffix bug by passing a corrected `JKOR_STYLE_NO_TEXT` override (drops the JOKR-lettering line + adds explicit no-text instruction) plus triple-redundant no-text emphasis in the prompt (top-priority bullet block + repeated reminders + final summary line).
- All canonical traits intact; text-free; clean 1024² square; passes the structural audit floor.
- Trade-off: in v2 the mini-jester-head is held in the left hand rather than mounted on the staff. Still present per the canonical-trait list, just composed differently. Operator visual call.

**Total spend this session:** $0.078 (2× $0.039). Logged to `memory/cost-ledger.md`. Proven prompt + lesson appended to `memory/prompts-that-worked.md`.

**Followup filed:** patch `tools/nano-banana/nano_banana/api.py :: JKOR_STYLE` to drop the JOKR-lettering line so future calls don't need the override. Coordinated via [ASK] to the nano-banana SDK lane (not this lane's owned source).

**Open for operator:**
- 👍/👎 on v2 (memory/prompts-that-worked.md entry will record verdict)
- 🟡 nano-banana JKOR_STYLE patch — small targeted edit; can ship cross-lane via [ASK] inbox

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
