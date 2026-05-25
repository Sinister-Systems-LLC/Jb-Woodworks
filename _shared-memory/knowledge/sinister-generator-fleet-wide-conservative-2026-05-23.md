<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister Generator fleet-wide (conservative balance) - operator hard-canonical 2026-05-23

**Author:** RKOJ-ELENO :: 2026-05-23 (extracted from CLAUDE.md to reduce cold-start size; CLAUDE.md keeps a thin pointer)

## Operator verbatim (2026-05-23)

> "add to the start that all agents can use sinister geneartor if needed. just be conservative on the balance"

## Binding for every spawned EVE session

Sinister Generator is the fleet-wide image-gen project at `projects/sinister-generator/`, wrapper at `tools/nano-banana/nano_banana/api.py`. Available to EVERY lane that needs imagery: banners, social cards, brand visuals, mockups, doctrine illustrations, any LLM-driven design call. No per-lane gate; no operator-handoff for routine generation.

## Conservative balance rules

Gemini 2.5 Flash Image is paid (~$0.039/image). Hard rules:

1. **Pull from cache first** -- `projects/sinister-generator/outputs/` already has banner/social variants. Look before generating.
2. **One variant per concept first** -- generate v1, evaluate, iterate ONLY if the brief is unmet. Don't fan-out 5 variants on speculation.
3. **Cap per-task spend** -- <= 6 images per lane per task without surfacing to operator. Past 6, drop a row in `OPERATOR-ACTION-QUEUE.md` summarizing the spend before continuing.
4. **Re-use brand-locks** -- Showmasters / JB Woodworks / JKOR have brand-lock helpers; use them, don't reroll the brand from prose every call.
5. **Skip generation when text suffices** -- diagrams, ASCII art, or markdown tables often replace a generated image at zero cost.
6. **Log every generation** in the per-lane PROGRESS file (count + estimated $ spend) so operator can see the burn-rate per session.

## Green path (code)

```python
from nano_banana.api import generate, brand_lock_showmasters, brand_lock_jb_woodworks, brand_lock_jkor
# call with brief + reference image where relevant
# outputs land in projects/sinister-generator/outputs/<lane>/<ts>-<slug>.png
```

The wrapper is the policy-enforcement layer; agents call it directly, no MCP plumbing required.

## Composes with

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (precise verbs; don't claim image shipped if it's a draft)
- `forever-improve-review-doctrine-2026-05-24.md` (operator may flag generated images for replacement)
