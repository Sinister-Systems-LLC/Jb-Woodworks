# Brand-Library Workflow — repeatable image-gen + sort + iterate process

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Status:** binding (operator hard-canonical 2026-05-23T18:14Z: *"document this entire process as we are going to do this type of thing many times in many different ways"*)
> **Composes with:** `sinister-generator/CLAUDE.md`, `library/registry.py` (BrandConfig + ensure_sorter_folders), `library/feedback.py` (refresh + get_endorsed_refs + get_anti_patterns), `library/generator.py`, `sorter_web/`.

The reusable end-to-end workflow for running an image-gen iteration loop on any new (or existing) brand. Codified after the JKOR session 2026-05-23 (~$13 spent across 300+ gens) so the next brand starts with all the learnings baked in.

## The 9 phases

```
1. brand-init       → register the brand + scaffold desktop folders
2. ref-seed         → drop initial canonical refs into 📥 Refs/
3. fire-100         → first 100-pack (broad sweep across kinds)
4. operator-sort    → operator triages outputs into 9 tiers via web sorter
5. ref-promote      → operator clicks 🪄 Use as Ref on production-ready gens
6. read-signals     → master agent reads sort verdicts via library.feedback
7. iter-fire        → next 100-pack with refreshed refs + tightened anti-patterns
8. style-pivot      → if operator flags a wrong aesthetic, rewrite design DNA
9. chain-iter       → auto-fire next iteration when current finishes
```

Each phase has reusable patterns — pull from this doc, don't reinvent.

## Phase 1 — brand-init

For a new brand "foo":

```python
from sinister_generator.library import init_brand
init_brand(
    brand="foo",
    display_name="FOO",
    desktop_name="FOO",  # operator-facing desktop folder name
    kinds=["pfp", "banner", "card", "wordmark", "logo"],
    default_kind="pfp",
    style_helper="",  # optional nano_banana helper function name
)
```

Scaffolds:
- `C:\Users\Zonia\Desktop\FOO\` desktop library root (where gens land + operator sorts)
- 7 sort subdirs: `💎 Great` / `✅ Good` / `📐 Size Off` / `👤 Wrong Guy` / `🎨 Wrong Style` / `♻️ Skip Concept` / `❌ Bad`
- 1 ref subdir: `📥 Refs`
- `memory/learning/foo.json` (auto-written on first `refresh_feedback`)

Existing seed brands (jkor / showmasters / jb-woodworks) self-scaffold via `ensure_sorter_folders` called from `refresh_feedback`.

## Phase 2 — ref-seed

Initial canonical refs drop into `📥 Refs/`:

```bash
cp "C:\path\to\canonical-banner.png" "C:\Users\Zonia\Desktop\FOO\📥 Refs\"
cp "C:\path\to\canonical-pfp.png"    "C:\Users\Zonia\Desktop\FOO\📥 Refs\"
```

**Rules:**
- Refs in `📥 Refs/` are highest authority — `get_endorsed_refs` returns them first
- Naming: prefix with description so they sort meaningfully (`primary-banner-CANONICAL`, `peeking-CORRECT-canonical`, etc.)
- `max_refs=4` cap on Gemini calls — keep `📥 Refs/` short (1-4 entries ideal)
- Multiple character variants: keep ONE per identity; don't pollute Refs with sub-variants

## Phase 3 — fire-100 (first sweep)

Use the canonical fire-script template at `source/_fire_jkor_100_pack.py` as the pattern. For brand `foo`, copy + retitle:

```python
"""Fire 100 FOO variants — broad sweep."""
from sinister_generator.library import refresh_feedback, get_endorsed_refs
# ... build variant prompts per family ...

def pick_refs(kind: str) -> list[pathlib.Path]:
    return get_endorsed_refs("foo", max_refs=4)
```

**Composition pattern (5 families = 100):**
- 35 PFP — pose × lighting matrix
- 25 Banner — composition × atmosphere matrix
- 20 Card / product-shape variants
- 12 Wordmark / typography variants
- 8 Logo / icon contexts

**Rules:**
- **Sequential firing + `time.sleep(1.0)` between writes** — AV-quarantine cure
  (Windows Defender quarantines AI-gen PNG bursts; sequential survives)
- Each gen lands in `<desktop_root>/<prefix>-<utc>-<kind>-<slug>.png`
- `.meta.json` sidecar carries prompt + refs + model for audit
- Multi-ref via `get_endorsed_refs(max_refs=4)` — NOT single-ref
  (operator hard-canonical 2026-05-23T17:32Z: "i need the purple skull we have on
  the photos i marked good and great" — multi-ref locks character far harder)

**Fire it backgrounded:**
```bash
nohup python -X utf8 source/_fire_foo_100_pack.py > /tmp/fire-foo-100.log 2>&1 < /dev/null &
disown
```

**Monitor for events:**
```
tail -n 0 -F /tmp/fire-foo-100.log | grep --line-buffered -E "ok |ERROR|EXCEPTION|^\[\*\] Done"
```
(Monitor tool auto-emits one event per gen.)

**Cost:** 100 × $0.039 = $3.90 at gemini-2.5-flash-image. Surface in PROGRESS.

## Phase 4 — operator-sort (9-tier semantics)

Operator opens `http://127.0.0.1:7099/` (the sorter web UI):

