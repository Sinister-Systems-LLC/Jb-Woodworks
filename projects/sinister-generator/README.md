# Sinister Generator — fleet-wide image generation project

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Owner:** EVE on `general` lane (shared by all fleet agents)
> **Slug:** `sinister-generator`

## What this is

The Sinister fleet's canonical image-generation surface. Promoted from the `tools/nano-banana/` wrapper into a full project because we now have:

- **Multi-project routing** — JKOR / Showmasters / JB Woodworks (+ future lanes) all share one generator
- **Per-project memory** — what prompts worked, what failed, what the brand-lock should be
- **Per-project outputs** — organized by image type (banners / social / blog-heroes / thumbs / portfolio-teasers / etc) and a `_rejected/` bin
- **Operator satellite** — `Desktop\Sinister Generator\` is an NTFS junction to `outputs/`, so the operator browses finished images directly from the desktop
- **Anti-slop discipline** — visual review rules + cost discipline + reproducibility (every PNG carries a `.meta.json` sidecar)

The low-level SDK wrapper still lives at `D:\Sinister Sanctum\tools\nano-banana\`. This project is the **application layer** on top: brand-lock helpers, output routing, memory, audit.

## Directory map

```
projects/sinister-generator/
├── README.md                                  ← this file
├── source/                                    ← future Python package (not yet built)
│   └── sinister_generator/
│       ├── brands/                            ← per-project brand-lock modules
│       └── audit/                             ← anti-slop checks
├── config/
│   ├── projects.json                          ← registered image-gen projects
│   └── models.json                            ← available models + pricing
├── memory/
│   ├── _INDEX.md                              ← topic index
│   ├── prompts-that-worked.md                 ← cross-project prompt library
│   ├── prompts-that-failed.md
│   └── per-project/
│       ├── jkor/                              ← BRAND.md + reference/ + _prompts/
│       ├── showmasters/
│       └── jb-woodworks/
├── outputs/                                   ← junctioned to Desktop\Sinister Generator\
│   ├── jkor/{banners,social,thumbs,cutouts,_rejected}/
│   ├── showmasters/{banners,social,blog-heroes,service-illustrations,_rejected}/
│   ├── jb-woodworks/{banners,social,blog-heroes,portfolio-teasers,_rejected}/
│   └── _shared/references/
├── docs/
│   ├── WORKFLOW.md                            ← operator-vs-agent workflow audit
│   ├── BRAND-PACK-SPEC.md                     ← how to add a new project
│   └── ANTI-SLOP.md                           ← visual review rules
└── _archive/
```

## Quick start (any fleet agent)

```python
from nano_banana import jokr_image  # or smpl_image / jbw_image / generate

result = jokr_image(
    prompt="...",
    output_path=r"D:\Sinister Sanctum\projects\sinister-generator\outputs\JOKR\banners\next.png",
    ref_images=[r"D:\Sinister Sanctum\projects\sinister-generator\memory\per-project\jkor\reference\00-base-banner-original.png"],
)
print(result.status, result.output_path)
```

CLI:

```bash
python -m nano_banana \
  --prompt "..." \
  --output "D:/Sinister Sanctum/projects/sinister-generator/outputs/JOKR/banners/next.png" \
  --brand jkor \
  --ref "D:/Sinister Sanctum/projects/sinister-generator/memory/per-project/jkor/reference/00-base-banner-original.png"
```

## Operator surface (Desktop satellite)

`C:\Users\Zonia\Desktop\Sinister Generator\` is an NTFS junction to this project's `outputs/`. Open it from the desktop to browse every project's finished images by type. Files written via the wrapper appear instantly — no copy step.

## See also

- `docs/WORKFLOW.md` — lessons from the JKOR re-do incident
- `docs/ANTI-SLOP.md` — pre-save visual review checklist
- `docs/BRAND-PACK-SPEC.md` — adding a new project to the registry
- `tools/nano-banana/` — the underlying SDK wrapper
- `_shared-memory/knowledge/nano-banana-gemini-image.md` — fleet brain entry
