# Sinister Generator — memory index

> **Author:** RKOJ-ELENO :: 2026-05-23

Append-only catalog of what the generator has learned. Most-recent first.

## Per-project memory

| Project | Memory root | Brand spec |
|---|---|---|
| JKOR | `per-project/jkor/` | `per-project/jkor/BRAND.md` |
| Showmasters | `per-project/showmasters/` | (TBD — pull from `Showmasters Site/BRANDING/NANO-BANANA-INTEGRATION.md`) |
| JB Woodworks | `per-project/jb-woodworks/` | (TBD — pull from JB Woodworks v0.2.0 canonical brand pack) |

## Library + feedback loop (operator surface)

Desktop folders per brand — operator's review surface. Drag-drop ✅/❌/📥 is the training signal.

| Brand | Desktop folder | Learning state |
|---|---|---|
| JKOR | `C:\Users\Zonia\Desktop\JOKR\` | `learning/jkor.json` |
| Showmasters | `C:\Users\Zonia\Desktop\Showmasters\` (created on first gen) | `learning/showmasters.json` |
| JB Woodworks | `C:\Users\Zonia\Desktop\JB Woodworks\` (created on first gen) | `learning/jb-woodworks.json` |

Fleet-agent API: `from sinister_generator.library import generate; generate(brand=..., prompt=..., kind=...)`. See `docs/LIBRARY-AND-FEEDBACK.md` (agent-side) + `JOKR\README.md` (operator-side).

## Cross-project prompt libraries

| File | Purpose |
|---|---|
| `prompts-that-worked.md` | Prompts that produced a winner. Cite the output path + project + UTC. |
| `prompts-that-failed.md` | Prompts that missed. Cite WHY + what should've been different. |

## Brain entries (in `_shared-memory/knowledge/`)

- `nano-banana-gemini-image.md` — fleet doctrine for image generation

## Workflow

- `docs/WORKFLOW.md` — operator-vs-agent workflow audit + 7 lessons
- `docs/ANTI-SLOP.md` — visual review checklist
- `docs/BRAND-PACK-SPEC.md` — adding a new project