```bash
nohup python -X utf8 -m sinister_generator.sorter_web --folder "C:\Users\Zonia\Desktop\FOO" --port 7099 > /tmp/sorter.log 2>&1 < /dev/null &
disown
```

**9-tier semantics** (operator hard-canonical 2026-05-23T18:14Z: *"ok when i say great it doesnt mean i would use it if i say use as ref that means i would use it"*):

| Verdict | Folder | Semantic | Used as ref next gen? |
|---|---|---|---|
| 🪄 USE AS REF | `📥 Refs/` | **"I would actually use this — production-ready"** | ✅ refs[0..3] highest priority |
| 💎 GREAT | `💎 Great/` | Strong positive — high quality, NOT necessarily production-ready | ✅ secondary refs (rank below 📥 Refs) |
| ✅ GOOD | `✅ Good/` | On theme, needs work | ✅ tertiary refs (rank below 💎) |
| 📐 SIZE OFF | `📐 Size Off/` | Good idea, wrong size/aspect → PIL reshape candidate | ❌ not a ref (style is ok, aspect is wrong) |
| 👤 WRONG GUY | `👤 Wrong Guy/` | Good concept, character drifted | ❌ not a ref (don't propagate the drift) |
| 🎨 WRONG STYLE | `🎨 Wrong Style/` | Good composition, wrong vibe/lighting/palette | ❌ not a ref (don't propagate the vibe) |
| ♻️ SKIP CONCEPT | `♻️ Skip Concept/` | Drop this prompt direction in future iter | ❌ + treated as anti-pattern signal |
| ❌ BAD | `❌ Bad/` | Reject outright | ❌ treated as anti-pattern (notes pulled into next prompt) |

**Critical:** 💎 Great ≠ "would use" — that's what 🪄 Use as Ref means. The 9-tier UI must NOT label 💎 Great as "would use as-is" or similar (label corrected 2026-05-23T18:14Z).

**Keyboard shortcuts:** `N/Y/G/R/S/W/T/C` letters + `1-8` numerics + `␣` skip + `U` undo.

## Phase 5 — ref-promote

Operator's `🪄 Use as Ref` button moves a PNG into `📥 Refs/` directly. The next `get_endorsed_refs(brand)` call picks it up at the top of the rank.

This is the **highest-leverage operator action**: it directly steers the next iteration's character lock. Every iter+ should pull `max_refs=4` from `📥 Refs` first.

## Phase 6 — read-signals

Before firing iter2+, refresh + read:

```python
from sinister_generator.library import refresh_feedback, get_endorsed_refs, get_anti_patterns

state = refresh_feedback("foo")
print(f"💎 Great:     {len(state.great)}")
print(f"✅ Good:      {len(state.good)}")
print(f"📐 Size Off:  {len(state.size_off)}")
print(f"👤 Wrong Guy: {len(state.wrong_guy)}")
print(f"🎨 Wrong Style: {len(state.wrong_style)}")
print(f"♻️ Skip Concept: {len(state.skip_concept)}")
print(f"❌ Bad:       {len(state.rejected)}")
print(f"📥 Refs:      {len(state.references)}")

refs = get_endorsed_refs("foo", max_refs=4)  # ranked Refs > Great > Good
ap = get_anti_patterns("foo")                # anti-pattern text from Bad + Wrong Guy + Wrong Style + Skip Concept notes
```

**Reading the verdict mix:**
- **👤 Wrong Guy dominant** → prompt direction is right, character refs aren't locking it. Add more refs / tighter character lock language.
- **🎨 Wrong Style dominant** → composition is right, aesthetic is wrong. Pivot DESIGN DNA in next iter.
- **♻️ Skip Concept dominant** → prompt families are misaligned. Drop those families in next iter.
- **❌ Bad dominant** → fundamental mismatch. Audit refs + character lock; consider full re-canonical.
- **💎 Great dominant** → strong direction, iterate within the same prompt space.
- **🪄 Use as Ref dominant** → production-ready, scale up to full pack.

## Phase 7 — iter-fire (next 100-pack)

Copy the iter1 fire script, rename `_fire_foo_100_pack_iter2.py`, then:

1. Update prompt FAMILIES (different axes than iter1 — pose × scene vs lighting × expression)
2. Keep CHARACTER_LOCK + DESIGN_DNA constants
3. Add iter-specific REJECTION_ANTI_PATTERNS from operator's sort notes
4. `pick_refs()` calls `get_endorsed_refs("foo", max_refs=4)` — auto-refreshed

**Key learning** (operator hard-canonical 2026-05-23T17:32Z): **always default to multi-ref via the library**. Single-ref fire scripts are an anti-pattern.

## Phase 8 — style-pivot

When operator says "I want X aesthetic not Y" (e.g. JKOR 17:55Z: *"i want psycheldilic art not shitt crown king backgrounds"*):

1. **Stop current fire** if still running on the wrong aesthetic (`taskkill /F` the python pid)
2. **Rewrite DESIGN_DNA constant** in the active fire script — replace rejected adjectives with desired ones
3. **Update REJECTION_ANTI_PATTERNS** — explicitly enumerate the old aesthetic as anti-pattern
4. **Restart fire** from where it stopped (`--start N`)

The DESIGN_DNA constant is the leverage point — keep it as a single block so style pivots are one-edit.

### Style-pivot history — JKOR 2026-05-23

| Time | Operator directive | Pivot |
|---|---|---|
| 17:55Z | "i want psycheldilic art not shitt crown king backgrounds" | Drop royal/cosmic/library/casino scenes; embrace psychedelic mandalas/swirls |
| 18:24Z | "dont make background so bright" | Darken the psychedelic palette; restrained accents |
| 18:25Z | "make everything around selling snapchat accounts with sinister panel snap all that" | Pivot content theme from generic JKOR to Snapchat-account-sales focus |
| 18:26Z | "not so bright background more suttle professional sleek approach" | Drop loud psychedelia entirely; subtle + professional + sleek |
| 18:28Z | "but we are called jokr" | Brand remains JOKR (selling Snap accounts SOLD BY JOKR, not generic 'Snap accounts') |
| 18:29Z | "no words and all that shit way less bright and not as psychedilic a clean professional sleek approach" | **NO BAKED TEXT in imagery** — pivot to imagery-only pack; text overlays added later as SVG/CSS |

The 18:29Z directive triggered a full rewrite of the fire script content (HERO_TITLES / FEATURE_BUNDLES / PRICING_TIERS lists removed entirely). Replaced with imagery-only variant briefs that explicitly anti-pattern baked text. See `_fire_jkor_100_pack_clean.py` for the canonical imagery-only template.

### Key style-pivot lesson: imagery-only > text-baked

Once an operator wants production-grade selling-pack visuals, the imagery should be **text-free**. Text overlays add as SVG/CSS at the page layer — far easier to A/B test, localize, and edit than re-generating a $0.04 image to change a price. The 6 fire-script families (hero / feature / pricing / platform / lockup / thread / product) in iter3-snap baked text in, which got rejected; the 7 families in `_fire_jkor_100_pack_clean.py` (portrait / banner / phone / product / emblem / backdrop / interaction) are all text-free, with deliberate negative space for later text-overlay-in-CSS workflows.

**Banner composition rule**: when generating wide banners meant for headline text overlay, the prompt MUST specify "deliberate negative space on the right two-thirds / left two-thirds / center" so the layout designer has somewhere to place text. The clean-imagery banner briefs encode 20 different mascot-positioning + negative-space patterns.

## Phase 9 — chain-iter (auto-pipeline)

When operator wants multiple consecutive iters ("do another 100 then 100 more"), chain via shell:

```bash
cat > /tmp/auto-fire-next.sh << EOF
#!/bin/bash
while kill -0 \$PREV_PID 2>/dev/null; do sleep 5; done
echo "previous fire exited; firing next"
cd "D:/Sinister Sanctum/projects/sinister-generator"
nohup python -X utf8 source/_fire_foo_100_pack_iterN.py > /tmp/fire-iterN.log 2>&1 < /dev/null &
EOF
nohup bash /tmp/auto-fire-next.sh > /tmp/auto-chain.log 2>&1 < /dev/null &
disown
```

The chain script:
- Polls the previous fire's python pid every 5s
- When it exits, fires the next iter immediately
- Writes the new pid + log path to `/tmp/fire-iterN.pid` + `/tmp/fire-iterN.path`

## Anti-patterns — what NOT to do

1. **Single-ref fire scripts** — always pull `max_refs=4` from library
2. **Parallel image-gen burst** — Defender quarantines on parallel writes; sequential + 1s sleep is the cure
3. **Hard-coded canonical paths in fire scripts** — use `get_endorsed_refs` so operator's `🪄 Use as Ref` clicks propagate automatically
4. **Style-suffix overrides** — let refs drive the style; pass `style_suffix=None` to nano_banana
5. **Labeling 💎 Great as "would use as-is"** — that's what 🪄 Use as Ref means
6. **Treating 📐 Size Off / 👤 Wrong Guy / 🎨 Wrong Style as `endorsed`** — they're partial-fails, NOT refs
7. **Burning 100 gens on a wrong canonical** — kill the fire as soon as operator flags wrong character / aesthetic
8. **Committing other-lane changes** — use `git commit -- <paths>` pathspec form to commit only your lane's files

## Cost discipline

- gemini-2.5-flash-image: ~$0.039 per image
- 100-pack: $3.90
- 3 iters (typical session): ~$12
- Operator authorization: ≤6 images soft cap per conservative-balance doctrine; anything above surfaces a PROGRESS entry with spend summary
- Failed gens (text-only response, EXCEPTION) still don't bill — they return `status != "ok"`, no image_bytes, no charge

## Session example — JKOR 2026-05-23

- **Phase 1-2** — JKOR already registered; refs `peeking-CORRECT` + `banner-CORRECT` already in `📥 Refs/`
- **Phase 3** — `_fire_jkor_100_pack.py` fired 100 variants. Mid-run, operator dropped new canonical → swapped refs + rewrote CHARACTER_LOCK → resumed at gen 30
- **Phase 4-5** — operator sorted ~25 gens; 8 in ✅ Good, 14 in ❌ Bad, 0 in 💎 Great initially
- **Phase 6** — read signals: 👤 Wrong Guy dominant → character refs need tightening
- **Phase 7** — `_fire_jkor_100_pack_iter2.py` fresh axes (pose × scene-backdrop). Switched to multi-ref via `get_endorsed_refs` mid-pack after operator flagged single-ref usage
- **Phase 8** — operator: "i want psychedelic not crown king" → rewrote DESIGN_DNA for iter3-snap to psychedelic; explicitly anti-patterned royal/cosmic backgrounds
- **Phase 9** — auto-chained iter3-snap from iter2 via `/tmp/auto-fire-iter3.sh`; then iter4-social from iter3-snap

**Cost:** ~$13 across 300+ gens. **Time:** ~3 hours including operator sort cycles.

## Reusable templates in the repo

- **`source/_fire_jkor_100_pack_clean.py`** — **CANONICAL imagery-only template** (post-18:29Z lesson). 7 families: portraits / banners (with deliberate negative-space) / phone-mockups / product-mockups / emblems / backdrops / interactions. NO baked text. **Start every new brand from this template.**
- `source/_fire_jkor_100_pack.py` — first-pass template with mixed text-baked content (kept for reference but DO NOT copy directly)
- `source/_fire_jkor_100_pack_iter2.py` — second-iter template with pose × scene axes
- `source/_fire_jkor_100_pack_iter3_snap.py` — selling-pack with text-baked families (DEPRECATED — superseded by `_clean.py`)
- `source/_fire_jkor_100_pack_iter4_social.py` — social-commerce with text-baked families (DEPRECATED — superseded by `_clean.py`)
- `source/_fire_jkor_pfp_iter1.py` — tight 5-variant iteration template (when you don't need a full 100)
- `source/sinister_generator/library/` — registry + feedback + generator API
- `source/sinister_generator/sorter_web/` — 9-button sort UI

When starting a new brand: `cp _fire_jkor_100_pack_clean.py _fire_NEW_100_pack.py`, find-replace `jkor` / `JOKR` → `new_slug` / `NEW_BRAND`, swap CANONICAL_REF + the variant brief lists, run. The DESIGN_DNA + CHARACTER_LOCK + REJECTION_ANTI_PATTERNS structure stays — only the content swaps.

## What to update when this workflow evolves

This doc + its index row in `_shared-memory/knowledge/_INDEX.md`. Version-stamp at the top, archive prior version to `_archive/`. Per operator's forever-upgrade doctrine: every meaningful refactor bumps the `Updated:` date.
