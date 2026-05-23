# BRAND-PACK-SPEC — how to add a new project

> **Author:** RKOJ-ELENO :: 2026-05-23

When the fleet picks up a new project that needs image generation, follow these steps to register it.

## 1. Pick a slug

Lowercase, ASCII, dashes. Match the project's lane slug if it has one (`jkor`, `showmasters`, `jb-woodworks`). Bad: `JKOR Banners`, `joe_freeze`.

## 2. Create the output directory tree

```bash
mkdir -p "D:/Sinister Sanctum/projects/sinister-generator/outputs/<slug>/banners"
mkdir -p "D:/Sinister Sanctum/projects/sinister-generator/outputs/<slug>/social"
mkdir -p "D:/Sinister Sanctum/projects/sinister-generator/outputs/<slug>/_rejected"
# Add any image-type subfolders the project needs
```

Once created, they appear automatically under `C:\Users\Zonia\Desktop\Sinister Generator\<slug>\` via the NTFS junction.

## 3. Create the memory directory

```bash
mkdir -p "D:/Sinister Sanctum/projects/sinister-generator/memory/per-project/<slug>/reference"
mkdir -p "D:/Sinister Sanctum/projects/sinister-generator/memory/per-project/<slug>/_prompts"
```

Drop the canonical brand reference image(s) in `reference/`. Best: 1-3 reference PNGs at 1024×1024 or wider that capture the brand's character + palette + composition.

## 4. Write the brand spec

Copy a sibling project's `BRAND.md` (e.g. JKOR's) and adapt:

- Hero character / subject description
- Palette table (3-6 hex colors with role labels)
- Composition rules
- Anti-slop additions (project-specific reject criteria)
- Day-one use-cases

Save to `memory/per-project/<slug>/BRAND.md`.

## 5. Add a brand-lock helper to the wrapper

In `D:\Sinister Sanctum\tools\nano-banana\nano_banana\api.py`:

```python
NEW_STYLE = (
    " — <style suffix that DESCRIBES THE BRAND INCLUSIVELY> ..."
    " NO download icons, NO UI buttons, NO interface chrome ..."
)

def new_image(prompt, output_path, ref_images=None):
    return generate(prompt, output_path, ref_images=ref_images, style_suffix=NEW_STYLE)
```

Update `__init__.py` exports + add the brand to `cli.py`'s `--brand` choices + dispatch.

**Critical:** the style suffix must DESCRIBE the brand, not enforce a different one. Reread `docs/WORKFLOW.md` § Lesson 2 if unclear.

## 6. Update config

Add a row to `config/projects.json`.

## 7. Inbox-announce

Drop a `[BROADCAST]` in `_shared-memory/inbox/<lane-slug>/<UTC>-from-general-image-gen-ready.json`.

## 8. Commit on a per-agent branch

PROGRESS log. Don't push to `main` without operator OK.

## Anti-patterns

1. Skipping the brand-lock helper (every agent ends up writing the suffix inline, drifts).
2. Reusing a sibling project's helper (JKOR ≠ Showmasters).
3. No reference images in `reference/` (model drifts to training-data analogs).
4. No `_rejected/` folder (can't learn from past misses).
5. Slug with spaces or caps (breaks path handling).
